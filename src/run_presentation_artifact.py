"""Run a PDF-first agent team, generate HTML slides, render, and evaluate them."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from artifacts import normalize_submission
from artifacts.assets import file_sha256
from evaluate_artifact import build_task_asset
from evaluation import SlideDeckEvaluator, load_rubric
from llm import LLMAttachment, LLMRequest, RequestFn, make_openai_responses_caller

REPO_ROOT = Path(__file__).resolve().parent.parent

TEAM_SYSTEM = """You are one member of a team solving a presentation task.
The original task PDF is attached. Work from that PDF, not an extracted paraphrase.
Contribute new analysis, calculations, evidence, criticism, or coordination.
Read the team discussion carefully and do not repeat completed work."""

SYNTHESIS_SYSTEM = """You are the final slide editor for a team presentation.
The original task PDF is attached. Return one complete self-contained HTML document only.
Do not wrap it in a Markdown code fence."""


def discussion_text(messages: list[dict]) -> str:
    if not messages:
        return "(No discussion yet.)"
    return "\n\n".join(
        f"[Agent {message['agent_id']} — Round {message['round']}]\n{message['content']}"
        for message in messages
    )


def strip_html_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:html)?\s*", "", stripped, count=1, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped, count=1)
    return stripped.strip()


def run_team(
    request_fn: RequestFn,
    attachment: LLMAttachment,
    *,
    team_size: int,
    rounds: int,
    min_slides: int,
    max_slides: int,
) -> tuple[list[dict], str]:
    messages: list[dict] = []
    for round_number in range(1, rounds + 1):
        for agent_id in range(1, team_size + 1):
            prompt = f"""TEAM DISCUSSION:
{discussion_text(messages)}

YOUR TURN:
You are Agent {agent_id}, round {round_number}/{rounds}. What is your contribution?"""
            response = request_fn(
                LLMRequest(
                    system_prompt=TEAM_SYSTEM,
                    user_prompt=prompt,
                    attachments=(attachment,),
                    purpose="collaboration",
                    metadata={"agent_id": agent_id, "round": round_number},
                )
            )
            messages.append(
                {
                    "agent_id": agent_id,
                    "round": round_number,
                    "content": response.text,
                    "model": response.model,
                    "usage": response.usage,
                }
            )
            print(f"Round {round_number}/{rounds}, Agent {agent_id}/{team_size}: done")

    synthesis_prompt = f"""FULL TEAM DISCUSSION:
{discussion_text(messages)}

FINAL DELIVERABLE:
Create a complete {min_slides}–{max_slides} slide deck that answers the attached task.

HTML CONTRACT:
- Full HTML document with inline CSS only.
- One <section> per 16:9 slide; each section has an h1 or h2 title.
- Use strong visual hierarchy and concise text.
- Inline SVG charts and diagrams are allowed and encouraged.
- Put speaker notes in <aside class="speaker-notes">.
- No scripts, external URLs/assets, video, audio, iframe, or animation.
- Follow every required deliverable and constraint stated in the task PDF.
"""
    final_response = request_fn(
        LLMRequest(
            system_prompt=SYNTHESIS_SYSTEM,
            user_prompt=synthesis_prompt,
            attachments=(attachment,),
            purpose="synthesis",
        )
    )
    return messages, strip_html_fence(final_response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-pdf", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--task-pages", default=None, help="Inclusive range, e.g. 1-10")
    parser.add_argument("--task-label", default="presentation task")
    parser.add_argument("--team-size", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--min-slides", type=int, default=10)
    parser.add_argument("--max-slides", type=int, default=15)
    parser.add_argument("--max-file-size-mb", type=int, default=20)
    parser.add_argument("--agent-model", default=os.environ.get("AGENT_MODEL", "gpt-4.1"))
    parser.add_argument(
        "--judge-model", default=os.environ.get("EVALUATOR_MODEL", "gpt-4.1")
    )
    args = parser.parse_args()

    task_asset = build_task_asset(args.task_pdf, args.task_pages)
    attachment = LLMAttachment(
        path=task_asset.path,
        mime_type=task_asset.mime_type,
        role=task_asset.role,
        page_start=task_asset.page_start,
        page_end=task_asset.page_end,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = (
        REPO_ROOT
        / "results"
        / "presentation_artifacts"
        / f"{task_asset.path.stem}_{stamp}"
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    messages, html = run_team(
        make_openai_responses_caller(args.agent_model),
        attachment,
        team_size=args.team_size,
        rounds=args.rounds,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
    )
    html_path = run_dir / "slides.html"
    html_path.write_text(html, encoding="utf-8")

    normalized = normalize_submission(
        html_path,
        run_dir,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
        max_file_size_mb=args.max_file_size_mb,
    )
    if not normalized.validation.valid:
        raise ValueError(
            "Generated deck failed validation: " + "; ".join(normalized.validation.errors)
        )

    evaluator = SlideDeckEvaluator(
        request_fn=make_openai_responses_caller(args.judge_model),
        task_asset=task_asset,
        submission=normalized,
        rubric=load_rubric(args.rubric.resolve()),
        task_label=args.task_label,
    )
    evaluation = evaluator.evaluate()
    result = {
        "task_pdf": str(task_asset.path),
        "task_page_range": [task_asset.page_start, task_asset.page_end],
        "task_pdf_sha256": task_asset.sha256,
        "rubric": str(args.rubric.resolve()),
        "agent_model": args.agent_model,
        "judge_model": args.judge_model,
        "team_size": args.team_size,
        "rounds": args.rounds,
        "submission_pdf_sha256": file_sha256(normalized.pdf_path),
        "discussion": messages,
        "artifacts": {
            "html": str(html_path.relative_to(REPO_ROOT)),
            "pdf": str(normalized.pdf_path.relative_to(REPO_ROOT)),
        },
        "evaluation": evaluation.to_dict(),
    }
    result_path = run_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Score: {evaluation.total_score:g}/{evaluation.max_score:g}")
    print(f"Saved: {result_path}")


if __name__ == "__main__":
    main()
