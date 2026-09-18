from __future__ import annotations

import io
import os
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import run_competition_batch as cli
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import ContestRunConfig, _system_prompt, _resolved_actions, run_contest
from llm import LLMResponse, LLMToolCall


def example(competition="icpc"):
    return ContestManifest("settings-test", competition, (
        ManifestTask("q1", "q1", None, "Compute 6*7", "quiz", 1, False,
                     {"problem_id": "q1", "gold_label": {"expected_answer": "42"}}),
    ))


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class ContestSettingsTests(unittest.TestCase):
    def setUp(self):
        # CLI main loads .env; do not leak remote judge settings into later tests.
        env_patch = patch.dict(os.environ)
        env_patch.start()
        self.addCleanup(env_patch.stop)


    def prepare(self, *flags, competition="icpc"):
        args = cli._build_parser().parse_args([
            "--live", "--contest-manifest", "fixture.json", "--system-variant", "decentralized", *flags,
        ])
        with patch.object(cli, "load_contest_manifest", return_value=example(competition)):
            return cli._prepare_contest_run(args)


    def test_review_override_controls_both_gates(self):
        config = review_ablation_config(3, 12, require_review=False)
        self.assertFalse(config.review_required)
        self.assertFalse(config.final_review_required)


    def test_rule_options_with_off_mode_are_not_silently_ignored(self):
        for flags in (("--rules-root", "custom"), ("--rules-strict",)):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                self.prepare(*flags)


    def test_final_only_review_is_actually_executable(self):
        def request(req):
            functions = {item["name"]: item for item in req.tools}
            if req.metadata.get("task_id") is None and "select_problem" in functions:
                name, arguments = "select_problem", {"problem_id": "q1"}
            elif "review_answer" in functions:
                props = functions["review_answer"]["parameters"]["properties"]
                name, arguments = "review_answer", {
                    "problem_id": props["problem_id"]["enum"][0],
                    "version_hash": props["version_hash"]["enum"][0],
                    "decision": "approve", "content": "Verified 6 times 7 is 42",
                }
            elif "submit" in functions:
                props = functions["submit"]["parameters"]["properties"]
                name, arguments = "submit", ({"answer": "42"} if "answer" in props else {})
            elif "work" in functions:
                name, arguments = "work", {"content": "42"}
            else:
                name, arguments = "rest", {}
            return LLMResponse("", "perplexity", "mock", tool_calls=(LLMToolCall(name, arguments),))
        sheet = example("arml_local")
        sheet = replace(sheet, tasks=(*sheet.tasks, replace(sheet.tasks[0], task_id="q2", parent_problem_id="q2")))
        for variant in ("decentralized", "centralized"):
            with self.subTest(variant=variant):
                result = run_with_test_plan(
                    sheet, lambda *_: "{}", ContestRunConfig(
                        variant, 2, 5, require_review=False, require_final_review=True,
                    ), action_request_fn=request, action_transport="native",
                    coach_query_fn=(lambda *_: "{}") if variant == "centralized" else None,
                )
                kinds = [event["kind"] for event in result["memory"]["events"]]
                self.assertIn("final_review_approved", kinds)
                self.assertIn("final_review_completed", kinds)
                self.assertFalse(result["baseline"]["review_workflow"])
                self.assertTrue(result["final_review_required"])


if __name__ == "__main__":
    unittest.main()
