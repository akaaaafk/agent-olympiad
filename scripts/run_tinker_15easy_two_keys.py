"""Run 15 easier competitions on full data: single_agent + otc on two Tinker keys."""
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
VARIANTS = ("single_agent", "otc")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def lane(name: str, variant: str, key_env: str, out: Path) -> dict:
    load_repo_dotenv()
    key = os.environ.get(key_env, "").strip()
    if not key:
        raise ValueError(f"{key_env} is unset or empty")
    env = dict(os.environ)
    env["TINKER_API_KEY"] = key
    env.pop("AGENT_OLYMPIAD_DATA_ROOT", None)
    lane_out = out / variant
    lane_out.mkdir(parents=True, exist_ok=True)
    log_path = out / "logs" / f"{variant}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    states = []
    with log_path.open("a", encoding="utf-8") as log:
        log.write(
            f"\n=== lane={name} variant={variant} "
            f"start={datetime.now(timezone.utc).isoformat()} data=full ===\n"
        )
        log.flush()
        for competition in COMPETITIONS:
            job_out = lane_out / competition
            record = {
                "competition": competition,
                "variant": variant,
                "output": str(job_out),
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            states.append(record)
            write_json(out / f"{variant}_status.json", states)
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
            log.write(f"\n--- {competition} ---\n")
            log.flush()
            proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            record["exit_code"] = proc.returncode
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
            sessions = list(job_out.glob("runs/*/contest_session.json"))
            complete = 0
            pending = 0
            for session in sessions:
                result = json.loads(session.read_text(encoding="utf-8-sig"))
                if result.get("evaluation_pending"):
                    pending += 1
                else:
                    complete += 1
            if proc.returncode == 0 and sessions:
                record["status"] = "complete" if pending == 0 else "partial_pending"
            elif sessions:
                record["status"] = "partial_failed"
            else:
                record["status"] = "failed"
            record["sessions"] = len(sessions)
            record["complete"] = complete
            record["pending"] = pending
            write_json(out / f"{variant}_status.json", states)
            print(
                f"lane={name} variant={variant} competition={competition} "
                f"status={record['status']} sessions={len(sessions)} exit={proc.returncode}",
                flush=True,
            )
    return {"lane": name, "variant": variant, "jobs": states}


def main() -> int:
    load_repo_dotenv()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / "results" / f"tinker_qwen_15easy_full_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    write_json(
        out / "plan.json",
        {
            "model": MODEL,
            "competitions": list(COMPETITIONS),
            "variants": list(VARIANTS),
            "data": "data/benchmarks",
            "scope": "full_ready_sessions",
            "lanes": {
                "single_agent": "TINKER_API_KEY",
                "otc": "TINKER_API_KEY2",
            },
        },
    )
    print(json.dumps({"output": str(out), "competitions": len(COMPETITIONS), "variants": 2}, indent=2), flush=True)
    lock = out / "supervisor.lock"
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(lane, "key1", "single_agent", "TINKER_API_KEY", out),
                pool.submit(lane, "key2", "otc", "TINKER_API_KEY2", out),
            ]
            results = [future.result() for future in as_completed(futures)]
        write_json(out / "summary.json", results)
    finally:
        lock.unlink(missing_ok=True)
    failed = [job for result in results for job in result["jobs"] if job["status"] == "failed"]
    print(json.dumps({"failed": len(failed), "output": str(out)}, indent=2), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
