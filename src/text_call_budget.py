"""Budgeted non-action requests behind the existing two-string query interface.

The engine reserves one API call before entry. Structured adapters opt in via
``supports_budgeted_requests`` and ``request``; legacy custom text callbacks keep
their existing estimated accounting. Actual provider overruns are recorded, not
clamped away, and prevent further contestant calls.
"""
from llm import LLMRequest, LLMResponse
from llm_usage import response_usage, charge_reserved_usage, completion_error, failure_usage


class AccountedText(str):
    def __new__(cls, text, *, accepted, usage, reason='', request_failed=False):
        value = super().__new__(cls, text)
        value.accepted, value.usage, value.reason = accepted, usage, reason
        value.request_failed = request_failed
        return value


def call_text(query, session, system, user, *, purpose):
    budget = session.budget
    remaining_calls = None if budget.max_api_calls is None else budget.max_api_calls - budget.api_calls_used + 1
    remaining_tokens = None if budget.max_tokens is None else budget.max_tokens - budget.tokens_used
    if ((remaining_calls is not None and remaining_calls <= 0) or
            (remaining_tokens is not None and remaining_tokens <= 0)):
        budget.api_calls_used -= 1
        return AccountedText('', accepted=False, usage={'api_calls': 0, 'output_tokens': 0},
                             reason='No remaining model-call budget')
    if getattr(query, 'supports_budgeted_requests', False) is not True:
        try:
            return query(system, user)
        except Exception as exc:
            usage = charge_reserved_usage(budget, failure_usage(exc))
            return AccountedText('', accepted=False, usage=usage, request_failed=True,
                                 reason='Non-action provider request failed: ' + type(exc).__name__)
    metadata = {}
    if remaining_calls is not None:
        metadata['max_transport_attempts'] = remaining_calls
    if remaining_tokens is not None:
        metadata['max_transport_output_tokens'] = remaining_tokens
        metadata['max_output_tokens_override'] = min(remaining_tokens, query.max_output_tokens)
    request = LLMRequest(system, user, purpose=purpose, metadata=metadata)
    error = ''
    request_failed = False
    try:
        response = query.request(request)
        error = completion_error(response.usage)
        request_failed = bool(response.usage.get('transport_failed'))
    except Exception as exc:
        # Adapters may carry known usage through failures. Otherwise do not
        # invent a token count for an unsuccessful network attempt.
        response = LLMResponse('', 'unknown', 'unknown', usage=failure_usage(exc))
        error = 'Non-action provider request failed: ' + type(exc).__name__
        request_failed = True
    calls = response.usage.get('api_calls', 1)
    if type(calls) is not int or calls < 0:
        error = error or 'Invalid provider API usage'
    usage = charge_reserved_usage(budget, response_usage(response))
    overrun = usage['budget_overrun']
    return AccountedText('' if error or overrun else response.text,
                         accepted=not (error or overrun), usage=usage,
                         request_failed=request_failed,
                         reason=error or ('Provider exceeded the requested budget' if overrun else ''))
