import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import run_competition_batch as runner


class BaselineEntrypointTests(unittest.TestCase):
    def test_explicit_baselines_cannot_fall_back_to_legacy_batch(self):
        for variant in runner.BASELINE_NAMES:
            with self.subTest(variant=variant):
                stderr = io.StringIO()
                with patch.object(sys, "argv", ["runner", "--system-variant", variant]), \
                     patch.object(runner, "load_repo_dotenv"), \
                     patch.object(runner, "_select_cases") as select_cases, \
                     contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as error:
                        runner.main()
                self.assertEqual(error.exception.code, 2)
                self.assertIn("requires --contest-manifest", stderr.getvalue())
                select_cases.assert_not_called()

    def test_manifest_preserves_selected_pair(self):
        for variant in ("vallina_otc", "otc"):
            args = runner._build_parser().parse_args([
                "--contest-manifest", "data/contest_manifests/generated/arml_local_2009.json",
                "--system-variant", variant,
            ])
            self.assertEqual(args.system_variant, variant)
            self.assertEqual(runner.BASELINES[variant].memory_actions, variant == "otc")
