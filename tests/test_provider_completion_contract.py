"""Exercise real provider adapters and all consumers with offline wire responses."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from llm import LLMRequest, resolve_request_fn
from action_transport import request_single_action
from text_call_budget import call_text
from contest_reporting import metered_judge
from evaluation.models import Criterion, Rubric, EvaluationError
from evaluation.structured_judge import evaluate_structured_response

PROVIDERS = ['openai', 'perplexity', 'glm', 'openagents', 'vectorengine',
             'openai_compatible', 'deepseek', 'anthropic', 'gemini']
TOOL = {'type': 'function', 'name': 'work', 'parameters': {'type': 'object',
        'properties': {'content': {'type': 'string'}}, 'required': ['content']}}
SCORE = json.dumps(dict(criteria=[dict(id='a', score=1, max_score=1, evidence=['Fixture'],
    justification='Supported.', confidence=1, observable=True)],
    total_score=1, max_score=1, warnings=[], limitations=[]))


def adapter(monkeypatch, provider, outcome, *, action=False):
    import openai
    import requests
    for name in ('OPENAI', 'PERPLEXITY', 'OPENAGENTS', 'VECTORENGINE', 'OPENAI_COMPATIBLE',
                 'DEEPSEEK', 'ANTHROPIC', 'GEMINI'):
        monkeypatch.setenv(name + '_API_KEY', 'offline-fixture')
    monkeypatch.setenv('OPENAI_COMPATIBLE_BASE_URL', 'https://fixture.invalid/v1')
    args = '{invalid' if outcome == 'malformed' else json.dumps({'content': 'Final answer: 42'})
    usage = {'input_tokens': 10, 'output_tokens': 20}
    if provider in {'openai', 'perplexity'}:
        output = ([{'type': 'function_call', 'name': 'work', 'arguments': args, 'call_id': 'fixture'}]
                  if action else [{'type': 'message', 'content': [{'type': 'output_text', 'text': SCORE}]}])
        raw = dict(output=output, usage=usage,
                   status='incomplete' if outcome in {'length', 'refusal'} else 'completed')
        if raw['status'] == 'incomplete':
            raw['incomplete_details'] = {'reason': 'max_output_tokens' if outcome == 'length' else 'content_filter'}
    elif provider == 'anthropic':
        content = ([{'type': 'tool_use', 'name': 'work', 'id': 'fixture',
                     'input': args if outcome == 'malformed' else json.loads(args)}]
                   if action else [{'type': 'text', 'text': SCORE}])
        raw = dict(content=content, usage=usage, stop_reason={'length': 'max_tokens', 'refusal': 'refusal'}
                   .get(outcome, 'tool_use' if action else 'end_turn'))
    elif provider == 'gemini':
        parts = ([{'functionCall': {'name': 'work',
                   'args': args if outcome == 'malformed' else json.loads(args)}}]
                 if action else [{'text': SCORE}])
        raw = dict(candidates=[dict(content={'parts': parts},
            finishReason={'length': 'MAX_TOKENS', 'refusal': 'SAFETY'}.get(outcome, 'STOP'))],
            usageMetadata={'promptTokenCount': 10, 'candidatesTokenCount': 17, 'thoughtsTokenCount': 3})
    else:
        message = {'content': None if action else SCORE}
        if action:
            message['tool_calls'] = [{'id': 'fixture', 'type': 'function',
                                     'function': {'name': 'work', 'arguments': args}}]
        raw = dict(choices=[dict(message=message,
            finish_reason={'length': 'length', 'refusal': 'content_filter'}
                          .get(outcome, 'tool_calls' if action else 'stop'))],
            usage={'prompt_tokens': 10, 'completion_tokens': 20})
    wire = SimpleNamespace(model_dump=lambda: raw, output_text='' if action else SCORE,
                           usage=SimpleNamespace(model_dump=lambda: raw.get('usage', {})))
    sent = []
    def create(**kwargs):
        sent.append(kwargs)
        return wire
    sdk = SimpleNamespace(responses=SimpleNamespace(create=create),
                          chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: sdk)
    def post(*args, **kwargs):
        sent.append(kwargs['json'])
        return SimpleNamespace(ok=True, status_code=200, json=lambda: raw)
    monkeypatch.setattr(requests, 'post', post)
    caller = resolve_request_fn('openai' if provider == 'glm' else provider,
        'glm-fixture' if provider == 'glm' else 'fixture', max_output_tokens=64)
    return caller, sent


@pytest.mark.parametrize('provider', PROVIDERS)
@pytest.mark.parametrize('outcome', ['success', 'length', 'refusal', 'malformed'])
def test_action_consumers_reject_failed_completions_and_preserve_usage(monkeypatch, provider, outcome):
    caller, sent = adapter(monkeypatch, provider, outcome, action=True)
    response = request_single_action(caller, LLMRequest('System', 'User', purpose='contest_action',
        tools=(TOOL,), tool_choice='required', metadata={
            'max_transport_attempts': 2, 'max_transport_output_tokens': 5000}))
    assert len(response.tool_calls) == (1 if outcome == 'success' else 0)
    assert len(sent) == (2 if outcome == 'length' else 1)
    assert response.usage['api_calls'] == len(sent)
    assert response.usage['output_tokens'] == 20 * len(sent)
    for payload in sent:
        limit = payload.get('max_output_tokens', payload.get('max_tokens',
                            payload.get('generationConfig', {}).get('maxOutputTokens')))
        assert limit == 64  # Total budget must not become the per-call output allowance.


@pytest.mark.parametrize('provider', PROVIDERS)
@pytest.mark.parametrize('outcome', ['success', 'length', 'refusal'])
def test_non_action_consumers_accept_only_finished_text(monkeypatch, provider, outcome):
    caller, sent = adapter(monkeypatch, provider, outcome)
    query = Mock()
    query.supports_budgeted_requests = True
    query.request = caller
    query.max_output_tokens = 64
    budget = SimpleNamespace(max_api_calls=2, api_calls_used=1, max_tokens=1000, tokens_used=0)
    response = call_text(query, SimpleNamespace(budget=budget), 'System', 'User', purpose='private_think')
    assert response.accepted == (outcome == 'success')
    assert bool(response) == (outcome == 'success')
    assert len(sent) == budget.api_calls_used == 1
    assert budget.tokens_used == 20


@pytest.mark.parametrize('provider', PROVIDERS)
@pytest.mark.parametrize('outcome', ['success', 'length', 'refusal'])
def test_judges_do_not_accept_valid_json_from_an_incomplete_response(monkeypatch, provider, outcome):
    caller, sent = adapter(monkeypatch, provider, outcome)
    state = {}
    request = LLMRequest('Grade', 'Rubric', purpose='evaluation')
    options = dict(rubric=Rubric('r', 'Fixture', 1, (Criterion('a', 'A', 1, 'A'),)),
                   evaluator_id='test', evaluator_version='1', prompt_version='1')
    metered = metered_judge(caller, state)
    if outcome == 'success':
        result = evaluate_structured_response(metered, request, **options)
        assert result.total_score == 1
    else:
        with pytest.raises(EvaluationError):
            evaluate_structured_response(metered, request, **options)
    assert len(sent) == (3 if outcome == 'length' else 1)
    assert state['evaluation_usage']['api_calls'] == len(sent)
    assert state['evaluation_usage']['output_tokens'] == 20 * len(sent)


@pytest.mark.parametrize('provider', PROVIDERS)
@pytest.mark.parametrize('mime', ['application/pdf', 'application/octet-stream'])
def test_local_attachment_failure_has_zero_api_calls(monkeypatch, tmp_path, provider, mime):
    from llm import LLMAttachment
    caller, sent = adapter(monkeypatch, provider, 'success')
    state = {}
    with pytest.raises((ValueError, FileNotFoundError)):
        metered_judge(caller, state)(LLMRequest('S', 'U', purpose='evaluation',
            attachments=(LLMAttachment(tmp_path / 'missing.pdf', mime),)))
    assert not sent
    assert state['evaluation_usage']['api_calls'] == 0
    assert state['evaluation_usage']['unmetered_calls'] == 0


@pytest.mark.parametrize('remaining', [1, 2, 5])
def test_failed_gateway_retries_are_all_metered(monkeypatch, remaining):
    import openai
    import llm
    caller, _ = adapter(monkeypatch, 'openagents', 'success')
    # Construct a new real adapter with a failing SDK transport.
    sent = []
    def create(**kwargs):
        sent.append(kwargs)
        error = RuntimeError('Fixture gateway timeout')
        error.status_code = 504
        raise error
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm.time, 'sleep', lambda _: None)
    caller = resolve_request_fn('openagents', 'fixture', max_output_tokens=64)
    state = {}
    with pytest.raises(RuntimeError):
        metered_judge(caller, state)(LLMRequest('S', 'U', purpose='evaluation',
            metadata={'max_transport_attempts': remaining}))
    expected = min(remaining, 3)
    assert len(sent) == state['evaluation_usage']['api_calls'] == expected
    assert state['evaluation_usage']['unmetered_calls'] == expected
    assert state['evaluation_usage']['output_tokens'] == 0
