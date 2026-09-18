"""A model command is not an answer and must not become a submitted PDF."""
import sys
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / p) for p in ('src', 'tests')]
from contest_actions import _apply_action
from test_work_content_limits import setup
from test_tinker_action_mechanism import Samples, run, request
from answer_content import command_names, action_content_error
from action_transport import request_single_action
from llm import LLMResponse, LLMToolCall
from tool_registry import ACTION_REGISTRY, render_function_tools

COMMAND = 'read_problem_pdf(problem_id="deliverable", pages=[1, 2], document=2)'


@pytest.mark.parametrize('action', ['work', 'render_pdf'])
def test_captured_command_cannot_be_saved_or_rendered_as_artifact(action):
    manifest, config, session, memory = setup('single_agent', artifact_limit=60000)
    renderer = Mock(return_value={'valid': True})
    before = session.checkpoint(), memory.archival_snapshot()
    with pytest.raises(ValueError, match='tool command'):
        _apply_action(action=action, arguments={'content': COMMAND}, agent='Agent_1',
                      manifest=manifest, config=config, session=session, memory=memory,
                      strategic_policy=None, task_action_executor=renderer)
    renderer.assert_not_called()
    assert (session.checkpoint(), memory.archival_snapshot()) == before


def test_tinker_command_body_is_not_returned_as_a_valid_work_call():
    sample = Samples(('work","', 2, 'stop'), (COMMAND, 15, 'stop'),
                     (COMMAND, 15, 'stop'))
    sample.supports_prefix = True
    response = run(sample, request(max_transport_attempts=3))
    assert not response.tool_calls
    assert any('tool command' in str(row.get('error', ''))
               for row in response.usage['sampling_trace'])


@pytest.mark.parametrize('text', [COMMAND, '  ' + COMMAND + '\n', '`' + COMMAND + '`',
    '```python\n' + COMMAND + '\n```', 'functions.' + COMMAND, 'tools.' + COMMAND,
    COMMAND + '\ninspect_problem(problem_id="deliverable")', json.dumps(COMMAND),
    json.dumps({'name': 'read_problem_pdf', 'arguments': {'problem_id': 'q'}}),
    json.dumps({'type': 'tool_use', 'name': 'read_problem_pdf', 'input': {'problem_id': 'q'}}),
    json.dumps({'tool_calls': [{'type': 'function', 'function': {
        'name': 'read_problem_pdf', 'arguments': '{"problem_id":"q"}'}}]}),
])
def test_command_only_encodings_are_rejected(text):
    assert 'read_problem_pdf' in command_names(text)


@pytest.mark.parametrize('text', ['42', 'sin(x)', 'f(x)', 'Final answer: 42',
    'The tool read_problem_pdf(...) reads pages; our answer is 42.',
    'For example:\n```python\n' + COMMAND + '\n```\nThe result is 42.',
    '"read_problem_pdf"', 'Let work(x) = x + 1. Then work(2) = 3.',
    json.dumps({'name': 'read_problem_pdf', 'explanation': 'A function name example'}),
    'def read_problem_pdf(x):\n    return x\nread_problem_pdf(42)',
])
def test_regular_answers_and_quoted_examples_are_not_commands(text):
    assert not command_names(text)


@pytest.mark.parametrize('variant', ['single_agent', 'decentralized', 'centralized', 'vallina_otc', 'otc'])
@pytest.mark.parametrize('action,field', [('work', 'content'), ('render_pdf', 'content'), ('submit', 'answer')])
def test_dispatch_is_atomic_across_baselines_and_inline_submission(variant, action, field):
    manifest, config, session, memory = setup(variant)
    session.create_answer('Final answer: 7', author='Agent_1')
    before = session.checkpoint(), memory.archival_snapshot()
    with pytest.raises(ValueError, match='tool command'):
        _apply_action(action=action, arguments={field: COMMAND}, agent='Agent_1',
                      manifest=manifest, config=config, session=session, memory=memory,
                      strategic_policy=None, task_action_executor=None)
    assert (session.checkpoint(), memory.archival_snapshot()) == before


def native_response(name='work', arguments=None, **usage):
    return LLMResponse('', 'fixture', 'fixture', tool_calls=(LLMToolCall(name,
        {'content': COMMAND} if arguments is None else arguments),),
        usage={'api_calls': 1, 'output_tokens': 10, 'finish_reason': 'stop', **usage})


def reader_request(**metadata):
    reader = tuple(render_function_tools([ACTION_REGISTRY['read_problem_pdf']]))
    req = request(**metadata)
    return replace(req, tools=req.tools + reader)


def test_native_reselection_returns_only_the_models_explicit_reader_call():
    req = reader_request(action_argument_limits={'work': {'content': 20}})
    reader_args = {'problem_id': 'q', 'pages': [1]}
    fn = Mock(side_effect=[native_response(), native_response('read_problem_pdf', reader_args)])
    result = request_single_action(fn, req)
    assert result.tool_calls[0].name == 'read_problem_pdf'
    assert result.tool_calls[0].arguments == reader_args  # Not the embedded deliverable/document=2.
    repair = fn.call_args.args[0]
    assert repair.tools == req.tools and repair.attachments == req.attachments
    assert 'tool command' in repair.user_prompt and 'invent' in repair.user_prompt
    assert result.usage['api_calls'] == 2 and result.usage['output_tokens'] == 20
    assert result.usage['rejected_tool_calls'][0]['rejection_reason'] == 'answer_is_tool_command'


@pytest.mark.parametrize('budget', [1, 2])
def test_native_repeated_command_exhaustion_never_executes(budget):
    fn = Mock(return_value=native_response())
    result = request_single_action(fn, request(max_transport_attempts=budget))
    assert not result.tool_calls and 'tool command' in result.usage['tool_error']
    assert fn.call_count == result.usage['api_calls'] == budget
    assert len(result.usage['rejected_tool_calls']) == budget


def test_native_reselection_cannot_use_an_unavailable_tool():
    fn = Mock(side_effect=[native_response(), native_response('read_problem_pdf', {'problem_id': 'q'})])
    result = request_single_action(fn, request())  # No reader in the current surface.
    assert not result.tool_calls
    assert result.usage['api_calls'] == 2


def test_managed_transport_cannot_bypass_guard_or_restart_its_budget():
    fn = Mock(return_value=native_response(transport_recovery_managed=True))
    result = request_single_action(fn, request())
    assert not result.tool_calls and 'tool command' in result.usage['tool_error']
    assert fn.call_count == 1


def test_tinker_reselects_reader_instead_of_rewriting_command_into_an_answer():
    sample = Samples((json.dumps({'name': 'work', 'arguments': {}, 'body_argument': 'content'}), 12, 'stop'),
                     (COMMAND, 15, 'stop'),
                     (json.dumps({'name': 'read_problem_pdf', 'arguments': {'problem_id': 'q', 'pages': [1]}}), 14, 'stop'))
    response = run(sample, reader_request(max_transport_attempts=3))
    assert response.tool_calls[0].name == 'read_problem_pdf'
    assert response.usage['api_calls'] == 3 and response.usage['output_tokens'] == 41
    assert [r['stage'] for r in response.usage['sampling_trace']] == ['select', 'body', 'select']
    assert 'tool command' in sample.requests[-1][1]
    assert 'RAW ARGUMENT REWRITE' not in sample.requests[-1][0]


def test_tinker_inline_descriptor_cannot_bypass_guard():
    bad = json.dumps({'name': 'work', 'arguments': {'content': COMMAND}})
    sample = Samples((bad, 12, 'stop'), (bad, 12, 'stop'))
    result = run(sample, request(max_transport_attempts=2))
    assert not result.tool_calls and result.usage['api_calls'] == 2


def test_reader_reselection_metadata_can_resume_without_resuming_bad_body():
    req = reader_request(max_transport_attempts=4)
    sample = Samples(('work","', 2, 'stop'), (COMMAND, 15, 'stop'),
                     ('read_problem_pdf","', 3, 'stop'), ('q","', 2, 'stop'))
    sample.supports_prefix = True
    first = run(sample, req)
    assert not first.tool_calls
    draft = json.loads(json.dumps(first.usage['unexecuted_action_draft']))
    assert 'pending_body' not in draft
    assert draft['pending_metadata']['name'] == 'read_problem_pdf'
    second = Samples(('read_problem_pdf","', 3, 'stop'), ('[1]}', 3, 'stop'), ('1}', 2, 'stop'))
    second.supports_prefix = True
    final = run(second, replace(req, metadata={**req.metadata, 'unexecuted_action_draft': draft}))
    assert final.tool_calls[0].arguments == {'problem_id': 'q', 'pages': [1], 'document': 1}
    assert final.usage['api_calls'] == 3


def test_programming_source_is_exempt_but_another_task_is_not():
    manifest, config, session, memory = setup('single_agent', programming=True)
    _apply_action(action='work', arguments={'content': COMMAND}, agent='Agent_1',
                  manifest=manifest, config=config, session=session, memory=memory,
                  strategic_policy=None, task_action_executor=None)
    assert session.active_task.versions[-1].content == COMMAND
    metadata = {'task_id': 'q1', 'source_task_ids': ['q1']}
    assert action_content_error('work', {'content': COMMAND}, metadata) is None
    assert action_content_error('work', {'problem_id': 'other', 'content': COMMAND}, metadata)
    sample = Samples(('work","', 2, 'stop'), (COMMAND, 15, 'stop'))
    sample.supports_prefix = True
    response = run(sample, request(source_task_ids=['q']))
    assert response.tool_calls[0].arguments['content'] == COMMAND


def test_artifact_renderer_refuses_command_before_creating_files(tmp_path):
    from artifact_contract import ArtifactContract
    from artifacts.contest_delivery import ArtifactRenderer
    renderer = ArtifactRenderer(tmp_path / 'versions', ArtifactContract(kind='document'))
    with pytest.raises(ValueError, match='tool command'):
        renderer(None, 'render_pdf', {'content': COMMAND})
    assert renderer.latest is None and not (tmp_path / 'versions').exists()


def test_artifact_pipeline_recovers_to_real_reader_and_judges_only_real_answer(tmp_path):
    import pymupdf
    from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
    from evaluation.models import load_rubric
    task_pdf = tmp_path / 'task.pdf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((50, 50), 'Synthetic task: explain why one plus one equals two.')
        pdf.save(task_pdf)
    prepared = prepare_artifact_run(competition='arml_national_power', task_pdf=task_pdf,
        output=tmp_path / 'run', max_turns=2, provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
        system_variant='single_agent')
    actions = iter([
        ('select_problem', {'problem_id': 'deliverable'}),
        ('work', {'problem_id': 'deliverable', 'content': COMMAND}),
        ('read_problem_pdf', {'problem_id': 'deliverable', 'pages': [1], 'document': 1}),
        ('render_pdf', {'content': 'Two disjoint singleton sets have two elements. Final answer: 2.'}),
    ])
    seen = []
    def agent(req):
        seen.append(req)
        names = {tool['name'] for tool in req.tools}
        fallback = ('submit', {}) if names == {'submit'} else (
            'rest', {'reason': 'Keep the recorded answer until the deadline.'})
        name, args = next(actions, fallback)
        assert name in names
        return native_response(name, args)
    rubric = load_rubric(prepared['rubric'])
    payload = {'criteria': [dict(id=c.id, score=c.min_score, max_score=c.max_score,
        evidence=['Synthetic fixture only'], justification='Offline plumbing test.',
        confidence=1, observable=c.observable) for c in rubric.criteria],
        'total_score': sum(c.min_score for c in rubric.criteria),
        'max_score': rubric.total_points, 'warnings': [], 'limitations': []}
    judge = Mock(return_value=LLMResponse(json.dumps(payload), 'fixture', 'fixture',
                                         usage={'api_calls': 1, 'output_tokens': 20}))
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    assert result['status'] == 'complete' and result['graded']
    assert Path(result['artifact']['source']).read_text(encoding='utf-8').endswith('Final answer: 2.')
    session = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
    versions = session['session_checkpoint']['tasks'][0]['versions']
    assert len(versions) == 1 and COMMAND not in versions[0]['content']
    assert len(list((tmp_path / 'run/versions').iterdir())) == 1
    executed = [row['name'] for row in session['action_transport_log'] if row.get('executed')]
    assert executed[:3] == ['select_problem', 'read_problem_pdf', 'render_pdf']
    assert all(name in {'rest', 'submit'} for name in executed[3:])
    assert seen[3].metadata.get('problem_pdf_read') and seen[3].attachments
    assert 'Do not put a reader command in work.content' in seen[1].user_prompt
    assert session['budget']['api_calls_used'] == len(seen)
    assert judge.called
