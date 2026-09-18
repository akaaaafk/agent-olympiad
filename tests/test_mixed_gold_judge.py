"""Gold scores remain deterministic and cannot be replaced by rubric judgment."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from contest_manifest import ManifestTask
from contest_task_judge import judge_task
from llm import LLMResponse


class MixedGoldJudgeTests(unittest.TestCase):
    def test_real_packets_keep_gold_and_llm_weights_separate(self):
        rows=json.loads((ROOT/'data/benchmarks/hmmt_team/benchmark.json').read_text(encoding='utf8'))
        calls=[]
        def judge(request):
            prompt=request.user_prompt
            schema=json.loads(prompt.split('STRUCTURED RUBRIC:\n\n')[1].split('\n\n')[0])
            calls.append(schema)
            return LLMResponse(json.dumps(dict(criteria=[dict(id=c['id'],score=c['max_score'],max_score=c['max_score'],
                evidence=['fixture evidence'],justification='fixture',confidence=1,observable=c['observable']) for c in schema['criteria']],
                total_score=schema['total_points'],max_score=schema['total_points'])),'mock','mock')
        count=0
        for row in rows:
            exact=[p for p in row['gold_label']['parts'] if p.get('expected') is not None]
            task=ManifestTask(row['problem_id'],row['problem_id'],None,row['problem_description'],'math',row['total_points'],False,row)
            with self.subTest(packet=row['problem_id']):
                submission='\n'.join(f"{p['id']}. {p['expected']}" for p in exact)+'\nProof evidence for remaining parts.'
                correct=judge_task(task,submission,judge)
                self.assertEqual(correct['score'],row['total_points'])
                self.assertEqual(correct['max_score'],row['total_points'])
                gold_ids={f"problem_{p['id']}" for p in exact}
                self.assertTrue(gold_ids.isdisjoint(c['id'] for c in calls[-1]['criteria']))
                wrong=judge_task(task,'Proof evidence only; no numbered final answers.',judge)
                self.assertEqual(wrong['score'],row['total_points']-sum(p['points'] for p in exact))
                count+=len(exact)
        self.assertEqual(count,31)

    def test_llm_only_receives_remaining_criteria(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'rubric.json'
            path.write_text(json.dumps(dict(rubric_id='test',title='test',total_points=30,
                criteria=[dict(id='problem_1',name='answer',max_score=10,description='gold'),
                          dict(id='problem_2',name='proof',max_score=20,description='proof')])) )
            row=dict(competition_id='hmmt_team',evaluation=dict(rubric_path=str(path),grading_policy='gold_else_llm_v1'),
                gold_label=dict(parts=[dict(id='1',points=10,expected='16',match_mode='normalized'),
                                       dict(id='2',points=20,expected=None,match_mode='reference_llm')]))
            task=ManifestTask('packet','packet',None,'test','math',30,False,row)
            evaluator=MagicMock()
            evaluator.return_value.evaluate.return_value.to_dict.return_value=dict(total_score=7,max_score=20)
            with patch('contest_task_judge.RubricDocumentEvaluator',evaluator), \
                 patch('judge_references.winner_references',return_value=[]), \
                 patch('rules.loader.load_rule_card',return_value=None), \
                 patch('numeric_gold_check.check_submission',return_value=None):
                result=judge_task(task,'1. 16\n2. partial proof',lambda *_: '')
            self.assertEqual(result['score'],17)
            self.assertEqual(result['max_score'],30)
            self.assertEqual([c.id for c in evaluator.call_args.kwargs['rubric'].criteria],['problem_2'])
            self.assertEqual(result['gold_part_ids'],['1'])

    def test_empty_submission_scores_zero_without_llm(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'rubric.json'
            path.write_text(json.dumps(dict(rubric_id='test',title='test',total_points=10,
                criteria=[dict(id='problem_1',name='answer',max_score=10,description='answer')])) )
            row=dict(evaluation=dict(rubric_path=str(path),grading_policy='gold_else_llm_v1'),
                     gold_label=dict(parts=[dict(id='1',points=10,expected='16')]))
            task=ManifestTask('packet','packet',None,'test','math',10,False,row)
            with patch('contest_task_judge.RubricDocumentEvaluator') as evaluator, \
                 patch('numeric_gold_check.check_submission',return_value=None):
                result=judge_task(task,'',None)
            evaluator.assert_not_called()
            self.assertEqual(result['score'],0)
            self.assertEqual(result['max_score'],10)

    def test_source_maximum_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'rubric.json'
            path.write_text(json.dumps(dict(rubric_id='test',title='test',total_points=10,
                criteria=[dict(id='problem_1',name='answer',max_score=10,description='answer')])) )
            row=dict(evaluation=dict(rubric_path=str(path),grading_policy='gold_else_llm_v1'),
                     gold_label=dict(parts=[dict(id='1',points=20,expected='16')]))
            task=ManifestTask('packet','packet',None,'test','math',10,False,row)
            with self.assertRaisesRegex(ValueError,'maxima disagree'):
                judge_task(task,'1. 16',None)

    def test_finalizer_cannot_bypass_remaining_proof_parts(self):
        from evaluation.finalize import apply_registered_judge
        row=json.loads((ROOT/'data/benchmarks/hmmt_team/benchmark.json').read_text(encoding='utf8'))[0]
        with patch('contest_task_judge.judge_task',return_value=dict(score=50,max_score=250)) as judge:
            scored=apply_registered_judge(row,'submission',dict(method='gold_answer_v1',graded=True,score=250),request_fn=lambda *_:'')
        judge.assert_called_once()
        self.assertEqual(scored['score'],50)
        self.assertFalse(scored['correct'])


if __name__=='__main__':unittest.main()
