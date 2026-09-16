"""Tinker receives bounded PDF text through the real adapter and artifact loop."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import llm
import problem_pdf
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from contest_runner import run_contest, ContestRunConfig
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
from evaluation.models import load_rubric


class PdfTextDeliveryTests(unittest.TestCase):
    def setUp(self):
        import pymupdf
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pdf = self.root / 'packet.pdf'
        with pymupdf.open() as doc:
            for text in ('PROBLEM: solve the supplied task.', 'SECRET ANSWER: hidden judge page'):
                page = doc.new_page()
                page.insert_text((60, 60), text)
            doc.save(self.pdf)

    def request(self, purpose='contest_action', role='agent_visible'):
        return llm.LLMRequest('system', 'user', purpose=purpose, attachments=(
            llm.LLMAttachment(self.pdf, 'application/pdf', role, 1, 1),))

    def test_tinker_receives_selected_text_without_binary_and_retries_keep_it(self):
        sampler = Mock(side_effect=['invalid', '{"name":"rest","arguments":{}}'])
        with patch.object(llm, 'make_tinker_caller', return_value=sampler):
            call = llm.make_tinker_request_fn('mock')
        from dataclasses import replace
        req = replace(self.request(), tools=({'type': 'function', 'name': 'rest',
            'parameters': {'type': 'object', 'properties': {}, 'required': [],
                           'additionalProperties': False}},), tool_choice='required')
        result = call(req)
        self.assertEqual(result.tool_calls[0].name, 'rest')
        for invocation in sampler.call_args_list:
            self.assertIn('PROBLEM: solve', invocation.args[1])
            self.assertNotIn('SECRET ANSWER', invocation.args[1])
        self.assertTrue(call.supports_pdf_text)
        self.assertFalse(call.supports_attachments)

    def test_judge_role_remains_blocked_for_contestant(self):
        with self.assertRaises(ValueError):
            self.request(role='judge_only')
        converted = llm.pdf_text_request(self.request(purpose='evaluation', role='judge_only'))
        self.assertIn('judge_only', converted.user_prompt)
        self.assertFalse(converted.attachments)

    def test_images_and_empty_scanned_pages_fail_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'PDFs only'):
            llm.pdf_text_request(llm.LLMRequest('', '', attachments=(
                llm.LLMAttachment(self.pdf, 'image/png'),)))
        import pymupdf
        blank = self.root / 'blank.pdf'
        with pymupdf.open() as doc:
            doc.new_page()
            doc.save(blank)
        with self.assertRaisesRegex(ValueError, 'no extractable text'):
            llm.pdf_text_request(llm.LLMRequest('', '', attachments=(
                llm.LLMAttachment(blank, 'application/pdf'),)))

    def test_real_reader_action_delivers_only_approved_page_text(self):
        sha = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        row = {'problem_id': 'q', 'assets': [dict(path='packet.pdf', sha256=sha,
            mime_type='application/pdf', role='agent_visible')]}
        registry = self.root / 'allowlist.json'
        registry.write_text(json.dumps({'assets': [dict(problem_id='q', path='packet.pdf',
            sha256=sha, pages=[1], review_status='approved_problem_only',
            review_evidence='Fixture page 1 only')]}), encoding='utf-8')
        task = ManifestTask('q', 'q', None, 'Read the PDF.', 'quiz', 1, False, row)
        manifest = ContestManifest('fixture', 'quiz', (task,))
        calls = []
        def act(request):
            calls.append(request)
            self.assertFalse(request.attachments)
            if len(calls) == 1:
                self.assertIn('read_problem_pdf', {t['name'] for t in request.tools})
                action = llm.LLMToolCall('read_problem_pdf', {'problem_id': 'q', 'pages': [1]})
            else:
                self.assertIn('PROBLEM: solve', request.user_prompt)
                self.assertNotIn('SECRET ANSWER', request.user_prompt)
                action = llm.LLMToolCall('work', {'problem_id': 'q', 'content': 'Answer: 4'})
            return llm.LLMResponse('', 'mock', 'mock', tool_calls=(action,))
        act.supports_attachments = False
        act.supports_pdf_text = True
        with patch.object(problem_pdf, 'ROOT', self.root), patch.object(problem_pdf, 'REGISTRY', registry):
            result = run_contest(manifest, lambda *_: '', ContestRunConfig('single_agent', 1, 2),
                                 action_request_fn=act)
        self.assertEqual(result['submissions']['q'], 'Answer: 4')

    def test_tinker_document_loop_renders_and_scores_same_submission(self):
        prepared = prepare_artifact_run(competition='vis_moot', task_pdf=self.pdf,
            task_pages='1-1', output=self.root / 'run', max_turns=2,
            provider='tinker', model='mock', judge_model='mock', system_variant='single_agent')
        rubric = load_rubric(prepared['rubric'])
        payload = dict(criteria=[dict(id=c.id, score=c.min_score, max_score=c.max_score,
            evidence=['Fixture submission'], justification='Plumbing fixture', confidence=1,
            observable=c.observable) for c in rubric.criteria],
            total_score=sum(c.min_score for c in rubric.criteria), max_score=rubric.total_points,
            warnings=[], limitations=[])
        def sampler(system, user):
            self.assertNotIn('SECRET ANSWER', user)
            self.assertIn('PROBLEM: solve', user)
            if 'expert olympiad grader' in system:
                self.assertIn('Complete fixture report', user)
                return json.dumps(payload)
            tools = json.JSONDecoder().raw_decode(system.split('FUNCTION SCHEMAS:\n')[1])[0]
            names = {t['name'] for t in tools}
            if 'render_pdf' in names:
                action, args = 'render_pdf', {'content': 'Complete fixture report'}
            else:
                action, args = 'select_problem', {'problem_id': 'deliverable'}
            return json.dumps({'name': action, 'arguments': args})
        with patch.object(llm, 'make_tinker_caller', return_value=sampler):
            agent = llm.make_tinker_request_fn('mock')
            judge = llm.make_tinker_request_fn('mock')
        result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertTrue(result['graded'])
        self.assertIn('PROBLEM: solve', (self.root / 'run/task_extracted.txt').read_text())
        self.assertEqual(prepared['identity']['settings']['execution']['action_transport'], 'emulated')


if __name__ == '__main__':
    unittest.main()
