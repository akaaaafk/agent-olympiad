"""Repair stays page- and content-bound and uses the real PDF text adapter."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import repair_reviewed_pdf_judges as repair
import artifacts.pdf_ingest as ingest
from llm import LLMAttachment, LLMRequest, pdf_text_request
import pymupdf


class ReviewedPdfRepairTests(unittest.TestCase):
    def test_import_preserves_callers_dataset_selection(self):
        code = ("import sys, os, json; sys.path.insert(0, 'scripts'); "
                "import repair_reviewed_pdf_judges; "
                "print(json.dumps(os.environ.get('AGENT_OLYMPIAD_DATA_ROOT')))")
        for selected in (None, str(ROOT / 'data')):
            with self.subTest(selected=selected):
                env = dict(os.environ)
                env.pop('AGENT_OLYMPIAD_DATA_ROOT', None)
                if selected is not None:
                    env['AGENT_OLYMPIAD_DATA_ROOT'] = selected
                result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                                        check=True, capture_output=True, text=True)
                self.assertEqual(json.loads(result.stdout), selected)

    def test_cfa_deduplication_preserves_all_page_content_and_rejects_mismatch(self):
        import re
        from dataclasses import replace
        path = ROOT / 'data/mini_data/raw/cfa_research_challenge/historical_2016/research_packet.pdf'
        if not path.exists():
            self.skipTest('Historical CFA packet not installed')
        text, _, warnings = ingest.extract_pdf_text(path, page_start=3, page_end=3)
        self.assertEqual(warnings, [])
        excerpt = text.split('\n', 1)[1]
        request = LLMRequest('', 'TASK TEXT:\n\nInstructions\nPacket page 3:\n' + excerpt +
                             '\n\nSUBMISSION TEXT:\nKeep the actual submission.',
                             purpose='evaluation', attachments=(
                                 LLMAttachment(path, 'application/pdf', 'agent_visible', 3, 3),))
        converted = repair.deduplicate_packet_excerpts(request, pdf_text_request)
        self.assertEqual(converted.metadata['deduplicated_packet_pages'], [3])
        self.assertIn('Keep the actual submission.', converted.user_prompt)
        self.assertIn(re.sub(r'\s+', ' ', text), converted.user_prompt)
        with self.assertRaisesRegex(ValueError, 'Cannot verify duplicate'):
            repair.deduplicate_packet_excerpts(replace(request, user_prompt=request.user_prompt.replace(
                'Packet page 3:\n', 'Packet page 3:\nInjected extra claim. ')), pdf_text_request)

    def test_hash_and_page_bound_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.pdf'
            with pymupdf.open() as doc:
                doc.new_page()
                page = doc.new_page()
                page.insert_text((60, 60), 'Keep original evidence')
                doc.new_page()
                doc.save(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            req = LLMRequest('', '', purpose='evaluation', attachments=(
                LLMAttachment(path, 'application/pdf', 'judge_only', 1, 2),))
            with self.assertRaisesRegex(ValueError, 'Page 1'):
                pdf_text_request(req)
            original = ingest.extract_pdf_text
            with patch.dict(repair.REVIEWED, {digest: {1: '[Reviewed blank page]'}}), patch.object(
                    ingest, 'extract_pdf_text', repair.reviewed_extractor(original)):
                converted = pdf_text_request(req)
                self.assertIn('[Reviewed blank page]', converted.user_prompt)
                self.assertIn('Keep original evidence', converted.user_prompt)
                self.assertNotIn('page 3', converted.user_prompt)
                all_pages = LLMRequest('', '', purpose='evaluation', attachments=(
                    LLMAttachment(path, 'application/pdf', 'judge_only'),))
                with self.assertRaisesRegex(ValueError, 'Page 3'):
                    pdf_text_request(all_pages)
            with patch.dict(repair.REVIEWED, {'wrong_hash': {1: 'unverified'}}), patch.object(
                    ingest, 'extract_pdf_text', repair.reviewed_extractor(original)):
                with self.assertRaisesRegex(ValueError, 'Page 1'):
                    pdf_text_request(req)


if __name__ == '__main__':
    unittest.main()
