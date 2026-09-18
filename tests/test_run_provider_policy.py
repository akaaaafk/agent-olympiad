import sys
import unittest
import tempfile
import subprocess
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from run_competition_batch import _resolve_judge_provider
from otc_artifact_pipeline import prepare_artifact_run
import run_competition_batch as batch


class RunProviderPolicyTests(unittest.TestCase):
    def test_all_main_clis_reject_mixed_provider_before_output_creation(self):
        root = Path(__file__).resolve().parents[1]
        commands = [
            ['src/run_competition_batch.py', '--live'],
            ['src/run_otc_artifact.py', '--competition', 'arml_power', '--task-pdf', 'missing.pdf'],
            ['scripts/run_pipeline.py', 'all'],
        ]
        for command in commands:
            with self.subTest(command=command[0]), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'must-not-exist'
                completed = subprocess.run([sys.executable, *command, '--provider', 'tinker',
                    '--model', 'mock', '--judge-provider', 'perplexity', '--output', str(output)],
                    cwd=root, capture_output=True, text=True, timeout=30)
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn('same provider', completed.stderr)
                self.assertFalse(output.exists())

    def test_every_provider_is_inherited_by_judges(self):
        for provider in ('tinker', 'perplexity', 'openagents', 'vectorengine', 'openai'):
            with self.subTest(provider=provider):
                self.assertEqual(_resolve_judge_provider(provider, None), provider)
                self.assertEqual(_resolve_judge_provider(provider, provider), provider)

    def test_mixed_provider_fails_before_live_calls(self):
        for solver, judge in (('perplexity', 'tinker'), ('tinker', 'perplexity')):
            with self.subTest(solver=solver), self.assertRaisesRegex(ValueError, 'same provider'):
                _resolve_judge_provider(solver, judge)

    def test_artifact_rejects_mixed_provider_before_loading_inputs(self):
        with self.assertRaisesRegex(ValueError, 'same provider'):
            prepare_artifact_run(competition='arml_power', task_pdf=Path('missing.pdf'),
                                 output=Path('unused'), provider='tinker', judge_provider='perplexity')

    def test_arml_identity_uses_one_provider_for_all_judges(self):
        root = Path(__file__).resolve().parents[1]
        for provider in ('tinker', 'perplexity', 'openagents', 'openai', 'vectorengine'):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory:
                state, identity = batch.inspect_contest_run([
                    '--live', '--contest-manifest', str(root / 'data/contest_manifests/arml_local_2009.json'),
                    '--system-variant', 'centralized', '--provider', provider,
                    '--model', 'fixture-model', '--output', str(Path(directory) / 'run')])
                self.assertEqual(state, 'new')
                settings = identity['settings']
                self.assertEqual(settings['execution']['provider'], provider)
                self.assertEqual(settings['evaluation']['provider'], provider)
                self.assertEqual(settings['evaluation']['model'], 'fixture-model')

    def test_solver_and_planning_caller_dispatch_does_not_fall_back(self):
        for provider in ('tinker', 'perplexity'):
            with self.subTest(provider=provider), \
                 patch.object(batch, 'make_tinker_query_fn') as tinker, \
                 patch.object(batch, 'make_perplexity_caller') as perplexity:
                caller = batch._make_live_query(provider, 'fixture-model')
                selected, unused = (tinker, perplexity) if provider == 'tinker' else (perplexity, tinker)
                self.assertIs(caller, selected.return_value)
                selected.assert_called_once()
                unused.assert_not_called()
