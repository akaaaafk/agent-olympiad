import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from env_config import load_repo_dotenv


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
