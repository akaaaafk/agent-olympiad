import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from evaluation.reference_answers import reference_matches
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from scripts.build_verified_mini_dataset import edition_members


class ReferenceAnswersTests(unittest.TestCase):
    def test_rebuild_preserves_reviewed_text_hunt_and_paired_eoes(self):
        for track, year, ids in [('mystery_hunt', 2012, ['mystery_hunt_01610']),
                                 ('eoes', 2021, ['eoes_t1', 'eoes_t2'])]:
            rows = json.loads((ROOT / 'data/benchmarks' / track / 'benchmark.json').read_text(encoding='utf-8'))
            self.assertEqual([r['problem_id'] for r in edition_members(track, rows, year)], ids)
            with self.assertRaises(ValueError):
                edition_members(track, [], year)
        self.assertEqual(edition_members('mystery_hunt', rows, 2011), [])

    def test_set_reorders_but_rejects_missing_duplicate_extra(self):
        spec = dict(kind='unordered_set', items=['EE', 'HH', 'GG'])
        self.assertTrue(reference_matches(spec, 'GG, EE, HH'))
        for value in ['EE HH', 'EE EE GG', 'EE HH GG II', '']:
            self.assertFalse(reference_matches(spec, value))

    def test_sequence_requires_order(self):
        spec = dict(kind='ordered_sequence', items=['C', 'D', 'A', 'E', 'B'])
        self.assertTrue(reference_matches(spec, 'C D A E B'))
        self.assertFalse(reference_matches(spec, 'A B C D E'))

    def test_range_units_and_bounds(self):
        spec = dict(kind='range', minimum=20e6, maximum=100e6,
                    units={'million years': 1e6, 'years': 1})
        for value in ['20-100 million years', '60 million years', '60000000 years']:
            self.assertTrue(reference_matches(spec, value), value)
        for value in ['19 million years', '101 million years', '30-60 million years',
                      '60 seconds', '60', '-60 million years', '1e999 years', 'NaN years']:
            self.assertFalse(reference_matches(spec, value), value)

    def test_actual_science_answer_sheet_full_correct_blank_and_wrong(self):
        row = json.loads((ROOT / 'data/mini_data/benchmarks/science_olympiad/benchmark.json').read_text(encoding='utf-8'))[0]
        parts = load_gold_parts(row['gold_label'])
        correct = '\n'.join(f'{p.id}. {p.expected}' for p in parts)
        result = GoldAnswerEvaluator(parts, correct).evaluate()
        self.assertEqual(result.total_score, 100, [(c.id, c.evidence) for c in result.criteria if not c.score])
        self.assertEqual(result.max_score, 100)
        self.assertEqual(GoldAnswerEvaluator(parts, '').evaluate().total_score, 0)
        self.assertEqual(GoldAnswerEvaluator(parts, '\n'.join(f'{p.id}. WRONG' for p in parts)).evaluate().total_score, 0)

    def test_science_aliases_and_set_sequence_flow(self):
        row = json.loads((ROOT / 'data/mini_data/benchmarks/science_olympiad/benchmark.json').read_text(encoding='utf-8'))[0]
        parts = load_gold_parts(row['gold_label'])
        result = GoldAnswerEvaluator(parts, '3. Caloris Basin\n9. N L K F D\n23. 4 billion years ago\n49. A B C D E\n95. GG HH EE').evaluate()
        self.assertEqual(result.total_score, 4)


if __name__ == '__main__':
    unittest.main()
