from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment


SOLUTION = (
    "w = int(input())\n"
    'print("YES" if w > 2 and w % 2 == 0 else "NO")\n'
)


class VJudgeTurnLoopTests(unittest.TestCase):
    def _submit(self, remote: dict) -> tuple[OlympiadEnvironment, dict]:
        env = OlympiadEnvironment("codeforces", "cf_4A", max_turns=8)
        with (
            patch.dict(
                "os.environ",
                {
                    "VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787",
                    "VJUDGE_CONTEST_ID": "845103",
                    "VJUDGE_PROBLEM": "A",
                },
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                return_value=remote,
            ),
        ):
            response = json.loads(
                env.execute_action("Agent_1", "submit_code", SOLUTION)
            )
        return env, response


    def test_submit_final_remote_wa_keeps_run_open(self):
        env = OlympiadEnvironment("codeforces", "cf_4A", max_turns=8)
        remote = {"status": "final", "verdict": "WA", "run_id": "44"}
        with (
            patch.dict(
                "os.environ",
                {
                    "VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787",
                    "VJUDGE_CONTEST_ID": "845103",
                    "VJUDGE_PROBLEM": "A",
                },
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                return_value=remote,
            ),
        ):
            response = json.loads(
                env.execute_action("Agent_1", "submit", SOLUTION)
            )

        self.assertEqual(response["remote"]["verdict"], "WA")
        self.assertFalse(env.submitted)
        self.assertTrue(response["continue_allowed"])


    def test_deferred_icpc_problem_uses_remote_judge_without_local_package(self):
        env = OlympiadEnvironment("icpc", "icpc_wf_2012_bustour", max_turns=4)
        captured = {}

        def fake_submit(**kwargs):
            captured.update(kwargs)
            return {"status": "final", "verdict": "AC", "run_id": "100"}

        with (
            patch.dict(
                "os.environ",
                {"VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787"},
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                side_effect=fake_submit,
            ),
            patch(
                "evaluation.programming_judge.judge_programming_submission"
            ) as local_judge,
        ):
            response = json.loads(
                env.execute_action("Agent_1", "submit_code", "print('candidate')")
            )

        local_judge.assert_not_called()
        self.assertEqual(response["verdict"], "AC")
        self.assertEqual(response["test_scope"], "remote")
        self.assertEqual(captured.get("oj"), "Kattis")
        self.assertEqual(captured.get("problem"), "bustour")
        self.assertTrue(env.submitted)


if __name__ == "__main__":
    unittest.main()
