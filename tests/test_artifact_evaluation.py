import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from pypdf import PdfWriter

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from artifacts.assets import Asset, AssetError, load_assets
from artifacts.slides import (
    ArtifactValidation,
    NormalizedSubmission,
    normalize_submission,
    validate_html_slides,
    validate_pdf_slides,
)
from evaluation.models import EvaluationError, load_rubric, parse_evaluation_payload
from evaluation.slides import SlideDeckEvaluator
from evaluation.rubric_llm import RubricDocumentEvaluator
from llm import LLMAttachment, LLMResponse, _attachment_bytes


def write_pdf(path: Path, pages: int = 1, width: float = 960, height: float = 540) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=width, height=height)
    with path.open("wb") as output:
        writer.write(output)


class AssetTests(unittest.TestCase):
    def test_role_filter_and_checksum(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf_path = root / "task.pdf"
            write_pdf(pdf_path, pages=2)
            checksum = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            problem = {
                "assets": [
                    {
                        "path": "task.pdf",
                        "mime_type": "application/pdf",
                        "role": "agent_visible",
                        "page_start": 1,
                        "page_end": 2,
                        "sha256": checksum,
                    }
                ]
            }
            assets = load_assets(problem, root, roles=("agent_visible",))
            self.assertEqual(len(assets), 1)
            self.assertEqual(assets[0].page_end, 2)
            self.assertEqual(load_assets(problem, root, roles=("judge_only",)), [])

    def test_checksum_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_pdf(root / "task.pdf")
            problem = {
                "assets": [
                    {
                        "path": "task.pdf",
                        "mime_type": "application/pdf",
                        "role": "agent_visible",
                        "sha256": "0" * 64,
                    }
                ]
            }
            with self.assertRaises(AssetError):
                load_assets(problem, root)

    def test_pdf_attachment_page_range_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "omnibus.pdf"
            write_pdf(pdf_path, pages=3)
            attachment = LLMAttachment(
                path=pdf_path,
                mime_type="application/pdf",
                page_start=2,
                page_end=2,
            )
            sliced = _attachment_bytes(attachment)
            sliced_path = Path(temp_dir) / "slice.pdf"
            sliced_path.write_bytes(sliced)
            from pypdf import PdfReader

            self.assertEqual(len(PdfReader(str(sliced_path)).pages), 1)


class SlideArtifactTests(unittest.TestCase):
    def test_html_contract_blocks_active_or_remote_content(self):
        html = """
        <html><body>
          <section><h1>One</h1><script>alert(1)</script></section>
          <section><h2>Two</h2><img src="https://example.com/chart.png"></section>
        </body></html>
        """
        result = validate_html_slides(html, min_slides=2, max_slides=2)
        self.assertFalse(result.valid)
        self.assertTrue(any("Scripts" in error for error in result.errors))
        self.assertTrue(any("External" in error for error in result.errors))

    def test_pdf_validation_rejects_non_widescreen(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "portrait.pdf"
            write_pdf(pdf_path, width=540, height=960)
            result = validate_pdf_slides(pdf_path)
            self.assertFalse(result.valid)
            self.assertTrue(any("16:9" in error for error in result.errors))

    def test_html_normalizes_to_two_page_pdf(self):
        html = """<!doctype html><html><head><style>
        section { font-family: sans-serif; }
        </style></head><body>
        <section><h1>Recommendation</h1><p>Proceed in stages.</p></section>
        <section><h2>Economics</h2><svg width="100" height="50"></svg></section>
        </body></html>"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "slides.html"
            source.write_text(html)
            result = normalize_submission(source, root / "output", min_slides=2, max_slides=2)
            self.assertTrue(result.validation.valid, result.validation.errors)
            self.assertEqual(result.validation.metadata["page_count"], 2)


class EvaluationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rubric = load_rubric(
            REPO_ROOT / "data" / "rubrics" / "business_case_slides_50.json"
        )

    def valid_payload(self) -> str:
        criteria = []
        scores = {"analytical": 12, "conceptual": 12, "quantitative": 8, "communication": 8}
        maxima = {"analytical": 15, "conceptual": 15, "quantitative": 10, "communication": 10}
        for criterion_id, score in scores.items():
            criteria.append(
                {
                    "id": criterion_id,
                    "score": score,
                    "max_score": maxima[criterion_id],
                    "evidence": ["Slide 2: visible evidence"],
                    "justification": "Grounded justification.",
                    "confidence": 0.8,
                    "observable": True,
                }
            )
        return json.dumps(
            {
                "criteria": criteria,
                "total_score": 40,
                "max_score": 50,
                "warnings": [],
                "limitations": ["oral delivery"],
            }
        )

    def test_valid_evaluation_payload(self):
        result = parse_evaluation_payload(
            self.valid_payload(),
            rubric=self.rubric,
            evaluator_id="slide_deck_v1",
            evaluator_version="1.0.0",
            prompt_version="test",
            model="mock",
        )
        self.assertEqual(result.total_score, 40)

    def test_invalid_latex_escapes_are_repaired_without_changing_valid_escapes(self):
        raw = self.valid_payload().replace(
            'Grounded justification.', r'Use \(\sqrt{2}\); newline\nquote\" and escaped \\sqrt{3}.')
        for wrapped in (raw, '```json\n' + raw + '\n```', 'Judge output:\n' + raw):
            with self.subTest(wrapped=wrapped[:12]):
                result = parse_evaluation_payload(
                    wrapped, rubric=self.rubric, evaluator_id='test',
                    evaluator_version='1', prompt_version='test', model='mock')
                self.assertEqual(result.total_score, 40)
                self.assertEqual(result.criteria[0].justification,
                                 'Use \\(\\sqrt{2}\\); newline\nquote" and escaped \\sqrt{3}.')
                self.assertTrue(any('escape' in warning for warning in result.warnings))

    def test_escape_repair_does_not_accept_broken_structure(self):
        raw = self.valid_payload().replace('Grounded justification.', r'Use \sqrt{2}.')
        raw = raw.replace('"total_score": 40', '"total_score":')
        with self.assertRaises(EvaluationError):
            parse_evaluation_payload(raw, rubric=self.rubric, evaluator_id='test',
                                     evaluator_version='1', prompt_version='test', model='mock')

    def test_inconsistent_total_is_recomputed_with_a_warning(self):
        payload = json.loads(self.valid_payload())
        payload["total_score"] = 41
        result = parse_evaluation_payload(
            json.dumps(payload),
            rubric=self.rubric,
            evaluator_id="slide_deck_v1",
            evaluator_version="1.0.0",
            prompt_version="test",
            model="mock",
        )
        self.assertEqual(result.total_score, 40)
        self.assertTrue(any("total_score=41" in warning for warning in result.warnings))

    def test_document_judge_retries_invalid_json_and_counts_all_attempts(self):
        request = Mock(side_effect=[
            LLMResponse('{"criteria":', 'mock', 'judge', usage={'input_tokens': 10, 'output_tokens': 3}),
            LLMResponse(self.valid_payload(), 'mock', 'judge', usage={'input_tokens': 20, 'output_tokens': 30}),
        ])
        result = RubricDocumentEvaluator(request_fn=request, rubric=self.rubric,
                                        submission_text='Saved submitted answer.').evaluate()
        self.assertEqual(request.call_count, 2)
        self.assertEqual(result.total_score, 40)
        self.assertEqual(result.usage['api_calls'], 2)
        self.assertEqual(result.usage['input_tokens'], 30)
        self.assertEqual(result.usage['output_tokens'], 33)
        self.assertEqual(result.usage['format_retries'], 1)
        retry = request.call_args.args[0]
        self.assertIn('Saved submitted answer.', retry.user_prompt)
        self.assertEqual(retry.purpose, 'evaluation')
        self.assertEqual(retry.metadata['evaluation_attempt'], 2)

    def test_document_judge_stops_after_three_invalid_responses(self):
        request = Mock(return_value=LLMResponse('{"criteria":', 'mock', 'judge'))
        with self.assertRaisesRegex(EvaluationError, '3 attempts'):
            RubricDocumentEvaluator(request_fn=request, rubric=self.rubric,
                                    submission_text='Saved answer.').evaluate()
        self.assertEqual(request.call_count, 3)

    def test_document_judge_does_not_retry_service_or_input_errors(self):
        request = Mock(side_effect=RuntimeError('service unavailable'))
        with self.assertRaisesRegex(RuntimeError, 'service unavailable'):
            RubricDocumentEvaluator(request_fn=request, rubric=self.rubric,
                                    submission_text='Saved answer.').evaluate()
        self.assertEqual(request.call_count, 1)
        request.reset_mock()
        with self.assertRaises(EvaluationError):
            RubricDocumentEvaluator(request_fn=request, rubric=self.rubric).evaluate()
        request.assert_not_called()

    def test_document_judge_retries_out_of_range_score_but_accepts_valid_zero(self):
        payload = json.loads(self.valid_payload())
        for criterion in payload['criteria']:
            criterion['score'] = 0
        payload['total_score'] = 0
        zero = json.dumps(payload)
        payload['criteria'][0]['score'] = 999
        payload['total_score'] = 999
        request = Mock(side_effect=[LLMResponse(json.dumps(payload), 'mock', 'judge'),
                                   LLMResponse(zero, 'mock', 'judge')])
        result = RubricDocumentEvaluator(request_fn=request, rubric=self.rubric,
                                        submission_text='Saved answer.').evaluate()
        self.assertEqual(result.total_score, 0)
        self.assertEqual(request.call_count, 2)

    def test_slide_evaluator_uses_both_pdfs_and_adds_limitations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task_pdf = root / "task.pdf"
            slides_pdf = root / "slides.pdf"
            write_pdf(task_pdf, pages=2)
            write_pdf(slides_pdf, pages=2)
            seen_request = {}

            def mock_request(request):
                seen_request["request"] = request
                return LLMResponse(
                    text=self.valid_payload(),
                    provider="mock",
                    model="mock-judge",
                    usage={"input_tokens": 10},
                )

            evaluator = SlideDeckEvaluator(
                request_fn=mock_request,
                task_asset=Asset(task_pdf, "application/pdf", "agent_visible", 1, 2),
                submission=NormalizedSubmission(
                    source_path=slides_pdf,
                    source_mime_type="application/pdf",
                    pdf_path=slides_pdf,
                    validation=ArtifactValidation(
                        True, metadata={"page_count": 2, "size_mb": 0.01}
                    ),
                ),
                rubric=self.rubric,
            )
            result = evaluator.evaluate()
            request = seen_request["request"]
            self.assertEqual(len(request.attachments), 2)
            self.assertEqual(request.attachments[0].role, "agent_visible")
            self.assertEqual(request.attachments[1].role, "judge_only")
            self.assertIn("oral delivery", result.limitations)
            self.assertEqual(result.usage["input_tokens"], 10)


if __name__ == "__main__":
    unittest.main()
