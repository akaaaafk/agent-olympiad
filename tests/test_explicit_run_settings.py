import argparse
import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from env_config import add_run_credentials, consume_run_credentials, require_explicit_model, RUN_API_KEY_ENV
from contest_budget import resolve_contest_budget, validate_temperature
import run_competition_batch as native
from otc_artifact_pipeline import prepare_artifact_run
from test_contest_run_identity import manifest


class ExplicitRunSettingsTests(unittest.TestCase):
    def test_invalid_budgets_are_rejected(self):
        for name in ('max_api_calls', 'max_total_tokens', 'max_output_tokens_per_call'):
            for value in (-1, 0, float('nan'), float('inf')):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, 'positive'):
                    resolve_contest_budget('arml_local', **{name: value})
        self.assertIsNone(resolve_contest_budget('arml_local').max_api_calls)

    def test_temperature_validation_matches_preflight(self):
        for value in (-1, float('nan'), float('inf')):
            with self.assertRaisesRegex(ValueError, 'temperature'):
                validate_temperature(value)
            args = native._build_parser().parse_args(['--contest-manifest', 'missing', '--temperature', str(value)])
            with self.assertRaisesRegex(ValueError, 'temperature'):
                native._prepare_contest_run(args)

    def test_no_model_fallback_from_environment(self):
        with patch.dict(os.environ, {'OPENAI_MODEL': 'must-not-use', 'TINKER_MODEL': 'must-not-use'}):
            for provider in RUN_API_KEY_ENV:
                with self.assertRaisesRegex(ValueError, '--model'):
                    native._resolve_model(provider, None)
                self.assertEqual(native._resolve_model(provider, 'explicit/model'), 'explicit/model')
        with self.assertRaisesRegex(ValueError, '--model'):
            prepare_artifact_run(competition='vis_moot', task_pdf='missing', output='unused', provider='openai')

    def test_pipeline_rejects_invalid_parameters_before_output_creation(self):
        from scripts import run_pipeline
        from contextlib import redirect_stderr
        import io
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'not-created'
            for flag, value in [('--max-api-calls', '-1'), ('--max-total-tokens', '0'),
                                ('--temperature', 'nan'), ('--max-output-tokens', '-1')]:
                with patch.object(sys, 'argv', ['pipeline', 'all', '--model', 'mock',
                    '--output', str(output), flag, value]), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        run_pipeline.main()
                self.assertEqual(raised.exception.code, 2)
                self.assertFalse(output.exists())

    def test_runtime_key_routes_to_selected_provider_and_is_consumed(self):
        for provider, target in RUN_API_KEY_ENV.items():
            parser = argparse.ArgumentParser()
            parser.add_argument('--provider')
            add_run_credentials(parser)
            with patch.dict(os.environ, {'RUN_TEST_KEY': 'test-secret-only'}, clear=True):
                args = parser.parse_args(['--provider', provider, '--api-key-env', 'RUN_TEST_KEY'])
                consume_run_credentials(args)
                self.assertEqual(os.environ[target], 'test-secret-only')
                self.assertEqual(vars(args), {'provider': provider})
                self.assertFalse(any(k in os.environ for k in RUN_API_KEY_ENV.values() if k != target))
                args = parser.parse_args(['--provider', provider, '--api-key', 'replacement-test-key'])
                consume_run_credentials(args)
                self.assertEqual(os.environ[target], 'replacement-test-key')
                self.assertNotIn('api_key', vars(args))

    def test_plain_baselines_accept_public_rules_root_and_key_is_not_in_identity(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ):
            for baseline in ('single_agent', 'centralized', 'decentralized'):
                args = native._build_parser().parse_args(['--live', '--model', 'explicit/model',
                    '--contest-manifest', 'fixture', '--system-variant', baseline,
                    '--rules-root', str(ROOT / 'data/rules'), '--output', d,
                    '--api-key', 'test-secret-only'])
                with patch.object(native, 'load_contest_manifest', return_value=replace(manifest(), competition_id='arml_local')):
                    _, config, _, identity = native._prepare_contest_run(args)
                self.assertIsNone(config.rule_card)
                self.assertIn('OFFICIAL COMPETITION RULES', config.rule_guidance)
                self.assertNotIn('test-secret-only', json.dumps(identity))
                self.assertNotIn('api_key', vars(args))


if __name__ == '__main__':
    unittest.main()
