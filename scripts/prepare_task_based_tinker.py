"""Register repaired ARML scopes and full ICPC years for the two-key runner."""
import argparse
from collections import defaultdict
from pathlib import Path

from run_tinker_two_lanes import ROOT, VARIANTS, MODEL, read, write, digest, command
from run_competition_batch import inspect_contest_run
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result


def prepare(out):
    if (out / "registry.json").exists():
        raise ValueError("Choose a fresh registry output")
    data = ROOT / "data"
    scopes, blocked = [], []
    for competition in ("arml_local", "arml_national_team"):
        for row in read(data / "benchmarks" / competition / "benchmark.json"):
            problem = row["problem_id"]
            existing = data / "contest_manifests" / (problem + ".json")
            if existing.exists():
                manifest = read(existing)
            else:
                parts = (row.get("gold_label") or {}).get("parts") or []
                supported = [str(p["id"]) for p in parts if str(p.get("expected") or "").strip()
                             and p.get("match_mode") != "reference_llm"]
                if not supported:
                    blocked.append(dict(problem_id=problem, reason="no_supported_structured_answer_parts"))
                    continue
                manifest = dict(session_id=problem, competition_id=competition, problem_ids=[problem],
                                split_parts=True, question_ids=supported,
                                excluded_question_ids=[str(p["id"]) for p in parts if str(p["id"]) not in supported])
            scopes.append(manifest)
    years = defaultdict(list)
    for row in read(data / "benchmarks/icpc/benchmark.json"):
        years[row["year"]].append(row)
    for year, rows in sorted(years.items()):
        if any((r.get("evaluation") or {}).get("status") != "remote_judge_ready"
               or not (r.get("evaluation") or {}).get("vjudge_prob_num") for r in rows):
            blocked.append(dict(problem_id=f"icpc_wf_{year}", reason="full_year_remote_mapping_incomplete"))
            continue
        scopes.append(dict(session_id=f"icpc_wf_{year}", competition_id="icpc",
                           problem_ids=[r["problem_id"] for r in rows], split_parts=False))
    jobs = []
    for manifest in scopes:
        for variant in VARIANTS:
            job_id = manifest["session_id"] + "_" + variant
            job = dict(id=job_id, competition=manifest["competition_id"], problem_id=manifest["session_id"],
                       variant=variant, problem_ids=manifest["problem_ids"],
                       max_output_tokens=4096 if manifest["competition_id"] == "icpc" else 8192)
            path = out / "manifests" / (job_id + ".json")
            write(path, manifest)
            try:
                loaded = load_contest_manifest(path, benchmark_root=data / "benchmarks")
                if manifest["competition_id"] != "icpc" and not grade_contest_result(loaded, {}).get("graded"):
                    raise ValueError("Selected ARML scope lacks complete gold coverage")
                state, identity = inspect_contest_run(command(out, data, job)[3:])
                if state != "new":
                    raise ValueError("Output is not new")
                job.update(run_identity=identity, task_count=len(loaded.tasks),
                           max_turns=identity["settings"]["config"]["max_turns"])
                jobs.append(job)
            except Exception as exc:
                blocked.append(dict(id=job_id, reason=f"{type(exc).__name__}: {exc}"))
    # Start one ARML and one ICPC job to verify both runtime paths promptly.
    jobs.sort(key=lambda j: (VARIANTS.index(j["variant"]), j["competition"], j["problem_id"]))
    arml = [j for j in jobs if j["competition"] != "icpc"]
    icpc = [j for j in jobs if j["competition"] == "icpc"]
    jobs = []
    while arml or icpc:
        if arml:
            jobs.append(arml.pop(0))
        if icpc:
            jobs.append(icpc.pop(0))
    files = list((ROOT / "src").rglob("*.py")) + list((data / "rules").rglob("*.json")) + list((ROOT / "configs").rglob("*.json")) + list((data / "benchmarks").glob("*/benchmark.json"))
    registry = dict(model=MODEL, data=str(data), jobs=jobs, blocked=blocked,
                    judge_preflight="Kattis hello AC 20440507; Docker isolated Python printed 42",
                    file_hashes={str(p): digest(p) for p in files})
    write(out / "registry.json", registry)
    print({"jobs": len(jobs), "blocked": blocked,
           "ARML": sum(j["competition"] != "icpc" for j in jobs),
           "ICPC": sum(j["competition"] == "icpc" for j in jobs)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args().output.resolve())
