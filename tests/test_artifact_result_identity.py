"""Completed artifact reuse requires identity, submission and score bindings."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from artifacts.assets import file_sha256
from contest_run_identity import content_hash
from evaluation.models import CriterionResult, EvaluationResult
from otc_artifact_pipeline import run_artifact_contest, _evaluation_binding
from saved_run_metrics import ensure_coordination
from llm import LLMResponse


class ArtifactResultIdentityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        settings = {"run": "A", "config": {"team_size": 2, "system_variant": "centralized"},
                    "evaluation": {"judge_collab": True, "required_metrics_version": 1}}
        self.identity = {"settings": settings, "fingerprint": content_hash(settings)}
        self.rubric = self.root / "rubric.json"
        self.write("rubric.json", {"rubric_id": "r", "title": "R", "total_points": 1,
            "criteria": [{"id": "c", "name": "C", "max_score": 1, "description": "Evidence"}]})
        settings['evaluation'].update(provider='openai', model='mock', rubric_sha256=file_sha256(self.rubric))
        self.identity['fingerprint'] = content_hash(settings)
        source = self.root / "submission.txt"
        source.write_text("Submitted answer", encoding="utf-8")
        pdf = self.root / "submission.pdf"
        pdf.write_bytes(b"%PDF-1.4 fixture")
        receipt = {"source": str(source), "source_sha256": file_sha256(source),
                   "pdf": str(pdf), "pdf_sha256": file_sha256(pdf)}
        evaluation = EvaluationResult("fixture", "1", "1", "mock", "r",
            [CriterionResult("c", 1, 1, ["Evidence"], "Fixture", 1)], 1, 1).to_dict()
        self.result = {"status": "complete", "graded": True, "run_identity": self.identity,
            "artifact": receipt, "evaluation": evaluation,
            "contest_file": str(self.root / "contest_session.json"),
            "evaluation_binding": _evaluation_binding(self.identity, receipt, evaluation)}
        self.contest = {"run_identity": self.identity, "system_variant": "centralized", "memory": {"events": []},
                        "submissions": {"deliverable": "Submitted answer"},
                        "session_checkpoint": {"final_summary": {}}}
        self.write("run_identity.json", self.identity)
        self.write("contest_session.json", self.contest)
        self.prepared = {"output": self.root, "identity": self.identity, "rubric": self.rubric,
                         "judge_provider": "openai", "judge_model": "mock"}
        (self.root / 'coordination_task.txt').write_text('Fixture task', encoding='utf-8')
        ensure_coordination(self.root, result=self.result, task_text='Fixture task',
                            judge_provider='openai', judge_model='mock',
                            judge_request=lambda _: LLMResponse('{"score":4}', 'openai', 'mock'))

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def resume(self):
        self.write("result.json", self.result)
        no_call = Mock(side_effect=AssertionError("No model calls during completed reuse"))
        try:
            return run_artifact_contest(self.prepared, resume=True,
                                        agent_request=no_call, judge_request=no_call)
        finally:
            no_call.assert_not_called()

    def test_valid_complete_result_is_reused_exactly(self):
        resumed = self.resume()
        for key in self.result:
            self.assertEqual(resumed[key], self.result[key])
        self.assertEqual(resumed['required_metrics']['CS'], 2)

    def test_foreign_result_is_refused_even_when_directory_identity_matches(self):
        self.result["run_identity"] = {"settings": {"run": "B"},
                                       "fingerprint": content_hash({"run": "B"})}
        with self.assertRaisesRegex(ValueError, "configuration mismatch"):
            self.resume()

    def test_missing_result_identity_is_refused(self):
        del self.result["run_identity"]
        with self.assertRaisesRegex(ValueError, "missing resolved run identity"):
            self.resume()

    def test_score_cannot_be_swapped_without_changing_binding(self):
        self.result["evaluation"]["total_score"] = 0
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.resume()

    def test_invalid_score_is_rejected_even_with_recomputed_binding(self):
        self.result["evaluation"]["total_score"] = 0
        self.result["evaluation_binding"] = _evaluation_binding(
            self.identity, self.result["artifact"], self.result["evaluation"])
        with self.assertRaisesRegex(ValueError, "criterion sum"):
            self.resume()

    def test_receipt_cannot_point_to_another_submission(self):
        self.contest["submissions"]["deliverable"] = "Different answer"
        self.write("contest_session.json", self.contest)
        with self.assertRaisesRegex(ValueError, "finalized submission"):
            self.resume()

    def test_foreign_session_is_rejected(self):
        self.contest["run_identity"] = {"settings": {"run": "B"},
                                       "fingerprint": content_hash({"run": "B"})}
        self.write("contest_session.json", self.contest)
        with self.assertRaisesRegex(ValueError, "configuration mismatch"):
            self.resume()

    def test_tampered_pdf_is_rejected(self):
        Path(self.result["artifact"]["pdf"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "modified"):
            self.resume()

    def test_ungraded_complete_marker_is_rejected(self):
        self.result["graded"] = False
        with self.assertRaisesRegex(ValueError, "successful evaluation"):
            self.resume()

    def test_legacy_unbound_result_is_not_certified(self):
        del self.result["evaluation_binding"]
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.resume()

    def test_backfill_cached_metrics_preserves_historical_result_and_session(self):
        import evaluate_saved_metrics as backfill
        self.write('result.json', self.result)
        result_bytes = (self.root / 'result.json').read_bytes()
        session_bytes = (self.root / 'contest_session.json').read_bytes()
        with patch.object(backfill, 'resolve_request_fn', side_effect=AssertionError('No provider initialization for cached scores')):
            row = backfill.process_run(self.root)
        self.assertEqual(row['status'], 'complete')
        self.assertEqual(row['CS'], 2)
        self.assertEqual((self.root / 'result.json').read_bytes(), result_bytes)
        self.assertEqual((self.root / 'contest_session.json').read_bytes(), session_bytes)

    def test_backfill_refuses_tampered_task_score_before_judge_calls(self):
        import evaluate_saved_metrics as backfill
        self.result['evaluation']['total_score'] = 0
        self.write('result.json', self.result)
        with patch.object(backfill, 'resolve_request_fn', side_effect=AssertionError('Invalid scores must not call judges')):
            with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                backfill.process_run(self.root)


if __name__ == "__main__":
    unittest.main()
