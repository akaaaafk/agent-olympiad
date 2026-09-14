"""Run contest jobs with one isolated subprocess per Tinker credential slot."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import time
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from env_config import load_repo_dotenv
from contest_config import BASELINE_NAMES
from run_competition_batch import inspect_contest_run, _write_json_atomic


def job_command(manifest: Path, variant: str, destination: Path, turns: int) -> list[str]:
    return [sys.executable, "-u", str(ROOT / "src/run_competition_batch.py"),
            "--live", "--provider", "tinker", "--contest-manifest", str(manifest),
            "--system-variant", variant, "--action-calling", "auto",
            "--rules-mode", "enforced" if variant in {"vallina_otc", "otc"} else "off",
            "--max-output-tokens", "8192", "--temperature", "0.2",
            "--max-turns", str(turns), "--max-simulated-minutes", str(turns * 5),
            "--deadline-submit", "--no-judge-task", "--no-judge-collab", "--no-judge-cce",
            "--output", str(destination)]


def child_environment(base: dict[str, str], key_name: str) -> dict[str, str]:
    selected = base[key_name]
    env = {k: v for k, v in base.items() if not k.startswith("TINKER_API_KEY")}
    env["TINKER_API_KEY"] = selected
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--variants", nargs="+", choices=BASELINE_NAMES, default=["otc"])
    parser.add_argument("--key-env", nargs="+", help="Credential variable names, never key values")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    load_repo_dotenv(args.env_file)
    base = dict(os.environ)
    names = args.key_env or sorted(k for k in base if
        (k == "TINKER_API_KEY" or k.startswith("TINKER_API_KEY_")
         or k.removeprefix("TINKER_API_KEY").isdigit()) and base[k].strip())
    if not names or any(not base.get(k, "").strip() for k in names):
        parser.error("Missing configured Tinker credential variables")
    if len({base[k].removeprefix("tinker:").strip() for k in names}) != len(names):
        parser.error("Credential slots must contain distinct keys")
    if not base.get("TINKER_MODEL"):
        parser.error("Set TINKER_MODEL in the environment or --env-file")
    if args.max_turns <= 0:
        parser.error("--max-turns must be positive")
    manifests = [p.resolve() for p in args.manifest]
    if any(not p.is_file() for p in manifests):
        parser.error("A requested manifest does not exist")
    out = args.output or ROOT / "results" / ("tinker_parallel_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    jobs = queue.Queue()
    plan = []
    for index, manifest in enumerate(manifests):
        for variant in args.variants:
            destination = out / f"{index + 1:02d}_{manifest.stem}" / variant
            cmd = job_command(manifest, variant, destination, args.max_turns)
            _, identity = inspect_contest_run(cmd[3:])
            job = {"manifest": str(manifest), "variant": variant, "output": str(destination),
                   "identity": identity, "command": cmd,
                   "manifest_file_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}
            jobs.put(job)
            plan.append(job)
    _write_json_atomic(out / "plan.json", {"model": base["TINKER_MODEL"], "key_slots": names, "jobs": plan})
    print(f"OUTPUT={out} MODEL={base['TINKER_MODEL']} SLOTS={len(names)} JOBS={jobs.qsize()}", flush=True)
    if args.preflight_only:
        return 0
    records = []
    lock = threading.Lock()

    def record_status(record: dict) -> None:
        with lock:
            records.append(record)
            _write_json_atomic(out / "summary.json", records)

    def worker(name: str) -> list[dict]:
        completed = []
        env = child_environment(base, name)
        while True:
            try:
                job = jobs.get_nowait()
            except queue.Empty:
                return completed
            manifest, variant, destination = Path(job["manifest"]), job["variant"], Path(job["output"])
            cmd = job["command"]
            _, current_identity = inspect_contest_run(cmd[3:])
            if (current_identity != job["identity"] or
                hashlib.sha256(manifest.read_bytes()).hexdigest() != job["manifest_file_sha256"]):
                record = {"variant": variant, "output": str(destination), "valid_result": False,
                          "error": "Run inputs or source changed since batch preflight; not launched"}
                record_status(record)
                completed.append(record)
                print(f"BLOCKED variant={variant} contest={manifest.stem}: input identity changed", flush=True)
                continue
            destination.mkdir(parents=True)
            started = time.perf_counter()
            print(f"START slot={name} contest={manifest.stem} variant={variant}", flush=True)
            with (destination / "runner.log").open("w", encoding="utf-8") as log:
                process = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            record = {"key_slot": name, "manifest": str(manifest), "variant": variant,
                      "output": str(destination), "exit_code": process.returncode,
                      "elapsed_seconds": time.perf_counter() - started}
            result_path = destination / "contest_session.json"
            record["valid_result"] = False
            if process.returncode == 0 and result_path.is_file():
                result = json.loads(result_path.read_text(encoding="utf-8"))
                record["valid_result"] = (result.get("system_variant") == variant
                    and bool(result.get("grade", {}).get("graded"))
                    and result.get("run_identity") == job["identity"])
                record["grade"] = {k: result.get("grade", {}).get(k) for k in ("score", "max_score")}
            (destination / "launch_summary.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
            completed.append(record)
            record_status(record)
            print(f"END slot={name} variant={variant} exit={process.returncode} valid={record['valid_result']}", flush=True)

    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        futures = [pool.submit(worker, name) for name in names]
        for future in futures:
            future.result()
    (out / "summary.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return 0 if all(r["valid_result"] for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
