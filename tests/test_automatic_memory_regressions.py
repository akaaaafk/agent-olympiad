"""Replay ARML 2010 failures without a model call or gold-driven selection."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
import automatic_memory
from contest_actions import _apply_action
from contest_engine import _ContestEngine, _AgentTurn
from contest_memory import ContestMemory
from contest_manifest import ContestManifest, ManifestTask
from contest_policy import _card_focus_task, _card_task_claimed_this_turn, _resolved_actions
from contest_session import ContestSession
from llm import LLMResponse, LLMToolCall
from strategy import StrategicPolicy
from test_live_failure_regressions import state, BASELINES
from test_checkpoint_cursor import manifest, config

SAVED = json.loads((ROOT / 'tests/fixtures/arml2010_memory_failure.json').read_text(encoding='utf-8'))


class AutomaticMemoryFailureTests(unittest.TestCase):
    def append(self, memory, task, kind, payload, actor='Agent_1'):
        return memory.append(task_id=task, question_id=None, actor=actor,
            visibility='private', kind=kind, payload=payload, turn=1)

    def test_saved_unlabelled_wrong_target_is_atomic_for_all_baselines_and_resume(self):
        for baseline in BASELINES:
            for restore in (False, True):
                with self.subTest(baseline=baseline, restore=restore):
                    original = SAVED['original_work']
                    m, s, memory, cfg = state(baseline, target=original['task_id'],
                                             initial=original['payload']['content'])
                    # Same focus/target relationship as saved Q4 -> Q1 native call.
                    focus = SAVED['preceding_think']['task_id']
                    s.tasks[0].task_id = focus
                    s = ContestSession(s.tasks, s.budget)
                    s.select_task(focus)
                    if restore:
                        s = ContestSession.from_checkpoint(s.checkpoint())
                    before = s.checkpoint(), memory.to_checkpoint_json()
                    with self.assertRaisesRegex(ValueError, 'task.*binding|cross-task'):
                        _apply_action(action='work', arguments=SAVED['bad_call']['arguments'],
                            agent='Agent_2', manifest=m, session=s, memory=memory, config=cfg,
                            strategic_policy=None, task_action_executor=Mock())
                    self.assertEqual((s.checkpoint(), memory.to_checkpoint_json()), before)

    def test_mixed_task_summary_is_separated_and_wrong_task_identity_rejected(self):
        memory = ContestMemory(run_id='scope', session_id='scope', competition_id='arml_local')
        task = SAVED['preceding_think']['task_id']
        self.append(memory, task, 'think', SAVED['preceding_think']['payload'])
        update = {'task_id': task, 'takeaways': 'Problem 4 has candidate 81; Problem 3 finalized 51/100.',
                  'open_questions': 'Check tiling recurrence.', 'next_step': 'Verify end cases.',
                  'team_progress': 'Problem 7 needs a review.'}
        automatic_memory.sync(memory, viewer='Agent_1', turn=1, task_id=task, essence=update)
        ctx = automatic_memory.context(memory, viewer='Agent_1', current_task_id=task)
        self.assertNotIn('51/100', json.dumps(ctx['current_task']['essence']))
        self.assertIn('51/100', json.dumps(ctx['team_progress']))
        self.assertIn('Check tiling', json.dumps(ctx['current_task']['essence']))
        bad = {**update, 'task_id': 'arml_local_2010:1'}
        _, essence = automatic_memory.split_think('<memory_update>' + json.dumps(bad) +
                                                  '</memory_update>', task_id=task)
        self.assertIsNone(essence)

    def test_real_errors_survive_dialogue_churn_focus_switch_and_restore(self):
        memory = ContestMemory(run_id='failure', session_id='failure', competition_id='arml_local')
        error = SAVED['action_errors'][0]
        source = self.append(memory, error['task_id'], 'action_error', error['payload'])
        automatic_memory.sync(memory, viewer='Agent_1', turn=1)
        for i in range(12):
            self.append(memory, error['task_id'], 'speak', {'content': 'Later dialogue ' + str(i)})
        automatic_memory.sync(memory, viewer='Agent_1', turn=2)
        memory = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
        before = memory.to_checkpoint_json()
        automatic_memory.sync(memory, viewer='Agent_1', turn=2)
        self.assertEqual(before, memory.to_checkpoint_json())
        ctx = automatic_memory.context(memory, viewer='Agent_1', current_task_id='other', max_chars=1800)
        self.assertIn(source.event_id, json.dumps(ctx['recent_action_errors']))
        self.assertIn(error['payload']['error'], json.dumps(ctx['recent_action_errors']))
        self.assertLessEqual(len(json.dumps(ctx, ensure_ascii=False)), 1800)
        other = automatic_memory.context(memory, viewer='Agent_2', current_task_id=error['task_id'])
        self.assertNotIn(source.event_id, json.dumps(other))

    def test_memory_bookkeeping_never_claims_another_seats_task(self):
        _, _, memory, _ = state('otc')
        self.append(memory, 'arml_local_2009:5', 'automatic_memory', {}, actor='Agent_2')
        self.assertFalse(_card_task_claimed_this_turn(memory, 'arml_local_2009:5', agent='Agent_1', turn=1))

    def test_memory_bookkeeping_never_changes_own_recent_task(self):
        _, session, memory, _ = state('otc')
        for task in session.tasks:
            if not task.versions:
                session.select_task(task.task_id)
                session.create_answer('Candidate', author='Agent_1')
        self.append(memory, session.tasks[0].task_id, 'work', {'content': 'Candidate'})
        before = _card_focus_task(session, memory, 'Agent_1', None, StrategicPolicy())
        self.append(memory, session.tasks[1].task_id, 'automatic_memory', {})
        after = _card_focus_task(session, memory, 'Agent_1', None, StrategicPolicy())
        self.assertEqual(after.task_id, before.task_id)

    def test_native_validation_failure_is_recorded_before_the_seat_returns(self):
        engine = _ContestEngine(manifest(), Mock(), config())
        engine.action_request_fn = lambda _: LLMResponse('', 'mock', 'invalid-review',
            tool_calls=(LLMToolCall('review_answer', {'problem_id': 'q1'}),),
            usage={'api_calls': 1, 'output_tokens': 1})
        turn = _AgentTurn('Agent_1')
        turn.available_actions = _resolved_actions(engine.manifest, engine.config)
        self.assertFalse(engine._request_action(turn))
        errors = automatic_memory.context(engine.memory, viewer='Agent_1', current_task_id='q1')['recent_action_errors']
        self.assertEqual(errors[-1]['action'], 'review_answer')
        self.assertEqual(errors[-1]['target_task_id'], 'q1')
        self.assertIn('decision', errors[-1]['error'])

    def test_labelled_cross_task_writes_and_selected_unlabelled_revisions_remain_legal(self):
        for baseline in BASELINES:
            for content in ('Problem 7: Final answer: 43',
                            '{"problem_id":"arml_local_2009:7","final_answer":"43"}'):
                with self.subTest(baseline=baseline, content=content):
                    m, s, memory, cfg = state(baseline, initial='Final answer: 42')
                    s.select_task(s.tasks[0].task_id)
                    _apply_action(action='work', arguments={'problem_id': 'arml_local_2009:7', 'content': content},
                        agent='Agent_1', manifest=m, session=s, memory=memory, config=cfg,
                        strategic_policy=None, task_action_executor=Mock())
                    self.assertEqual(s.active_task.task_id, 'arml_local_2009:7')
                    self.assertEqual(s.active_task.versions[-1].content, content)
                    _apply_action(action='work', arguments={'content': 'Final answer: 44'},
                        agent='Agent_1', manifest=m, session=s, memory=memory, config=cfg,
                        strategic_policy=None, task_action_executor=Mock())
                    self.assertEqual(s.active_task.versions[-1].content, 'Final answer: 44')

    def test_engine_rejects_saved_call_and_delivers_failure_on_next_decision_without_recall(self):
        task_id = SAVED['original_work']['task_id']
        focus = SAVED['preceding_think']['task_id']
        m = ContestManifest('saved-trace', 'arml_local', tuple(
            ManifestTask(pid, pid, None, 'Public statement', 'team_contest', 4, False,
                         {'problem_id': pid, 'task_type': 'team_contest'}) for pid in (task_id, focus)))
        for baseline in ('vallina_otc', 'otc'):
            with self.subTest(baseline=baseline):
                captures = []
                engine = _ContestEngine(m, Mock(return_value='Check the current task.'), config(baseline))
                engine.session.select_task(task_id)
                original = SAVED['original_work']['payload']['content']
                engine.session.create_answer(original, author='Agent_2')
                engine.session.select_task(focus)
                def request(req):
                    captures.append(req)
                    call = LLMToolCall('work', SAVED['bad_call']['arguments']) if len(captures) == 1 else LLMToolCall('rest', {'reason': 'Correct next call'})
                    return LLMResponse('', 'mock', 'saved-trace', tool_calls=(call,),
                                       usage={'api_calls': 1, 'output_tokens': 1})
                engine.action_request_fn = request
                for _ in range(2):
                    turn = _AgentTurn('Agent_2', prepared=True)
                    turn.available_actions = _resolved_actions(m, engine.config)
                    engine._run_agent_turn(turn)
                self.assertEqual(engine.session.task(task_id).versions[-1].content, original)
                self.assertEqual(len(engine.session.task(task_id).versions), 1)
                self.assertIn('cross-task work needs explicit task binding', captures[-1].user_prompt)
                if baseline == 'otc':
                    ctx = automatic_memory.context(engine.memory, viewer='Agent_2', current_task_id=focus)
                    self.assertEqual(ctx['recent_action_errors'][-1]['target_task_id'], task_id)
                else:
                    self.assertNotIn('recent_action_errors', captures[-1].user_prompt)

    def test_old_binding_runtime_is_rejected_for_memory_off_too(self):
        engine = _ContestEngine(manifest(), Mock(), config('vallina_otc'))
        checkpoint = engine._checkpoint()
        checkpoint['engine_state']['settings'].pop('work_task_binding_version')
        from contest_runner import run_contest
        query = Mock(side_effect=AssertionError('must not query'))
        with self.assertRaisesRegex(ValueError, 'runtime version/settings mismatch'):
            run_contest(manifest(), query, config('vallina_otc'),
                session_checkpoint=checkpoint, memory_checkpoint=engine.memory.to_checkpoint_json())
        query.assert_not_called()


if __name__ == '__main__':
    unittest.main()
