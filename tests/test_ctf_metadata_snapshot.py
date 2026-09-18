"""Active CTF snapshots expose one current, hash-bound readiness contract."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class CtfMetadataSnapshotTests(unittest.TestCase):
    def test_active_rows_have_no_superseded_readiness_copy(self):
        for catalog in ('data', 'data/mini_data'):
            for track in ('cybench', 'nyu_ctf_bench'):
                for row in read(ROOT / catalog / 'benchmarks' / track / 'benchmark.json'):
                    with self.subTest(catalog=catalog, problem=row['problem_id']):
                        self.assertNotIn('remaining_limitations', row['source_review'])
                        binding = row['evaluation']['runtime_validation']
                        raw = (ROOT / binding['report']).read_bytes()
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), binding['report_sha256'])
                        report = json.loads(raw)
                        entry = next(r for r in report['records'] if r['problem_id'] == row['problem_id'])
                        self.assertEqual(entry['status'], 'passed')

    def test_mini_evaluation_matches_current_main_and_scorecards(self):
        for track in ('cybench', 'nyu_ctf_bench'):
            main = {r['problem_id']: r for r in read(ROOT / 'data/benchmarks' / track / 'benchmark.json')}
            mini = read(ROOT / 'data/mini_data/benchmarks' / track / 'benchmark.json')
            cards = read(ROOT / 'data/mini_data/rubrics/task_scorecards' / (track + '.json'))
            self.assertEqual([r['problem_id'] for r in cards['records']], [r['problem_id'] for r in mini])
            for row, card in zip(mini, cards['records']):
                with self.subTest(problem=row['problem_id']):
                    actual = json.loads(json.dumps(row['evaluation']).replace('data/mini_data/', 'data/'))
                    expected = main[row['problem_id']]['evaluation']
                    for key in set(expected) - {'runtime_validation'}:
                        self.assertEqual(actual[key], expected[key])
                    self.assertEqual(card, scorecard(row, ROOT))
                    local_report = (ROOT / row['evaluation']['runtime_validation']['report']).resolve()
                    self.assertTrue(local_report.is_relative_to(ROOT / 'data/mini_data'))
                    self.assertEqual(row['evaluation']['runtime_validation']['report_sha256'],
                                     expected['runtime_validation']['report_sha256'])


if __name__ == '__main__':
    unittest.main()
