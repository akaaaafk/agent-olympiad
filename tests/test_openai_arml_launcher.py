import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('openai_launcher', Path(__file__).resolve().parents[1] / 'scripts/run_openai_arml2009.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_saved_config_is_explicit_and_does_not_mutate_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('OPENAI_API_KEY=slot-test\nOPENAI_BASE_URL=https://api.openai.com/v1\nOPENAI_MODEL=gpt-5.4-mini\n')
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'other', 'OPENAGENTS_API_KEY': 'gateway'}):
                env = launcher.openai_environment(path)
                self.assertEqual(env['OPENAI_API_KEY'], 'slot-test')
                self.assertEqual(env['OPENAGENTS_API_KEY'], 'gateway')
                self.assertEqual(os.environ['OPENAI_API_KEY'], 'other')

    def test_missing_config_never_borrows_key(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('OPENAI_API_KEY_1=other\nOPENAGENTS_API_KEY=gateway\n')
            with self.assertRaisesRegex(ValueError, 'OPENAI_API_KEY'):
                launcher.openai_environment(path)

    def test_baselines_and_model_are_explicit(self):
        self.assertEqual(launcher.VARIANTS, ('single_agent', 'vallina_otc', 'otc'))
        cmd = launcher.command('gpt-5.4-mini', 'otc', Path('new_gpt-5.4-mini'))
        self.assertEqual(cmd[cmd.index('--provider') + 1], 'openai')
        self.assertEqual(cmd[cmd.index('--judge-model') + 1], 'gpt-5.4-mini')
        self.assertEqual(cmd[cmd.index('--max-total-tokens') + 1], '220000')
