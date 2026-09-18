"""Check year-specific case grading and explicit archival adaptation identity."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from otc_artifact_pipeline import prepare_artifact_run
from evaluation.models import load_rubric


class CaseJudgeTests(unittest.TestCase):
    def test_all_new_cases_have_distinct_bound_rubrics(self):
        rows = json.loads((ROOT / 'data/benchmarks/gcch_harvard/benchmark.json').read_text(encoding='utf-8'))
        rubrics = set()
        for row in rows:
            if row['year'] == 2021:
                continue
            p = ROOT / row['evaluation']['rubric_path']
            rubric = load_rubric(p)
            rubrics.add(p)
            self.assertEqual(rubric.total_points, 100)
            self.assertEqual(len(rubric.criteria), 5)
            self.assertNotIn('Nvidia', p.read_text(encoding='utf-8'))
            self.assertFalse(row['evaluation']['official_score_equivalent'])
        self.assertEqual(len(rubrics), 6)

    def test_adaptation_is_visible_and_changes_run_identity(self):
        rows = json.loads((ROOT / 'data/benchmarks/gcch_harvard/benchmark.json').read_text(encoding='utf-8'))
        row = next(r for r in rows if r['year'] == 2026)
        pdf = ROOT / next(a['path'] for a in row['assets'] if a['role'] == 'agent_visible')
        with tempfile.TemporaryDirectory() as temp, patch('otc_artifact_pipeline.preflight_renderer'):
            def prepare(value):
                with patch('judge_references.benchmark_for_asset', return_value=value):
                    return prepare_artifact_run(competition='gcch_harvard', task_pdf=pdf,
                        rubric=ROOT / value['evaluation']['rubric_path'],
                        output=Path(temp), max_turns=1, system_variant='single_agent',
                        provider='openai', model='mock', judge_model='mock')
            original = prepare(row)
            self.assertIn('explicitly adapted offline benchmark permits AI-generated decks', original['manifest'].tasks[0].prompt)
            changed = deepcopy(row)
            changed['evaluation']['benchmark_instructions'] += ' Changed scoring scope.'
            self.assertNotEqual(original['identity']['fingerprint'], prepare(changed)['identity']['fingerprint'])


if __name__ == '__main__':
    unittest.main()
