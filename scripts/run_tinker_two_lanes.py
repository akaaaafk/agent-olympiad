"""Frozen native-text benchmark queue; two credentials, three isolated baselines."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from env_config import load_repo_dotenv
from run_competition_batch import inspect_contest_run
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result
from contest_reporting import report_row

VARIANTS = ("single_agent", "vallina_otc", "otc")
MODEL = "Qwen/Qwen3.6-35B-A3B"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=True, indent=2), encoding="utf-8")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(out, data, job):
    return [sys.executable, "-u", str(ROOT / "src/run_competition_batch.py"),
            "--live", "--provider", "tinker", "--model", MODEL,
            "--benchmark-root", str(data / "benchmarks"),
            "--contest-manifest", str(out / "manifests" / (job["id"] + ".json")),
            "--system-variant", job["variant"], "--max-output-tokens", str(job.get("max_output_tokens", 8192)),
            "--max-total-tokens", "220000", "--temperature", "0.2",
            "--action-calling", "emulated", "--judge-collab", "--judge-provider", "tinker",
            "--judge-model", MODEL, "--no-judge-cce", "--output", str(out / "runs" / job["id"])]


def register(out, data):
    if (out / "registry.json").exists():
        raise ValueError("Registry exists; use run to continue, never re-register an existing batch")
    jobs, blocked = [], []
    for path in sorted((data / "benchmarks").glob("*/benchmark.json")):
        competition = path.parent.name
        current_path = ROOT / "data/benchmarks" / competition / "benchmark.json"
        current_rows = {r["problem_id"]: r for r in read(current_path)} if current_path.exists() else {}
        for row in read(path):
            problem = row["problem_id"]
            evaluation = row.get("evaluation") or {}
            gold = row.get("gold_label") or {}
            parts = gold.get("parts") or []
            reason = None
            current = current_rows.get(problem, {})
            current_status = (current.get("evaluation") or {}).get("status")
            if competition in ("nyu_ctf_bench", "cybench", "ccdc"):
                reason = "requires_provisioned_external_environment"
            elif current_status not in ("ready", "ready_with_limitations"):
                reason = "current_source_audit_does_not_confirm_readiness"
            elif row.get("problem_description") != current.get("problem_description"):
                reason = "backup_prompt_differs_from_current_repaired_source"
            elif evaluation.get("status") in ("not_ready", "deferred"):
                reason = "dataset_not_ready_or_deferred"
            elif not parts and not str(gold.get("expected_answer") or "").strip():
                reason = "requires_non_native_gold_route_or_unverified_evaluator"
            elif not str(row.get("problem_description") or "").strip():
                reason = "missing_text_prompt"
            elif any(a.get("role") == "agent_visible" for a in row.get("assets", [])):
                reason = "agent_visible_assets_require_verified_text_or_multimodal_route"
            if reason:
                blocked.append(dict(competition=competition, problem_id=problem, reason=reason))
                continue
            manifest = dict(session_id=problem, competition_id=competition,
                            problem_ids=[problem], split_parts=bool(parts) and competition in ("arml_local", "arml_national_team"))
            if manifest["split_parts"]:
                supported = [str(p["id"]) for p in parts if str(p.get("expected") or "").strip()
                             and p.get("match_mode") != "reference_llm"]
                if not supported:
                    blocked.append(dict(competition=competition, problem_id=problem, reason="no_supported_gold_parts"))
                    continue
                manifest["question_ids"] = supported
                manifest["excluded_question_ids"] = [str(p["id"]) for p in parts if str(p["id"]) not in supported]
            for variant in VARIANTS:
                job_id = competition + "_" + hashlib.sha256(problem.encode()).hexdigest()[:12] + "_" + variant
                job = dict(id=job_id, competition=competition, problem_id=problem, variant=variant,
                           question_ids=manifest.get("question_ids"), excluded_question_ids=manifest.get("excluded_question_ids", []))
                if competition == "science_bowl":
                    job["packet"] = row.get("parent_session_id") or row.get("packet") or problem
                elif competition == "qanta":
                    job["packet"] = f"qanta_{row.get('year', 'unknown')}_{row.get('tournament', 'unknown')}"
                target = out / "manifests" / (job_id + ".json")
                write(target, manifest)
                try:
                    loaded = load_contest_manifest(target, benchmark_root=data / "benchmarks")
                    # Empty submissions test evaluator coverage, never answer selection.
                    grade = grade_contest_result(loaded, {})
                    if not grade.get("graded"):
                        raise ValueError("Selected scope lacks complete native gold coverage")
                    state, identity = inspect_contest_run(command(out, data, job)[3:])
                    if state != "new":
                        raise ValueError("Output already exists")
                    job["run_identity"] = identity
                    jobs.append(job)
                except Exception as exc:
                    blocked.append(dict(competition=competition, problem_id=problem, variant=variant,
                                        reason=f"{type(exc).__name__}: {exc}"))
    grouped = {}
    final_jobs = []
    for job in jobs:
        if "packet" not in job:
            final_jobs.append(job)
        else:
            grouped.setdefault((job["competition"], job["packet"], job["variant"]), []).append(job)
    for (competition, packet, variant), members in grouped.items():
        job_id = competition + "_" + hashlib.sha256(packet.encode()).hexdigest()[:12] + "_" + variant
        job = dict(id=job_id, competition=competition, problem_id=packet, variant=variant,
                   problem_ids=[m["problem_id"] for m in members])
        write(out / "manifests" / (job_id + ".json"), dict(session_id=packet, competition_id=competition,
                                                          problem_ids=job["problem_ids"], split_parts=False))
        _, job["run_identity"] = inspect_contest_run(command(out, data, job)[3:])
        final_jobs.append(job)
    jobs = sorted(final_jobs, key=lambda j: (j["competition"] != "arml_local", j["competition"], j["problem_id"], VARIANTS.index(j["variant"])))
    files = list((ROOT / "src").rglob("*.py")) + list((ROOT / "data/rules").rglob("*.json")) + list((ROOT / "configs").rglob("*.json")) + list((data / "benchmarks").glob("*/benchmark.json"))
    registry = dict(model=MODEL, data=str(data), jobs=jobs, blocked=blocked,
                    file_hashes={str(p): digest(p) for p in files})
    write(out / "registry.json", registry)
    print(json.dumps({"jobs": len(jobs), "blocked": len(blocked)}), flush=True)


def lane(out, registry, slot, key):
    states = []
    env = dict(os.environ, TINKER_API_KEY=key)
    for job in registry["jobs"][slot::2]:
        if any(not Path(p).is_file() or digest(Path(p)) != h for p, h in registry["file_hashes"].items()):
            raise RuntimeError("Frozen source/data changed; stop before mixing run identities")
        cmd = command(out, Path(registry["data"]), job)
        state, identity = inspect_contest_run(cmd[3:])
        if identity != job["run_identity"]:
            raise RuntimeError("Effective settings changed since registration")
        dest = out / "runs" / job["id"]
        record = dict(id=job["id"], status="running", slot=slot + 1)
        states.append(record)
        write(out / f"lane{slot+1}.json", states)
        if state != "complete":
            if state == "resume":
                cmd.append("--resume")
            logs = out / "logs"
            logs.mkdir(exist_ok=True)
            with (logs / (job["id"] + ".log")).open("a", encoding="utf-8") as log:
                proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            record["exit_code"] = proc.returncode
        result_path = dest / "contest_session.json"
        if result_path.exists():
            result = read(result_path)
            record["status"] = "evaluation_pending" if result.get("evaluation_pending") else "complete"
            record["report"] = report_row(result)
            record["evaluation_stages"] = result.get("evaluation_stages", {})
        else:
            record["status"] = "failed"
        write(out / f"lane{slot+1}.json", states)
        print(f"lane={slot+1} job={job['id']} status={record['status']}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("register", "run"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args()
    load_repo_dotenv()
    if args.stage == "register":
        register(args.output.resolve(), args.data.resolve())
        return
    keys = [os.environ.get("TINKER_API_KEY"), os.environ.get("TINKER_API_KEY2")]
    if not all(keys) or keys[0] == keys[1]:
        raise ValueError("Two distinct nonempty Tinker credentials required")
    lock = args.output / "supervisor.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        registry = read(args.output / "registry.json")
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(lane, args.output, registry, i, keys[i]) for i in range(2)]
            for future in futures:
                future.result()
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
