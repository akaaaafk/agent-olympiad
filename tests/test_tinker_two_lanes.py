import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_tinker_two_lanes as runner


class LaneTests(unittest.TestCase):
    def test_second_lane_uses_second_key_without_mutating_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = [dict(id=f"job{i}", variant="single_agent", run_identity={}) for i in range(2)]
            registry = dict(jobs=jobs, data=str(root), file_hashes={})
            original = os.environ.get("TINKER_API_KEY")
            with patch.object(runner, "inspect_contest_run", return_value=("new", {})), patch.object(
                runner.subprocess, "run", return_value=SimpleNamespace(returncode=1)
            ) as run:
                runner.lane(root, registry, 1, "test-second-key")
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.kwargs["env"]["TINKER_API_KEY"], "test-second-key")
                self.assertIn("--judge-collab", run.call_args.args[0])
                self.assertEqual(os.environ.get("TINKER_API_KEY"), original)
            state = json.loads((root / "lane2.json").read_text())
            self.assertEqual(state[0]["id"], "job1")
            self.assertEqual(state[0]["status"], "failed")

    def test_changed_source_prevents_any_paid_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = dict(jobs=[dict(id="job")], file_hashes={str(root / "absent"): "old"})
            with patch.object(runner.subprocess, "run") as run, self.assertRaisesRegex(RuntimeError, "changed"):
                runner.lane(root, registry, 0, "test-key")
            run.assert_not_called()
