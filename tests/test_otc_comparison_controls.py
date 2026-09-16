"""Regression seams from the ARML 2012 paired-request diagnosis."""
import json
import sys
import unittest
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_checkpoint_cursor import config, manifest
from contest_engine import _ContestEngine, _AgentTurn
from contest_memory import ContestMemory
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from contest_policy import _card_focus_task
from strategy import StrategicPolicy
import run_competition_batch as cli


class SamplingControlsTests(unittest.TestCase):
    def test_cli_text_call_sends_the_requested_sampling_settings(self):
        response=Mock(ok=True)
        response.json.return_value={'output':[{'content':[{'type':'output_text','text':'thought'}]}]}
        with patch.dict('os.environ',{'PERPLEXITY_API_KEY':'offline-test'}), patch('requests.post',return_value=response) as post:
            call=cli._make_live_query('perplexity','test-model',temperature=0.13,max_output_tokens=321)
            self.assertEqual(call('system','user'),'thought')
        payload=post.call_args.kwargs['json']
        self.assertEqual(payload.get('temperature'),0.13)
        self.assertEqual(payload['max_output_tokens'],321)


class SharedSchedulingTests(unittest.TestCase):
    def state(self):
        s=ContestSession([TaskUnit('q1',kind='non_programming'),TaskUnit('q2',kind='non_programming')],ContestBudgetState(max_turns=20))
        m=ContestMemory(run_id='comparison',session_id='fixture',competition_id='arml_local')
        s.select_task('q1');s.create_answer('Final answer: 11',author='Agent_2')
        s.select_task('q2');s.create_answer('Final answer: 22',author='Agent_3')
        s.budget.turns_used=3
        return s,m

    def append(self,m,kind,turn,actor='Agent_1',task='q1'):
        m.append(task_id=task,question_id=None,actor=actor,visibility='public',kind=kind,
                 payload={'content':'Already checked; unchanged.'},turn=turn)

    def test_empty_second_round_has_same_rotation_for_both_conditions(self):
        one=manifest();two=replace(one,tasks=one.tasks+(replace(one.tasks[0],task_id='q2',parent_problem_id='q2'),))
        selected=[]
        for name in ('vallina_otc','otc'):
            e=_ContestEngine(two,Mock(return_value='Prepare and verify.'),config(name,max_turns=3))
            e._prepare_coach();e.session.budget.turns_used=2
            order=list(e.session._tasks)
            e._prepare_agent(_AgentTurn('Agent_1'))
            selected.append(e.session.active_task.task_id)
            self.assertEqual(list(e.session._tasks),order)
        self.assertEqual(selected,['q2','q2'])

    def test_rejected_candidate_precedes_an_unreviewed_peer(self):
        s,m=self.state()
        s.record_task_review('q2','Agent_2','Counterexample; repair needed.',decision='reject')
        focus=_card_focus_task(s,m,'Agent_1',None,StrategicPolicy(),review_required=True)
        self.assertEqual(focus.task_id,'q2')

    def test_two_status_only_visits_yield_to_another_candidate(self):
        s,m=self.state()
        for turn in (1,2):self.append(m,'speak',turn)
        focus=_card_focus_task(s,m,'Agent_1',None,StrategicPolicy(),review_required=True)
        self.assertEqual(focus.task_id,'q2')

    def test_current_round_filter_does_not_use_old_status_visits(self):
        from contest_observation import current_memory
        s,m=self.state()
        for turn in (1,2):self.append(m,'speak',turn)
        focus=_card_focus_task(s,current_memory(m,3),'Agent_1',None,StrategicPolicy(),review_required=True)
        self.assertEqual(focus.task_id,'q1')

    def test_new_visible_evidence_resets_the_report_streak(self):
        from contest_policy import _card_repeated_math_report
        s,m=self.state()
        self.append(m,'speak',1)
        self.append(m,'work',2,actor='Agent_2')
        self.append(m,'speak',2)
        self.assertIsNone(_card_repeated_math_report(m,'Agent_1'))

    def test_private_peer_evidence_is_not_used_by_the_scheduler(self):
        from contest_policy import _card_repeated_math_report
        s,m=self.state()
        self.append(m,'speak',1)
        m.append(task_id='q1',question_id=None,actor='Agent_2',visibility='private',recipients=('Agent_2',),
                 kind='provide_evidence',payload={'content':'Private claim'},turn=2)
        self.append(m,'speak',2)
        self.assertEqual(_card_repeated_math_report(m,'Agent_1'),'q1')

    def test_yield_does_not_bypass_work_or_review_assignments(self):
        s,m=self.state()
        for turn in (1,2):self.append(m,'speak',turn)
        focus=_card_focus_task(s,m,'Agent_1',None,StrategicPolicy(),review_required=True,
                              work_task_ids={'q1'},review_task_ids={'q1'})
        self.assertIsNone(focus)


class FrozenCoachTests(unittest.TestCase):
    def test_cli_preflight_binds_the_contents_of_the_brief(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'brief.txt';path.write_text('Shared opening A',encoding='utf-8')
            args=cli._build_parser().parse_args(['--contest-manifest','unused.json','--system-variant','otc',
                                               '--coach-brief-file',str(path)])
            with patch.object(cli,'load_contest_manifest',return_value=manifest()):
                _,first,_,identity_a=cli._prepare_contest_run(args)
                path.write_text('Shared opening B',encoding='utf-8')
                _,second,_,identity_b=cli._prepare_contest_run(args)
            self.assertEqual(first.precontest_brief,'Shared opening A')
            self.assertEqual(second.precontest_brief,'Shared opening B')
            self.assertNotEqual(identity_a,identity_b)

    def test_oversize_shared_brief_fails_before_a_model_call(self):
        with self.assertRaisesRegex(ValueError,'character limit'):
            replace(config('otc'),precontest_brief='x'*10000)
    def test_one_supplied_brief_is_identical_without_an_extra_model_call(self):
        brief='Allocate time, verify arithmetic independently, and reconcile the answer sheet.'
        for name in ('otc','vallina_otc'):
            query=Mock(side_effect=AssertionError('A supplied brief must not call the model'))
            e=_ContestEngine(manifest(),query,replace(config(name),precontest_brief=brief))
            e._prepare_coach()
            self.assertEqual(e.coach_guidance,brief)
            self.assertEqual(e.session.budget.api_calls_used,0)
            events=[v for v in e.memory.archival_snapshot()['events'] if v['kind']=='precontest_coach_guidance']
            self.assertEqual(len(events),1)
            self.assertEqual(events[0]['payload']['source'],'provided')
            self.assertIn('precontest_brief_sha256',e._runtime_settings())
            e._prepare_coach()
            query.assert_not_called()

    def test_supplied_brief_cannot_enable_coach_on_plain_baselines(self):
        with self.assertRaisesRegex(ValueError,'Coach'):
            replace(config('decentralized'),precontest_brief='Advice')

    def test_resume_cannot_change_the_frozen_brief(self):
        first=replace(config('otc'),precontest_brief='Brief one')
        e=_ContestEngine(manifest(),Mock(),first);e._prepare_coach()
        saved=e._checkpoint()
        with self.assertRaisesRegex(ValueError,'runtime version/settings mismatch'):
            _ContestEngine(manifest(),Mock(),replace(first,precontest_brief='Brief two'),
                session_checkpoint=saved,memory_checkpoint=e.memory.to_checkpoint_json())


if __name__=='__main__':unittest.main()
