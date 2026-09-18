"""Permanent production adapter regressions; no repair-script monkeypatches."""
import json
import os
import re
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import llm
from artifacts.pdf_ingest import extract_pdf_text
from test_tinker_provider import _native_sdk, MODEL


class ProductionPdfTests(unittest.TestCase):
    def test_actual_ccdc_cover_through_normal_adapter(self):
        path = ROOT / 'data/mini_data/raw/ccdc/nationals/2025-NCCDC-TeamPacket.pdf'
        if not path.exists():
            self.skipTest('Mini data not installed')
        request = llm.LLMRequest('', 'Judge the submission', purpose='evaluation', attachments=(
            llm.LLMAttachment(path, 'application/pdf', 'agent_visible', 1, 20),))
        converted = llm.pdf_text_request(request)
        self.assertIn('manual transcription', converted.user_prompt)
        self.assertIn('page 20', converted.user_prompt)

    def test_actual_cfa_full_packet_without_repeated_excerpts(self):
        path = ROOT / 'data/mini_data/raw/cfa_research_challenge/historical_2016/research_packet.pdf'
        if not path.exists():
            self.skipTest('Mini data not installed')
        benchmark = json.loads((ROOT / 'data/mini_data/benchmarks/cfa_research_challenge/benchmark.json').read_text())
        request = llm.LLMRequest('', 'TASK TEXT:\n\n' + benchmark[0]['problem_description'] +
            '\n\nSUBMISSION TEXT:\nActual submission unchanged.', purpose='evaluation', attachments=(
                llm.LLMAttachment(path, 'application/pdf', 'agent_visible', 1, 70),))
        converted = llm.pdf_text_request(request)
        self.assertEqual(len(converted.metadata['deduplicated_packet_pages']), 12)
        self.assertIn('Actual submission unchanged.', converted.user_prompt)
        self.assertIn('reviewed blank page', converted.user_prompt)
        self.assertIn('page 70', converted.user_prompt)
        full, _, warnings = extract_pdf_text(path)
        self.assertFalse(warnings)
        self.assertIn(re.sub(r'\s+', '', full), re.sub(r'\s+', '', converted.user_prompt))
        self.assertLess(len(converted.user_prompt), 240000)
        changed = replace(request, user_prompt=request.user_prompt.replace(
            'Packet page 3:\n', 'Packet page 3:\nExtra claim must not disappear. '))
        retained = llm.pdf_text_request(changed)
        self.assertIn('Extra claim must not disappear.', retained.user_prompt)
        self.assertNotIn(3, retained.metadata['deduplicated_packet_pages'])
        contestant = llm.pdf_text_request(replace(request, purpose='contest_action'))
        self.assertIn('Packet page 3:', contestant.user_prompt)
        self.assertEqual(contestant.metadata.get('deduplicated_packet_pages', []), [])

    def test_real_tinker_adapter_budgets_output_from_encoded_input(self):
        sdk, _, client, _, _ = _native_sdk([1] * 62066)
        with patch.dict(os.environ, {'TINKER_API_KEY': 'fixture'}), patch.dict(sys.modules, {'tinker': sdk}):
            response = llm.make_tinker_request_fn(MODEL)(llm.LLMRequest('', 'large request'))
        limit = sdk.SamplingParams.call_args.kwargs['max_tokens']
        self.assertLessEqual(62066 + limit, 65536)
        self.assertGreaterEqual(limit, 3000)
        self.assertEqual(response.usage['max_output_tokens'], limit)
        client.sample.assert_called_once()

    def test_oversized_input_is_rejected_before_sampling_without_truncation(self):
        sdk, _, client, _, _ = _native_sdk([1] * 66000)
        with patch.dict(os.environ, {'TINKER_API_KEY': 'fixture'}), patch.dict(sys.modules, {'tinker': sdk}):
            with self.assertRaisesRegex(RuntimeError, 'context'):
                llm.make_tinker_caller(MODEL)('', 'oversized request')
        client.sample.assert_not_called()


if __name__ == '__main__':
    unittest.main()
