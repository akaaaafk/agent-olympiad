import sys
import unittest
import tempfile
import os
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_tinker_parallel import child_environment, job_command
from env_config import load_repo_dotenv


class CredentialIsolationTests(unittest.TestCase):
    def test_queue_keeps_rule_cards_exclusive_to_otc(self):
        for variant in ("single_agent", "centralized", "decentralized", "vallina_otc", "otc"):
            cmd = job_command(Path("manifest.json"), variant, Path("output"), 10)
            self.assertEqual(cmd[cmd.index("--rules-mode") + 1],
                             "enforced" if variant in {"vallina_otc", "otc"} else "off")

    def test_windows_bom_does_not_hide_first_key(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            path.write_text("TINKER_API_KEY=first\nTINKER_API_KEY2=second\n", encoding="utf-8-sig")
            load_repo_dotenv(path)
            self.assertEqual(os.environ["TINKER_API_KEY"], "first")
            self.assertEqual(os.environ["TINKER_API_KEY2"], "second")

    def test_each_child_receives_only_its_selected_credential(self):
        parent = {"TINKER_API_KEY": "first", "TINKER_API_KEY2": "second", "TINKER_MODEL": "model"}
        first = child_environment(parent, "TINKER_API_KEY")
        second = child_environment(parent, "TINKER_API_KEY2")
        self.assertEqual(first["TINKER_API_KEY"], "first")
        self.assertEqual(second["TINKER_API_KEY"], "second")
        self.assertNotIn("TINKER_API_KEY2", first)
        self.assertNotIn("TINKER_API_KEY2", second)
        self.assertEqual(parent["TINKER_API_KEY"], "first")
        self.assertEqual(second["TINKER_MODEL"], "model")
