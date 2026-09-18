"""Exercise production non-action calls without paid sampling."""
import json
import sys
from pathlib import Path

import pytest
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from llm import LLMResponse
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest


def prepare(tmp_path, variant='otc', **budgets):
    path = tmp_path / 'task.pdf'
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((60, 60), 'Write an evidence-based report.')
        pdf.save(path)
    return prepare_artifact_run(competition='vis_moot', task_pdf=path, output=tmp_path / 'run',
        provider='tinker', model='Qwen/Qwen3.6-35B-A3B', max_turns=1,
        system_variant=variant, **budgets)


def judge(request):
    return LLMResponse('{"score":4,"justification":"Fixture."}', 'mock', 'mock',
                       usage={'output_tokens': 8})


@pytest.mark.parametrize('variant', ['otc', 'vallina_otc', 'centralized'])
def test_remaining_budget_reaches_non_action_provider_and_usage_is_retained(tmp_path, variant):
    prepared = prepare(tmp_path, variant, max_api_calls=2, max_tokens=100)
    calls = []
    def agent(request):
        calls.append(request)
        assert request.metadata.get('max_transport_attempts') == 2
        assert request.metadata.get('max_transport_output_tokens') == 100
        assert request.metadata.get('max_output_tokens_override') == 100
        return LLMResponse('Check.', 'mock', 'mock', usage={'api_calls': 2, 'output_tokens': 100})
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    contest = json.loads(Path(result['contest_file']).read_text())
    assert len(calls) == 1
    assert contest['budget']['api_calls_used'] == 2
    assert contest['budget']['tokens_used'] == 100


def test_provider_overrun_is_recorded_and_stops_further_contestant_calls(tmp_path):
    prepared = prepare(tmp_path, max_api_calls=2, max_tokens=100)
    calls = []
    def agent(request):
        calls.append(request)
        return LLMResponse('Check.', 'mock', 'mock', usage={'api_calls': 3, 'output_tokens': 4096})
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    contest = json.loads(Path(result['contest_file']).read_text())
    assert len(calls) == 1
    assert contest['budget']['api_calls_used'] == 3
    assert contest['budget']['tokens_used'] == 4096
    assert any(e['kind'] == 'model_usage' and e['payload']['budget_overrun']
               for e in contest['memory']['events'])


def test_private_think_receives_budget_remaining_after_coach(tmp_path):
    prepared = prepare(tmp_path, max_api_calls=2, max_tokens=100)
    calls = []
    def agent(request):
        calls.append(request)
        return LLMResponse('Check.', 'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 10})
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    assert [r.purpose for r in calls] == ['coach', 'private_think']
    assert calls[1].metadata['max_transport_attempts'] == 1
    assert calls[1].metadata['max_transport_output_tokens'] == 90
    assert calls[1].metadata['max_output_tokens_override'] == 90
    contest = json.loads(Path(result['contest_file']).read_text())
    assert contest['budget']['api_calls_used'] == 2
    assert contest['budget']['tokens_used'] == 20


def test_perplexity_non_action_requests_bound_internal_retries(monkeypatch):
    import requests
    from llm import LLMRequest, make_perplexity_caller
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'fixture')
    sent = []
    def post(*args, **kwargs):
        sent.append(kwargs['json'])
        raise requests.exceptions.Timeout('Fixture timeout')
    monkeypatch.setattr(requests, 'post', post)
    caller = make_perplexity_caller('fixture')
    with pytest.raises(requests.exceptions.Timeout) as error:
        caller.request(LLMRequest('System', 'User', metadata={
            'max_transport_attempts': 1, 'max_transport_output_tokens': 31,
            'max_output_tokens_override': 50}))
    assert len(sent) == 1
    assert sent[0]['max_output_tokens'] == 31
    assert 'temperature' not in sent[0]
    assert error.value.usage == {'api_calls': 1, 'unknown_usage_attempts': 1}


def test_zero_output_budget_skips_non_action_call_and_refunds_reservation():
    from types import SimpleNamespace
    from text_call_budget import call_text
    budget = SimpleNamespace(max_api_calls=5, api_calls_used=2, max_tokens=100, tokens_used=100)
    def query(*args):
        pytest.fail('No provider request is permitted with zero remaining tokens')
    response = call_text(query, SimpleNamespace(budget=budget), '', '', purpose='private_think')
    assert not response.accepted
    assert budget.api_calls_used == 1
    assert budget.tokens_used == 100


@pytest.mark.parametrize('failure_usage', [
    {'finish_reason': 'length'}, {'tool_error': 'Fixture provider rejection'}])
def test_incomplete_non_action_response_is_charged_and_stops_run(tmp_path, failure_usage):
    prepared = prepare(tmp_path, max_api_calls=5, max_tokens=100)
    calls = []
    def agent(request):
        calls.append(request)
        return LLMResponse('Incomplete thought', 'mock', 'mock', usage={
            'api_calls': 1, 'output_tokens': 10, **failure_usage})
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    contest = json.loads(Path(result['contest_file']).read_text())
    assert len(calls) == 1
    assert contest['budget']['api_calls_used'] == 1
    assert contest['budget']['tokens_used'] == 10
    events = [e['payload'] for e in contest['memory']['events'] if e['kind'] == 'model_usage']
    assert len(events) == 1 and not events[0]['accepted']
