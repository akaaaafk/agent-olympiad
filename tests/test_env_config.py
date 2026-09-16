import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from env_config import load_repo_dotenv, openagents_config, provider_config, tinker_config


class DotenvTests(unittest.TestCase):
    def test_bom_first_key_and_existing_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("TINKER_API_KEY=test-only\nTINKER_MODEL=file-model\n", encoding="utf-8-sig")
            with patch.dict(os.environ, {"TINKER_MODEL": "shell-model"}, clear=True):
                load_repo_dotenv(path)
                self.assertEqual(os.environ["TINKER_API_KEY"], "test-only")
                self.assertEqual(os.environ["TINKER_MODEL"], "shell-model")
                self.assertNotIn("\ufeffTINKER_API_KEY", os.environ)


class ProviderProfileTests(unittest.TestCase):
    def test_tinker_profile_and_environment_override(self):
        with patch.dict(os.environ, {"TINKER_MODEL": "custom/model"}, clear=True):
            profile = tinker_config()
        self.assertEqual(profile["model"], "custom/model")
        self.assertEqual(profile["api_key_env"], "TINKER_API_KEY")
        self.assertIn("Qwen/Qwen3.6-35B-A3B", profile["models"])

    def test_openagents_catalog_contains_requested_models(self):
        with patch.dict(os.environ, {}, clear=True):
            profile = openagents_config()
        self.assertIn("glm-5.2", profile["models"])
        self.assertIn("kimi-k2.6", profile["models"])

    def test_unknown_or_unsafe_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid provider profile name"):
            provider_config("../secrets")
        with self.assertRaisesRegex(ValueError, "Unknown provider profile"):
            provider_config("missing")
