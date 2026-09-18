"""All pipeline CLI writers must own the output lock before touching state."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import run_pipeline as pipeline


class PipelineLockingTests(unittest.TestCase):
    def test_second_writer_cannot_touch_registry_or_status(self):
        for stage in ("all", "register", "run", "report"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                out = Path(directory)
                (out / "pipeline.lock").write_text("existing-supervisor", encoding="utf-8")
                pipeline.write(out / "registry.json", {"jobs": []})
                pipeline.write(out / "batch_status.json", {"jobs": {}, "counts": {}})
                before = {p.name: p.read_bytes() for p in out.iterdir()}
                with patch.object(sys, "argv", ["pipeline", stage, "--model", "mock", "--output", str(out)]), \
                     patch.object(pipeline, "register", side_effect=AssertionError("Premature registration")), \
                     patch.object(pipeline, "report", side_effect=AssertionError("Premature reporting")):
                    with self.assertRaises(FileExistsError):
                        pipeline.main()
                self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, before)

    def test_registration_and_final_report_hold_the_same_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            phases = []
            def register(path):
                phases.append("register")
                self.assertTrue((path / "pipeline.lock").is_file())
                return {"jobs": []}
            def report(path, registry, states):
                phases.append("report")
                self.assertTrue((path / "pipeline.lock").is_file())
            with patch.object(sys, "argv", ["pipeline", "all", "--model", "mock", "--output", str(out)]), \
                 patch.object(pipeline, "register", side_effect=register), \
                 patch.object(pipeline, "report", side_effect=report):
                self.assertEqual(pipeline.main(), 0)
            self.assertEqual(phases, ["register", "report"])
            self.assertFalse((out / "pipeline.lock").exists())

    def test_failure_releases_only_the_lock_we_acquired(self):
        for stage in ("all", "register", "run", "report"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                out = Path(directory)
                pipeline.write(out / "registry.json", {"jobs": []})
                with patch.object(sys, "argv", ["pipeline", stage, "--model", "mock", "--output", str(out)]), \
                     patch.object(pipeline, "register", side_effect=RuntimeError("registration failed")), \
                     patch.object(pipeline, "report", side_effect=RuntimeError("report failed")):
                    with self.assertRaises(RuntimeError):
                        pipeline.main()
                self.assertFalse((out / "pipeline.lock").exists())

    def test_nonpositive_pilot_limit_fails_before_any_output(self):
        for limit in ("0", "-1"):
            with self.subTest(limit=limit), tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / "new-output"
                with patch.object(sys, "argv", ["pipeline", "all", "--model", "mock", "--output", str(out), "--limit", limit]), \
                     patch.object(pipeline, "register", side_effect=AssertionError("Invalid limit started work")), \
                     redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        pipeline.main()
                self.assertEqual(raised.exception.code, 2)
                self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
