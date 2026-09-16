"""Run the current MCM ready set as a text-only Qwen/Tinker continuation."""
from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
from queue import Queue
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor


ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT.parent / "qwen-extension-runtime-20260915"
OUT = ROOT / "results/tinker_mcm_textonly_20260916"
MODEL = "Qwen/Qwen3.6-35B-A3B"
VARIANTS = ("single_agent", "vallina_otc", "otc")

sys.path.insert(0, str(SNAP / "src"))
from contest_adapters import grade_contest_result  # noqa: E402
from contest_manifest import load_contest_manifest  # noqa: E402
from contest_reporting import report_row  # noqa: E402
from run_competition_batch import inspect_contest_run  # noqa: E402


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(path)


def command(job: dict) -> list[str]:
    return [
        sys.executable, "-u", str(SNAP / "src/run_competition_batch.py"),
        "--live",
        "--provider", "tinker",
        "--model", MODEL,
        "--benchmark-root", str(SNAP / "data/benchmarks"),
        "--contest-manifest", str(OUT / "manifests" / f"{job['id']}.json"),
        "--system-variant", job["variant"],
        "--action-calling", "emulated",
        "--max-output-tokens", "8192",
        "--max-total-tokens", "220000",
        "--temperature", "0.2",
        "--judge-collab",
        "--judge-provider", "tinker",
        "--judge-model", MODEL,
        "--no-judge-cce",
        "--output", str(OUT / "runs" / job["id"]),
    ]


def kill_process_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc.kill()


def latest_mtime(paths: list[Path]) -> float:
    times = [p.stat().st_mtime for p in paths if p.exists()]
    return max(times) if times else 0.0


def prepare() -> None:
    if (OUT / "registry.json").exists():
        raise ValueError("Registry exists; do not overwrite this experiment")
    rows = read(SNAP / "data/benchmarks/mcm/benchmark.json")
    jobs = []
    excluded = []
    for row in rows:
        status = (row.get("evaluation") or {}).get("status")
        text = (row.get("problem_description") or "").strip()
        missing = []
        for asset in row.get("assets", []):
            p = asset.get("path")
            if p and not (SNAP / p).is_file():
                missing.append(p)
        if status != "ready":
            excluded.append({"problem_id": row["problem_id"], "reason": f"status={status}"})
            continue
        if not text:
            excluded.append({"problem_id": row["problem_id"], "reason": "missing problem_description"})
            continue
        if missing:
            excluded.append({"problem_id": row["problem_id"], "reason": "missing assets", "missing": missing})
            continue
        for variant in VARIANTS:
            job_id = f"mcm_{row['problem_id'].split('_', 1)[1].lower()}_{variant}"
            manifest = {
                "session_id": row["problem_id"],
                "competition_id": "mcm",
                "problem_ids": [row["problem_id"]],
                "split_parts": False,
            }
            write(OUT / "manifests" / f"{job_id}.json", manifest)
            job = {
                "id": job_id,
                "competition": "mcm",
                "session_id": row["problem_id"],
                "variant": variant,
                "problem_ids": [row["problem_id"]],
                "route": "text_only_proxy",
                "limitations": [
                    "MCM official source is PDF/document route; this run uses extracted canonical problem_description only.",
                    "Rubric scoring is an LLM proxy, not official COMAP judging.",
                ],
            }
            loaded = load_contest_manifest(OUT / "manifests" / f"{job_id}.json", benchmark_root=SNAP / "data/benchmarks")
            grade = grade_contest_result(loaded, {})
            rubric_tasks = {
                task.task_id
                for task in loaded.tasks
                if task.benchmark.get("evaluation", {}).get("evaluator_id") == "rubric_llm_v1"
            }
            unsupported = [tid for tid, result in grade["tasks"].items() if not result["graded"] and tid not in rubric_tasks]
            if unsupported:
                raise ValueError("No evaluator for " + ", ".join(unsupported))
            state, identity = inspect_contest_run(command(job)[3:])
            if state != "new":
                raise ValueError(f"Fresh output required for {job_id}: {state}")
            job["run_identity"] = identity
            job["task_count"] = len(loaded.tasks)
            job["rubric_scored"] = bool(rubric_tasks)
            jobs.append(job)
    write(OUT / "registry.json", {
        "provider": "tinker",
        "model": MODEL,
        "competition": "mcm",
        "mode": "text_only_proxy",
        "jobs": jobs,
        "excluded": excluded,
        "counts": dict(collections.Counter(job["variant"] for job in jobs)),
    })
    print(f"prepared jobs={len(jobs)} excluded={len(excluded)}")


def lane(registry: dict, work_queue: Queue, slot: int, key: str, idle_seconds: int) -> None:
    records = []
    env = dict(os.environ, TINKER_API_KEY=key)
    while True:
        job = work_queue.get()
        if job is None:
            work_queue.task_done()
            break
        record = {
            "id": job["id"],
            "competition": job["competition"],
            "session_id": job["session_id"],
            "variant": job["variant"],
            "status": "running",
            "limitations": job["limitations"],
        }
        records.append(record)
        write(OUT / f"lane{slot + 1}.json", records)
        cmd = command(job)
        state, identity = inspect_contest_run(cmd[3:])
        if identity != job["run_identity"]:
            raise RuntimeError(f"Registered run identity changed for {job['id']}")
        if state == "complete":
            result_path = OUT / "runs" / job["id"] / "contest_session.json"
        else:
            if state == "resume":
                cmd.append("--resume")
            log = OUT / "logs" / f"{job['id']}.log"
            dest = OUT / "runs" / job["id"]
            log.parent.mkdir(parents=True, exist_ok=True)
            progress_paths = [log, dest / "contest_checkpoint.json", dest / "contest_session.json"]
            last_progress = time.time()
            with log.open("a", encoding="utf-8") as handle:
                proc = subprocess.Popen(cmd, cwd=SNAP, env=env, stdout=handle, stderr=subprocess.STDOUT)
                while True:
                    rc = proc.poll()
                    latest = latest_mtime(progress_paths)
                    if latest > last_progress:
                        last_progress = latest
                    if rc is not None:
                        break
                    if idle_seconds and time.time() - last_progress > idle_seconds:
                        handle.write(f"\n[watchdog] No progress for {idle_seconds}s; killing pid {proc.pid}.\n")
                        handle.flush()
                        kill_process_tree(proc)
                        rc = proc.wait()
                        record["watchdog_killed"] = True
                        break
                    time.sleep(15)
            record["exit_code"] = rc
            result_path = dest / "contest_session.json"
        if result_path.exists():
            result = read(result_path)
            record["status"] = "evaluation_pending" if result.get("evaluation_pending") else "complete"
            record["report"] = report_row(result)
        else:
            record["status"] = "failed"
        write(OUT / f"lane{slot + 1}.json", records)
        print(f"lane={slot + 1} {job['id']} {record['status']}", flush=True)
        work_queue.task_done()


def run() -> None:
    from dotenv import dotenv_values

    for name, value in dotenv_values(ROOT / ".env").items():
        if value is not None:
            os.environ[name] = value
    keys = [os.environ.get("TINKER_API_KEY"), os.environ.get("TINKER_API_KEY2")]
    keys = [key for key in keys if key]
    if not keys:
        raise ValueError("TINKER_API_KEY is required")
    lanes = int(os.environ.get("QWEN_MCM_LANES", "1"))
    idle_seconds = int(os.environ.get("QWEN_MCM_WATCHDOG_IDLE_SECONDS", "600"))
    registry = read(OUT / "registry.json")
    lock = OUT / "supervisor.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        work_queue: Queue = Queue()
        queued = 0
        for job in registry["jobs"]:
            if not (OUT / "runs" / job["id"] / "contest_session.json").exists():
                work_queue.put(job)
                queued += 1
        print(f"queued_unfinished={queued} lanes={lanes}", flush=True)
        for _ in range(lanes):
            work_queue.put(None)
        with ThreadPoolExecutor(max_workers=lanes) as pool:
            futures = [pool.submit(lane, registry, work_queue, i, keys[i % len(keys)], idle_seconds) for i in range(lanes)]
            for future in futures:
                future.result()
        write(OUT / "finished.json", {"status": "queue_exhausted"})
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    prepare() if sys.argv[1:] == ["prepare"] else run()
