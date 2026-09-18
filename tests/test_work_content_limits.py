"""Work storage, generation and reading share an explicit, baseline-neutral budget."""
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import pytest

from contest_actions import _apply_action
from contest_config import ContestRunConfig
from contest_engine import _AgentTurn, _ContestEngine
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_prompts import _user_prompt
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card

VARIANTS = ('single_agent', 'decentralized', 'centralized', 'vallina_otc', 'otc')


def setup(variant='otc', *, programming=False, artifact_limit=None):
    competition = 'icpc' if programming else 'arml_local'
    task = ManifestTask('q1', 'q1', None, 'Solve the supplied task.',
                        'algorithmic_programming' if programming else 'math', 1, programming, {})
    metadata = {'artifact_contract': {'max_source_chars': artifact_limit}} if artifact_limit else {}
    manifest = ContestManifest('work-limit-test', competition, (task,), metadata)
    config = ContestRunConfig(variant, 1 if variant == 'single_agent' else 6, 10,
        rule_card=load_rule_card(competition) if variant in {'otc', 'vallina_otc'} else None)
    session = ContestSession([TaskUnit('q1', kind='programming' if programming else 'non_programming')],
                             ContestBudgetState(max_turns=10))
    session.select_task('q1')
    memory = ContestMemory(run_id='test', session_id=manifest.session_id, competition_id=competition)
    return manifest, config, session, memory


def apply(state, action, arguments, agent='Agent_1'):
    manifest, config, session, memory = state
    return _apply_action(action=action, arguments=arguments, agent=agent, manifest=manifest,
                         config=config, session=session, memory=memory,
                         strategic_policy=None, task_action_executor=None)


@pytest.mark.parametrize('variant', VARIANTS)
def test_full_8000_character_candidate_is_saved_and_checkpointed(variant):
    state = setup(variant)
    text = 'x' * (8000 - len('\nFinal answer: 42')) + '\nFinal answer: 42'
    apply(state, 'work', {'content': text})
    session, memory = state[2:]
    assert session.active_task.versions[-1].content == text
    assert ContestSession.from_checkpoint(session.checkpoint()).active_task.versions[-1].content == text
    assert next(e for e in memory.view('Agent_1') if e.kind == 'work').payload['content'] == text


@pytest.mark.parametrize('variant', VARIANTS)
def test_overlimit_is_atomic_and_does_not_replace_old_answer(variant):
    state = setup(variant)
    state[2].create_answer('Final answer: 7', author='Agent_1')
    before = state[2].checkpoint(), state[3].archival_snapshot()
    with pytest.raises(ValueError, match='8000-character'):
        apply(state, 'work', {'content': 'x' * 8001})
    assert (state[2].checkpoint(), state[3].archival_snapshot()) == before


@pytest.mark.parametrize('variant', VARIANTS)
def test_actual_engine_passes_same_cap_and_only_soft_target_to_model(variant):
    manifest, config, _, _ = setup(variant)
    seen = []
    def request(req):
        seen.append(req)
        return LLMResponse('', 'fixture', 'fixture', tool_calls=(
            LLMToolCall('work', {'content': 'A' * 4500 + '\nFinal answer: 42'}),),
            usage={'api_calls': 1, 'output_tokens': 1000})
    engine = _ContestEngine(manifest, lambda *_: 'Use the supplied task.', config,
                             action_request_fn=request, action_transport='emulated')
    engine.session.select_task('q1')
    turn = _AgentTurn('Agent_1')
    assert engine._prepare_agent(turn)
    turn.think_completed = True
    engine._build_agent_prompts(turn)
    assert engine._request_action(turn)
    engine._apply_agent_action(turn)
    assert seen[0].metadata['action_argument_limits']['work']['content'] == 8000
    assert '2,000-4,000' in seen[0].user_prompt
    assert len(seen) == 1
    assert len(engine.session.active_task.versions[-1].content) > 4000


def test_selected_version_pages_reassemble_full_text_without_moving_task_or_review():
    state = setup('decentralized')
    text = ('甲乙\n' * 2100) + '\nFinal answer: 42'
    version = state[2].create_answer(text, author='Agent_1')
    offset, pages = 0, []
    while offset is not None:
        apply(state, 'inspect_problem', {'problem_id': 'q1', 'version_hash': version.version_hash,
              'offset': offset, 'limit': 1800}, agent='Agent_2')
        result = state[3].view('Agent_2')[-1].payload
        row = result['versions'][0]
        pages.append(row['content'])
        offset = row['content_page']['next_offset']
        assert len(row['content']) <= 1800
        assert len(result['versions']) == 1
    assert ''.join(pages) == text
    assert state[2].active_task.task_id == 'q1'
    assert not state[2].active_task.reviews
    assert not any(e.kind == 'inspect_problem_result' for e in state[3].view('Agent_1'))


def test_page_does_not_rehydrate_earlier_round_in_memory_off_variant():
    state = setup('vallina_otc')
    version = state[2].create_answer('Old draft secret', author='Agent_1')
    state[2].consume_budget(turns=1)
    with pytest.raises(ValueError, match='visible version'):
        apply(state, 'inspect_problem', {'problem_id': 'q1', 'version_hash': version.version_hash})
    assert not any(e.kind == 'inspect_problem_result' for e in state[3].view('Agent_1'))


def test_requested_page_reaches_next_prompt_without_repeated_whole_drafts():
    state = setup('otc')
    text = 'Repeated detail. ' * 350 + '\nTAIL_MARKER Final answer: 42'
    apply(state, 'work', {'content': text})
    version = state[2].active_task.versions[-1]
    apply(state, 'inspect_problem', {'problem_id': 'q1', 'version_hash': version.version_hash,
                                    'offset': 5000, 'limit': 2000})
    prompt = _user_prompt(state[0], state[2], state[3], state[1], 'Agent_1')
    assert 'TAIL_MARKER' in prompt
    assert 'REQUESTED ANSWER PAGE' in prompt
    assert text not in prompt
    apply(state, 'rest', {'reason': 'Read complete.'})
    prompt = _user_prompt(state[0], state[2], state[3], state[1], 'Agent_1')
    assert 'REQUESTED ANSWER PAGE' not in prompt


@pytest.mark.parametrize('arguments', [
    {'offset': -1}, {'limit': 0}, {'limit': 4001}, {'offset': True}, {'offset': 1},
    {'version_hash': 'unknown'},
])
def test_bad_paging_arguments_do_not_return_a_draft(arguments):
    state = setup('decentralized')
    state[2].create_answer('Draft', author='Agent_1')
    with pytest.raises(ValueError):
        apply(state, 'inspect_problem', {'problem_id': 'q1', **arguments})
    assert not any(e.kind == 'inspect_problem_result' for e in state[3].view('Agent_1'))


def test_document_keeps_its_own_source_limit_in_all_baselines():
    for variant in VARIANTS:
        state = setup(variant, artifact_limit=60000)
        # The action validator must accept >8k; the full renderer is covered elsewhere.
        from work_content import action_argument_limits, validate_work_content
        assert action_argument_limits(state[0])['work']['content'] == 60000
        validate_work_content(state[0], 'q1', 'x' * 10000)
        with pytest.raises(ValueError, match='60000-character'):
            validate_work_content(state[0], 'q1', 'x' * 60001)


def test_source_review_and_programming_do_not_inherit_draft_cap():
    from work_content import action_argument_limits, work_guidance
    state = setup('single_agent', programming=True)
    assert action_argument_limits(state[0]) == {}
    manifest = replace(state[0], tasks=(replace(state[0].tasks[0], programming=False),))
    assert action_argument_limits(manifest) == {}
    assert '2,000-4,000' not in work_guidance(manifest, 'q1')


def test_native_proof_packet_keeps_larger_limit_and_identity_records_it():
    from work_content import action_argument_limits, work_guidance, validate_work_content
    from contest_run_identity import build_run_identity
    manifest, _, _, _ = setup('single_agent')
    manifest = replace(manifest, competition_id='hmmt_team')
    assert action_argument_limits(manifest)['work']['content'] == 60000
    validate_work_content(manifest, 'q1', 'x' * 20000)
    assert '2,000-4,000' not in work_guidance(manifest, 'q1')
    for variant in VARIANTS:
        config = ContestRunConfig(variant, 1 if variant == 'single_agent' else 8, 10,
            rule_card=load_rule_card('hmmt_team') if variant in {'otc', 'vallina_otc'} else None)
        identity = build_run_identity(manifest, config, execution={}, evaluation={})
        assert identity['settings']['config']['work_content_limits']['work']['content'] == 60000


@pytest.mark.parametrize('variant', VARIANTS[:3])
def test_inline_submit_cannot_bypass_candidate_storage_limit(variant):
    state = setup(variant)
    before = state[2].checkpoint(), state[3].archival_snapshot()
    with pytest.raises(ValueError, match='8000-character'):
        apply(state, 'submit', {'answer': 'x' * 8001})
    assert (state[2].checkpoint(), state[3].archival_snapshot()) == before


def test_legacy_paging_reassembles_inspection_and_rejects_changed_snapshot():
    from env import OlympiadEnvironment
    env = OlympiadEnvironment('arml_local', 'arml_local_2012')
    env.register_agents(['Agent_1', 'Agent_2'])
    env.begin_turn()
    whole = env.execute_action('Agent_1', 'inspect_problem', {'problem_id': '1'})
    first = json.loads(env.execute_action('Agent_1', 'inspect_problem',
                       {'problem_id': '1', 'limit': 70}))
    parts, page = [], first
    while True:
        parts.append(page['content'])
        if page['next_offset'] is None:
            break
        page = json.loads(env.execute_action('Agent_1', 'inspect_problem', {
            'problem_id': '1', 'version_hash': first['version_hash'],
            'offset': page['next_offset'], 'limit': 70}))
    assert ''.join(parts) == whole
    env.execute_action('Agent_1', 'work', '1 | Changed draft')
    result = env.execute_action('Agent_1', 'inspect_problem', {
        'problem_id': '1', 'version_hash': first['version_hash'], 'offset': 70, 'limit': 70})
    assert 'snapshot changed' in result


def test_increasing_work_does_not_increase_coach_or_think_or_speak_allowances():
    from action_modules.coach import coach_brief_prompts
    manifest, config, _, _ = setup('otc')
    policy = config.otc_policy
    assert policy.char_limit('work') == 8000
    assert policy.char_limit('think') == 2400
    assert policy.char_limit('speak') == 320
    system, _ = coach_brief_prompts(config.rule_card, policy, manifest,
                                    team_size=6, max_turns=10, max_api_calls=None)
    assert 'at most 2400 characters' in system
    with pytest.raises(ValueError, match='opening-brief'):
        replace(config, precontest_brief='x' * 2401)
