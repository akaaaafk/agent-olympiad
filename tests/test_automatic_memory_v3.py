"""Live-trace regressions for summary resilience, evidence and task recovery."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
import automatic_memory as am
from action_modules.memory import agent_context, private_think_context
from contest_memory import ContestMemory
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from contest_policy import _card_focus_task
from strategy import StrategicPolicy
from test_checkpoint_cursor import config, manifest
from contest_engine import _ContestEngine, _AgentTurn
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import run_contest
from llm import LLMResponse, LLMToolCall

FIXTURE = json.loads((ROOT / 'tests/fixtures/arml2011_memory_v3_failures.json').read_text('utf-8'))

def summary(task='q1', **fields):
    return {'task_id': task, 'takeaways': 'OLD_CLAIM is solved; no check needed.',
            'open_questions': '', 'next_step': '', 'team_progress': '', **fields}

def make_state():
    memory = ContestMemory(run_id='v3', session_id='test', competition_id='arml_local')
    session = ContestSession([TaskUnit('q1', kind='non_programming'),
                              TaskUnit('q2', kind='non_programming')], ContestBudgetState(max_turns=10))
    session.select_task('q1')
    return memory, session

def append(memory, kind, content, task='q1', actor='Agent_1', turn=1, **payload):
    return memory.append(task_id=task, question_id=None, actor=actor,
        visibility='private' if kind in {'think', 'action_error'} else 'public',
        kind=kind, payload={'content': content, **payload}, turn=turn)

class SummaryRecoveryTests(unittest.TestCase):
    def test_actual_valid_fields_survive_small_overflow_and_latex_escapes(self):
        for event in FIXTURE['summaries'][:3]:
            with self.subTest(event=event['event_id']):
                thought, s = am.split_think(event['raw_content'], task_id=event['task_id'])
                self.assertIsNotNone(s)
                self.assertTrue(s['takeaways'])
                self.assertLessEqual(len(s['team_progress']), 300)
                self.assertNotIn('<memory_update>', thought)

    def test_proposal_and_quadrant_labels_are_not_problem_ids(self):
        for e in [FIXTURE['summaries'][-1], FIXTURE['quadrant']]:
            with self.subTest(task=e['task_id']):
                _, s = am.split_think(e['raw_content'], task_id=e['task_id'])
                scoped, _ = am._scoped_summary(s, e['task_id'])
                self.assertEqual(scoped['takeaways'], s['takeaways'])

    def test_explicit_cross_task_still_quarantined_and_identity_never_repaired(self):
        s = summary('arml_local_2011:8', takeaways='Problem 9 has a separate answer.')
        scoped, team = am._scoped_summary(s, s['task_id'])
        self.assertFalse(scoped['takeaways'])
        self.assertIn(s['takeaways'], team)
        for bad in ('q2', '', 1):
            text = '<memory_update>' + json.dumps(summary(bad)) + '</memory_update>'
            self.assertIsNone(am.split_think(text, task_id='q1')[1])

    def test_bad_field_does_not_destroy_other_fields_and_broken_json_not_guessed(self):
        s = summary(takeaways='Keep this valid premise', team_progress=['wrong type'])
        recovered = am.split_think('<memory_update>' + json.dumps(s) + '</memory_update>', task_id='q1')[1]
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered['takeaways'], s['takeaways'])
        self.assertFalse(recovered['team_progress'])
        self.assertIsNone(am.split_think('<memory_update>{"task_id":"q1",', task_id='q1')[1])

class EvidenceBindingTests(unittest.TestCase):
    def setup_candidate(self):
        m, s = make_state()
        v = s.create_answer('Final answer: OLD_CLAIM', author='Agent_1')
        append(m, 'work', v.content)
        append(m, 'think', 'OLD_CLAIM is settled.')
        am.sync(m, viewer='Agent_1', turn=1, task_id='q1', essence=summary(), session=s)
        return m, s, v

    def test_self_asserted_solved_stays_unreviewed_and_rejection_wins(self):
        m, s, v = self.setup_candidate()
        c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s)['current_task']
        self.assertEqual(c['answer_state']['review_status'], 'unreviewed')
        s.record_task_review('q1', 'Agent_2', 'Counterexample disproves the claim.', decision='reject')
        s.record_task_review('q1', 'Agent_3', 'Looks good.', decision='approve')
        c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s)['current_task']
        self.assertEqual(c['answer_state']['review_status'], 'rejected')
        self.assertIsNone(c['essence'])
        self.assertIn('Counterexample', json.dumps(c['answer_state']))
        self.assertNotIn('no check needed', json.dumps(c))

    def test_new_version_invalidates_summary_and_approval_even_across_restore(self):
        m, s, v = self.setup_candidate()
        s.record_task_review('q1', 'Agent_2', 'Independent check.', decision='approve')
        append(m, 'think', 'OLD_CLAIM confirmed', turn=2)
        am.sync(m, viewer='Agent_1', turn=2, task_id='q1', essence=summary(), session=s)
        before = am.context(m, viewer='Agent_1', current_task_id='q1', session=s)['current_task']
        self.assertEqual(before['answer_state']['review_status'], 'approved')
        new = s.create_answer('Final answer: NEW_CLAIM', author='Agent_2')
        m = ContestMemory.from_checkpoint_json(m.to_checkpoint_json())
        s = ContestSession.from_checkpoint(s.checkpoint())
        c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s)['current_task']
        self.assertIsNone(c['essence'])
        self.assertEqual(c['answer_state']['version_hash'], new.version_hash)
        self.assertEqual(c['answer_state']['review_status'], 'unreviewed')
        self.assertNotIn('OLD_CLAIM', json.dumps(c))
        self.assertIn('OLD_CLAIM', m.to_checkpoint_json())

    def test_rejected_attempt_is_not_promoted_to_live_candidate(self):
        m, s, v = self.setup_candidate()
        append(m, 'work', 'Final answer: FORGED_ATTEMPT', actor='Agent_3', turn=2)
        am.sync(m, viewer='Agent_1', turn=2, session=s)
        c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s)['current_task']
        self.assertEqual(c['answer_state']['final_answer'], 'OLD_CLAIM')
        self.assertNotIn('FORGED_ATTEMPT', json.dumps(c.get('candidate_claim')))

    def test_summary_state_is_read_only_and_hidden_tasks_stay_hidden(self):
        m, s, _ = self.setup_candidate()
        before = s.checkpoint(), m.to_checkpoint_json()
        am.context(m, viewer='Agent_1', current_task_id='q1', session=s)
        self.assertEqual(before, (s.checkpoint(), m.to_checkpoint_json()))
        off = agent_context(m, viewer='Agent_2', enabled=False, current_task_id='q1', session=s)
        self.assertNotIn('automatic_memory', json.dumps(off))

    def test_past_thoughts_are_not_duplicated_beside_consolidated_memory(self):
        m, _ = make_state()
        append(m, 'think', 'OLD_PRIVATE', task='q2', turn=1)
        append(m, 'think', 'CURRENT_PRIVATE', turn=2)
        before = private_think_context(m, 'Agent_1', enabled=True, current_turn=2, limit=3, include_current=False)
        during = private_think_context(m, 'Agent_1', enabled=True, current_turn=2, limit=3)
        self.assertEqual(before, [])
        self.assertNotIn('OLD_PRIVATE', json.dumps(during))
        self.assertIn('CURRENT_PRIVATE', json.dumps(during))

    def test_team_observations_expire_when_the_referenced_draft_changes(self):
        m, s, _ = self.setup_candidate()
        s.select_task('q2'); s.create_answer('Final answer: TEAM_OLD', author='Agent_2')
        append(m, 'think', 'Current task reasoning.', turn=2)
        am.sync(m, viewer='Agent_1', turn=2, session=s, task_id='q1',
                essence=summary(team_progress='Problem 2 is solved with TEAM_OLD.'))
        self.assertIn('TEAM_OLD', json.dumps(am.context(m, viewer='Agent_1',
                      current_task_id='q1', session=s)['team_progress']))
        s.create_answer('Final answer: TEAM_NEW', author='Agent_2')
        self.assertEqual(am.context(m, viewer='Agent_1', current_task_id='q1',
                                   session=s)['team_progress'], [])

    def test_hidden_task_cannot_reappear_from_old_records_or_live_state(self):
        m, s, _ = self.setup_candidate()
        s.select_task('q2'); s.create_answer('Final answer: HIDDEN_CANARY', author='Agent_2')
        append(m, 'work', 'Final answer: HIDDEN_CANARY', task='q2', actor='Agent_2')
        am.sync(m, viewer='Agent_1', turn=2, session=s)
        s.competition_flow = Mock()
        s.competition_flow.is_visible.side_effect = lambda task_id: task_id == 'q1'
        c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s)
        self.assertNotIn('HIDDEN_CANARY', json.dumps(c))
        self.assertFalse(c['recent_other_tasks'])

    def test_bounded_context_prioritizes_counterevidence_and_does_not_mutate_archive(self):
        m, s, _ = self.setup_candidate()
        for index in range(5):
            s.record_task_review('q1', f'Reviewer_{index}', 'X' * 800, decision='approve')
        s.record_task_review('q1', 'Skeptic', 'COUNTEREXAMPLE disproves it.', decision='reject')
        append(m, 'think', 'Recheck premise.', turn=2)
        am.sync(m, viewer='Agent_1', turn=2, session=s, task_id='q1',
                essence=summary(takeaways='a' * 500, open_questions='b' * 300, next_step='c' * 200))
        before = m.to_checkpoint_json()
        c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s, max_chars=1800)
        self.assertEqual(c['current_task']['answer_state']['review_status'], 'rejected')
        self.assertIn('COUNTEREXAMPLE', json.dumps(c))
        self.assertLessEqual(len(json.dumps(c, ensure_ascii=False)), 1800)
        for limit in (256, 600, 1200):
            c = am.context(m, viewer='Agent_1', current_task_id='q1', session=s, max_chars=limit)
            self.assertLessEqual(len(json.dumps(c, ensure_ascii=False)), limit)
        self.assertEqual(before, m.to_checkpoint_json())

class SharedFocusRecoveryTests(unittest.TestCase):
    def test_approved_focus_yields_to_unreviewed_peer_for_both_otc_settings(self):
        for baseline in ('otc', 'vallina_otc'):
            with self.subTest(baseline=baseline):
                e = _ContestEngine(manifest(), Mock(return_value=''), config(baseline))
                _, e.session = make_state()
                e.session.create_answer('Final answer: 11', author='Agent_1')
                e.session.record_task_review('q1', 'Agent_2', 'Checked.', decision='approve')
                e.session.select_task('q2')
                e.session.create_answer('Final answer: 22', author='Agent_3')
                append(e.memory, 'review_answer', 'Checked.', actor='Agent_2')
                focus = _card_focus_task(e.session, e.memory, 'Agent_2', None, StrategicPolicy(), review_required=True)
                self.assertEqual(focus.task_id, 'q2')

    def test_repeated_mismatch_releases_explicit_choice_without_retargeting_content(self):
        m, s = make_state()
        s.create_answer('Final answer: 11', author='Agent_1')
        s.select_task('q2'); s.create_answer('Final answer: 22', author='Agent_2')
        append(m, 'select_problem', '', problem_id='q1')
        for turn in (2, 3):
            append(m, 'action_error', '', turn=turn, action='work', target_task_id='q2',
                   error="answer task mismatch: content declares 'q1', but work targets 'q2'")
        before = s.checkpoint()
        focus = _card_focus_task(s, m, 'Agent_1', None, StrategicPolicy(), review_required=True)
        self.assertEqual(focus.task_id, 'q2')
        self.assertEqual(s.checkpoint(), before)

    def test_peer_routing_respects_visibility_locks_and_review_assignments(self):
        m, s = make_state()
        s.create_answer('Final answer: 11', author='Agent_1')
        s.record_task_review('q1', 'Agent_2', 'Checked.', decision='approve')
        s.select_task('q2'); s.create_answer('Final answer: 22', author='Agent_3')
        append(m, 'select_problem', '', problem_id='q1')
        for lock, allowed in ((False, set()), (True, {'q2'})):
            s.task('q2').locked = lock
            focus = _card_focus_task(s, m, 'Agent_1', None, StrategicPolicy(),
                        review_required=True, work_task_ids={'q1'}, review_task_ids=allowed)
            self.assertEqual(focus.task_id, 'q1')

    def test_successful_action_resets_mismatch_streak(self):
        m, s = make_state()
        append(m, 'select_problem', '', problem_id='q1')
        for turn in (1, 3):
            append(m, 'action_error', '', turn=turn, action='work', error='answer task mismatch')
            if turn == 1:
                append(m, 'speak', 'New reasoning.', turn=2)
        focus = _card_focus_task(s, m, 'Agent_1', None, StrategicPolicy(), review_required=True)
        self.assertEqual(focus.task_id, 'q1')

    def test_old_focus_checkpoint_rejected_for_both_otc_variants(self):
        for baseline in ('otc', 'vallina_otc'):
            e = _ContestEngine(manifest(), Mock(), config(baseline))
            saved = e._checkpoint()
            saved['engine_state']['settings'].pop('otc_focus_version')
            query = Mock(side_effect=AssertionError('No new model call'))
            with self.assertRaisesRegex(ValueError, 'runtime version/settings mismatch'):
                run_contest(manifest(), query, config(baseline), session_checkpoint=saved,
                            memory_checkpoint=e.memory.to_checkpoint_json())
            query.assert_not_called()

    def test_actual_failed_calls_preserve_drafts_then_recover_focus_before_thinking(self):
        for baseline in ('otc', 'vallina_otc'):
            for call in FIXTURE['mismatched_work_calls']:
                for restore in (False, True):
                    with self.subTest(baseline=baseline, call=call['call_id'], restore=restore):
                        source = call['arguments']['content'].split(':\n')[0].removeprefix('Problem ')
                        target = call['arguments']['problem_id']
                        case = ContestManifest('saved-mismatch', 'arml_local', tuple(
                            ManifestTask(t, t, None, 'Solve this problem.', 'math', 1, False,
                                         {'problem_id': t}) for t in (source, target)))
                        e = _ContestEngine(case, Mock(return_value='Re-evaluate current problem.'),
                                           config(baseline, max_turns=9))
                        e.session.select_task(source)
                        e.session.create_answer(call['arguments']['content'], author=call['agent'])
                        e.session.select_task(target)
                        e.session.create_answer('Final answer: EXISTING_TARGET', author='Peer')
                        e.session.select_task(source)
                        append(e.memory, 'select_problem', '', task=source, actor=call['agent'], problem_id=source)
                        e.action_request_fn = lambda _: LLMResponse('', 'mock', 'saved',
                            tool_calls=(LLMToolCall('work', call['arguments']),),
                            usage={'api_calls': 1, 'output_tokens': 1})
                        from contest_policy import _resolved_actions
                        for turn_no in (2, 3):
                            e.session.budget.turns_used = turn_no
                            turn = _AgentTurn(call['agent'], prepared=True)
                            turn.available_actions = _resolved_actions(case, e.config)
                            e._run_agent_turn(turn)
                        self.assertEqual(len(e.session.task(target).versions), 1)
                        self.assertEqual(e.session.task(target).versions[-1].content, 'Final answer: EXISTING_TARGET')
                        if restore:
                            e = _ContestEngine(case, Mock(return_value='New thought.'), e.config,
                                session_checkpoint=e._checkpoint(), memory_checkpoint=e.memory.to_checkpoint_json())
                        e.session.budget.turns_used = 4
                        turn = _AgentTurn(call['agent'])
                        self.assertTrue(e._prepare_agent(turn))
                        # The strict control cannot use last round's mismatch
                        # streak or existing target draft to recover focus.
                        expected_task = target if not e.config.current_turn_only else (source, target)[3 % 2]
                        self.assertEqual(e.session.active_task.task_id, expected_task)
                        self.assertTrue(e._build_agent_prompts(turn))
                        thoughts = [event for event in e.memory.view(call['agent'])
                                    if event.kind == 'think' and event.turn == 4]
                        self.assertTrue(thoughts)
                        self.assertTrue(all(event.task_id == expected_task for event in thoughts))
                        if e.config.current_turn_only:
                            self.assertNotIn('EXISTING_TARGET', turn.user_prompt)

if __name__ == '__main__':
    unittest.main()
