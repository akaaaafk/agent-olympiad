"""Frozen, deduplicated continuation of the explicitly requested competitions."""
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT.parent / "qwen-extension-runtime-20260915"
OUT = ROOT / "results/tinker_requested_remaining_20260915"
sys.path.insert(0, str(SNAP / "src"))
from run_competition_batch import inspect_contest_run
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result
from contest_reporting import report_row
from rules.loader import load_rule_card
from artifact_contract import delivery_route

MODEL = "Qwen/Qwen3.6-35B-A3B"
VARIANTS = ("single_agent", "vallina_otc", "otc")
TRACKS = ("arml_local", "arml_national_team", "purple_comet", "wmtc", "hmmt_guts",
          "history_olympiad", "qanta", "science_bowl", "arml_national_power",
          "arml_power", "pumac_power", "iol_team", "ioaa_group", "ijso_practical", "wsc_writing")

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    temp.replace(path)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def latest_progress_time(paths):
    existing = [path.stat().st_mtime for path in paths if path.exists()]
    return max(existing) if existing else 0.0

def kill_process_tree(proc):
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        proc.kill()

def command(job):
    cmd = [sys.executable, "-u", str(SNAP / "src/run_competition_batch.py"),
            "--live", "--provider", "tinker", "--model", MODEL,
            "--benchmark-root", str(SNAP / "data/benchmarks"),
            "--contest-manifest", str(OUT / "manifests" / (job["id"] + ".json")),
            "--system-variant", job["variant"], "--action-calling", "emulated",
            "--max-output-tokens", "8192", "--max-total-tokens", str(job.get("max_total_tokens_override", 220000)),
            "--temperature", "0.2", "--judge-collab", "--judge-provider", "tinker",
            "--judge-model", MODEL, "--no-judge-cce", "--output", str(OUT / "runs" / job["id"])]
    if job.get("max_turns_override"):
        cmd.extend(["--max-turns", str(job["max_turns_override"])])
    return cmd

def prepare():
    if (OUT / "registry.json").exists():
        raise ValueError("Registry exists; do not overwrite an experiment")
    original = read(ROOT / "results/tinker_task_based_arml_icpc_20260914/registry.json")
    reserved = {(j["competition"], j["problem_id"], j["variant"]) for j in original["jobs"]}
    completed = {}
    for path in (ROOT / "results").glob("tinker*/runs/*/contest_session.json"):
        result = read(path)
        execution = (result.get("run_identity") or {}).get("settings", {}).get("execution", {})
        if execution.get("model") != MODEL or execution.get("provider") != "tinker":
            continue
        if (result.get("grade") or {}).get("graded"):
            completed[(result.get("competition_id"), result.get("session_id"),
                       result.get("system_variant"))] = (path, set((result.get("run_identity") or {}).get("settings", {}).get("task_ids", [])))
    jobs, excluded, coverage = [], [], []
    for track in TRACKS:
        rows = read(SNAP / "data/benchmarks" / track / "benchmark.json")
        groups = collections.defaultdict(list)
        route = delivery_route(load_rule_card(track))
        for row in rows:
            key = row["problem_id"]
            if track == "qanta":
                key = f"qanta_{row.get('year', 'unknown')}_{row.get('tournament', 'unknown')}"
            elif track == "science_bowl":
                key = row.get("parent_session_id") or row.get("packet") or key
            groups[str(key)].append(row)
        before = len(jobs)
        for session, members in groups.items():
            reason = None
            if any((r.get("evaluation") or {}).get("status") not in {"ready", "ready_with_limitations"} for r in members):
                reason = "Source audit marks at least one required record not ready"
            elif route in {"document", "slides", "artifact_bundle"}:
                reason = "Existing PDF/document pipeline does not support Tinker; needs a verified PDF-capable provider"
            elif any(not str(r.get("problem_description") or "").strip() for r in members):
                reason = "Missing contestant statement"
            for variant in VARIANTS:
                base = dict(competition=track, session_id=session, variant=variant,
                            problem_ids=[r["problem_id"] for r in members])
                if (track, session, variant) in reserved:
                    excluded.append(dict(**base, status="original_queue", reason="Covered by the original 93-job batch"))
                    continue
                if reason:
                    excluded.append(dict(**base, status="blocked", reason=reason))
                    continue
                job_id = track + "_" + hashlib.sha256(session.encode()).hexdigest()[:12] + "_" + variant
                job = dict(**base, id=job_id, route="native", input_mode="canonical_text_only",
                           limitations=["Tinker has no PDF/image input; extracted formulas and diagrams are not visually verified."]
                           if track in {"purple_comet", "wmtc", "hmmt_guts"} else [])
                if any("sample" in r["problem_id"].lower() or "practice" in r["problem_id"].lower() for r in members):
                    job["limitations"].append("Archive identifies this as a sample/practice release; included in the user's requested benchmark scope, not claimed as a live competition edition.")
                manifest = dict(session_id=session, competition_id=track,
                                problem_ids=job["problem_ids"], split_parts=False)
                path = OUT / "manifests" / (job_id + ".json")
                write(path, manifest)
                try:
                    loaded = load_contest_manifest(path, benchmark_root=SNAP / "data/benchmarks")
                    prior = completed.get((track, session, variant))
                    if prior and prior[1] == {t.task_id for t in loaded.tasks}:
                        excluded.append(dict(**base, status="already_completed", reason=str(prior[0])))
                        continue
                    grade = grade_contest_result(loaded, {})
                    rubric_tasks = {t.task_id for t in loaded.tasks
                                    if t.benchmark.get("evaluation", {}).get("evaluator_id") == "rubric_llm_v1"}
                    unsupported = [t for t, g in grade["tasks"].items() if not g["graded"] and t not in rubric_tasks]
                    if unsupported:
                        raise ValueError("No complete evaluator for tasks: " + ", ".join(unsupported))
                    state, identity = inspect_contest_run(command(job)[3:])
                    if state != "new":
                        raise ValueError("Fresh output required")
                    job.update(run_identity=identity, task_count=len(loaded.tasks),
                               rubric_scored=bool(rubric_tasks),
                               max_turns=identity["settings"]["config"]["max_turns"])
                    jobs.append(job)
                except Exception as exc:
                    excluded.append(dict(**base, status="blocked", reason=f"{type(exc).__name__}: {exc}"))
        coverage.append(dict(competition=track, records=len(rows), scopes=len(groups), queued=len(jobs)-before))
        print(track, "queued", len(jobs)-before, flush=True)
    write(OUT / "registry.json", dict(model=MODEL, provider="tinker", jobs=jobs, excluded=excluded,
                                      coverage=coverage, snapshot=str(SNAP),
                                      file_hashes=read(SNAP / "snapshot_hashes.json")))
    lines = ["# Requested Qwen continuation", "", "Original 93-job batch runs first. Two Tinker credentials; single_agent, vallina_otc, otc.",
             "", "New runs use a separate frozen snapshot. Historical scores are preserved.", "",
             "Math packet runs use canonical extracted text only; PDF diagrams/formula layout are not available to this Tinker adapter. Rubric scores are proxies, not official contest results.", "",
             "| Competition | Records | Scopes | Queued jobs |", "|---|---:|---:|---:|"]
    lines += [f"| {c['competition']} | {c['records']} | {c['scopes']} | {c['queued']} |" for c in coverage]
    lines += ["", "## Exclusions and dependencies", "", "Full per-scope reasons are in registry.json."]
    lines += [f"- {reason}: {count} jobs" for reason, count in collections.Counter(e["reason"] for e in excluded if e['status']!='already_completed').items()]
    (OUT / "COVERAGE.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("TOTAL", len(jobs), "EXCLUDED", len(excluded), flush=True)

def lane(registry, work_queue, slot, key, skip_variants, watchdog_idle_seconds):
    records = []
    env = dict(os.environ, TINKER_API_KEY=key)
    while True:
        job = work_queue.get()
        if job is None:
            work_queue.task_done()
            break
        if job["variant"] in skip_variants:
            state, identity = inspect_contest_run(command(job)[3:])
            if identity != job["run_identity"]:
                raise RuntimeError("Registered run identity changed")
            if state != "complete":
                record = dict(id=job["id"], competition=job["competition"], session_id=job["session_id"],
                              variant=job["variant"], status="skipped_by_variant")
                records.append(record)
                write(OUT / f"lane{slot+1}.json", records)
                print(f"lane={slot+1} {job['id']} skipped_by_variant", flush=True)
                work_queue.task_done()
                continue
        changed = [p for p,h in registry["file_hashes"].items() if not (SNAP/p).is_file() or digest(SNAP/p)!=h]
        if changed:
            raise RuntimeError("Frozen extension changed: " + ", ".join(changed[:5]))
        record = dict(id=job["id"], competition=job["competition"], session_id=job["session_id"],
                      variant=job["variant"], status="running", limitations=job["limitations"])
        records.append(record)
        write(OUT / f"lane{slot+1}.json", records)
        for attempt in range(2):
            state, identity = inspect_contest_run(command(job)[3:])
            if identity != job["run_identity"]:
                raise RuntimeError("Registered run identity changed")
            if state == "complete":
                break
            cmd = command(job)
            if state == "resume":
                cmd.append("--resume")
            log = OUT / "logs" / (job["id"] + ".log")
            log.parent.mkdir(parents=True, exist_ok=True)
            dest = OUT / "runs" / job["id"]
            progress_paths = [log, dest / "contest_checkpoint.json", dest / "contest_session.json"]
            last_progress = time.time()
            with log.open("a", encoding="utf-8") as handle:
                proc = subprocess.Popen(cmd, cwd=SNAP, env=env, stdout=handle, stderr=subprocess.STDOUT)
                while True:
                    returncode = proc.poll()
                    latest = latest_progress_time(progress_paths)
                    if latest > last_progress:
                        last_progress = latest
                    if returncode is not None:
                        break
                    if watchdog_idle_seconds and time.time() - last_progress > watchdog_idle_seconds:
                        handle.write(f"\n[watchdog] No progress for {watchdog_idle_seconds}s; killing pid {proc.pid} for resume.\n")
                        handle.flush()
                        kill_process_tree(proc)
                        returncode = proc.wait()
                        record["watchdog_restarts"] = record.get("watchdog_restarts", 0) + 1
                        break
                    time.sleep(15)
            record.update(exit_code=returncode, attempts=attempt+1)
            if not (dest / "contest_checkpoint.json").exists() and not (dest / "contest_session.json").exists():
                break
            if attempt == 0:
                time.sleep(10)
        result_path = OUT / "runs" / job["id"] / "contest_session.json"
        if result_path.exists():
            result = read(result_path)
            record["status"] = "evaluation_pending" if result.get("evaluation_pending") else "complete"
            record["report"] = report_row(result)
        else:
            record["status"] = "failed"
        write(OUT / f"lane{slot+1}.json", records)
        print(f"lane={slot+1} {job['id']} {record['status']}", flush=True)
        work_queue.task_done()

def run():
    from dotenv import dotenv_values
    for name, value in dotenv_values(ROOT / ".env").items():
        if value is not None:
            os.environ[name] = value
    keys = [os.environ.get("TINKER_API_KEY"), os.environ.get("TINKER_API_KEY2")]
    if not all(keys) or keys[0] == keys[1]:
        raise ValueError("Two distinct credentials required")
    lanes = int(os.environ.get("QWEN_EXT_LANES", "2"))
    if lanes < 1:
        raise ValueError("QWEN_EXT_LANES must be at least 1")
    registry = read(OUT / "registry.json")
    lock = OUT / "supervisor.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        skip_variants = {part.strip() for part in os.environ.get("QWEN_SKIP_VARIANTS", "").split(",") if part.strip()}
        only_competitions = {part.strip() for part in os.environ.get("QWEN_ONLY_COMPETITIONS", "").split(",") if part.strip()}
        skip_competitions = {part.strip() for part in os.environ.get("QWEN_SKIP_COMPETITIONS", "").split(",") if part.strip()}
        watchdog_idle_seconds = int(os.environ.get("QWEN_WATCHDOG_IDLE_SECONDS", "0"))
        work_queue = Queue()
        queued = 0
        for job in registry["jobs"]:
            if only_competitions and job["competition"] not in only_competitions:
                continue
            if job["competition"] in skip_competitions:
                continue
            result_path = OUT / "runs" / job["id"] / "contest_session.json"
            if result_path.exists():
                continue
            work_queue.put(job)
            queued += 1
        print(f"queued_unfinished={queued} lanes={lanes} skip_variants={sorted(skip_variants)} "
              f"only_competitions={sorted(only_competitions)} skip_competitions={sorted(skip_competitions)}",
              flush=True)
        for _ in range(lanes):
            work_queue.put(None)
        with ThreadPoolExecutor(max_workers=lanes) as pool:
            futures = [pool.submit(lane, registry, work_queue, i, keys[i % len(keys)], skip_variants, watchdog_idle_seconds) for i in range(lanes)]
            for future in futures:
                future.result()
        write(OUT / "finished.json", {"status": "queue_exhausted"})
    finally:
        lock.unlink(missing_ok=True)

if __name__ == "__main__":
    prepare() if sys.argv[1:] == ["prepare"] else run()
