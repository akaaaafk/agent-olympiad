"""Run the remaining task-based scopes only after the OpenAgents pilots pass."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT.parent / "openagents-runtime-20260914"
sys.path.insert(0, str(RUNTIME / "src"))
from env_config import load_repo_dotenv
from run_competition_batch import inspect_contest_run

OUT = ROOT / "results/openagents_glm52_remaining_task_based_20260914"
SOURCE = ROOT / "results/tinker_task_based_arml_icpc_20260914"
PILOTS = {
    "single_agent": ROOT / "results/openagents_glm52_arml2009_single_20260914",
    "vallina_otc": ROOT / "results/openagents_glm52_arml2009_vallina_otc_8192fix_20260914",
    "otc": ROOT / "results/openagents_glm52_arml2009_otc_8192fix_20260914",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(job):
    return [sys.executable, "-u", str(RUNTIME / "src/run_competition_batch.py"),
            "--live", "--provider", "openagents", "--model", "glm-5.2",
            "--benchmark-root", str(ROOT / "data/benchmarks"),
            "--contest-manifest", str(SOURCE / "manifests" / (job["id"] + ".json")),
            "--system-variant", job["variant"], "--action-calling", "native",
            "--max-output-tokens", str(job["max_output_tokens"]),
            "--max-total-tokens", "220000", "--temperature", "0.2",
            "--judge-collab", "--judge-provider", "openagents", "--judge-model", "glm-5.2",
            "--no-judge-cce", "--output", str(OUT / "runs" / job["id"])]


def pilot_state(variant, directory):
    exit_path = directory / "launcher_exit.json"
    if exit_path.exists() and read(exit_path).get("exit_code") != 0:
        return "failed"
    result_path = directory / "contest_session.json"
    if not result_path.exists():
        return "waiting"
    result = read(result_path)
    run = result.get("run") or {}
    if (run.get("provider") != "openagents" or run.get("model") != "glm-5.2"
            or result.get("system_variant") != variant or result.get("session_id") != "arml_local_2009"):
        return "incompatible"
    if not (result.get("grade") or {}).get("graded"):
        return "failed"
    if result.get("evaluation_pending"):
        return "failed"
    stages = result.get("evaluation_stages") or {}
    if any((stages.get(name) or {}).get("status") != "complete" for name in ("coordination", "interaction")):
        return "waiting"
    if variant != "single_agent" and not exit_path.exists():
        return "waiting"
    return "complete"


def prepare():
    if (OUT / "registry.json").exists():
        raise ValueError("Registry already exists")
    source = read(SOURCE / "registry.json")
    jobs = []
    for original in source["jobs"]:
        if original["problem_id"] == "arml_local_2009":
            continue
        job = {k: original[k] for k in ("id", "variant", "competition", "problem_id", "max_output_tokens")}
        state, job["run_identity"] = inspect_contest_run(command(job)[3:])
        if state != "new":
            raise ValueError("Fresh output required")
        jobs.append(job)
    files = list((RUNTIME / "src").rglob("*.py")) + list((RUNTIME / "configs").rglob("*.json"))
    files += list((ROOT / "data/rules").rglob("*.json")) + list((ROOT / "data/benchmarks").glob("*/benchmark.json"))
    files += [SOURCE / "manifests" / (j["id"] + ".json") for j in jobs]
    write(OUT / "registry.json", dict(jobs=jobs, pilots={k: str(v) for k, v in PILOTS.items()},
                                      file_hashes={str(p): digest(p) for p in files}))
    print(f"Registered {len(jobs)} remaining jobs; three pilots are dependencies, not reruns.")


def run():
    lock = OUT / "supervisor.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        while True:
            pilots = {v: pilot_state(v, p) for v, p in PILOTS.items()}
            if any(s in ("failed", "incompatible") for s in pilots.values()):
                write(OUT / "status.json", dict(status="blocked_by_pilot", pilots=pilots))
                return
            if all(s == "complete" for s in pilots.values()):
                break
            write(OUT / "status.json", dict(status="waiting_for_pilots", pilots=pilots))
            time.sleep(30)
        registry = read(OUT / "registry.json")
        rows = []
        failed = 0
        for job in registry["jobs"]:
            if any(not Path(p).exists() or digest(Path(p)) != h for p, h in registry["file_hashes"].items()):
                write(OUT / "status.json", dict(status="blocked_source_changed", jobs=rows))
                return
            cmd = command(job)
            state, identity = inspect_contest_run(cmd[3:])
            if identity != job["run_identity"]:
                raise ValueError("Effective run identity changed")
            item = dict(id=job["id"], status="running")
            rows.append(item)
            write(OUT / "status.json", dict(status="running", jobs=rows))
            if state != "complete":
                if state == "resume":
                    cmd.append("--resume")
                logs = OUT / "logs"
                logs.mkdir(exist_ok=True)
                with (logs / (job["id"] + ".log")).open("a", encoding="utf-8") as log:
                    completed = subprocess.run(cmd, cwd=RUNTIME, stdout=log, stderr=subprocess.STDOUT)
                item["exit_code"] = completed.returncode
            path = OUT / "runs" / job["id"] / "contest_session.json"
            if path.exists():
                result = read(path)
                item.update(status="evaluation_pending" if result.get("evaluation_pending") else "complete",
                            report=result.get("report"), evaluation_stages=result.get("evaluation_stages"))
                failed = 0
            else:
                item["status"] = "failed"
                failed += 1
            write(OUT / "status.json", dict(status="running", jobs=rows))
            if failed >= 3:
                write(OUT / "status.json", dict(status="blocked_repeated_failures", jobs=rows))
                return
        write(OUT / "status.json", dict(status="queue_finished", jobs=rows))
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "run"))
    args = parser.parse_args()
    load_repo_dotenv(ROOT / ".env")
    prepare() if args.stage == "prepare" else run()
