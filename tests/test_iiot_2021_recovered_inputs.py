"""Source recovery must not silently turn unpaired inputs into official tests."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IIOT2021RecoveryTests(unittest.TestCase):
    def test_input_counts_hashes_and_judge_only_boundary(self):
        expected = [0, 33, 41, 35, 32, 28, 32, 35]
        for prefix in ['data', 'data/mini_data']:
            rows = json.loads((ROOT / prefix / 'benchmarks/iiot/benchmark.json').read_text())
            selected = sorted([r for r in rows if r.get('year') == 2021], key=lambda r: r['problem_id'])
            self.assertEqual(len(selected), 8)
            for row, count in zip(selected, expected):
                evaluation = row['evaluation']
                self.assertEqual(evaluation['archived_test_inputs'], count)
                self.assertEqual(evaluation['official_test_pair_count'], 0)
                self.assertEqual(evaluation['official_execution_status'], 'not_ready')
                self.assertFalse(evaluation['execution_verified'])
                self.assertEqual(evaluation['grading_policy'], 'source_review_llm_v1')
                assets = [a for a in row['assets'] if '/tests/' in a['path']]
                self.assertEqual(len(assets), count)
                for asset in assets:
                    self.assertEqual(asset['role'], 'judge_only')
                    self.assertTrue(asset['path'].startswith(prefix + '/'))
                    self.assertEqual(hashlib.sha256((ROOT / asset['path']).read_bytes()).hexdigest(), asset['sha256'])

    def test_chimneys_uses_quality_ratio_not_exact_output(self):
        rows = json.loads((ROOT / 'data/benchmarks/iiot/benchmark.json').read_text())
        row = next(r for r in rows if r['problem_id'] == 'iiot_2021_01')
        self.assertEqual(row['evaluation']['official_scoring_mode'], 'minimum_case_quality_ratio_per_subtask')
        self.assertEqual(row['evaluation']['official_max_score'], 100)
        for result in row['evaluation']['reference_execution_validation']['samples']:
            self.assertTrue(result['valid_construction'])
            self.assertFalse(result['score_validated'])


if __name__ == '__main__':
    unittest.main()
