"""Accounting is identical across action success, overrun, failure and resume."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from contest_config import ContestRunConfig
from contest_engine import _ContestEngine
from contest_manifest import ContestManifest, ManifestTask
from llm import LLMResponse, LLMToolCall


def engine(request, *, calls=4, tokens=100, turns=2, callback=None, saved=None):
    manifest = ContestManifest('usage-resume', 'arml_local', (
        ManifestTask('q1', 'q1', None, 'What is 6 times 7?', 'math', 1, False,
                     {'problem_id': 'q1', 'gold_label': {'expected_answer': '42'}}),))
    return _ContestEngine(manifest, lambda *_: 'Check.',
        ContestRunConfig('single_agent', 1, turns, max_api_calls=calls, max_tokens=tokens),
        action_request_fn=request, action_transport='native', checkpoint_callback=callback,
        session_checkpoint=saved[0] if saved else None, memory_checkpoint=saved[1] if saved else None)


@pytest.mark.parametrize('api_calls,output', [(0, 0), (1, 4096), (3, 4096)])
def test_spent_usage_is_never_clamped_or_forced_to_one(api_calls, output):
    def request(req):
        return LLMResponse('', 'mock', 'mock', usage={'api_calls': api_calls, 'output_tokens': output,
            'tool_error': 'Local failure' if api_calls == 0 else ''},
            tool_calls=() if api_calls == 0 else (LLMToolCall('select_problem', {'problem_id': 'q1'}),))
    result = engine(request, calls=2, turns=1).run()
    assert result['budget']['api_calls_used'] == api_calls
    assert result['budget']['tokens_used'] == output
    assert not any(e['kind'] == 'task_selected' for e in result['memory']['events'])


def test_exhausted_output_budget_has_no_phantom_api_calls():
    sent = []
    def request(req):
        sent.append(req)
        return LLMResponse('', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 100},
            tool_calls=(LLMToolCall('select_problem', {'problem_id': 'q1'}),))
    result = engine(request, calls=10, turns=3).run()
    assert len(sent) == result['budget']['api_calls_used'] == 1
    assert result['budget']['tokens_used'] == 100


@pytest.mark.parametrize('call_cap', [3, 4])
def test_failed_retry_checkpoint_retains_usage_and_resumes_only_remaining_allowance(call_cap):
    checkpoints, sent = [], []
    def save(state, memory):
        checkpoints.append((copy.deepcopy(state), memory))
    def request(req):
        sent.append(req)
        if len(sent) == 1:
            return LLMResponse('', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 5},
                tool_calls=(LLMToolCall('select_problem', {'problem_id': 'q1'}),))
        if len(sent) == 2:
            return LLMResponse('', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 7,
                'finish_reason': 'length', 'max_output_tokens': 8})
        error = RuntimeError('Fixture retry failure')
        error.usage = {'api_calls': 1, 'unknown_usage_attempts': 1}
        raise error
    with pytest.raises(RuntimeError) as caught:
        engine(request, calls=call_cap, callback=save).run()
    assert len(sent) == 3
    assert caught.value.usage['api_calls'] == 2  # This logical action's two attempts.
    assert caught.value.usage['output_tokens'] == 7
    saved = checkpoints[-1]
    assert saved[0]['budget']['api_calls_used'] == 3
    assert saved[0]['budget']['tokens_used'] == 12
    assert saved[0]['engine_state']['pending_turn']['agent'] == 'Agent_1'
    resumed_calls = []
    def resume(req):
        resumed_calls.append(req)
        assert req.metadata['max_transport_attempts'] == 1
        assert req.metadata['max_transport_output_tokens'] == 88
        return LLMResponse('', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 2},
            tool_calls=(LLMToolCall('work', {'problem_id': 'q1', 'content': 'Final answer: 42'}),))
    result = engine(resume, calls=call_cap, saved=saved).run()
    assert len(resumed_calls) == call_cap - 3
    assert result['budget']['api_calls_used'] == call_cap
    assert result['budget']['tokens_used'] == 12 + 2 * len(resumed_calls)


def test_local_request_failure_persists_zero_usage_for_resume():
    checkpoints = []
    def request(req):
        error = ValueError('Fixture local preparation failure')
        error.usage = {'api_calls': 0, 'output_tokens': 0}
        raise error
    with pytest.raises(RuntimeError):
        engine(request, callback=lambda state, memory: checkpoints.append(copy.deepcopy(state))).run()
    assert checkpoints[-1]['budget']['api_calls_used'] == 0
    assert checkpoints[-1]['budget']['tokens_used'] == 0


@pytest.mark.parametrize('variant,purpose', [
    ('otc', 'coach'), ('vallina_otc', 'coach'), ('centralized', 'leader_plan'),
    ('otc', 'private_think'), ('vallina_otc', 'private_think')])
def test_non_action_transport_failure_resumes_pending_phase_without_replaying_completed_calls(variant, purpose):
    from dataclasses import replace
    from types import SimpleNamespace
    from test_checkpoint_cursor import config, manifest
    checkpoints, sent = [], []
    prior = 1 if purpose == 'private_think' else 0
    cfg = replace(config(variant), max_api_calls=2 + prior, max_tokens=100)
    def fail(req):
        sent.append(req)
        if req.purpose == purpose:
            error = RuntimeError('Fixture connection failure')
            error.usage = {'api_calls': 1, 'output_tokens': 7, 'unknown_usage_attempts': 1}
            raise error
        assert req.purpose == 'coach'
        return LLMResponse('Check independently.', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 5})
    def make(request, saved=None):
        query = SimpleNamespace(supports_budgeted_requests=True, request=request, max_output_tokens=64)
        return _ContestEngine(manifest(), query, cfg,
            action_request_fn=lambda req: pytest.fail('Budget must stop ordinary actions'),
            action_transport='native', coach_query_fn=query,
            checkpoint_callback=lambda state, memory: checkpoints.append((copy.deepcopy(state), memory)),
            session_checkpoint=saved[0] if saved else None, memory_checkpoint=saved[1] if saved else None)
    with pytest.raises(RuntimeError, match='Non-action provider request failed'):
        make(fail).run()
    saved = checkpoints[-1]
    assert len(sent) == saved[0]['budget']['api_calls_used'] == 1 + prior
    assert saved[0]['budget']['tokens_used'] == 7 + 5 * prior
    resumed = []
    def succeed(req):
        resumed.append(req)
        assert req.purpose == purpose
        assert req.metadata['max_transport_attempts'] == 1
        assert req.metadata['max_transport_output_tokens'] == 93 - 5 * prior
        return LLMResponse('Check independently.', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 3})
    result = make(succeed, saved).run()
    assert len(resumed) == 1
    assert result['budget']['api_calls_used'] == 2 + prior
    assert result['budget']['tokens_used'] == 10 + 5 * prior


def test_legacy_action_callback_failure_saves_usage_before_resume():
    from test_checkpoint_cursor import manifest
    checkpoints = []
    cfg = ContestRunConfig('single_agent', 1, 1, max_api_calls=2, max_tokens=100)
    def fail(*args):
        raise RuntimeError('Fixture legacy request failure')
    def make(query, saved=None):
        return _ContestEngine(manifest(), query, cfg,
            checkpoint_callback=lambda state, memory: checkpoints.append((copy.deepcopy(state), memory)),
            session_checkpoint=saved[0] if saved else None, memory_checkpoint=saved[1] if saved else None)
    with pytest.raises(RuntimeError, match='Non-action provider request failed'):
        make(fail).run()
    saved = checkpoints[-1]
    assert saved[0]['budget']['api_calls_used'] == 1
    assert saved[0]['budget']['tokens_used'] == 0
    assert saved[0]['engine_state']['pending_turn']['agent'] == 'Agent_1'
    calls = []
    def succeed(*args):
        calls.append(args)
        return 'ACTION: rest | PAYLOAD: Check independently.'
    result = make(succeed, saved).run()
    assert len(calls) == 1
    assert result['budget']['api_calls_used'] == 2
    events = [e['payload'] for e in result['memory']['events'] if e['kind'] == 'model_usage']
    assert events[0]['unknown_usage_attempts'] == 1
