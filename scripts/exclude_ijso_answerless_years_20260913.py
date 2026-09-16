"""Reversibly exclude five IJSO editions lacking any verified answer reference."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from dataset_catalog import update_track_index
from contest_manifest import load_contest_manifest
from scripts.build_data_packages import section
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures

CID = "ijso_practical"
YEARS = {2005, 2007, 2008, 2024, 2025}
IDS = {f"ijso_practical_{y}_team_practical_{y}" for y in YEARS}
TASKS = {CID + "/" + p for p in IDS}
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
CARDS = f"data/rubrics/task_scorecards/{CID}.json"
RULE = f"data/rules/{CID}/evaluation.json"
SCORES = "data/rubrics/ijso_practical_active_score_membership.json"
CACHE = "data/.cache/ijso_answerless_exclusion_20260913"
EXCLUDED = "data/excluded/ijso_answerless_years_20260913"
MANIFEST = EXCLUDED + "/manifest.json"
REPORT = "data/excluded/benchmark_audit_reports/ijso_answerless_exclusion_20260913.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def has_answer_material(row):
    gold = row.get("gold_label", {})
    return bool(row.get("solution_file") or gold.get("expected_answer") or
        any(p.get("expected") or p.get("reference") for p in gold.get("parts", [])) or
        row.get("evaluation", {}).get("judge_assets") or
        any(a.get("role") == "judge_only" for a in row.get("assets", [])))


def partition(rows):
    keys = [r["problem_id"] for r in rows]
    require(len(keys) == len(set(keys)) and IDS.issubset(keys), "Missing/duplicate selected IDs")
    active = [r for r in rows if r["problem_id"] not in IDS]
    excluded = [r for r in rows if r["problem_id"] in IDS]
    require({r["year"] for r in excluded} == YEARS, "Edition identity differs")
    require(not any(has_answer_material(r) for r in excluded), "Selected year now has answer material; review before exclusion")
    return active, excluded


def score_membership(rows, cards):
    lookup = {c["problem_id"]: c for c in cards}
    require(len(lookup) == len(cards) and set(lookup) == {r["problem_id"] for r in rows}, "Scorecard membership differs")
    return dict(schema_version="1.0", dataset=CID, visibility="judge_only", active_records=len(rows),
        active_years=sorted(r["year"] for r in rows), excluded_years=sorted(YEARS),
        aggregate_official_max_score=None,
        aggregation_policy="Do not pool proxy report rubric capacities as an official cross-year maximum. Remove excluded IDs from earned and possible score membership together; never retain an old numerator with a reduced denominator.",
        historical_scores_modified=False,
        records=[dict(problem_id=r["problem_id"], year=r["year"], evaluation_status=r["evaluation"]["status"],
            official_total_points=r.get("total_points"), rubric_path=r["evaluation"].get("rubric_path"),
            rubric_capacities=[dict(path=x["path"], total_points=x.get("total_points")) for x in lookup[r["problem_id"]]["rubrics"]],
            score_basis=lookup[r["problem_id"]].get("scoring_basis")) for r in rows])


def prepare():
    require(not (ROOT / MANIFEST).exists() and not (ROOT / CACHE / "plan.json").exists(), "Already prepared/applied")
    store = Store(ROOT)
    index = deepcopy(store.read("data/benchmarks/index.json"))
    rows = deepcopy(store.read(BENCHMARK))
    require(index["total_records"] == 1727 and len(rows) == 20, "Catalog starting point differs")
    active, excluded = partition(rows)
    audit = store.read(CACHE + "/source_review.json")
    require(set(audit["excluded_years"]) == YEARS, "Search review differs from selection")
    cards = deepcopy(store.read(CARDS))
    require({c["problem_id"] for c in cards["records"]} == {r["problem_id"] for r in rows}, "Original scorecards differ")
    removed_cards = [c for c in cards["records"] if c["problem_id"] in IDS]
    cards["records"] = [c for c in cards["records"] if c["problem_id"] not in IDS]
    cards["active_score_membership_path"] = SCORES
    rule = deepcopy(store.read(RULE))
    sync_rules(CID, rule, active)
    for key in ("record_evaluator_overrides", "record_rubric_overrides", "record_score_basis_overrides"):
        rule["scoring"][key] = {p: v for p, v in rule["scoring"].get(key, {}).items() if p not in IDS}
    rule["scoring"]["active_score_membership"] = dict(records=15, path=SCORES, exclusion_manifest=MANIFEST,
        official_aggregate_max_score=None, remaining_per_record_scoring_unchanged=True)
    writes = {BENCHMARK: active, CARDS: cards, RULE: rule, SCORES: score_membership(active, cards["records"])}
    selected_files, retained_files, targets, unrelated = {}, {}, [], {}
    for layout in ("base", "last_exam"):
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            path = f"data/{layout}/{name}"
            catalog = deepcopy(store.read(path))
            unrelated[layout + "/" + name] = stable([c for c in catalog[key] if c["task_id"] not in TASKS])
            if key == "tasks":
                require(len([c for c in catalog[key] if c["task_id"] in TASKS]) == 5, "Task selection differs")
                for card in catalog[key]:
                    if not card["task_id"].startswith(CID + "/"):
                        continue
                    folder = store.path(f"data/{layout}/" + card["source_repo_path"])
                    expected = store.path(f"data/{layout}/tasks/" + card["task_id"])
                    require(folder == expected and folder.is_dir(), "Unvalidated task directory")
                    bucket = selected_files if card["task_id"] in TASKS else retained_files
                    bucket.update({rel(p): sha(p) for p in folder.rglob("*") if p.is_file()})
                    if card["task_id"] in TASKS:
                        targets.append(rel(folder))
            catalog[key] = [c for c in catalog[key] if c["task_id"] not in TASKS]
            if key == "tasks":
                catalog["n_tasks"] = len(catalog[key])
                require(catalog["n_tasks"] == 1722, "Unexpected new task count")
            writes[path] = catalog
        path = f"data/{layout}/index.json"
        layout_index = deepcopy(store.read(path))
        layout_index["n_tasks"] = 1722
        if layout == "base":
            next(t for t in layout_index["competitions"] if t["id"] == CID)["n_tasks"] = 15
        writes[path] = layout_index
    source_hashes = {rel(p): sha(p) for p in (ROOT / "data/raw/ijso").rglob("*") if p.is_file()}
    protected = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    for tree in ("data/rules", "data/rubrics"):
        protected.extend(rel(p) for p in (ROOT / tree).rglob("*.json") if rel(p) not in writes)
    protected.extend(rel(p) for p in (ROOT / f"data/last_exam/competitions/{CID}").rglob("*") if p.is_file() and "eval" not in p.parts)
    protected.extend(["data/excluded/benchmark_audit_reports/ijso_2005_packet_repair_20260913.json", "data/excluded/benchmark_audit_reports/mystery_hunt_exclusion_20260913.json",
        "output/pdf/ijso_2005_experimental.pdf", "data/last_exam/competitions/index.json"])
    expected = set(writes) - {SCORES} | {"data/benchmarks/index.json", "data/README.md", "data/benchmarks/README.md",
        "data/base/README.md", "data/last_exam/README.md", f"data/last_exam/competitions/{CID}/eval/evaluation.json",
        f"data/last_exam/competitions/{CID}/eval/scoring.md"}
    expected.update(rel(p) for p in (ROOT / "data/viz").iterdir() if p.is_file())
    plan = dict(before_rows=rows, active_rows=active, excluded_rows=excluded, excluded_scorecards=removed_cards,
        before_index=index, writes=writes, source_review=audit, selected_files=selected_files, retained_files=retained_files,
        targets=targets, unrelated_derived_hashes=unrelated, source_hashes=source_hashes,
        protected_hashes={p: sha(ROOT / p) for p in protected}, expected_hashes={p: sha(ROOT / p) for p in expected})
    store.save(CACHE + "/plan.json", plan)
    print(json.dumps(dict(excluded_years=sorted(YEARS), before_records=20, active_records=15, global_records=1722,
        selected_generated_files=len(selected_files), retained_generated_files=len(retained_files), raw_files_preserved=len(source_hashes)), indent=2))


def verify(plan, report):
    for path, expected in {**plan["source_hashes"], **plan["protected_hashes"], **plan["retained_files"]}.items():
        require(sha(ROOT / path) == expected, "Protected file changed: " + path)
    for path, value in plan["writes"].items():
        require(read(ROOT / path) == value, "Metadata readback differs: " + path)
    require(read(ROOT / EXCLUDED / "records.json") == plan["excluded_rows"], "Archived records differ")
    require(read(ROOT / EXCLUDED / "scorecards.json") == plan["excluded_scorecards"], "Archived scores differ")
    for path, expected in plan["selected_files"].items():
        require(not (ROOT / path).exists() and sha(ROOT / report["backup"] / path) == expected, "Archived generated file differs")
    ids, statuses = [], Counter()
    index = read(ROOT / "data/benchmarks/index.json")
    for t in index["olympiads"]:
        rows = read(ROOT / t["benchmark_path"])
        require(len(rows) == t["problems_collected"], "Per-track count differs")
        ids.extend(t["id"] + "/" + r["problem_id"] for r in rows)
        statuses.update(r["evaluation"]["status"] for r in rows)
    require(len(ids) == len(set(ids)) == index["total_records"] == 1722, "Global count/membership differs")
    require(statuses["ready_with_limitations"] == 194 and statuses["not_ready"] == 699, "Readiness counts differ")
    active_ids = {r["problem_id"] for r in plan["active_rows"]}
    for layout in ("base", "last_exam"):
        cards = read(ROOT / f"data/{layout}/task_cards.json")
        require(len(cards["tasks"]) == cards["n_tasks"] == 1722 and {c["task_id"] for c in cards["tasks"]} == set(ids), "Task cards differ")
        require({p.name for p in (ROOT / f"data/{layout}/tasks/{CID}").iterdir() if p.is_dir()} == active_ids, "Task directories differ")
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            values = read(ROOT / f"data/{layout}/{name}")[key]
            require(not any(c["task_id"] in TASKS for c in values), "Excluded task still active")
            require(stable(values) == plan["unrelated_derived_hashes"][layout + "/" + name], "Retained derived entries changed")
    rule = read(ROOT / RULE)
    require(read(ROOT / f"data/last_exam/competitions/{CID}/eval/evaluation.json") == rule, "Shared score config differs")
    expected_text = "# Hidden scoring configuration\n\n" + section("Evaluation", rule)
    require((ROOT / f"data/last_exam/competitions/{CID}/eval/scoring.md").read_text(encoding="utf-8") == expected_text, "Shared score text differs")
    summary = read(ROOT / "data/viz/summary.json")
    require(summary["n_primary_records"] == 1722 and summary["records_by_track"][CID] == 15 and summary["evaluation_status_counts"] == dict(statuses), "Visualization summary differs")
    probe = ROOT / CACHE / "excluded_probe.json"
    require(read(probe)["problem_ids"] == sorted(IDS), "Loader rejection probe differs")
    try:
        load_contest_manifest(probe, benchmark_root=ROOT / "data/benchmarks")
    except ValueError as error:
        require("missing from benchmark" in str(error), "Unexpected loader rejection")
    else:
        raise ValueError("Excluded IDs still resolve")
    return dict(active_tracks=43, active_global_records=1722, active_ijso_records=15, excluded_years=sorted(YEARS),
        active_ijso_status_counts=dict(Counter(r["evaluation"]["status"] for r in plan["active_rows"])),
        archived_generated_files=len(plan["selected_files"]), retained_generated_files_unchanged=len(plan["retained_files"]),
        raw_files_preserved=len(plan["source_hashes"]), other_tracks_unchanged=42, remaining_scorecards_unchanged=True,
        global_status_counts=dict(statuses), excluded_ids_rejected_by_loader=True, historical_scores_modified=False)


def apply():
    store = Store(ROOT)
    require(not (ROOT / MANIFEST).exists() and not (ROOT / REPORT).exists(), "Already applied")
    plan = read(ROOT / CACHE / "plan.json")
    for path, expected in {**plan["expected_hashes"], **plan["protected_hashes"], **plan["source_hashes"],
                           **plan["selected_files"], **plan["retained_files"]}.items():
        require(sha(ROOT / path) == expected, "Concurrent change detected: " + path)
        if path in plan["expected_hashes"]:
            if path.endswith(".json"):
                store.read(path)
            else:
                store.raw[store.path(path)] = store.path(path).read_bytes()
    for name in plan["targets"]:
        target = store.path(name)
        require(target.name in IDS and target.parent.name == CID and target.parent.parent.name == "tasks", "Unsafe archive target")
        require(target.is_dir(), "Missing archive target")
    report = dict(operation="user_requested_reversible_ijso_answerless_year_exclusion", status="preparing",
        timestamp_utc=store.stamp, backup=rel(store.backup), excluded_years=sorted(YEARS), excluded_ids=sorted(IDS),
        exclusion_manifest=MANIFEST, score_membership=SCORES, old_global_records=1727, new_global_records=1722)
    store.finish(report)
    try:
        store.save(EXCLUDED + "/records.json", plan["excluded_rows"])
        store.save(EXCLUDED + "/scorecards.json", plan["excluded_scorecards"])
        store.save(EXCLUDED + "/source_review.json", plan["source_review"])
        store.save(MANIFEST, dict(visibility="maintainer_only", disposition="excluded_from_active_catalog_not_deleted",
            reason="User requested excluding IJSO years whose answers could not be found; selected years lack any verified edition-specific answer material.",
            absence_claim_scope="No verified answer recovered from checked sources; not a claim that answers never existed.",
            excluded_years=sorted(YEARS), excluded_ids=sorted(IDS), records_path=EXCLUDED + "/records.json",
            scorecards_path=EXCLUDED + "/scorecards.json", source_review=EXCLUDED + "/source_review.json",
            raw_files_retained_in_place=plan["source_hashes"], generated_packet_backup=report["backup"],
            generated_file_hashes=plan["selected_files"], retained_partial_answer_years=[2011],
            restore_policy="Restore only after explicit inclusion decision and answer verification; synchronize records, scores, task packages and counts together."))
        for path, value in plan["writes"].items():
            store.save(path, value)
        index = deepcopy(plan["before_index"])
        update_track_index(index, CID, plan["active_rows"])
        index["latest_selection_exclusion_report"] = REPORT
        index.setdefault("curated_record_exclusion_manifests", []).append(MANIFEST)
        store.save("data/benchmarks/index.json", index)
        rule = plan["writes"][RULE]
        store.save(f"data/last_exam/competitions/{CID}/eval/evaluation.json", rule)
        store.save_text(f"data/last_exam/competitions/{CID}/eval/scoring.md", "# Hidden scoring configuration\n\n" + section("Evaluation", rule))
        for name in plan["targets"]:
            expected = {p: v for p, v in plan["selected_files"].items() if p.startswith(name + "/")}
            require({rel(p): sha(p) for p in store.path(name).rglob("*") if p.is_file()} == expected, "Task changed before archive")
            store.archive(name)
        for layout in ("base", "last_exam"):
            path = f"data/{layout}/README.md"
            text = store.raw[store.path(path)].decode("utf-8-sig")
            require("43 tracks, 1727 records" in text, "README current count not found")
            store.save_text(path, text.replace("43 tracks, 1727 records", "43 tracks, 1722 records"))
        benchmarks = {t["id"]: read(ROOT / t["benchmark_path"]) for t in index["olympiads"]}
        summary_and_figures(store, index, benchmarks)
        for path in ("data/README.md", "data/benchmarks/README.md"):
            text = store.raw[store.path(path)].decode("utf-8-sig")
            text = text.replace("(43 tracks, 1,727 records; 702 not_ready)", "(43 tracks, 1,722 records; 699 not_ready)")
            text = text.replace("currently 1,727 records", "currently 1,722 records")
            text = text.replace("Current catalog: 43 tracks, 1,727 records, including 702 not_ready.", "At the Mystery Hunt exclusion snapshot: 43 tracks, 1,727 records, including 702 not_ready.")
            text += ("\n## IJSO answerless-year exclusion (2026-09-13)\n\n"
                "Current catalog: 43 tracks, 1,722 records, including 699 not_ready. IJSO Practical has 15 active years "
                "(11 ready_with_limitations and 4 not_ready). Years 2005, 2007, 2008, 2024 and 2025 were reversibly excluded "
                "because no verified edition-specific answer reference was recovered from checked sources. "
                "2011 remains not_ready with Biology/Chemistry answers and a missing Physics reference. "
                "All original files and historical scores are preserved; existing records, scoring capacities and other competitions are unchanged. "
                "Active scorecards and task entries omit excluded years; proxy rubric capacities are not pooled as official points.\n\n"
                f"See `{MANIFEST}`, `{SCORES}`, and `{REPORT}`. Earlier totals are historical snapshots.\n")
            store.save_text(path, text)
        store.save(CACHE + "/excluded_probe.json", dict(session_id="ijso_excluded_probe", competition_id=CID, problem_ids=sorted(IDS), split_parts=False))
        report["validation"] = verify(plan, report)
        report["status"] = "completed_reversible_exclusion_and_score_membership_sync"
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in ("status", "backup", "validation")}, indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "apply", "verify"))
    mode = parser.parse_args().mode
    if mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"prepare": prepare, "apply": apply}[mode]()
