"""Generic multimodal, rubric-grounded evaluator for slide-deck submissions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from artifacts.assets import Asset
from artifacts.slides import NormalizedSubmission
from llm import LLMAttachment, LLMRequest, RequestFn

from .models import EvaluationError, EvaluationResult, Rubric, parse_evaluation_payload


class Evaluator(Protocol):
    def evaluate(self) -> EvaluationResult: ...


@dataclass
class SlideDeckEvaluator:
    request_fn: RequestFn
    task_asset: Asset
    submission: NormalizedSubmission
    rubric: Rubric
    evaluator_id: str = "slide_deck_v1"
    evaluator_version: str = "1.0.0"
    prompt_version: str = "slide_deck_pdf_v1"
    task_label: str = "presentation task"

    def _system_prompt(self) -> str:
        return (
            "You are an expert presentation evaluator. Evaluate the submitted slide deck "
            "against the supplied task PDF and structured rubric. Inspect both content "
            "and the visible rendered deck. Be strict, evidence-grounded, and do not "
            "infer oral behavior that is not visible."
        )

    def _user_prompt(self) -> str:
        checks = {
            "valid": self.submission.validation.valid,
            "errors": self.submission.validation.errors,
            "warnings": self.submission.validation.warnings,
            "metadata": self.submission.validation.metadata,
        }
        schema = {
            "criteria": [
                {
                    "id": criterion.id,
                    "score": "number",
                    "max_score": criterion.max_score,
                    "evidence": ["Slide N: concrete visible evidence"],
                    "justification": "2-4 sentences",
                    "confidence": "number from 0 to 1",
                    "observable": criterion.observable,
                }
                for criterion in self.rubric.criteria
            ],
            "total_score": "sum of criterion scores",
            "max_score": self.rubric.total_points,
            "warnings": ["artifact or scoring warning"],
            "limitations": ["what cannot be judged from this deck"],
        }
        return f"""Two PDFs are attached in this order:
1. the official {self.task_label};
2. the team's normalized slide deck.

STRUCTURED RUBRIC:
{json.dumps(self.rubric.as_prompt_dict(), indent=2)}

DETERMINISTIC ARTIFACT CHECKS:
{json.dumps(checks, indent=2)}

SCORING RULES:
- Score only the attached submission, using the task PDF as context.
- Cite specific slide numbers and visible evidence for every criterion.
- Check quantitative claims for internal coherence; do not reward unsupported precision.
- Score written and visual communication only where the rubric requests it.
- Do not infer oral delivery, timing, Q&A, or on-stage teamwork.
- Use each exact criterion id and maximum from the rubric.
- The total_score must equal the sum of criterion scores.
- Return JSON only, with no Markdown fence or commentary.

REQUIRED JSON SHAPE:
{json.dumps(schema, indent=2)}
"""

    def evaluate(self) -> EvaluationResult:
        if not self.submission.validation.valid:
            raise EvaluationError(
                "Submission failed deterministic validation: "
                + "; ".join(self.submission.validation.errors)
            )
        response = self.request_fn(
            LLMRequest(
                system_prompt=self._system_prompt(),
                user_prompt=self._user_prompt(),
                attachments=(
                    LLMAttachment(
                        path=self.task_asset.path,
                        mime_type=self.task_asset.mime_type,
                        role=self.task_asset.role,
                        page_start=self.task_asset.page_start,
                        page_end=self.task_asset.page_end,
                    ),
                    LLMAttachment(
                        path=self.submission.pdf_path,
                        mime_type="application/pdf",
                        role="judge_only",
                    ),
                ),
                purpose="evaluation",
                metadata={
                    "evaluator_id": self.evaluator_id,
                    "rubric_id": self.rubric.rubric_id,
                },
            )
        )
        result = parse_evaluation_payload(
            response.text,
            rubric=self.rubric,
            evaluator_id=self.evaluator_id,
            evaluator_version=self.evaluator_version,
            prompt_version=self.prompt_version,
            model=response.model,
            warnings=self.submission.validation.warnings,
            artifact_checks=self.submission.validation.metadata,
            usage=response.usage,
        )
        for limitation in self.rubric.not_observable_from_deck:
            if limitation not in result.limitations:
                result.limitations.append(limitation)
        return result
