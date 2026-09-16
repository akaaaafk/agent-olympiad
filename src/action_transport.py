"""Validate one contest action before handing any call to the executor."""
from __future__ import annotations

import json
from dataclasses import replace

from contest_budget import estimate_tokens
from llm import LLMRequest, LLMResponse, RequestFn


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
    input_tokens_used = 0
    rejected = []
    current = request
    for attempt in range(2):
        response = request_fn(current)
        exhausted = response.usage.get("finish_reason") == "length"
        if len(response.tool_calls) <= 1 and not exhausted and attempt == 0:
            return response
        calls_used += max(1, int(response.usage.get("api_calls") or 1))
        serialized = json.dumps([{"name": c.name, "arguments": c.arguments}
                                 for c in response.tool_calls], ensure_ascii=False)
        tokens_used += int(response.usage.get("output_tokens")
                           or response.usage.get("completion_tokens")
                           or estimate_tokens(serialized or response.text))
        input_tokens_used += int(response.usage.get("input_tokens") or response.usage.get("prompt_tokens") or 0)
        retries += max(0, int(response.usage.get("tool_retries") or 0))
        if len(response.tool_calls) <= 1 and not exhausted:
            break
        rejected.extend({"call_id": c.call_id, "name": c.name,
                         "arguments": c.arguments, "executed": False,
                         "rejection_reason": "output_token_limit" if exhausted else "multiple_actions_in_one_response"}
                        for c in response.tool_calls)
        if attempt == 1 or (budget is not None and calls_used >= budget):
            response = replace(response, tool_calls=(), usage={
                **response.usage,
                "tool_error": ("Output token limit reached; no partial action executed." if exhausted else
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
        if exhausted:
            previous_limit = int(response.usage.get("max_output_tokens") or 8192)
            increased_limit = previous_limit
            if remaining is not None:
                increased_limit = min(increased_limit, remaining)
            if increased_limit <= 0:
                response = replace(response, tool_calls=(), usage={**response.usage,
                    "tool_error": "Output token budget exhausted; no partial action executed."})
                retries -= 1
                break
            current = replace(request, user_prompt=request.user_prompt +
                "\n\nACTION RESPONSE REJECTED\nYour reasoning output hit its token limit. "
                "No action executed. Return exactly one available function call with concise arguments.",
                metadata={**request.metadata, "max_output_tokens_override": increased_limit,
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
                     **({"max_output_tokens_override": min(remaining,
                         int(response.usage.get("max_output_tokens") or remaining))}
                        if remaining is not None else {}),
                     "max_transport_attempts": None if budget is None else budget - calls_used})
    return replace(response, usage={
        **response.usage, "api_calls": calls_used, "output_tokens": tokens_used,
        "input_tokens": input_tokens_used,
        **({"completion_tokens": tokens_used} if "completion_tokens" in response.usage else {}),
        **({"prompt_tokens": input_tokens_used} if "prompt_tokens" in response.usage else {}),
        **({"total_tokens": input_tokens_used + tokens_used} if "total_tokens" in response.usage else {}),
        "tool_retries": retries, "rejected_tool_calls": rejected,
    })
