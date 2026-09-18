"""Stopped Qwen replies must get an editing task, not the original solving task.

The captured outputs are real. The responsive rewrite below is an offline
protocol fixture, not a claim that a live model always obeys a length request.
"""
import json
from dataclasses import replace
from pathlib import Path

from test_tinker_action_mechanism import Samples, request, run

FIXTURE = json.loads((Path(__file__).parent / 'fixtures' /
                     'qwen_otc_body_repeat_20260918.json').read_text(encoding='utf8'))
ORIGINAL_TASK = 'ORIGINAL_SOLVING_TASK: solve the current problem and explain the derivation.'
ORIGINAL_ROLE = 'ORIGINAL_CONTEST_ROLE: select an action and coordinate the team.'


def failed_request():
    tools = ({'name': 'work', 'parameters': {'type': 'object', 'properties': {
        'problem_id': {'type': 'string', 'enum': ['arml_local_2012:9']},
        'content': {'type': 'string'}}, 'required': ['problem_id', 'content'],
        'additionalProperties': False}},)
    return replace(request(max_transport_attempts=5,
        action_argument_limits={'work': {'content': 2400}}),
        tools=tools, system_prompt=ORIGINAL_ROLE, user_prompt=ORIGINAL_TASK)


class RepeatingBody(Samples):
    supports_prefix = True

    def __init__(self, responsive=True):
        super().__init__(*[(r['text'], r['output_tokens'], r['finish_reason'])
                           for r in FIXTURE['samples']])
        self.responsive = responsive

    def __call__(self, system, user, **kwargs):
        if (self.responsive and 'RAW ARGUMENT REWRITE' in system
                and ORIGINAL_ROLE not in system
                and ORIGINAL_TASK not in user
                and '3564 characters' in user and 'at most 1800 characters' in user):
            # A deterministic model stand-in only responds to the narrowed
            # editing contract. Preserve the proposed answer from the fixture.
            self.requests.append((system, user, kwargs))
            text = FIXTURE['samples'][2]['text'].split('Final answer:')[-1]
            text = 'Final answer:' + text
            self.last_sample_tokens = list(map(ord, text))
            self.last_usage = dict(api_calls=1, output_tokens=20, finish_reason='stop')
            return text
        return super().__call__(system, user, **kwargs)


def test_captured_repeat_gets_focused_bounded_rewrite_and_valid_action():
    sampler = RepeatingBody()
    response = run(sampler, failed_request())
    assert response.tool_calls, response.usage.get('tool_error')
    call = response.tool_calls[0]
    assert call.name == 'work' and call.arguments['problem_id'] == 'arml_local_2012:9'
    assert 0 < len(call.arguments['content']) <= 2400
    assert response.usage['api_calls'] == 4
    assert [s['stage'] for s in response.usage['sampling_trace']] == ['select', 'arguments', 'body', 'body']
    assert not sampler.requests[-1][2].get('continuation_tokens')
    assert ORIGINAL_ROLE in sampler.requests[2][0]  # Initial generation keeps its role.
    assert ORIGINAL_ROLE not in sampler.requests[3][0]


def test_unresponsive_recorded_outputs_still_cannot_execute():
    sampler = RepeatingBody(responsive=False)
    response = run(sampler, failed_request())
    assert not response.tool_calls
    assert response.usage['api_calls'] == 5
    assert '2400' in response.usage['tool_error']
    assert FIXTURE['samples'][-1]['text'] in response.usage['unexecuted_action_draft']['text']
    first, second = sampler.requests[3:5]
    assert 'at most 1800 characters' in first[1]
    assert 'at most 900 characters' in second[1]
    assert first[:2] != second[:2]
    assert all(not req[2].get('continuation_tokens') for req in (first, second))
    assert [row.get('rewrite_target_chars') for row in response.usage['sampling_trace'][3:]] == [1800, 900]


def test_rewrite_continuation_keeps_exact_prompt_and_checkpoint_target():
    rows = FIXTURE['samples'][:3]
    first = Samples(*[(r['text'], r['output_tokens'], r['finish_reason']) for r in rows],
                    ('Final answer: ', 4, 'length'))
    first.supports_prefix = True
    req = failed_request()
    partial = run(first, replace(req, metadata={**req.metadata, 'max_transport_attempts': 4}))
    assert not partial.tool_calls
    draft = json.loads(json.dumps(partial.usage['unexecuted_action_draft']))
    assert draft['pending_body']['rewrite_attempt'] == 1
    assert draft['pending_body']['rewrite_target'] == 1800
    second = Samples(*[(r['text'], r['output_tokens'], r['finish_reason']) for r in rows[:2]],
                     ('42', 1, 'stop'))
    second.supports_prefix = True
    final = run(second, replace(req, metadata={**req.metadata, 'unexecuted_action_draft': draft}))
    assert final.tool_calls[0].arguments['content'] == 'Final answer: 42'
    assert second.requests[-1][:2] == first.requests[-1][:2]
    assert second.requests[-1][2]['continuation_tokens'] == list(map(ord, 'Final answer: '))
    assert final.usage['sampling_trace'][-1]['rewrite_target_chars'] == 1800


def test_full_otc_request_and_dispatch_accept_the_repaired_work():
    from contest_config import ContestRunConfig
    from contest_engine import _ContestEngine, _AgentTurn
    from contest_manifest import ContestManifest, ManifestTask
    from rules.loader import load_rule_card
    from tinker_action import request_action
    manifest = ContestManifest('rewrite-integration', 'arml_local', (
        ManifestTask('arml_local_2012:9', 'Question 9', None,
                     'Use the provided logarithm problem.', 'math', 1, False, {}),))
    config = ContestRunConfig('otc', 6, 10,
                             rule_card=load_rule_card('arml_local', required=True))
    sampler = RepeatingBody()
    def action(req):
        assert req.metadata['action_argument_limits']['work']['content'] == 8000
        return request_action(sampler, req, model='fixture', max_output_tokens=8192, max_tool_retries=2)
    engine = _ContestEngine(manifest, lambda *_: 'Use the supplied task.', config,
                           action_request_fn=action, action_transport='emulated')
    turn = _AgentTurn('Agent_3')
    assert engine._prepare_agent(turn)
    turn.think_completed = True
    engine._build_agent_prompts(turn)
    assert engine._request_action(turn)
    engine._apply_agent_action(turn)
    assert engine.session.task('arml_local_2012:9').versions
    assert engine.session.task('arml_local_2012:9').versions[-1].content == FIXTURE['samples'][2]['text']
    assert len(sampler.requests) == 3  # The captured 3,564-char answer needs no rewrite at 8k.
    assert engine.transport_failures == 0
    assert engine.action_transport_log[-1]['executed']
