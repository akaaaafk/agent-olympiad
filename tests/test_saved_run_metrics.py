import json
from hashlib import sha256
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from saved_run_metrics import ensure_coordination, coordination_complete, flat_metrics, valid_coordination, task_context_judge
from llm import LLMResponse, LLMRequest


class SavedMetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.session = dict(system_variant='centralized', run_identity={'settings': {
            'config': {'team_size': 2, 'system_variant': 'centralized'},
            'execution': {'provider': 'tinker'}, 'evaluation': {'judge_collab': True}}},
            memory={'events': [{'actor': 'Agent_1', 'kind': 'speak', 'payload': {'content': 'Please verify Q1.'}}]},
            budget={'turns_used': 3, 'api_calls_used': 5, 'tokens_used': 123, 'wall_seconds_used': 12},
            grade={'score': 8, 'max_score': 10})
        self.write_session()
        self.result = dict(evaluation={'total_score': 80, 'max_score': 100},
            task_evaluation_usage={'api_calls': 1, 'output_tokens': 7, 'sec': 1})
        self.judge = Mock(return_value=LLMResponse('{"score":4,"justification":"fixture"}', 'tinker', 'mock', {'output_tokens': 3}))

    def write_session(self):
        (self.output / 'contest_session.json').write_text(json.dumps(self.session), encoding='utf-8')

    def evaluate(self, **changes):
        options=dict(result=self.result, task_text='Task text', judge_request=self.judge,
                     judge_provider='tinker', judge_model='mock')
        options.update(changes)
        return ensure_coordination(self.output, **options)

    def test_scores_flat_report_and_separate_usage(self):
        raw = (self.output / 'contest_session.json').read_bytes()
        saved = self.evaluate()
        self.assertTrue(coordination_complete(self.output, self.result))
        flat = flat_metrics(self.session, self.result, saved)
        self.assertEqual([flat[k] for k in ('score', 'max_score', 'accuracy', 'Communication', 'Planning', 'CS')],
                         [80, 100, .8, 4, 4, 4])
        self.assertEqual(flat['api_calls'], 5)
        self.assertEqual(flat['eval_api_calls'], 3)
        self.assertEqual(flat['eval_tokens'], 13)
        self.assertEqual((self.output / 'contest_session.json').read_bytes(), raw)
        self.evaluate(judge_request=Mock(side_effect=AssertionError('Cached run must not call judges')))

    def test_nan_or_invalid_planning_is_pending_and_not_cached(self):
        for score in ('NaN', '0', '6'):
            with self.subTest(score=score):
                path=self.output / 'coordination_required.json'
                path.unlink(missing_ok=True)
                judge=Mock(side_effect=[LLMResponse('{"score":4}', 'tinker', 'mock'),
                                        LLMResponse('{"score":'+score+'}', 'tinker', 'mock')])
                saved=self.evaluate(judge_request=judge)
                self.assertEqual(saved['status'], 'failed')
                self.assertFalse(coordination_complete(self.output, self.result))
                self.assertEqual(flat_metrics(self.session,self.result,saved)['CS'], 'N/A')
                retry=Mock(return_value=LLMResponse('{"score":3}', 'tinker', 'mock'))
                self.assertEqual(self.evaluate(judge_request=retry)['coordination']['coordination_score'],3.5)
                self.assertEqual(retry.call_count,1)

    def test_changed_evidence_or_outcome_invalidates_cache(self):
        self.evaluate()
        self.session['memory']['events'][0]['payload']['content']='Different evidence'
        self.write_session()
        self.assertFalse(coordination_complete(self.output,self.result))
        self.evaluate()
        self.assertEqual(self.judge.call_count,4)
        self.result['evaluation']['total_score']=81
        self.assertFalse(coordination_complete(self.output,self.result))
        self.evaluate()
        self.assertEqual(self.judge.call_count,6)

    def test_no_communication_is_zero_not_judge_failure(self):
        self.session['memory']['events']=[]
        self.write_session()
        saved=self.evaluate()
        self.assertEqual(saved['coordination']['communication_score'],0)
        self.assertEqual(saved['coordination']['coordination_score'],2)
        self.assertEqual(self.judge.call_count,1)

    def test_single_agent_explicit_not_applicable_without_calls(self):
        self.session['system_variant']='single_agent'
        self.session['run_identity']['settings']['config'].update(system_variant='single_agent',team_size=1)
        self.write_session()
        saved=self.evaluate()
        self.assertEqual(saved['status'],'not_applicable')
        self.assertTrue(coordination_complete(self.output,self.result))
        self.assertEqual(flat_metrics(self.session,self.result,saved)['CS'],'N/A')
        self.judge.assert_not_called()

    def test_inconsistent_mean_is_not_complete(self):
        self.assertFalse(valid_coordination(dict(communication_score=4,planning_score=3,coordination_score=4)))

    def test_scanned_task_context_is_bound_to_original_input_and_not_attached_to_planning(self):
        task=self.output/'task.pdf';task.write_bytes(b'%PDF-1.4 synthetic media')
        digest=sha256(task.read_bytes()).hexdigest()
        self.session['run_identity']['settings']['execution'].update(task_pdf_sha256=digest,task_pages=[1,1])
        (self.output/'coordination_task_assets.json').write_text(json.dumps(dict(path=str(task),sha256=digest,pages=[1,1])),encoding='utf-8')
        judge=task_context_judge(self.output,self.session,self.judge,'openai')
        judge(LLMRequest('system','communication',purpose='collaboration_communication_score'))
        self.assertEqual(self.judge.call_args.args[0].attachments[0].path,task)
        judge(LLMRequest('system','planning',purpose='collaboration_planning_score'))
        self.assertEqual(self.judge.call_args.args[0].attachments,())
        task.write_bytes(b'Changed media')
        with self.assertRaisesRegex(ValueError,'differs from original'):
            task_context_judge(self.output,self.session,self.judge,'openai')

    def test_historical_unknown_rubric_usage_is_not_reported_as_zero(self):
        saved=self.evaluate()
        del self.result['task_evaluation_usage']
        self.session['run_identity']['settings']['evaluation']={}
        flat=flat_metrics(self.session,self.result,saved)
        self.assertEqual(flat['eval_api_calls'],'N/A')


if __name__=='__main__':
    unittest.main()
