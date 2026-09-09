from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_manifest import ContestManifest, load_contest_manifest  # noqa: E402
from run_contest_smoke import run_pair  # noqa: E402


class ContestMatchedSmokeTests(unittest.TestCase):
    def test_hard_first_problem_preserves_strategic_switch_under_same_limits(self) -> None:
        full = load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "icpc_wf_2012_5.json",
            benchmark_root=REPO_ROOT / "data" / "benchmarks",
        )
        manifest = ContestManifest(
            session_id="icpc-two-smoke",
            competition_id=full.competition_id,
            tasks=full.tasks[:2],
        )
        pair = run_pair(
            manifest,
            max_turns=10,
            max_api_calls=30,
            max_tokens=10000,
        )
        vanilla = pair["results"]["vanilla_team"]
        strategic = pair["results"]["strategic_team"]

        self.assertTrue(pair["matched_constraints"]["action_sets_equal"])
        self.assertEqual(
            vanilla["budget"]["max_api_calls"],
            strategic["budget"]["max_api_calls"],
        )
        self.assertEqual(vanilla["diagnostics"]["switch_count"], 0)
        self.assertGreater(strategic["diagnostics"]["switch_count"], 0)


if __name__ == "__main__":
    unittest.main()
