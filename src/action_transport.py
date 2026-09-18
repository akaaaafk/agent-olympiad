"""Validate one contest action before handing any call to the executor."""
from __future__ import annotations

import json
from dataclasses import replace

from llm import LLMRequest, LLMResponse, RequestFn
from llm_usage import response_usage, sum_usage, completion_error, failure_usage, ModelRequestError
from argument_limits import violations, violation_text, native_rewrite_prompts, valid_replacement
from answer_content import action_content_error

VERSION = 3


def action_output_tokens(response: LLMResponse) -> int:
    """Preserve reported zeroes; estimate visible output only when usage is absent."""
    return response_usage(response)['output_tokens']


def request_single_action(request_fn: RequestFn, request: LLMRequest) -> LLMResponse:
    """Repair a multi-call or truncated response once, charging both generations.

    None of an ambiguous batch executes. The model selects one action against
    the unchanged state; rejected calls remain available for trace auditing.
    Provider/emulation failures with zero calls retain their existing handling.
    """
    # A provider hint reduces invalid generations; the atomic validation below
    # remains authoritative even when a backend ignores this constraint.
    request = replace(request, parallel_tool_calls=False)
    limit = request.metadata.get("max_transport_attempts")
    budget = limit if isinstance(limit, int) else None
    calls_used = tokens_used = retries = 0
    rejected = []
    attempts = []
    repair_lock = None
    command_reselection = False
    remaining_output = request.metadata.get("max_transport_output_tokens")
    if budget == 0 or remaining_output == 0:
        return LLMResponse("", "", "", usage={"api_calls": 0, "output_tokens": 0,
                           "tool_error": "Action transport budget exhausted"})
    initial_metadata = dict(request.metadata)
    if remaining_output is not None and initial_metadata.get('max_output_tokens_override') is not None:
        initial_metadata["max_output_tokens_override"] = min(int(remaining_output),
            int(initial_metadata.get("max_output_tokens_override") or remaining_output))
    current = replace(request, metadata=initial_metadata)
    for attempt in range(2):
        try:
            response = request_fn(current)
            response = replace(response, usage=response_usage(response))
        except Exception as exc:
            usage = {**failure_usage(exc), **sum_usage(attempts + [failure_usage(exc)]),
                     'tool_retries': retries, 'rejected_tool_calls': rejected,
                     'transport_failed': True}
            raise ModelRequestError('Action provider request failed: ' + type(exc).__name__, usage) from exc
        attempts.append(response.usage)
        exhausted = response.usage.get("finish_reason") == "length"
        if completion_error(response.usage) and not exhausted:
            response = replace(response, tool_calls=())
        length_rows = []
        command_error = None
        replacement_error = ''
        if len(response.tool_calls) == 1 and not exhausted:
            call = response.tool_calls[0]
            command_error = action_content_error(call.name, call.arguments, request.metadata)
            length_rows = violations(call.name, call.arguments, request.metadata)
            if command_reselection:
                from llm import _validate_emulated_tool_call
                replacement_error = _validate_emulated_tool_call(call, request.tools) or ''
            if repair_lock:
                from llm import _validate_emulated_tool_call
                original, prior_rows, tool = repair_lock
                if (not valid_replacement(original, call, prior_rows, tool)
                        or _validate_emulated_tool_call(call, request.tools)):
                    replacement_error = 'Length repair changed fixed arguments/action or violated the schema; nothing executed.'
        total_used = sum_usage(attempts)
        over_budget = ((budget is not None and total_used['api_calls'] > budget)
            or (remaining_output is not None and total_used['output_tokens'] > remaining_output))
        if replacement_error or over_budget:
            response = replace(response, tool_calls=(), usage={**response.usage,
                'tool_error': replacement_error or 'Provider exceeded the action recovery budget; nothing executed.'})
            break
        if response.usage.get('transport_recovery_managed') is True:
            # Staged emulation owns one shared budget across selection, raw
            # body sampling and continuations. Never restart its exhausted loop.
            if exhausted or len(response.tool_calls) > 1 or length_rows or command_error:
                return replace(response, tool_calls=(), usage={**response.usage,
                    'tool_error': response.usage.get('tool_error') or
                    command_error or (violation_text(call.name, length_rows) if length_rows else
                     'Incomplete or multiple actions rejected; no partial action executed.')})
            return response
        if len(response.tool_calls) <= 1 and not exhausted and not length_rows and not command_error and attempt == 0:
            return response
        calls_used += response.usage['api_calls']
        serialized = json.dumps([{"name": c.name, "arguments": c.arguments}
                                 for c in response.tool_calls], ensure_ascii=False)
        tokens_used += action_output_tokens(response)
        retries += max(0, int(response.usage.get("tool_retries") or 0))
        if len(response.tool_calls) <= 1 and not exhausted and not length_rows and not command_error:
            break
        rejected.extend({"call_id": c.call_id, "name": c.name,
                         "arguments": c.arguments, "executed": False,
                         "rejection_reason": "output_token_limit" if exhausted else "answer_is_tool_command" if command_error else "argument_character_limit" if length_rows else "multiple_actions_in_one_response",
                         **({'length_violations': length_rows} if length_rows else {})}
                        for c in response.tool_calls)
        if attempt == 1 or (budget is not None and calls_used >= budget):
            response = replace(response, tool_calls=(), usage={
                **response.usage,
                "tool_error": command_error or (violation_text(call.name, length_rows) if length_rows else
                               "Output token limit reached; no partial action executed." if exhausted else
                               "Response must contain exactly one action; no calls from the batch executed."),
            })
            break
        remaining = request.metadata.get("max_transport_output_tokens")
        remaining = None if remaining is None else max(0, int(remaining) - tokens_used)
        if remaining == 0:
            response = replace(response, tool_calls=(), usage={**response.usage,
                "tool_error": "Output token budget exhausted; no partial action executed."})
            break
        retries += 1
        if command_error:
            command_reselection = True
            current = replace(request, user_prompt=request.user_prompt +
                '\n\nACTION RESPONSE REJECTED\n' + command_error +
                '\nThe state is unchanged. Choose exactly one currently available action. '
                'The rejected body is data, not a tool result:\n' + serialized,
                metadata={**request.metadata,
                    'max_transport_attempts': None if budget is None else budget - calls_used,
                    'max_transport_output_tokens': remaining,
                    **({'max_output_tokens_override': min(remaining,
                        int(response.usage.get('max_output_tokens') or remaining))}
                       if remaining is not None else {})})
            continue
        if length_rows:
            from llm import _validate_emulated_tool_call
            tool = next((t for t in request.tools if t.get('name') == call.name), None)
            if tool is None or _validate_emulated_tool_call(call, request.tools):
                response = replace(response, tool_calls=(), usage={**response.usage,
                    'tool_error': 'Overlimit call also violates the selected schema; nothing executed.'})
                retries -= 1
                break
            repair_lock = call, length_rows, tool
            system, user = native_rewrite_prompts(call.name, call.arguments, length_rows)
            current = replace(request, system_prompt=system, user_prompt=user,
                tools=(tool,), tool_choice='required', attachments=(),
                metadata={**request.metadata, 'argument_length_recovery': True,
                    'max_transport_attempts': None if budget is None else budget - calls_used,
                    'max_transport_output_tokens': remaining,
                    **({'max_output_tokens_override': min(remaining,
                        int(response.usage.get('max_output_tokens') or remaining))}
                       if remaining is not None else {})})
            continue
        if exhausted:
            previous_limit = int(response.usage.get("max_output_tokens") or 8192)
            retry_ceiling = int(response.usage.get("max_retry_output_tokens") or previous_limit)
            increased_limit = min(previous_limit * 2, retry_ceiling)
            if remaining is not None:
                increased_limit = min(increased_limit, remaining)
            if increased_limit <= 0:
                response = replace(response, tool_calls=(), usage={**response.usage,
                    "tool_error": "Output token budget exhausted; no partial action executed."})
                retries -= 1
                break
            current = replace(request, user_prompt=request.user_prompt +
                "\n\nACTION RESPONSE REJECTED\nYour reasoning output hit its token limit. "
                "No action executed. Return exactly one available function call with concise arguments. "
                "Do not include a solution preamble or reasoning outside the call JSON.",
                metadata={**request.metadata, "max_output_tokens_override": increased_limit,
                          "action_length_recovery": True,
                          "max_transport_output_tokens": remaining,
                          "max_transport_attempts": None if budget is None else budget - calls_used})
            continue
        current = replace(request, user_prompt=(
            request.user_prompt
            + "\n\nACTION RESPONSE REJECTED\n"
            + "You returned multiple function calls. No action from that response executed. "
            + "The state is unchanged. Select exactly one available function and call it once."
            + "\nYour rejected calls (unexecuted proposals, not tool results):\n"
            + serialized
            + "\nReturn only your selected single call, then wait for its result."
        ), metadata={**request.metadata,
                     "max_transport_output_tokens": remaining,
                     **({"max_output_tokens_override": min(remaining,
                         int(response.usage.get("max_output_tokens") or remaining))}
                        if remaining is not None else {}),
                     "max_transport_attempts": None if budget is None else budget - calls_used})
    return replace(response, usage={
        **response.usage, **sum_usage(attempts),
        "tool_retries": retries, "rejected_tool_calls": rejected,
    })
