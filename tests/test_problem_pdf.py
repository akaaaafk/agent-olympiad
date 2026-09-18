from pathlib import Path
import sys
import json
import hashlib
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import problem_pdf
from llm import LLMRequest, LLMAttachment, LLMResponse, LLMToolCall
from contest_manifest import ContestManifest, ManifestTask, load_contest_manifest
from contest_memory import ContestMemory
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from contest_runner import run_contest, ContestRunConfig


class PdfReaderTests(unittest.TestCase):
    def setUp(self):
        import pymupdf
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        pdf = pymupdf.open()
        for text in ['PROBLEM: What is 2+2?', 'SECRET ANSWER: 4']:
            p = pdf.new_page()
            p.insert_text((60, 60), text)
        pdf.save(self.root / 'packet.pdf')
        pdf.close()
        self.sha = hashlib.sha256((self.root / 'packet.pdf').read_bytes()).hexdigest()
        self.row = {'problem_id': 'q', 'assets': [dict(path='packet.pdf', sha256=self.sha,
                    mime_type='application/pdf', role='agent_visible')]}
        self.entry = dict(problem_id='q', path='packet.pdf', sha256=self.sha, pages=[1],
                          review_status='approved_problem_only', review_evidence='Test reviewed page 1 only')
        self.registry = self.root / 'allowlist.json'
        self.write_registry()
        for name, value in [('ROOT', self.root), ('REGISTRY', self.registry)]:
            p = patch.object(problem_pdf, name, value)
            p.start()
            self.addCleanup(p.stop)

    def write_registry(self):
        self.registry.write_text(json.dumps({'assets': [self.entry]}), encoding='utf-8')

    def test_page_allowlist_and_no_arbitrary_paths(self):
        for pages in [[2], [0], [-1], [True], [1, 1], [1, 2, 3], ['../packet.pdf'], []]:
            with self.subTest(pages=pages), self.assertRaises(problem_pdf.ProblemPdfError):
                problem_pdf.read_problem_pdf(self.row, pages)
        for doc in [0, -1, True, '../packet.pdf', 2]:
            with self.assertRaises(problem_pdf.ProblemPdfError):
                problem_pdf.read_problem_pdf(self.row, [1], doc)

    def test_no_approval_or_wrong_hash_or_judge_role_is_denied(self):
        for change in [{'review_status': 'pending'}, {'sha256': '0'*64}, {'review_evidence': ''},
                       {'path': '../packet.pdf'}]:
            original = dict(self.entry)
            self.entry.update(change)
            self.write_registry()
            self.assertEqual(problem_pdf.approved_assets(self.row), [])
            self.entry = original
        self.write_registry()
        self.row['assets'][0]['role'] = 'judge_only'
        self.assertEqual(problem_pdf.approved_assets(self.row), [])

    def test_tampered_file_denied_even_after_initial_approval(self):
        self.assertTrue(problem_pdf.describe(self.row))
        with (self.root / 'packet.pdf').open('ab') as f:
            f.write(b'changed')
        self.assertFalse(problem_pdf.describe(self.row))

    def fixture(self):
        task = ManifestTask('q', 'q', None, 'Read the original PDF.', 'quiz', 1, False, self.row)
        manifest = ContestManifest('test', 'quiz', (task,))
        session = ContestSession([TaskUnit('q')], ContestBudgetState(max_turns=4))
        session.select_task('q')
        memory = ContestMemory(run_id='run', session_id='test', competition_id='quiz')
        return task, manifest, session, memory

    def test_private_images_reach_request_and_are_cleaned(self):
        _, manifest, session, memory = self.fixture()
        payload, _ = problem_pdf.read_problem_pdf(self.row, [1], render=False)
        memory.append(task_id='q', question_id=None, actor='Tool', visibility='private',
                      recipients=('Agent_1',), kind='read_problem_pdf_result', payload=payload, turn=0)
        request = LLMRequest('sys', 'prompt', purpose='contest_action')
        with problem_pdf.attached_request(request, manifest, session, memory, 'Agent_1') as actual:
            self.assertEqual(len(actual.attachments), 1)
            path = actual.attachments[0].path
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(actual.attachments[0].mime_type, 'image/png')
        self.assertFalse(path.exists())
        self.assertEqual(problem_pdf.request_attachments(manifest, session, memory, 'Agent_2'), ())

    def test_contest_loop_calls_reader_then_delivers_pixels(self):
        _, manifest, _, _ = self.fixture()
        calls = []
        def request_fn(request):
            calls.append(request)
            if len(calls) == 1:
                self.assertIn('read_problem_pdf', str(request.tools))
                self.assertIn('PROBLEM PDF READING', request.user_prompt)
                call = LLMToolCall('read_problem_pdf', {'problem_id': 'q', 'pages': [1]})
            else:
                self.assertEqual(len(request.attachments), 1)
                self.assertTrue(request.attachments[0].path.is_file())
                self.assertNotIn('SECRET ANSWER', request.user_prompt)
                call = LLMToolCall('work', {'problem_id': 'q', 'content': 'Problem q: Final answer: 4'})
            return LLMResponse('', 'mock', 'vision', usage={'output_tokens': 5}, tool_calls=(call,))
        result = run_contest(manifest, lambda *_: '',
                             ContestRunConfig('single_agent', 1, 1), action_request_fn=request_fn)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result['submissions']['q'], 'Problem q: Final answer: 4')

    def test_judge_attachments_rejected_across_contest_purposes(self):
        a = LLMAttachment(self.root / 'packet.pdf', 'application/pdf', role='judge_only')
        for purpose in ['generation', 'contest_action', 'coach', 'unknown']:
            with self.assertRaises(ValueError):
                LLMRequest('sys', 'prompt', (a,), purpose=purpose)
        self.assertEqual(LLMRequest('sys', 'prompt', (a,), purpose='evaluation').attachments, (a,))

    def test_split_packet_subset_is_not_exposed(self):
        task, manifest, session, _ = self.fixture()
        row = {**self.row, 'gold_label': {'parts': [{'id': '1'}, {'id': '2'}]}}
        task = replace(task, question_id='1', benchmark=row)
        manifest = replace(manifest, tasks=(task,))
        self.assertEqual(problem_pdf.visible_benchmark(manifest, session, task)['assets'], [])

    def test_access_scope_is_part_of_run_identity(self):
        from contest_run_identity import build_run_identity
        _, manifest, _, _ = self.fixture()
        config = ContestRunConfig('single_agent', 1, 2)
        before = build_run_identity(manifest, config, execution={}, evaluation={})
        self.entry['pages'] = [1, 2]
        self.write_registry()
        after = build_run_identity(manifest, config, execution={}, evaluation={})
        self.assertNotEqual(before['fingerprint'], after['fingerprint'])

    def test_reader_not_offered_to_text_only_transport(self):
        _, manifest, _, _ = self.fixture()
        def request_fn(request):
            self.assertNotIn('read_problem_pdf', {t['name'] for t in request.tools})
            return LLMResponse('', 'mock', 'text', tool_calls=(LLMToolCall('rest', {}),))
        request_fn.supports_attachments = False
        run_contest(manifest, lambda *_: '', ContestRunConfig('single_agent', 1, 1),
                    action_request_fn=request_fn)

    def test_missing_json_split_can_use_approved_packet(self):
        folder = self.root / 'quiz'
        folder.mkdir()
        row = {**self.row, 'task_type': 'quiz', 'gold_label': {'parts': [{'id': '1'}, {'id': '2'}]}}
        (folder/'benchmark.json').write_text(json.dumps([row]), encoding='utf-8')
        path = self.root/'manifest.json'
        path.write_text(json.dumps({'session_id': 's', 'competition_id': 'quiz',
                                   'problem_ids': ['q'], 'split_parts': True}), encoding='utf-8')
        manifest = load_contest_manifest(path, benchmark_root=self.root)
        self.assertEqual(len(manifest.tasks), 2)
        self.assertIn('read_problem_pdf', manifest.tasks[0].prompt)


if __name__ == '__main__':
    unittest.main()
