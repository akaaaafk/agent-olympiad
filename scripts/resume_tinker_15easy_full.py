"""Resume incomplete jobs from the 15easy full batch. Uses KEY1 for both lanes if KEY2 is billed out."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from env_config import load_repo_dotenv

MODEL = "Qwen/Qwen3.6-35B-A3B"
BATCH = ROOT / "results" / "tinker_qwen_15easy_full_20260918_011924"
COMPETITIONS = (
    "arml_local",
    "arml_national_team",
    "purple_comet",
    "wmtc",
    "hmmt_team",
    "qanta",
    "science_bowl",
    "arml_national_power",
    "arml_power",
    "pumac_power",
    "iol_team",
    "ioaa_group",
    "wsc_writing",
    "ethics_bowl_nhseb",
    "fyziklani",
)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def missing(variant: str, competition: str) -> tuple[int, int]:
    rows = json.loads((ROOT / "data/benchmarks" / competition / "benchmark.json").read_text(encoding="utf-8"))
    ready = sum(
        1
        for r in rows
        if (r.get("evaluation") or {}).get("status") in ("ready", "ready_with_limitations")
    )
    out = BATCH / variant / competition
    done = len(list(out.glob("runs/*/contest_session.json"))) if out.exists() else 0
    return ready, done


def lane(name: str, variant: str, key: str) -> dict:
    env = dict(os.environ)
    env["TINKER_API_KEY"] = key
    env.pop("AGENT_OLYMPIAD_DATA_ROOT", None)
    log_path = BATCH / "logs" / f"resume_{variant}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    states = []
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== resume lane={name} variant={variant} start={datetime.now(timezone.utc).isoformat()} ===\n")
        log.flush()
        for competition in COMPETITIONS:
            ready, done = missing(variant, competition)
            if done >= ready:
                continue
            job_out = BATCH / variant / competition
            job_out.mkdir(parents=True, exist_ok=True)
            lock = job_out / "pipeline.lock"
            lock.unlink(missing_ok=True)
            record = {
                "competition": competition,
                "variant": variant,
                "ready": ready,
                "done_before": done,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            states.append(record)
            write_json(BATCH / f"resume_{variant}_status.json", states)
            cmd = [
                sys.executable,
                "-u",
                str(ROOT / "scripts" / "run_pipeline.py"),
                "all",
                "--output",
                str(job_out),
                "--provider",
                "tinker",
                "--model",
                MODEL,
                "--competitions",
                competition,
                "--system-variant",
                variant,
                "--max-output-tokens",
                "8192",
                "--temperature",
                "0.2",
            ]
            log.write(f"\n--- resume {competition} ready={ready} done={done} ---\n")
            log.flush()
            proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            _, done_after = missing(variant, competition)
            record["exit_code"] = proc.returncode
            record["done_after"] = done_after
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
            record["status"] = "complete" if done_after >= ready and proc.returncode == 0 else "partial"
            write_json(BATCH / f"resume_{variant}_status.json", states)
            print(
                f"lane={name} {variant}/{competition} {done}->{done_after}/{ready} exit={proc.returncode}",
                flush=True,
            )
    return {"lane": name, "variant": variant, "jobs": states}


def main() -> int:
    load_repo_dotenv()
    key1 = os.environ.get("TINKER_API_KEY", "").strip()
    if not key1:
        raise ValueError("TINKER_API_KEY missing")
    # KEY2 is billing-blocked (402); run both lanes on KEY1 in parallel.
    otc_key = key1
    plan = {
        "batch": str(BATCH),
        "model": MODEL,
        "lanes": {
            "single_agent": "TINKER_API_KEY",
            "otc": "TINKER_API_KEY(fallback; KEY2 billing 402)",
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(BATCH / "resume_plan.json", plan)
    print(json.dumps(plan, indent=2), flush=True)
    lock = BATCH / "resume_supervisor.lock"
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(lane, "key1", "single_agent", key1),
                pool.submit(lane, "key2-or-fallback", "otc", otc_key),
            ]
            results = [f.result() for f in as_completed(futures)]
        write_json(BATCH / "resume_summary.json", results)
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
