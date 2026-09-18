"""Offline regressions for the two stopped mini queues' production failures."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from test_tinker_provider import _native_sdk, MODEL
import llm
from action_transport import request_single_action
from artifacts.pdf_ingest import extract_pdf_text
from artifacts.reviewed_pdf_text import ARML_2013_TEXT

TOOLS = ({'type': 'function', 'name': 'rest', 'description': 'Rest.',
          'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}},)


class LengthRecoveryTests(unittest.TestCase):
    def test_selector_is_bounded_and_judge_retains_configured_limit(self):
        for tools in ((), TOOLS):
            sdk, _, _, _, _ = _native_sdk([1, 2], decoded='{"name":"rest","arguments":{}}')
            with patch.dict(os.environ, {'TINKER_API_KEY': 'offline-test'}), patch.dict(sys.modules, {'tinker': sdk}):
                fn = llm.make_tinker_request_fn(MODEL, max_output_tokens=4096)
                fn(llm.LLMRequest(system_prompt='s', user_prompt='u', tools=tools,
                    metadata={'max_output_tokens_override': 16000}))
            self.assertEqual(sdk.SamplingParams.call_args.kwargs['max_tokens'], 512 if tools else 4096)

    def sample(self, remaining=20000, calls=2, second_length=False):
        sdk, _, client, tokenizer, result = _native_sdk([1, 2, 3])
        result.result.side_effect = [
            SimpleNamespace(sequences=[SimpleNamespace(tokens=[7] * 512, stop_reason='length')]),
            SimpleNamespace(sequences=[SimpleNamespace(tokens=[7] * (512 if second_length else min(10, remaining - 512)),
                                                       stop_reason='length' if second_length else 'stop')])]
        # Even syntactically valid JSON with a length stop must not execute.
        # Both per-sample and accumulated continuation tokens may be decoded.
        # Decoding is deterministic and must not consume a two-item call queue.
        tokenizer.decode.side_effect = lambda tokens, **kwargs: '{"name":"rest","arguments":{}}'
        with patch.dict(os.environ, {'TINKER_API_KEY': 'offline-test'}), patch.dict(sys.modules, {'tinker': sdk}):
            fn = llm.make_tinker_request_fn(MODEL, max_output_tokens=4096)
            response = request_single_action(fn, llm.LLMRequest(system_prompt='s', user_prompt='u',
                tools=TOOLS, metadata={'max_transport_attempts': calls, 'max_transport_output_tokens': remaining}))
        return response, [c.kwargs['max_tokens'] for c in sdk.SamplingParams.call_args_list]

    def test_real_sdk_completes_short_descriptor_and_charges_both_samples(self):
        response, limits = self.sample()
        self.assertEqual(limits, [512, 512])
        self.assertEqual(len(response.tool_calls), 1)
        self.assertEqual(response.usage['api_calls'], 2)
        self.assertEqual(response.usage['output_tokens'], 522)

    def test_remaining_budget_caps_recovery(self):
        response, limits = self.sample(remaining=520)
        self.assertEqual(limits, [512, 8])
        self.assertEqual(len(response.tool_calls), 1)

    def test_call_budget_blocks_retry_and_partial_execution(self):
        response, limits = self.sample(calls=1)
        self.assertEqual(limits, [512])
        self.assertFalse(response.tool_calls)

    def test_repeated_truncation_never_executes_valid_looking_partial_action(self):
        response, limits = self.sample(second_length=True)
        self.assertEqual(limits, [512, 512])
        self.assertFalse(response.tool_calls)
        self.assertEqual(response.usage['output_tokens'], 1024)


class PromptIntegrityTests(unittest.TestCase):
    def load_manifest(self, competition, problem, split=False):
        from contest_manifest import load_contest_manifest
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text(json.dumps({'session_id': 'test', 'competition_id': competition,
                'problem_ids': [problem], 'split_parts': split}), encoding='utf-8')
            return load_contest_manifest(path, benchmark_root=ROOT / 'data/mini_data/benchmarks')

    def test_split_manifest_preserves_each_reviewed_question(self):
        manifest = self.load_manifest('arml_local', 'arml_local_2013', split=True)
        self.assertEqual(len(manifest.tasks), 10)
        ninth = next(t for t in manifest.tasks if t.question_id == '9')
        self.assertIn('a/(b+1) = (b-7*a)/(a+5)', ninth.prompt)
        self.assertNotIn('cos(x)', ninth.prompt)

    def test_problem_heading_packet_can_select_one_question(self):
        manifest = self.load_manifest('purple_comet', 'purple_comet_ms_2017', split=True)
        self.assertEqual(len(manifest.tasks), 20)
        first = manifest.tasks[0]
        self.assertIn('Sophia', first.prompt)
        self.assertNotIn('congruent squares', first.prompt)

    def test_source_review_inspection_is_programming_without_execution_routing(self):
        from contest_actions import _inspect_problem_payload
        from contest_session import TaskUnit
        from contest_memory import ContestMemory
        manifest = self.load_manifest('iiot', 'iiot_2021_04')
        task = manifest.tasks[0]
        self.assertFalse(task.programming)  # Routing contract remains unchanged.
        memory = ContestMemory(run_id='test', session_id='test', competition_id='iiot')
        payload = _inspect_problem_payload(task, TaskUnit(task_id=task.task_id), memory)
        self.assertTrue(payload['programming'])
        self.assertFalse(payload['execution_judge'])
        self.assertIn('C++', payload['submission_format'])
        self.assertNotIn('Chimneys', payload['statement'])

    def test_arml_original_pdf_and_benchmark_have_same_reviewed_math(self):
        for base in ('data', 'data/mini_data'):
            rows = json.loads((ROOT / base / 'benchmarks/arml_local/benchmark.json').read_text(encoding='utf-8'))
            row = next(r for r in rows if r['problem_id'] == 'arml_local_2013')
            text, count, warnings = extract_pdf_text(ROOT / row['source_file'])
            self.assertFalse(warnings)
            self.assertEqual(count, 1)
            self.assertEqual(row['problem_description'], ARML_2013_TEXT)
            for equation in ('a/(b+1) = (b-7*a)/(a+5) = (3*b+a)/(4*b+5)',
                             'A^(B^C)', '2^3 * 3^4 * 4^5 * 5^6'):
                self.assertIn(equation, text)

    def test_iiot_disclaimer_belongs_only_to_chimneys(self):
        for base in ('data', 'data/mini_data'):
            rows = json.loads((ROOT / base / 'benchmarks/iiot/benchmark.json').read_text(encoding='utf-8'))
            for row in rows:
                if str(row.get('year')) == '2021':
                    self.assertEqual('Chimneys receives' in row['problem_description'], row['problem_id'] == 'iiot_2021_01')

    def test_mystery_hunt_runtime_cards_do_not_import_2026_faq(self):
        from rules.loader import load_rule_card
        from competition_guidance import competition_guidance
        for base in ('data', 'data/mini_data'):
            root = ROOT / base / 'rules'
            load_rule_card('mystery_hunt', rules_root=root, required=True)
            for name in ('competition', 'collaboration', 'evaluation'):
                text = (root / 'mystery_hunt' / (name + '.json')).read_text(encoding='utf-8')
                self.assertNotIn('2026 FAQ', text)
                self.assertNotIn('2026 hunt', text)
                self.assertNotIn('2026 winner', text)
            config = SimpleNamespace(system_variant='single_agent', team_size=1, max_turns=12,
                max_api_calls=60, max_tokens=20000, max_simulated_minutes=60, minutes_per_turn=5)
            manifest = SimpleNamespace(competition_id='mystery_hunt', tasks=[])
            guidance = competition_guidance(manifest, config, rules_root=root)
            self.assertTrue(guidance.startswith('BENCHMARK PUZZLE RULES'))
            self.assertNotIn('OFFICIAL COMPETITION RULES', guidance)


if __name__ == '__main__':
    unittest.main()
