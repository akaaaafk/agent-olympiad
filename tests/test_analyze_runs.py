"""Focused tests for the deterministic run-analysis CLI."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analyze_runs import (
    analyze_files,
    compute_decompositions,
    main,
    normalized_task_score,
    group_summaries,
)


class AnalyzeRunsTests(unittest.TestCase):
    @staticmethod
    def controls():
        return dict(provider='tinker', model='mock', temperature=0.2, max_turns=10,
                    max_api_calls=None, max_tokens=None, max_output_tokens=8192,
                    protocol_version='current', source_hashes={'runner.py': 'hash'},
                    evaluation={'judge_model': 'judge'}, rules_identity='public-rules-hash')

    def paired_rows(self):
        return [dict(competition='demo', problem_id='p1', team='model', schema=c,
                     condition=c, grade_score=score, grade_max_score=10,
                     comparison_controls=self.controls())
                for c, score in [('solo', 4), ('subagent', 6), ('team', 8)]]

    def test_changed_controls_never_produce_cross_setting_gains(self):
        for key, value in [('provider', 'other'), ('temperature', 0.8), ('max_turns', 90),
                           ('max_tokens', 100), ('source_hashes', {'runner.py': 'changed'}),
                           ('evaluation', {'judge_model': 'other'}), ('rules_identity', 'other')]:
            rows=self.paired_rows()
            rows[-1]['comparison_controls'][key]=value
            with self.subTest(key=key):
                result=compute_decompositions(rows)
                self.assertEqual(len(result), 2)
                self.assertTrue(all(r['division_gain'] is None and r['cohesion_gain'] is None for r in result))

    def test_missing_controls_are_unverified_and_not_averaged(self):
        rows=self.paired_rows()
        for row in rows:
            del row['comparison_controls']
        results=compute_decompositions(rows)
        self.assertTrue(all(not r['comparison_verified'] and r['division_gain'] is None for r in results))
        self.assertTrue(all('unverified_settings' in r['gain_reason'] for r in results))
        self.assertEqual(len(group_summaries([dict(rows[0]), dict(rows[0])])), 2)

    def test_saved_identity_controls_override_display_values(self):
        rows=self.paired_rows()
        for row in rows:
            c=row.pop('comparison_controls')
            row['run_identity']={'settings': {
                'config': {'max_turns': c.pop('max_turns'), 'max_api_calls': None,
                           'max_tokens': None, 'system_variant': row['condition'],
                           'rule_guidance': 'OFFICIAL COMPETITION RULES (shared by every baseline)\n{"competition_id":"demo"}\nBENCHMARK ADAPTATION'},
                'execution': {'provider': c.pop('provider'), 'model': c.pop('model'),
                              'temperature': c.pop('temperature'), 'max_output_tokens': c.pop('max_output_tokens')},
                'protocol_version': 'current', 'source_hashes': c['source_hashes'],
                'evaluation': c['evaluation']}}
        self.assertEqual(len(compute_decompositions(rows)), 1)
        self.assertIsNone(compute_decompositions(rows)[0]['gain_reason'])
        rows[-1]['run_identity']['settings']['config']['max_turns']=90
        rows[-1]['max_turns']=10
        self.assertEqual(len(compute_decompositions(rows)), 2)

    def test_group_means_separate_provider_and_budget(self):
        rows=[self.paired_rows()[0] for _ in range(3)]
        rows[1]['comparison_controls']['provider']='other'
        rows[2]['comparison_controls']['max_turns']=90
        groups=group_summaries(rows)
        self.assertEqual(len(groups), 3)
        self.assertTrue(all(g['runs']==1 for g in groups))

    def test_normalized_score_and_complete_decomposition(self):
        rows = [
            {
                "competition": "demo",
                "problem_id": "p1",
                "team": "gpt",
                "condition": "solo",
                "grade_score": 4,
                "grade_max_score": 10,
            },
            {
                "competition": "demo",
                "problem_id": "p1",
                "team": "gpt",
                "condition": "subagent",
                "grade_score": 6,
                "grade_max_score": 10,
            },
            {
                "competition": "demo",
                "problem_id": "p1",
                "team": "gpt",
                "condition": "team",
                "grade_score": 8,
                "grade_max_score": 10,
                "transcript_ceiling": 0.9,
            },
        ]
        for row in rows:
            row['comparison_controls'] = self.controls()
        self.assertEqual(normalized_task_score(rows[0]), 0.4)
        result = compute_decompositions(rows)[0]
        self.assertAlmostEqual(result["division_gain"], 0.2)
        self.assertAlmostEqual(result["cohesion_gain"], 0.2)
        self.assertAlmostEqual(result["synthesis_loss"], 0.1)
        self.assertIsNone(result["gain_reason"])

    def test_decomposition_missing_data_is_null_with_reason(self):
        result = compute_decompositions(
            [
                {
                    "competition": "demo",
                    "problem_id": "p1",
                    "condition": "team",
                    "grade_score": 1,
                    "grade_max_score": 2,
                }
            ]
        )[0]
        self.assertIsNone(result["division_gain"])
        self.assertIsNone(result["cohesion_gain"])
        self.assertIn("solo", result["gain_reason"])
        self.assertIsNone(result["synthesis_loss"])
        self.assertEqual(result["synthesis_loss_reason"], "missing_transcript_ceiling")

    def test_cli_writes_analysis_and_errors_csv(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            transcript = root / "transcript.json"
            transcript.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "agents": ["Leader", "Worker"],
                            "allowed_tools": ["execute_code"],
                        },
                        "chat_history": [
                            {"sender": "Leader", "message": "Can you check this?"},
                            {"sender": "Worker", "message": "pass"},
                        ],
                        "action_log": [
                            {
                                "turn": 2,
                                "agent": "Leader",
                                "action": "submit_final",
                                "payload": "long enough final answer",
                                "result": "ok",
                            }
                        ],
                        "submission": {"final_answer": "long enough final answer"},
                    }
                ),
                encoding="utf-8",
            )
            phase = root / "phase.json"
            phase.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "competition": "demo",
                                "problem_id": "p1",
                                "schema": "centralized",
                                "grade_score": 1,
                                "grade_max_score": 2,
                                "transcript_path": "transcript.json",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            analysis, errors = analyze_files([phase])
            self.assertEqual(analysis["runs"][0]["normalized_task_score"], 0.5)
            self.assertIsNotNone(analysis["runs"][0]["team_metrics"])
            self.assertTrue(errors)

            output = root / "output"
            self.assertEqual(main([str(phase), "--output-dir", str(output)]), 0)
            analysis_path = output / "analysis.json"
            errors_path = output / "errors.csv"
            self.assertTrue(analysis_path.is_file())
            self.assertTrue(errors_path.is_file())
            emitted = json.loads(analysis_path.read_text(encoding="utf-8"))
            self.assertEqual(emitted["schema_version"], "team-analysis.v1")
            with errors_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertIn("code", rows[0])
            self.assertFalse(any(path.suffix == ".tmp" for path in output.iterdir()))


if __name__ == "__main__":
    unittest.main()
