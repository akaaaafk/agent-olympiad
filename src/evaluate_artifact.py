"""Evaluate an HTML or PDF slide deck against a task PDF and rubric JSON."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

from artifacts import Asset, normalize_submission
from artifacts.assets import file_sha256
from evaluation import SlideDeckEvaluator, load_rubric
from llm import make_openai_responses_caller

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_page_range(value: str | None, page_count: int) -> tuple[int, int]:
    if not value:
        return 1, page_count
    try:
        start_text, end_text = value.split("-", 1)
        start, end = int(start_text), int(end_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("Page range must look like START-END, e.g. 3-12.") from exc
    if start < 1 or end < start or end > page_count:
        raise ValueError(f"Invalid page range {start}-{end} for {page_count}-page PDF.")
    return start, end


def build_task_asset(task_pdf: Path, pages: str | None) -> Asset:
    path = task_pdf.resolve()
    if not path.is_file() or path.read_bytes()[:5] != b"%PDF-":
        raise ValueError(f"Task input is not a readable PDF: {path}")
    page_count = len(PdfReader(str(path)).pages)
    page_start, page_end = parse_page_range(pages, page_count)
    return Asset(
        path=path,
        mime_type="application/pdf",
        role="agent_visible",
        page_start=page_start,
        page_end=page_end,
        sha256=file_sha256(path),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path, help="Self-contained HTML deck or PDF deck")
    parser.add_argument("--task-pdf", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--task-pages", default=None, help="Inclusive range, e.g. 1-10")
    parser.add_argument("--task-label", default="presentation task")
    parser.add_argument("--min-slides", type=int, default=1)
    parser.add_argument("--max-slides", type=int, default=20)
    parser.add_argument("--max-file-size-mb", type=int, default=20)
    parser.add_argument("--model", default=os.environ.get("EVALUATOR_MODEL", "gpt-4.1"))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    task_asset = build_task_asset(args.task_pdf, args.task_pages)
    rubric = load_rubric(args.rubric.resolve())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = (
        REPO_ROOT / "results" / "evaluations" / f"{task_asset.path.stem}_{timestamp}"
    )
    normalized = normalize_submission(
        args.submission,
        run_dir,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
        max_file_size_mb=args.max_file_size_mb,
    )
    if not normalized.validation.valid:
        raise ValueError(
            "Submission validation failed: " + "; ".join(normalized.validation.errors)
        )

    evaluator = SlideDeckEvaluator(
        request_fn=make_openai_responses_caller(model=args.model),
        task_asset=task_asset,
        submission=normalized,
        rubric=rubric,
        task_label=args.task_label,
    )
    result = evaluator.evaluate()
    payload = {
        "task_pdf": str(task_asset.path),
        "task_page_range": [task_asset.page_start, task_asset.page_end],
        "task_pdf_sha256": task_asset.sha256,
        "rubric": str(args.rubric.resolve()),
        "submission_sha256": file_sha256(normalized.pdf_path),
        "submission_source": str(args.submission.resolve()),
        "normalized_pdf": str(normalized.pdf_path.relative_to(REPO_ROOT)),
        "evaluation": result.to_dict(),
    }

    output_path = args.output.resolve() if args.output else run_dir / "evaluation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Score: {result.total_score:g}/{result.max_score:g}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
