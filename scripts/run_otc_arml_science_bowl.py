#!/usr/bin/env python3
"""Generate contest manifests and run OTC contest-session batch for ARML + Science Bowl."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "data" / "benchmarks"
MANIFEST_ROOT = REPO_ROOT / "data" / "contest_manifests" / "generated"
PYTHON = Path(r"e:\agent_olympiad\.venv\Scripts\python.exe")

# Known OCR/diagram repairs for ARML Local packets.
ARML_PROMPT_OVERRIDES: dict[str, dict[str, str]] = {
    "arml_local_2010": {
        "3": (
            "At a meeting of the Nuclear Powerplant Workers of America, every person "
            "has 3, 4, 5, 6, or 7 fingers on each hand. The probability of having k "
            "fingers on one hand is 2^(2-|5-k|)/10. The numbers of fingers on the left "
            "and right hands are independent. Compute the probability that a member "
            "has at least 10 fingers total."
        ),
        "10": (
            "In the multiplication puzzle, A, B, C, D, E, and F are distinct non-zero "
            "digits. The aligned equations shown in the original diagram are "
            "ABC × D = DEC and ABC × E = FEC, where juxtaposition denotes decimal "
            "digits. Compute the six-digit number ABCDEF."
        ),
    },
}


def _gradeable_question_ids(problem: dict) -> list[str]:
    ids: list[str] = []
    for part in (problem.get("gold_label") or {}).get("parts") or []:
        expected = part.get("expected")
        if (
            isinstance(expected, str)
            and expected.strip()
            and part.get("match_mode") != "reference_llm"
            and float(part.get("points") or 0) > 0
            and part.get("id") is not None
        ):
            ids.append(str(part["id"]))
    return ids


def write_manifests(competitions: list[str]) -> list[Path]:
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for competition in competitions:
        problems = json.loads(
            (BENCH_ROOT / competition / "benchmark.json").read_text(encoding="utf-8")
        )
        for problem in problems:
            problem_id = str(problem["problem_id"])
            gradeable = _gradeable_question_ids(problem)
            if not gradeable:
                continue
            payload: dict = {
                "session_id": problem_id,
                "competition_id": competition,
                "problem_ids": [problem_id],
                "description": f"OTC contest-session manifest for {problem_id}",
            }
            if competition == "arml_local":
                payload["split_parts"] = True
                payload["question_ids"] = gradeable
                overrides = ARML_PROMPT_OVERRIDES.get(problem_id)
                if overrides:
                    payload["prompt_overrides"] = {
                        key: value
                        for key, value in overrides.items()
                        if key in gradeable
                    }
            else:
                # Single-part short-answer contests stay one task.
                payload["split_parts"] = False
            path = MANIFEST_ROOT / f"{problem_id}.json"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            paths.append(path)
    return paths


def case_complete(out_dir: Path) -> bool:
    session = out_dir / "contest_session.json"
    if not session.is_file():
        return False
    try:
        payload = json.loads(session.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    grade = payload.get("grade") or {}
    return bool(grade.get("graded")) and "task_utility" in (payload.get("metrics") or {})


def run_one(
    manifest: Path,
    *,
    out_root: Path,
    team_size: int,
    max_turns: int,
    max_api_calls: int,
    system_variant: str,
) -> dict:
    problem_id = manifest.stem
    out_dir = out_root / problem_id
    out_dir.mkdir(parents=True, exist_ok=True)
    if case_complete(out_dir):
        return {"problem_id": problem_id, "status": "skipped_complete", "out_dir": str(out_dir)}

    cmd = [
        str(PYTHON),
        "-u",
        str(REPO_ROOT / "src" / "run_competition_batch.py"),
        "--live",
        "--provider",
        "perplexity",
        "--model",
        "openai/gpt-5.4-mini",
        "--contest-manifest",
        str(manifest),
        "--system-variant",
        system_variant,
        "--action-calling",
        "native",
        "--team-size",
        str(team_size),
        "--max-turns",
        str(max_turns),
        "--max-api-calls",
        str(max_api_calls),
        "--max-total-tokens",
        "220000",
        "--no-judge-task",
        "--no-judge-cce",
        "--output",
        str(out_dir),
    ]
    # The baseline decides the review workflow; no override is passed.
    log_path = out_dir / "run.log"
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n==== RUN {problem_id} ====\n")
        log.flush()
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    status = "ok" if proc.returncode == 0 and case_complete(out_dir) else "error"
    return {
        "problem_id": problem_id,
        "status": status,
        "returncode": proc.returncode,
        "out_dir": str(out_dir),
    }


def summarize(out_root: Path, problem_ids: list[str]) -> Path:
    rows = []
    for problem_id in problem_ids:
        session_path = out_root / problem_id / "contest_session.json"
        row = {
            "problem_id": problem_id,
            "status": "missing",
            "score": "",
            "max_score": "",
            "task_utility": "",
            "coordination_score": "",
            "turns_used": "",
            "api_calls_used": "",
            "deadline_submission": "",
        }
        if session_path.is_file():
            try:
                payload = json.loads(session_path.read_text(encoding="utf-8"))
                grade = payload.get("grade") or {}
                metrics = payload.get("metrics") or {}
                diag = payload.get("diagnostics") or {}
                budget = payload.get("budget") or {}
                row.update(
                    {
                        "status": "ok" if grade.get("graded") else "ungraded",
                        "score": grade.get("score", ""),
                        "max_score": grade.get("max_score", ""),
                        "task_utility": metrics.get("task_utility", ""),
                        "coordination_score": metrics.get("coordination_score", ""),
                        "turns_used": budget.get("turns_used", ""),
                        "api_calls_used": budget.get("api_calls_used", ""),
                        "deadline_submission": diag.get("deadline_submission", ""),
                    }
                )
            except json.JSONDecodeError:
                row["status"] = "corrupt"
        rows.append(row)
    path = out_root / "summary.tsv"
    fields = list(rows[0].keys()) if rows else ["problem_id", "status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--competitions",
        default="arml_local,science_bowl",
        help="Comma-separated competition ids",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "otc_arml_science_bowl_20260903",
    )
    parser.add_argument(
        "--system-variant",
        default="strategic_team",
        choices=[
            "single_agent",
            "decentralized",
            "centralized",
            "open_table_coach",
            "open_table_coach_memory",
            # legacy aliases
            "strategic_team",
            "vanilla_team",
        ],
    )
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--arml-max-turns", type=int, default=50)
    parser.add_argument("--arml-max-api-calls", type=int, default=151)
    parser.add_argument("--sb-max-turns", type=int, default=50)
    parser.add_argument("--sb-max-api-calls", type=int, default=151)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    competitions = [item.strip() for item in args.competitions.split(",") if item.strip()]
    manifests = write_manifests(competitions)
    if args.limit is not None:
        manifests = manifests[: args.limit]
    args.output.mkdir(parents=True, exist_ok=True)
    index_path = args.output / "manifest_index.json"
    index_path.write_text(
        json.dumps([str(path.relative_to(REPO_ROOT)) for path in manifests], indent=2),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(manifests)} manifests under {MANIFEST_ROOT} | "
        f"variant={args.system_variant}",
        flush=True,
    )

    results = []
    for index, manifest in enumerate(manifests, start=1):
        competition = json.loads(manifest.read_text(encoding="utf-8"))["competition_id"]
        if competition == "arml_local":
            max_turns, max_api = args.arml_max_turns, args.arml_max_api_calls
        else:
            max_turns, max_api = args.sb_max_turns, args.sb_max_api_calls
        print(
            f"[{index}/{len(manifests)}] {manifest.stem} "
            f"variant={args.system_variant} (turns={max_turns}, api={max_api})",
            flush=True,
        )
        result = run_one(
            manifest,
            out_root=args.output,
            team_size=args.team_size,
            max_turns=max_turns,
            max_api_calls=max_api,
            system_variant=args.system_variant,
        )
        print(f"  -> {result['status']}", flush=True)
        results.append(result)
        summarize(args.output, [path.stem for path in manifests])

    summary = summarize(args.output, [path.stem for path in manifests])
    ok = sum(1 for row in results if row["status"] in {"ok", "skipped_complete"})
    print(f"DONE {ok}/{len(results)} complete | summary={summary}", flush=True)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
