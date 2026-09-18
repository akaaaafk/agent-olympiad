"""Channel-aware regression for the GLM all-actions-failed run (no network)."""
import os
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from test_tinker_action_mechanism import Samples, request, run
from test_tinker_model_policy import TemplateTokenizer
import llm
from tinker_model_policy import model_policy


def test_truncated_selection_continues_same_prompt_and_exact_tokens():
    first = '{"name":"rest","arg'
    sampler = Samples((first, 10, 'length'), ('uments":{}}', 5, 'stop'))
    result = run(sampler, request(max_transport_attempts=2))
    assert result.tool_calls and result.tool_calls[0].name == 'rest'
    assert sampler.requests[0][:2] == sampler.requests[1][:2]
    assert sampler.requests[1][2]['continuation_tokens'] == list(map(ord, first))


def test_glm_uses_supported_low_effort_not_max_or_fake_disable():
    policy = model_policy('zai-org/GLM-5.3:peft:262144')
    assert policy.renderer == 'glm5_3_low_reasoning'
    assert not policy.supports_prefix and not policy.disable_thinking_kwarg


@pytest.mark.parametrize('stop_token', ['', '<|user|>'])
def test_glm_sdk_to_action_continues_thinking_without_executing_it(stop_token):
    import tinker
    tokenizer = TemplateTokenizer()
    chunks = [('Need to choose the allowed action. ', 'length'),
              ('Done.</think>{"name":"rest","arguments":{}}' + stop_token, 'stop')]
    client = Mock()
    client.get_tokenizer.return_value = tokenizer
    def sample(prompt, **kwargs):
        text, reason = chunks.pop(0)
        return SimpleNamespace(result=lambda: SimpleNamespace(sequences=[
            SimpleNamespace(tokens=tokenizer.encode(text), stop_reason=reason)]))
    client.sample.side_effect = sample
    with patch.dict(os.environ, {'TINKER_API_KEY': 'offline-test'}), patch.object(tinker, 'ServiceClient') as svc:
        svc.return_value.create_sampling_client.return_value = client
        fn = llm.make_tinker_request_fn('zai-org/GLM-5.3:peft:262144', max_output_tokens=6144)
        result = fn(request(max_transport_attempts=2))
    assert result.tool_calls and result.tool_calls[0].name == 'rest'
    calls = client.sample.call_args_list
    assert calls[0].kwargs['sampling_params'].max_tokens == 6144
    assert calls[1].args[0].to_ints() == (calls[0].args[0].to_ints()
        + tokenizer.encode('Need to choose the allowed action. '))
    assert result.usage['api_calls'] == 2
    assert all('Need to choose' not in row['text'] for row in result.usage['sampling_trace'])


def test_reasoning_only_stopped_reply_is_not_an_action():
    from tinker_model_policy import decode_response, make_text_renderer
    tokenizer = TemplateTokenizer()
    renderer = make_text_renderer(model_policy('zai-org/GLM-5.3'), tokenizer)
    # Even an apparently valid JSON call inside unfinished reasoning is private.
    tokens = tokenizer.encode('{"name":"rest","arguments":{}}<|user|>')
    assert decode_response(tokenizer, renderer, tokens) == ''


@pytest.mark.parametrize('model,renderer', [
    ('openai/gpt-oss-120b', 'gpt_oss_low_reasoning'),
    ('moonshotai/Kimi-K2-Thinking', 'kimi_k2'),
    ('moonshotai/Kimi-K2.5', 'kimi_k25_disable_thinking'),
    ('nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16', 'nemotron3_disable_thinking'),
    ('nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16', 'nemotron3_ultra_disable_thinking'),
    ('Qwen/Qwen3-235B-A22B-Instruct-2507', 'qwen3_instruct'),
    ('Qwen/Qwen3.8-27B', 'qwen3_8_disable_thinking'),
])
def test_additional_family_templates(model, renderer):
    from tinker_model_policy import make_text_renderer
    from tinker_vision import generation_input
    policy = model_policy(model)
    assert policy.renderer == renderer
    tokenizer = TemplateTokenizer()
    rendered = make_text_renderer(policy, tokenizer)
    prompt = generation_input(rendered, tokenizer, 'RULES', 'TASK', ())
    text = tokenizer.decode(prompt.to_ints())
    assert 'RULES' in text and 'TASK' in text


@pytest.mark.parametrize('model,reasoning,final', [
    ('openai/gpt-oss-120b', '<|channel|>analysis<|message|>PRIVATE',
     '<|end|><|start|>assistant<|channel|>final<|message|>'),
    ('moonshotai/Kimi-K2-Thinking', '<think>PRIVATE', '</think>'),
    ('zai-org/GLM-5.3', 'PRIVATE', '</think>'),
])
def test_reasoning_boundaries_even_without_returned_stop(model, reasoning, final):
    from tinker_model_policy import decode_response, make_text_renderer
    tokenizer = TemplateTokenizer()
    renderer = make_text_renderer(model_policy(model), tokenizer)
    assert decode_response(tokenizer, renderer, tokenizer.encode(reasoning)) == ''
    expected = '{"name":"rest","arguments":{}}'
    assert decode_response(tokenizer, renderer, tokenizer.encode(reasoning + final + expected)) == expected


def test_qwen_unknown_and_base_never_inherit_fake_thinking_switch():
    assert not model_policy('Qwen/Qwen3-Future-Thinking').supports_prefix
    assert not model_policy('Qwen/Qwen3-Future-Thinking').disable_thinking_kwarg
    with pytest.raises(ValueError, match='base model'):
        model_policy('Qwen/Qwen3-8B-Base')


def test_selection_checkpoint_resumes_only_identical_observation():
    first = '{"name":"rest","arg'
    req = request(max_transport_attempts=1)
    response = run(Samples((first, 10, 'length')), req)
    saved = json.loads(json.dumps(response.usage['unexecuted_action_draft']))
    assert saved['pending_selection']['tokens'] == list(map(ord, first))
    sampler = Samples(('uments":{}}', 5, 'stop'))
    resumed = run(sampler, replace(req, metadata={**req.metadata, 'unexecuted_action_draft': saved}))
    assert resumed.tool_calls[0].name == 'rest'
    assert sampler.requests[0][2]['continuation_tokens'] == list(map(ord, first))
    sampler = Samples(('{"name":"rest","arguments":{}}', 5, 'stop'))
    run(sampler, replace(req, user_prompt='New observation.', metadata={**req.metadata, 'unexecuted_action_draft': saved}))
    assert not sampler.requests[0][2].get('continuation_tokens')


def test_complete_looking_json_at_length_is_never_executed_and_batches_stay_atomic():
    call = '{"name":"rest","arguments":{}}'
    response = run(Samples((call, 10, 'length')), request(max_transport_attempts=1))
    assert not response.tool_calls
    response = run(Samples((call, 10, 'length'), (call, 10, 'stop')), request(max_transport_attempts=2))
    assert not response.tool_calls
    assert response.usage['output_tokens'] == 20 and response.usage['tool_error']


def test_unlimited_contest_metadata_still_has_bounded_text_continuation():
    sampler = Samples(('first ', 6, 'length'), ('second', 6, 'stop'))
    with patch.object(llm, 'make_tinker_caller', return_value=sampler):
        fn = llm.make_tinker_request_fn('test')
    result = fn(llm.LLMRequest('', '', metadata={'max_transport_attempts': None,
        'max_transport_output_tokens': None, 'max_output_tokens_override': None}))
    assert result.text == 'first second' and result.usage['api_calls'] == 2


def test_circuit_breaker_saves_costs_and_never_finalizes_failed_contest():
    from contest_config import ContestRunConfig
    from contest_engine import _ContestEngine
    from contest_manifest import ContestManifest, ManifestTask
    manifest = ContestManifest('circuit', 'arml_local', (
        ManifestTask('q', 'q', None, '6*7?', 'math', 1, False, {}),))
    config = ContestRunConfig('single_agent', 1, 10, max_api_calls=100, max_tokens=10000)
    checkpoints = []
    failed = Mock(return_value=llm.LLMResponse('', 'tinker', 'test', usage={
        'api_calls': 2, 'output_tokens': 7, 'tool_error': 'bad format', 'transport_recovery_managed': True}))
    engine = _ContestEngine(manifest, lambda *_: 'probe', config, action_request_fn=failed,
        action_transport='emulated', checkpoint_callback=lambda s, m: checkpoints.append((s, m)))
    with pytest.raises(RuntimeError, match='circuit open'):
        engine.run()
    assert failed.call_count == 3 and engine.transport_api_calls == 6
    saved, memory = checkpoints[-1]
    assert saved.get('final_summary') is None
    assert saved['engine_state']['phase'] == 'rounds'
    assert saved['engine_state']['state']['transport_abort_reason']
    assert engine.session.budget.tokens_used >= 21
    assert not any(t.submissions for t in engine.session.tasks)
    resumed = _ContestEngine(manifest, lambda *_: 'probe', config, action_request_fn=failed,
        action_transport='emulated', session_checkpoint=saved, memory_checkpoint=memory)
    with pytest.raises(RuntimeError, match='circuit open'):
        resumed.run()
    assert failed.call_count == 3  # Restarting a failed checkpoint must not spend again.
