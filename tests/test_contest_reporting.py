import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from contest_reporting import report_row, metered_judge


class ReportingTests(unittest.TestCase):
    def test_scores_zero_is_valid_and_disabled_is_missing(self):
        row = report_row({"grade": {"score": 0, "max_score": 40}})
        self.assertEqual(row["accuracy"], 0)
        self.assertEqual(row["CS"], "N/A")
        self.assertEqual(json.loads(row["missing_reasons"])["CS"], "judge_disabled")
        self.assertEqual(row["eval_api_calls"], 0)

    def test_coordination_mean_and_failure(self):
        result = {"metrics": {"communication_score": 4, "planning_score": 2}}
        self.assertEqual(report_row(result)["CS"], 3)
        result["evaluation_stages"] = {"coordination": {"status": "failed", "error": "bad JSON"}}
        row = report_row(result)
        self.assertEqual(row["Communication"], "N/A")
        self.assertEqual(json.loads(row["missing_reasons"])["CS"], "bad JSON")

    def test_usage_is_separate_and_accumulates_across_attempts(self):
        result = {"budget": {"tokens_used": 123, "api_calls_used": 10}}
        response = SimpleNamespace(usage={"api_calls": 2, "output_tokens": 17})
        metered_judge(lambda r: response, result)(None)
        metered_judge(lambda r: response, result)(None)
        def fail(request):
            raise ValueError("failed")
        with self.assertRaises(ValueError):
            metered_judge(fail, result)(None)
        self.assertEqual(result["evaluation_usage"]["api_calls"], 5)
        self.assertEqual(result["evaluation_usage"]["output_tokens"], 34)
        self.assertEqual(result["evaluation_usage"]["unmetered_calls"], 1)
        self.assertEqual(result["budget"]["tokens_used"], 123)

    def test_unmetered_historical_judge_is_not_zero(self):
        result = {"run_identity": {"settings": {"evaluation": {"judge_collab": True}}}}
        self.assertEqual(report_row(result)["eval_tokens"], "N/A")

    def test_missing_denominator_and_nan(self):
        self.assertEqual(report_row({"grade": {"score": 1, "max_score": 0}})["accuracy"], "N/A")
        self.assertEqual(report_row({"metrics": {"communication_score": float('nan')}})["Communication"], "N/A")

    def test_single_agent_collaboration_is_not_applicable(self):
        row = report_row({"system_variant": "single_agent", "metrics": {"communication_score": 0, "planning_score": 0}})
        self.assertEqual(row["CS"], "N/A")
        self.assertEqual(json.loads(row["missing_reasons"])["CS"], "not_applicable_single_agent")
