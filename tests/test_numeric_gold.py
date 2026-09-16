import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from evaluation.numeric import compare_numeric
from evaluation.models import EvaluationError
from numeric_gold_check import load_packet, check_submission, numeric_identity


def spec(value='1', unit='m', tolerance='0'):
    return dict(value=value, unit=unit, abs_tol=tolerance, rel_tol='0', tolerance_basis='test fixture')


class NumericGoldTests(unittest.TestCase):
    def test_gold_evaluator_numeric_and_zero(self):
        from evaluation.gold import load_gold_parts, GoldAnswerEvaluator
        parts=load_gold_parts({'parts':[dict(id='1', expected=0, points=1, match_mode='numeric', numeric_spec=spec('0'))]})
        self.assertEqual(GoldAnswerEvaluator(parts,'0 cm').evaluate().total_score,1)
        self.assertEqual(GoldAnswerEvaluator(parts,'1 cm').evaluate().total_score,0)

    def test_conversions(self):
        for target, answer in [(spec(), '100 cm'), (spec('10','m/s'),'36 km/h'),
                (spec('10','degC'),'283.15 K'), (spec('75','nm'),'7.5e-8 m'),
                (spec('0.5',''),'50%'), (spec('-0.40','m'),'−40 cm')]:
            with self.subTest(answer=answer):
                self.assertTrue(compare_numeric(target,answer)['correct'])

    def test_boundaries(self):
        self.assertTrue(compare_numeric(spec('1','m','0.005'),'1.005 m')['correct'])
        self.assertFalse(compare_numeric(spec('1','m','0.005'),'1.005001 m')['correct'])
        self.assertFalse(compare_numeric(spec('0','m'),'0.0001 m')['correct'])

    def test_rejects_unsafe_ambiguous_values(self):
        for answer in ['NaN m','inf m','1e999 m','1 s','1','1 m or 2 m','1+0 m','__import__("os")']:
            self.assertFalse(compare_numeric(spec(),answer)['correct'],answer)
        for change in [dict(abs_tol='-1'),dict(unit='unknown'),dict(tolerance_basis=''),dict(allow_implicit_unit=1)]:
            with self.assertRaises(EvaluationError):
                compare_numeric({**spec(),**change},'1 m')

    def rows(self):
        return json.loads((ROOT/'data/benchmarks/fyziklani/benchmark.json').read_text(encoding='utf-8'))

    def test_verified_five(self):
        total=0
        for row in self.rows():
            packet=load_packet(row)
            if not packet: continue
            answer='\n'.join(f"{p['id']}: {p['numeric_spec']['value']} {p['numeric_spec']['unit']}" for p in packet[0]['parts'])
            result=check_submission(row,answer)
            self.assertEqual(result['correct_count'],result['checked_parts'])
            self.assertFalse(result['included_in_rubric_score'])
            self.assertLess(result['coverage'],1)
            total+=result['checked_parts']
        self.assertEqual(total,5)

    def test_duplicate_missing_and_intermediate(self):
        row=next(r for r in self.rows() if r['problem_id']=='fyziklani_2013')
        for answer in ['', 'FoL.1: 3.60 m', 'FoL.1: -0.40 m\nFoL.1: -0.40 m']:
            self.assertEqual(check_submission(row,answer)['correct_count'],0)
        result=check_submission(row,'FoL.1: -0.40 m\nFoL.2: 75 nm\nFoL.3: 999 m')
        self.assertEqual(result['correct_count'],2)

    def test_source_hash_and_role(self):
        row=self.rows()[0]
        bad=copy.deepcopy(row)
        bad['assets']=[a for a in bad['assets'] if a['role']!='judge_only']
        with self.assertRaises(ValueError): load_packet(bad)
        original=Path.read_bytes
        def tamper(path):
            return b'tampered' if path.name=='fyziklani_2012_en.pdf' else original(path)
        with patch.object(Path,'read_bytes',tamper):
            with self.assertRaises(ValueError): load_packet(row)
        self.assertIn('registry_sha256',numeric_identity(row))

    def test_post_submission_score_and_isolation(self):
        from test_conditional_task_judge import task, ConditionalJudgeTests
        from contest_task_judge import judge_task
        seen=[]
        fixture=ConditionalJudgeTests()
        def judge(request):
            seen.append(request)
            self.assertNotIn('numeric_spec',request.user_prompt)
            self.assertNotIn('half-unit',request.user_prompt)
            self.assertTrue(all(a.role!='judge_only' for a in request.attachments))
            return fixture.judge(request)
        result=judge_task(task('fyziklani'),'FoL.1: 0.46 rad',judge)
        self.assertEqual(result['score'],100)
        self.assertEqual(result['numeric_gold_check']['correct_count'],1)
        self.assertTrue(seen)


if __name__=='__main__': unittest.main()
