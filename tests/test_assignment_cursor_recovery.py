"""A drafted centralized assignment remains a worker's revision target."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from contest_config import ContestRunConfig
from contest_engine import _ContestEngine, _AgentTurn
from contest_manifest import ContestManifest, ManifestTask
from contest_prompts import _user_prompt
from contest_session import TaskState
from tinker_action import request_action


def prepared():
    tasks = tuple(ManifestTask(f'q{i}', f'Question {i}', None, 'What is 6 times 7?',
        'math', 1, False, {'gold_label': {'expected_answer': '42'}}) for i in range(1, 7))
    manifest = ContestManifest('assigned-drafts', 'arml_local', tasks)
    plan = {'summary': 'Solve assigned problems.', 'task_order': [t.task_id for t in tasks],
            'work_assignments': {f'Agent_{i}': [f'q{i}'] for i in range(1, 7)}}
    config = ContestRunConfig('centralized', 6, 10, max_api_calls=200, max_tokens=10000,
                              submission_turn=10)
    engine = _ContestEngine(manifest, lambda *_: json.dumps(plan), config,
                            action_request_fn=lambda req: None, action_transport='emulated')
    engine._prepare_coach()
    for i in range(1, 7):
        engine.session.select_task(f'q{i}')
        engine.session.create_answer('Final answer: 42', author=f'Agent_{i}')
    engine.session.select_task('q2')
    return engine


@pytest.mark.parametrize('agent', ['Agent_3', 'Agent_4', 'Agent_5'])
def test_drafted_worker_is_not_stranded_on_another_workers_active_task(agent):
    engine = prepared()
    turn = _AgentTurn(agent)
    assert engine._prepare_agent(turn)
    assert engine.session.active_task.task_id in turn.work_task_ids
    assert 'work' in {s.name for s in turn.available_actions}
    assert 'submit' not in {s.name for s in turn.available_actions}


@pytest.mark.parametrize('state', ['locked', 'blocked', 'submitted'])
def test_revision_fallback_does_not_reopen_ineligible_work(state):
    engine = prepared()
    own = engine.session.task('q3')
    if state == 'locked':
        own.locked = True
    elif state == 'blocked':
        own.state = TaskState.BLOCKED
        own.blocked_until_turn = 100
    else:
        from contest_session import SubmissionRecord
        own.submissions.append(SubmissionRecord(own.task_id, own.versions[-1].version_hash,
                                               'AC', 1, True, 1))
    turn = _AgentTurn('Agent_3')
    engine._prepare_agent(turn)
    assert engine.session.active_task.task_id == 'q2'
    assert 'work' not in {s.name for s in turn.available_actions}


def test_foreign_task_prompt_does_not_tell_worker_to_act_on_it_directly():
    engine = prepared()
    prompt = _user_prompt(engine.manifest, engine.session, engine.memory, engine.config,
        'Agent_3', personal_assignment=engine.personal_assignments['Agent_3'])
    assert 'act on it directly instead of calling select_problem again' not in prompt
    assert 'outside your work assignment' in prompt


def test_real_staged_work_requests_reach_deadline_without_cross_worker_circuit():
    engine = prepared()
    class WorkSampler:
        supports_sampling_metadata = supports_continuation = supports_prefix = True
        def __init__(self, req):
            self.req = req
        def __call__(self, system, user, **kwargs):
            prefix = kwargs.get('assistant_prefix', '')
            selected = 'submit' if {t['name'] for t in self.req.tools} == {'submit'} else 'work'
            raw = (selected + '","' if prefix == '{"name":"' else
                   self.req.metadata['task_id'] + '"}' if prefix else 'Final answer: 42')
            self.last_sample_tokens = list(map(ord, raw))
            self.last_usage = dict(api_calls=1, output_tokens=4, input_tokens=10,
                max_output_tokens=kwargs['max_output_tokens_override'], finish_reason='stop')
            return raw
        def decode_completion_tokens(self, tokens):
            return ''.join(map(chr, tokens))
    def request(req):
        # Replay the live wire response through the actual staged parser.
        return request_action(WorkSampler(req), req, model='fixture', max_output_tokens=512,
                              max_tool_retries=2)
    engine.action_request_fn = request
    result = engine.run()
    assert result['budget']['turns_used'] == 10
    assert sum(bool(v) for v in result['submissions'].values()) == 6
    assert not any('unavailable function' in str(e['payload'])
                   for e in result['memory']['events'] if e['kind'] == 'action_error')
