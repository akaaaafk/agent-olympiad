"""Run full mini_data for single_agent + otc on TINKER_API_KEY only."""
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
VARIANTS = ("single_agent", "otc")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def run_variant(variant: str, key: str, out: Path) -> dict:
    env = dict(os.environ)
    env["TINKER_API_KEY"] = key
    env["AGENT_OLYMPIAD_DATA_ROOT"] = str(ROOT / "data" / "mini_data")
    job_out = out / variant
    job_out.mkdir(parents=True, exist_ok=True)
    log_path = out / "logs" / f"{variant}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "variant": variant,
        "output": str(job_out),
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(out / f"{variant}_status.json", record)
    cmd = [
        sys.executable,
        "-u",
        str(ROOT / "scripts" / "run_mini_dataset.py"),
        "all",
        "--output",
        str(job_out),
        "--provider",
        "tinker",
        "--model",
        MODEL,
        "--system-variant",
        variant,
        "--max-output-tokens",
        "8192",
        "--temperature",
        "0.2",
    ]
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== {variant} start={record['started_at']} ===\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    sessions = list(job_out.glob("runs/*/contest_session.json"))
    record["exit_code"] = proc.returncode
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    record["sessions"] = len(sessions)
    record["status"] = "complete" if proc.returncode == 0 else "failed"
    write_json(out / f"{variant}_status.json", record)
    print(f"variant={variant} status={record['status']} sessions={len(sessions)} exit={proc.returncode}", flush=True)
    return record


def main() -> int:
    load_repo_dotenv()
    key = os.environ.get("TINKER_API_KEY", "").strip()
    if not key:
        raise ValueError("TINKER_API_KEY missing")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / "results" / f"tinker_qwen_mini_sa_otc_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    plan = {
        "model": MODEL,
        "data": "data/mini_data",
        "variants": list(VARIANTS),
        "api_key_env": "TINKER_API_KEY",
        "note": "KEY2 not used (billing 402)",
    }
    write_json(out / "plan.json", plan)
    print(json.dumps({"output": str(out), **plan}, indent=2), flush=True)
    lock = out / "supervisor.lock"
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(run_variant, v, key, out) for v in VARIANTS]
            results = [f.result() for f in as_completed(futures)]
        write_json(out / "summary.json", results)
    finally:
        lock.unlink(missing_ok=True)
    failed = sum(1 for r in results if r["status"] != "complete")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
