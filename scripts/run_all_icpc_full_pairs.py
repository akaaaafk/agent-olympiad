"""Run fresh full-contest OTC/Vanilla pairs for every remaining ICPC WF year.

The batch is resumable: a run is skipped only when its contest_session.json
exists and matches the requested session and variant. Generated manifests,
per-run logs, and batch_status.json live under the selected output root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCHMARK = REPO / "data" / "benchmarks" / "icpc" / "benchmark.json"
TRACE_RUNNER = (
    REPO
    / "results"
    / "icpc_2012_low_score_diagnosis_20260908"
    / "run_with_context_trace.py"
)
PYTHON = REPO.parent / ".venv" / "Scripts" / "python.exe"
GATEWAY_HEALTH = "http://127.0.0.1:8787/v1/health"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def gateway_ready() -> bool:
    try:
        with urllib.request.urlopen(GATEWAY_HEALTH, timeout=5) as response:
            payload = json.load(response)
        return response.status == 200 and payload.get("ok") is True
    except Exception:
        return False


def completed(run_dir: Path, session_id: str, variant: str) -> bool:
    result = run_dir / "contest_session.json"
    if not result.exists():
        return False
    try:
        payload = json.loads(result.read_text(encoding="utf-8"))
    except Exception:
        return False
    stored_variant = payload.get("system_variant")
    equivalent_variants = {
        "strategic_team": {"strategic_team", "strategic"},
        "vanilla_team": {"vanilla_team", "vanilla"},
    }
    return payload.get("session_id") == session_id and stored_variant in equivalent_variants.get(
        variant, {variant}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO / "results" / "icpc_all_full_pairs_20260909",
    )
    parser.add_argument("--start-year", type=int, default=2012)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--skip-year",
        type=int,
        action="append",
        default=[],
        help="Year already covered by a separately verified pair.",
    )
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    manifest_dir = output_root / "manifests"
    log_dir = output_root / "logs"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "batch_status.json"

    tasks = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    by_year: dict[int, list[str]] = {}
    for task in tasks:
        year = int(task["year"])
        evaluation = task.get("evaluation") or {}
        if not (
            args.start_year <= year <= args.end_year
            and evaluation.get("status") == "remote_judge_ready"
            and evaluation.get("vjudge_prob_num")
        ):
            continue
        by_year.setdefault(year, []).append(task["problem_id"])

    jobs = []
    for year in sorted(by_year):
        if year in set(args.skip_year):
            continue
        session_id = f"icpc_wf_{year}"
        manifest_path = manifest_dir / f"{session_id}.json"
        write_json(
            manifest_path,
            {
                "session_id": session_id,
                "competition_id": "icpc",
                "problem_ids": by_year[year],
                "split_parts": False,
                "description": (
                    f"Full ICPC World Finals {year} contest: "
                    f"{len(by_year[year])} problems under one shared turn budget."
                ),
            },
        )
        for variant in ("strategic_team", "vanilla_team"):
            short = "otc" if variant == "strategic_team" else "vanilla"
            run_dir = output_root / "runs" / f"{session_id}_{short}"
            jobs.append((year, session_id, manifest_path, variant, run_dir))

    state = {
        "created_at": now(),
        "updated_at": now(),
        "status": "running",
        "configuration": {
            "provider": "perplexity",
            "model": "openai/gpt-5.4-mini",
            "team_size": 3,
            "max_turns": 50,
            "max_simulated_minutes": 300,
            "programming_deadline_submit": True,
            "skipped_verified_years": sorted(set(args.skip_year)),
        },
        "total_jobs": len(jobs),
        "jobs": [],
    }
    if status_path.exists():
        try:
            previous = json.loads(status_path.read_text(encoding="utf-8"))
            state["created_at"] = previous.get("created_at", state["created_at"])
            state["jobs"] = previous.get("jobs", [])
        except Exception:
            pass
    job_state = {
        (entry.get("year"), entry.get("variant")): entry for entry in state["jobs"]
    }

    for year, session_id, manifest_path, variant, run_dir in jobs:
        key = (year, variant)
        entry = job_state.get(key, {"year": year, "variant": variant})
        if completed(run_dir, session_id, variant):
            entry.update(status="completed", skipped_on_resume=True, updated_at=now())
            job_state[key] = entry
            continue
        if not gateway_ready():
            entry.update(status="blocked", reason="gateway health check failed", updated_at=now())
            job_state[key] = entry
            state.update(status="blocked", updated_at=now(), jobs=list(job_state.values()))
            write_json(status_path, state)
            return 2

        run_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{session_id}_{variant}.log"
        resuming = (run_dir / "contest_checkpoint.json").is_file()
        runner_path = REPO / "src" / "run_competition_batch.py" if resuming else TRACE_RUNNER
        command = [
            str(PYTHON),
            "-u",
            str(runner_path),
            "--live",
            "--provider",
            "perplexity",
            "--model",
            "openai/gpt-5.4-mini",
            "--contest-manifest",
            str(manifest_path),
            "--system-variant",
            variant,
            "--action-calling",
            "native",
            "--team-size",
            "3",
            "--max-turns",
            "50",
            "--start-seat",
            "0",
            "--max-simulated-minutes",
            "300",
            "--programming-deadline-submit",
            "--no-judge-collab",
            "--no-judge-task",
            "--no-judge-cce",
            "--output",
            str(run_dir),
        ]
        # Preserve a partially completed contest after a transient provider
        # failure. The contest runner validates checkpoint compatibility.
        if resuming:
            command.append("--resume")
        entry.update(
            status="running",
            started_at=now(),
            output=str(run_dir),
            log=str(log_path),
        )
        job_state[key] = entry
        state.update(updated_at=now(), jobs=list(job_state.values()))
        write_json(status_path, state)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n[{now()}] START {' '.join(command)}\n")
            log.flush()
            result = subprocess.run(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
            log.write(f"[{now()}] EXIT {result.returncode}\n")
        entry.update(
            status="completed" if result.returncode == 0 else "failed",
            exit_code=result.returncode,
            finished_at=now(),
            updated_at=now(),
        )
        state.update(updated_at=now(), jobs=list(job_state.values()))
        write_json(status_path, state)
        if result.returncode != 0:
            state["status"] = "failed"
            write_json(status_path, state)
            return result.returncode
        time.sleep(15)

    state.update(status="completed", updated_at=now(), jobs=list(job_state.values()))
    write_json(status_path, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
