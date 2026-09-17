"""Bounded retries for invalid rubric responses, never for low scores."""

import logging
from dataclasses import replace

from llm import LLMRequest, RequestFn
from .models import EvaluationError, EvaluationResult, parse_evaluation_payload


def evaluate_structured_response(
    request_fn: RequestFn, request: LLMRequest, **parse_options,
) -> EvaluationResult:
    """Accept the first valid judgment; at most two format/schema retries.

    The original task, rubric and attachments accompany every attempt. Provider
    exceptions propagate to the provider's own retry policy. Failed-response
    usage is retained instead of reporting only the successful call.
    """
    attempts = []
    feedback = ''
    for attempt in range(1, 4):
        current = replace(
            request,
            system_prompt=request.system_prompt + (
                '\nReturn one complete JSON object. Escape every literal backslash '
                'inside JSON strings as two backslashes, including LaTeX commands. '
                'Use concise evidence and justifications so the full object fits.'
            ),
            user_prompt=request.user_prompt + feedback,
            metadata={**request.metadata, 'evaluation_attempt': attempt},
        )
        response = request_fn(current)
        attempts.append(dict(response.usage or {}))
        try:
            result = parse_evaluation_payload(
                response.text, model=response.model, usage=response.usage, **parse_options,
            )
        except EvaluationError as exc:
            if attempt == 3:
                raise EvaluationError(
                    f'Evaluator returned invalid output after 3 attempts: {exc}'
                ) from exc
            logging.getLogger(__name__).warning(
                'Judge output failed validation (attempt %s/3); retrying only the judge: %s',
                attempt, exc,
            )
            feedback = (
                '\n\nYour previous response failed output validation: ' + str(exc) +
                '\nReturn a complete replacement JSON object matching the required schema '
                'and exact rubric IDs, maxima and score ranges. No Markdown or extra text. '
                'Judge the same supplied submission; do not change the rubric.'
            )
            continue
        if len(attempts) > 1:
            usage = dict(response.usage or {})
            # Only aggregate a token counter when all attempts reported it.
            for key in ('input_tokens', 'output_tokens', 'total_tokens',
                        'prompt_tokens', 'completion_tokens'):
                if all(isinstance(row.get(key), (int, float)) for row in attempts):
                    usage[key] = sum(row[key] for row in attempts)
                else:
                    usage.pop(key, None)
            usage.update(api_calls=sum(row.get('api_calls', 1) for row in attempts),
                         format_retries=len(attempts) - 1, attempts=attempts)
            result.usage = usage
            result.warnings.append(
                f'Judge output required {len(attempts) - 1} validation retry attempt(s).'
            )
        return result
    raise AssertionError('Unreachable: rubric attempts exhausted')
