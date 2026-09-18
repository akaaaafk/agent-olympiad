"""Normalize reported model usage without inventing tokens or zero-call attempts."""
import math
import json
from functools import wraps

from contest_budget import estimate_tokens


def _count(value):
    return type(value) is int and value >= 0


def _tokens(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def normalized_usage(reported):
    reported = reported if isinstance(reported, dict) else {}
    calls = reported.get('api_calls', 1)
    valid_calls = _count(calls)
    calls = calls if valid_calls else 1
    input_tokens = reported.get('input_tokens', reported.get('prompt_tokens'))
    output_tokens = reported.get('output_tokens', reported.get('completion_tokens'))
    unknown = reported.get('unknown_usage_attempts', 0)
    unknown = unknown if _count(unknown) else 0
    # Missing output and an explicit unknown-attempt counter describe the same
    # failure; do not count it twice when multiple wrappers aggregate usage.
    unknown = max(unknown, int(not valid_calls or (calls > 0 and not _tokens(output_tokens))))
    return dict(api_calls=calls,
                input_tokens=input_tokens if _tokens(input_tokens) else 0,
                output_tokens=output_tokens if _tokens(output_tokens) else 0,
                unknown_usage_attempts=unknown)


def response_usage(response):
    """One contestant response, retaining measured or explicitly estimated output."""
    reported = dict(response.usage or {})
    usage = normalized_usage(reported)
    tokens = reported.get('output_tokens', reported.get('completion_tokens'))
    basis = reported.get('tokens_basis') or 'provider_reported'
    if not _tokens(tokens):
        visible = response.text or ''
        if response.tool_calls:
            visible += json.dumps([{'name': c.name, 'arguments': c.arguments} for c in response.tool_calls])
        usage['output_tokens'] = estimate_tokens(visible) if usage['api_calls'] else 0
        basis = 'estimated_visible_text' if usage['api_calls'] else 'known_no_call'
    return {**reported, **usage, 'tokens_basis': basis}


def sum_usage(attempts):
    """Keep known usage from every attempt, including partially metered failures."""
    total = dict(api_calls=0, input_tokens=0, output_tokens=0, unknown_usage_attempts=0)
    for attempt in attempts:
        for key, value in normalized_usage(attempt).items():
            total[key] += value
    for alias in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
        if attempts and all(_tokens(row.get(alias)) for row in attempts):
            total[alias] = sum(row[alias] for row in attempts)
    return total


def failure_usage(exc):
    reported = getattr(exc, 'usage', None)
    return {**(reported if isinstance(reported, dict) else {}), **normalized_usage(reported)}


def charge_reserved_usage(budget, usage, *, reserved_calls=1):
    """Record already-spent usage in full, then report a requested-budget overrun."""
    row = normalized_usage(usage)
    budget.api_calls_used += row['api_calls'] - reserved_calls
    budget.tokens_used += row['output_tokens']
    overrun = ((budget.max_api_calls is not None and budget.api_calls_used > budget.max_api_calls) or
               (budget.max_tokens is not None and budget.tokens_used > budget.max_tokens))
    return {**usage, **row, 'budget_overrun': overrun}


def completion_error(usage):
    if usage.get('tool_error'):
        return str(usage['tool_error'])
    reason = usage.get('finish_reason')
    if reason in {'length', 'max_tokens', 'max_length', 'MAX_TOKENS', 'max_output_tokens',
                  'content_filter', 'refusal', 'incomplete', 'failed', 'cancelled', 'queued', 'in_progress'}:
        return f'Incomplete or rejected completion ({reason})'
    return ''


class ModelRequestError(RuntimeError):
    """A failed transport attempt with all usage accumulated before the failure."""
    def __init__(self, message, usage):
        super().__init__(message)
        self.usage = usage


def local_preflight(function):
    """Attach explicit zero sampling usage to a local-only preparation failure."""
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            if not isinstance(getattr(exc, 'usage', None), dict):
                exc.usage = dict(api_calls=0, output_tokens=0, unknown_usage_attempts=0)
            raise
    return call
