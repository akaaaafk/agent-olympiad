import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from contest_adapters import _grade_non_programming


class GoldEncodingTests(unittest.TestCase):
    def test_qanta_reviewed_answerlines_on_actual_adapter(self):
        rows = {r['problem_id']: r for r in json.loads((ROOT / 'data/benchmarks/qanta/benchmark.json').read_text(encoding='utf-8'))}
        cases = [
            ('qanta_train_39387', ['Doppler effect', 'Doppler shift'], ['red shift']),
            ('qanta_train_83383', ['Fever', 'pyrexia'], ['hyperthermia']),
            ('qanta_train_126396', ['trumpet'], ['Carson']),
            ('qanta_train_107061', ['voltage', 'electric potential'], ['vector potential']),
            ('qanta_train_161577', ['acetic acid', 'ethanoic acid'], ['CH3COOH']),
        ]
        for pid, accepted, rejected in cases:
            row = rows[pid]
            task = SimpleNamespace(benchmark=row, task_type=row['task_type'], question_id=None, max_score=1)
            for answer in accepted:
                with self.subTest(pid=pid, answer=answer):
                    self.assertEqual(_grade_non_programming(task, answer, 'qanta'), (1, 1))
            for answer in ['', *rejected]:
                with self.subTest(pid=pid, answer=answer):
                    self.assertEqual(_grade_non_programming(task, answer, 'qanta'), (0, 1))

    def test_qanta_curated_mapping_and_mini_do_not_restore_annotations(self):
        main = {r['problem_id']:r for r in json.loads((ROOT/'data/benchmarks/qanta/benchmark.json').read_text(encoding='utf-8'))}
        for base in ('data', 'data/mini_data'):
            rows = json.loads((ROOT/base/'benchmarks/qanta/benchmark.json').read_text(encoding='utf-8'))
            mapping = json.loads((ROOT/base/'rubrics/qanta_short_answers.json').read_text(encoding='utf-8'))
            for row in rows:
                pid=row['problem_id'];part=row['gold_label']['parts'][0]
                self.assertEqual(part['expected'],main[pid]['gold_label']['parts'][0]['expected'])
                self.assertEqual(mapping[pid]['1']['expected'],part['expected'])
                self.assertEqual(mapping[pid]['1'].get('aliases',[]),part.get('aliases',[]))

    def rows(self, competition, problem_id):
        for base in ('data', 'data/mini_data'):
            rows = json.loads((ROOT / base / 'benchmarks' / competition / 'benchmark.json').read_text(encoding='utf-8'))
            yield next(r for r in rows if r['problem_id'] == problem_id)

    def test_qanta_acceptance_annotation_is_not_required_answer_text(self):
        for row in self.rows('qanta', 'qanta_train_119982'):
            for answer in ('zero', 'nothing', '0'):
                result = GoldAnswerEvaluator(load_gold_parts(row['gold_label']), answer).evaluate()
                self.assertEqual(result.total_score, 1)

    def test_science_bowl_superscripts_and_explicit_exclusion_survive(self):
        for row in self.rows('science_bowl', 'science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_17'):
            self.assertIn('x^6', row['problem_description'])
            parts = load_gold_parts(row['gold_label'])
            self.assertEqual(GoldAnswerEvaluator(parts, '30/x^7').evaluate().total_score, 1)
            self.assertEqual(GoldAnswerEvaluator(parts, '30x^-7').evaluate().total_score, 0)


if __name__ == '__main__':
    unittest.main()
