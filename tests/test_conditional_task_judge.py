import hashlib
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contest_task_judge import judge_task, task_judge_specs
from contest_manifest import ManifestTask, ContestManifest
from contest_run_identity import pending_contest_evaluations
from evaluation.rubric_llm import RubricDocumentEvaluator
from evaluation.models import load_rubric
from llm import LLMRequest, LLMResponse, make_perplexity_responses_caller
from judge_references import winner_references, with_winner_references, benchmark_for_asset


def task(track):
    row = json.loads((ROOT / 'data/benchmarks' / track / 'benchmark.json').read_text(encoding='utf-8'))[0]
    return ManifestTask(row['problem_id'], row['problem_id'], None, row['problem_description'], 'general', 1, False, row)


class ConditionalJudgeTests(unittest.TestCase):
    def judge(self, request):
        rubric = json.loads(request.user_prompt.split('STRUCTURED RUBRIC:\n\n')[1].split('\n\n')[0])
        self.assertEqual(request.purpose, 'evaluation')
        return LLMResponse(json.dumps(dict(criteria=[dict(id=c['id'], score=c['max_score'], max_score=c['max_score'],
            evidence=['submission evidence'], justification='fixture', confidence=1, observable=c['observable'])
            for c in rubric['criteria']], total_score=rubric['total_points'], max_score=rubric['total_points'])), 'mock', 'mock')

    def test_observable_denominators(self):
        for track, maximum, original in [('ethics_bowl_appe',30,60), ('ethics_bowl_nhseb',15,60), ('ichto',9,9), ('fyziklani',100,100)]:
            with self.subTest(track=track):
                row = judge_task(task(track), 'submission evidence', self.judge)
                self.assertEqual(row['max_score'], maximum)
                self.assertEqual(row['original_rubric_max_score'], original)
                self.assertFalse(row['official_score_equivalent'])

    def test_long_inputs_not_clipped(self):
        rubric = load_rubric(ROOT/'data/rubrics/worked_answer_100_v1.json')
        evaluator = RubricDocumentEvaluator(self.judge, rubric, task_text='T'*13000+'TASK_END',
            submission_text='S'*17000+'SUBMISSION_END', reference_text='R'*13000+'REFERENCE_END')
        prompt = evaluator._user_prompt()
        for marker in ('TASK_END', 'SUBMISSION_END', 'REFERENCE_END'):
            self.assertIn(marker, prompt)

    def test_empty_submission_finishes_without_judge_call(self):
        forbidden=Mock(side_effect=AssertionError('No API call for empty submission'))
        row=judge_task(task('ichto'),' ',forbidden)
        self.assertEqual((row['score'],row['max_score']),(0,9))
        forbidden.assert_not_called()

    def test_pending_binds_submission(self):
        t = task('ichto'); manifest = ContestManifest('x','ichto',(t,))
        identity = {'settings': {'evaluation': {'task_judges':task_judge_specs(manifest)}}}
        result = {'submissions':{t.task_id:'submission evidence'}, 'task_judgements':{t.task_id:judge_task(t,'submission evidence',self.judge)}}
        self.assertEqual(pending_contest_evaluations(result, identity), [])
        result['submissions'][t.task_id] += ' changed'
        self.assertEqual(pending_contest_evaluations(result, identity), ['task:'+t.task_id])

    def test_winners_judge_only_and_year_matched(self):
        refs = winner_references('jessup_2024')
        self.assertEqual(len(refs),1)
        self.assertEqual(winner_references('jessup_2023'),[])
        sink = Mock(return_value=None)
        wrapped = with_winner_references(sink,refs)
        with self.assertRaises(ValueError):
            wrapped(LLMRequest('system','solver',purpose='action'))
        sink.assert_not_called()
        wrapped(LLMRequest('system','grade',purpose='evaluation'))
        self.assertEqual(sink.call_args.args[0].attachments[0].role,'judge_only')
        self.assertIn('no known numeric calibration',sink.call_args.args[0].user_prompt)
        with self.assertRaises(ValueError):
            benchmark_for_asset('jessup', refs[0]['sha256'])

    def test_resume_retries_only_failed_task(self):
        from run_competition_batch import _run_contest_auxiliary_judges
        from contest_adapters import grade_contest_result
        one = replace(task('ichto'), task_id='one')
        two = replace(one, task_id='two')
        manifest = ContestManifest('x','ichto',(one,two))
        identity = {'settings': {'evaluation': {'task_judges':task_judge_specs(manifest)}}}
        result = dict(submissions={'one':'submission evidence','two':'submission evidence'},
                      memory={'events':[]},metrics={},diagnostics={})
        result['grade'] = grade_contest_result(manifest,result)
        requests = Mock(side_effect=[RuntimeError('temporary fixture failure'),self.judge_response(),self.judge_response()])
        args=dict(request_fn=requests,cce_request_fn=None,persist=lambda:None)
        config=SimpleNamespace(team_size=1,system_variant='single_agent')
        self.assertEqual(_run_contest_auxiliary_judges(result,manifest,config,identity,**args),['task:one'])
        self.assertIn('two',result['task_judgements'])
        self.assertEqual(_run_contest_auxiliary_judges(result,manifest,config,identity,**args),[])
        self.assertEqual(requests.call_count,3)
        self.assertTrue(result['grade']['graded'])

    def judge_response(self):
        rubric=load_rubric(ROOT/task('ichto').benchmark['evaluation']['rubric_path'])
        request=RubricDocumentEvaluator(self.judge,rubric,submission_text='submission evidence')
        return self.judge(LLMRequest('system',request._user_prompt(),purpose='evaluation'))

    def test_provider_alias_roundtrip(self):
        response=Mock(ok=True)
        response.json.return_value={'output':[{'type':'function_call','name':'contest_web_search','arguments':'{"query":"x"}','call_id':'1'}]}
        tools=({'type':'function','name':'web_search','parameters':{'type':'object'}},)
        with patch.dict('os.environ',{'PERPLEXITY_API_KEY':'test'}), patch('requests.post',return_value=response) as post:
            result=make_perplexity_responses_caller('mock')(LLMRequest('system','user',tools=tools))
        self.assertEqual(post.call_args.kwargs['json']['tools'][0]['name'],'contest_web_search')
        self.assertEqual(result.tool_calls[0].name,'web_search')
        self.assertEqual(tools[0]['name'],'web_search')


if __name__ == '__main__':
    unittest.main()
