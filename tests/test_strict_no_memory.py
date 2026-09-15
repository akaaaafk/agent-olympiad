"""The OTC control cannot read agent-generated state from earlier rounds."""
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from contest_memory import ContestMemory
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from contest_prompts import _user_prompt
from test_checkpoint_cursor import config, manifest
from contest_actions import _apply_action
from contest_observation import current_memory, current_session
from contest_policy import _resolved_actions, _actions_for_agent
from strategy import StrategicPolicy
from contest_engine import _ContestEngine, _AgentTurn
from contest_runner import run_contest
from llm import LLMResponse, LLMToolCall


class StrictNoMemoryTests(unittest.TestCase):
    def apply(self, action, arguments, session, memory, agent='Agent_2', variant='vallina_otc'):
        return _apply_action(action=action, arguments=arguments, agent=agent,
            manifest=manifest(), session=session, memory=memory, config=config(variant),
            strategic_policy=StrategicPolicy(), task_action_executor=Mock(side_effect=AssertionError('Unexpected execution')))

    def state(self):
        session = ContestSession([TaskUnit('q1', kind='non_programming')],
                                 budget=ContestBudgetState(max_turns=10))
        session.select_task('q1')
        session.current_turn_only = True
        session.budget.turns_used = 1
        session.create_answer('OLD_DRAFT_CANARY', author='Agent_1')
        memory = ContestMemory(run_id='strict-test', session_id='cursor-fixture',
                               competition_id='arml_local')
        for turn, text in [(1, 'OLD_CHAT_CANARY'), (2, 'CURRENT_CHAT_CANARY')]:
            memory.append(task_id='q1', question_id=None, actor='Agent_1',
                          visibility='public', kind='speak', payload={'content': text}, turn=turn)
        session.budget.turns_used = 2
        return session, memory

    def test_no_old_draft_in_real_prompt(self):
        session, memory = self.state()
        prompt = _user_prompt(manifest(), session, memory, config('vallina_otc'), 'Agent_2')
        self.assertNotIn('OLD_DRAFT_CANARY', prompt)

    def test_no_old_conversation_but_current_turn_visible(self):
        session, memory = self.state()
        prompt = _user_prompt(manifest(), session, memory, config('vallina_otc'), 'Agent_2')
        self.assertNotIn('OLD_CHAT_CANARY', prompt)
        self.assertIn('CURRENT_CHAT_CANARY', prompt)

    def test_memory_condition_retains_history(self):
        session, memory = self.state()
        prompt = _user_prompt(manifest(), session, memory, config('otc'), 'Agent_2')
        self.assertIn('OLD_DRAFT_CANARY', prompt)
        self.assertIn('OLD_CHAT_CANARY', prompt)

    def test_inspect_cannot_rehydrate_history(self):
        session, memory = self.state()
        self.apply('inspect_problem', {'problem_id': 'q1'}, session, memory)
        receipt = memory.archival_snapshot()['events'][-1]
        self.assertEqual(receipt['kind'], 'inspect_problem_result')
        self.assertEqual(receipt['payload']['versions'], [])
        self.assertNotIn('OLD_DRAFT_CANARY', json.dumps(receipt))
        prompt = _user_prompt(manifest(), session, memory, config('vallina_otc'), 'Agent_2')
        self.assertNotIn('OLD_DRAFT_CANARY', prompt)

    def test_old_review_rejected_before_event_or_mutation(self):
        session, memory = self.state()
        before = session.checkpoint(), memory.to_checkpoint_json()
        with self.assertRaisesRegex(ValueError, 'created in this round'):
            self.apply('review_answer', {'problem_id': 'q1', 'decision': 'approve',
                'content': 'Blind approval', 'version_hash': session.active_task.versions[-1].version_hash},
                session, memory)
        self.assertEqual(before, (session.checkpoint(), memory.to_checkpoint_json()))
        with self.assertRaisesRegex(ValueError, 'created in this round'):
            session.record_task_review('q1', 'Agent_2', 'Direct bypass')

    def test_same_round_work_and_independent_review_still_function(self):
        session, memory = self.state()
        self.apply('work', {'content': 'CURRENT_DRAFT_CANARY\nFinal answer: 42'}, session, memory, 'Agent_1')
        prompt = _user_prompt(manifest(), session, memory, config('vallina_otc'), 'Agent_2')
        self.assertIn('CURRENT_DRAFT_CANARY', prompt)
        self.assertNotIn('OLD_DRAFT_CANARY', prompt)
        self.apply('review_answer', {'problem_id': 'q1', 'decision': 'approve',
                                   'content': 'CURRENT_REVIEW_CANARY'}, session, memory)
        self.assertTrue(session.has_independent_approval())
        self.apply('inspect_problem', {'problem_id': 'q1'}, session, memory)
        receipt = memory.archival_snapshot()['events'][-1]['payload']
        self.assertEqual(len(receipt['versions']), 1)
        self.assertIsNone(receipt['versions'][0]['parent_hash'])
        session.budget.turns_used = 3
        prompt = _user_prompt(manifest(), session, memory, config('vallina_otc'), 'Agent_2')
        self.assertNotIn('CURRENT_DRAFT_CANARY', prompt)
        self.assertNotIn('CURRENT_REVIEW_CANARY', prompt)

    def test_all_scopes_expire_and_current_scopes_keep_access_control(self):
        session, memory = self.state()
        for turn in (1, 2):
            for scope, recipients in [('private', ('Agent_2',)), ('group', ('team_a',)), ('public', ())]:
                memory.append(task_id='q1', question_id=None, actor='Agent_1', visibility=scope,
                              recipients=recipients, kind='speak',
                              payload={'content': f'{scope}_TURN_{turn}'}, turn=turn)
        current = current_memory(memory, 2)
        visible = json.dumps([e.to_dict() for e in current.view('Agent_2', groups=('team_a',))])
        for scope in ('private', 'group', 'public'):
            self.assertIn(f'{scope}_TURN_2', visible)
            self.assertNotIn(f'{scope}_TURN_1', visible)
        other = json.dumps([e.to_dict() for e in current.view('Agent_3')])
        self.assertNotIn('private_TURN_2', other)
        self.assertNotIn('group_TURN_2', other)
        self.assertIn('public_TURN_2', other)

    def test_checkpoint_keeps_audit_but_does_not_restore_agent_history(self):
        session, memory = self.state()
        archive = json.loads(json.dumps(session.checkpoint()))
        restored = ContestSession.from_checkpoint(archive)
        self.assertTrue(restored.current_turn_only)
        self.assertEqual(restored.checkpoint(), archive)
        self.assertIn('OLD_DRAFT_CANARY', json.dumps(archive))
        memory = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
        self.apply('inspect_problem', {'problem_id': 'q1'}, restored, memory)
        prompt = _user_prompt(manifest(), restored, memory, config('vallina_otc'), 'Agent_2')
        self.assertNotIn('OLD_DRAFT_CANARY', prompt)
        self.assertNotIn('OLD_CHAT_CANARY', prompt)

    def test_old_proposal_cannot_be_reused_and_current_id_is_preserved(self):
        session, memory = self.state()
        session.budget.turns_used = 1
        self.apply('propose', {'content': 'OLD_PROPOSAL_CANARY'}, session, memory, 'Agent_1')
        session.budget.turns_used = 2
        with self.assertRaisesRegex(ValueError, 'not from this round'):
            self.apply('challenge', {'proposal_id': 'P1', 'content': 'Reuse history'}, session, memory)
        self.apply('propose', {'content': 'CURRENT_PROPOSAL_CANARY'}, session, memory, 'Agent_1')
        self.apply('challenge', {'proposal_id': 'P2', 'content': 'Check it'}, session, memory)
        from contest_observation import open_proposals
        self.assertEqual(open_proposals(memory, session, config('vallina_otc')), ('P2',))

    def test_native_review_schema_contains_no_old_hashes(self):
        session, memory = self.state()
        cfg = config('vallina_otc')
        actions = _actions_for_agent(_resolved_actions(manifest(), cfg), session, cfg, 'Agent_2',
                                    memory=memory, answer_sheet_contest=True)
        self.assertNotIn('review_answer', {a.name for a in actions})
        self.apply('work', {'content': 'Final answer: 42'}, session, memory, 'Agent_1')
        actions = _actions_for_agent(_resolved_actions(manifest(), cfg), session, cfg, 'Agent_2',
                                    memory=memory, answer_sheet_contest=True)
        review = next(a for a in actions if a.name == 'review_answer')
        hashes = next(a.enum for a in review.arguments if a.name == 'version_hash')
        self.assertEqual(hashes, (session.active_task.versions[-1].version_hash,))

    def test_duplicate_from_old_round_is_fresh_without_old_author_or_review(self):
        session, memory = self.state()
        previous = session.active_task.versions[-1]
        self.apply('work', {'content': previous.content}, session, memory)
        current = session.active_task.versions[-1]
        self.assertNotEqual(current.version_hash, previous.version_hash)
        self.assertEqual(current.author, 'Agent_2')
        self.assertTrue(session.version_created_this_turn(current.version_hash))
        self.assertEqual(len(current_session(session).active_task.versions), 1)

    def test_old_triage_and_budget_history_not_exposed(self):
        session, memory = self.state()
        session.set_triage('q1', 'hopeless', reason='OLD_TRIAGE_CANARY', actor='Agent_1', turn=1)
        self.apply('inspect_problem', {'problem_id': 'q1'}, session, memory)
        receipt = memory.archival_snapshot()['events'][-1]['payload']
        self.assertEqual(receipt['triage_reason'], '')
        self.assertEqual(receipt['priority'], 'normal')
        self.apply('check_budget', {}, session, memory)
        receipt = memory.archival_snapshot()['events'][-1]['payload']
        self.assertEqual(receipt['tasks'][0]['versions'], 0)

    def test_fresh_scoreboard_event_cannot_republish_old_task_history(self):
        from contest_lifecycle import _record_scoreboard
        session, memory = self.state()
        session.set_triage('q1', 'hopeless', reason='Old assessment',
                           actor='OLD_TRIAGE_AUTHOR_CANARY', turn=1)
        _record_scoreboard(memory, session)
        self.assertIn('OLD_TRIAGE_AUTHOR_CANARY', memory.to_checkpoint_json())
        prompt = _user_prompt(manifest(), session, memory, config('vallina_otc'), 'Agent_2')
        self.assertNotIn('OLD_TRIAGE_AUTHOR_CANARY', prompt)

    def test_old_native_proposal_enums_removed_even_with_new_proposal(self):
        session, memory = self.state()
        session.budget.turns_used = 1
        self.apply('propose', {'content': 'Old claim'}, session, memory, 'Agent_1')
        session.budget.turns_used = 2
        self.apply('propose', {'content': 'Current claim'}, session, memory, 'Agent_1')
        cfg = config('vallina_otc')
        actions = _actions_for_agent(_resolved_actions(manifest(), cfg), session, cfg,
                                    'Agent_2', memory=memory, answer_sheet_contest=True)
        challenge = next(a for a in actions if a.name == 'challenge')
        self.assertEqual(next(a.enum for a in challenge.arguments if a.name == 'proposal_id'), ('P2',))

    def test_legacy_checkpoint_rejected_before_model_call(self):
        engine = _ContestEngine(manifest(), Mock(), config('vallina_otc'))
        saved = engine._checkpoint()
        saved['engine_state']['settings'].pop('current_turn_context_version')
        query = Mock(side_effect=AssertionError('Must not call model'))
        with self.assertRaisesRegex(ValueError, 'runtime version/settings mismatch'):
            run_contest(manifest(), query, config('vallina_otc'), session_checkpoint=saved,
                        memory_checkpoint=engine.memory.to_checkpoint_json())
        query.assert_not_called()

    def test_stateless_focus_rotates_using_round_number(self):
        from dataclasses import replace
        case = replace(manifest(), tasks=(manifest().tasks[0],
            replace(manifest().tasks[0], task_id='q2', parent_problem_id='q2')))
        engine = _ContestEngine(case, Mock(), config('vallina_otc', max_turns=3))
        for turn, expected in [(1, 'q1'), (2, 'q2'), (3, 'q1')]:
            engine.session.budget.turns_used = turn
            self.assertTrue(engine._prepare_agent(_AgentTurn('Agent_1')))
            self.assertEqual(engine.session.active_task.task_id, expected)

    def test_code_and_samples_expire_without_implicit_old_source_submission(self):
        from test_otc_rulecard import icpc_manifest, ICPC
        from contest_config import ContestRunConfig
        cfg = ContestRunConfig('vallina_otc', 3, 4, rule_card=ICPC)
        engine = _ContestEngine(icpc_manifest(), Mock(), cfg,
            task_action_executor=Mock(return_value={'valid': True, 'sample_verdict': 'AC',
                                                    'sample_summary': 'OLD_SAMPLE_CANARY'}))
        engine.session.budget.turns_used = 1
        engine.session.select_task('p1')
        turn = _AgentTurn('Agent_1', action='execute_code',
                          arguments={'code': '# OLD_SOURCE_CANARY\nprint(42)'})
        self.assertTrue(engine._apply_agent_action(turn))
        old = engine.session.active_task.versions[-1]
        engine.session.budget.turns_used = 2
        prompt = _user_prompt(engine.manifest, engine.session, engine.memory, cfg, 'Agent_2')
        self.assertNotIn('OLD_SOURCE_CANARY', prompt)
        self.assertNotIn('OLD_SAMPLE_CANARY', prompt)
        before_calls = engine.executor.call_count
        self.assertFalse(engine._apply_agent_action(_AgentTurn('Agent_1', action='submit_code')))
        self.assertEqual(engine.executor.call_count, before_calls)
        self.assertEqual(engine.session.active_task.versions[-1], old)

    def test_fresh_and_resumed_engine_never_send_old_content_to_model(self):
        class Interrupted(BaseException):
            pass
        def execute(interrupt):
            captured, saved = [], []
            cfg = config('vallina_otc', max_turns=3)
            def round_number(user):
                return json.JSONDecoder().raw_decode(user.split('BUDGET ', 1)[1])[0]['turns_used']
            def query(system, user):
                if 'BUDGET ' not in user:
                    return 'Static blind briefing.'
                turn = round_number(user)
                captured.append((turn, system, user, None))
                return f'PRIVATE_CANARY_ROUND_{turn}'
            def request(req):
                turn = round_number(req.user_prompt)
                captured.append((turn, req.system_prompt, req.user_prompt, req.tools))
                name, args = 'rest', {'reason': 'Await current round work'}
                if turn == 1:
                    name, args = ('work', {'content': 'DRAFT_CANARY_ROUND_1\nFinal answer: 42'}) if req.metadata['agent'] == 'Agent_1' else (
                        'speak', {'content': 'PUBLIC_CANARY_ROUND_1'})
                elif turn == 2 and req.metadata['agent'] == 'Agent_1':
                    name, args = 'inspect_problem', {'problem_id': 'q1'}
                return LLMResponse('', 'mock', 'strict', tool_calls=(LLMToolCall(name, args),),
                                   usage={'api_calls': 1, 'output_tokens': 1})
            def checkpoint(session, memory):
                if interrupt and not saved and session['budget']['turns_used'] == 2:
                    saved[:] = [json.loads(json.dumps(session)), memory]
                    raise Interrupted()
            kwargs = dict(action_request_fn=request, coach_query_fn=query, checkpoint_callback=checkpoint)
            try:
                result = run_contest(manifest(), query, cfg, **kwargs)
            except Interrupted:
                result = run_contest(manifest(), query, cfg, session_checkpoint=saved[0],
                                     memory_checkpoint=saved[1], **kwargs)
            self.assertEqual(result['submissions']['q1'], 'DRAFT_CANARY_ROUND_1\nFinal answer: 42')
            self.assertIn('DRAFT_CANARY_ROUND_1', json.dumps(result['session_checkpoint']))
            self.assertTrue(any('DRAFT_CANARY_ROUND_1' in user for turn, _, user, _ in captured if turn == 1))
            for turn, system, user, schema in captured:
                if turn > 1:
                    visible = json.dumps([system, user, schema])
                    for canary in ('DRAFT_CANARY_ROUND_1', 'PUBLIC_CANARY_ROUND_1', 'PRIVATE_CANARY_ROUND_1'):
                        self.assertNotIn(canary, visible)
                if schema is not None:
                    self.assertIn(f'PRIVATE_CANARY_ROUND_{turn}', user)
            self.assertEqual(result['memory_action_policy']['context_scope'], 'current_team_round_only')
        execute(False)
        execute(True)


if __name__ == '__main__':
    unittest.main()
