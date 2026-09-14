"""User-requested reversible exclusion of fourteen reviewed puzzle records.

Preserves raw material and historical results. Rebuilds active answer/score
membership and derived counts without reweighting surviving problems.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from dataset_catalog import scorecard, update_track_index
from contest_manifest import load_contest_manifest
from scripts.build_data_packages import section
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures

CID = "mystery_hunt"
IDS = {f"mystery_hunt_{n:05d}" for n in (2, 3, 4, 6, 7, 14, 28, 32, 33, 35, 36, 38, 44, 819)}
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
RUBRIC = "data/rubrics/mystery_hunt_official_answer_key_v1.json"
ANSWERS = "data/rubrics/mystery_hunt_short_answers.json"
SCORECARD = "data/rubrics/task_scorecards/mystery_hunt.json"
SCORES = "data/rubrics/mystery_hunt_active_score_summary.json"
RULE = "data/rules/mystery_hunt/evaluation.json"
CACHE = "data/.cache/mystery_hunt_exclusion_20260913"
EXCLUDED = "data/excluded/mystery_hunt_curated_exclusion_20260913"
MANIFEST = EXCLUDED + "/manifest.json"
REPORT = "data/benchmarks/mystery_hunt_exclusion_20260913.json"
REPAIR_REPORT = "data/benchmarks/mystery_hunt_source_repair_20260913.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def partition(rows, ids):
    keys = [r["problem_id"] for r in rows]
    if len(keys) != len(set(keys)) or not ids.issubset(keys):
        raise ValueError("Duplicate record IDs or requested IDs missing")
    return [r for r in rows if r["problem_id"] not in ids], [r for r in rows if r["problem_id"] in ids]


def score_summary(rows):
    maxima, years = {}, {}
    for row in rows:
        parts = row["gold_label"]["parts"]
        if len(parts) != 1 or not parts[0].get("expected") or float(parts[0].get("points", 1)) != 1:
            raise ValueError("Expected existing one-point, one-answer puzzle contract")
        pid = row["problem_id"]
        if pid in maxima:
            raise ValueError("Duplicate record in score denominator")
        maxima[pid] = 1.0
        years.setdefault(str(row["year"]), []).append(pid)
    return dict(schema_version="1.0", dataset=CID, visibility="judge_only",
        scope="active_isolated_puzzle_record_weights_not_official_full_hunt_scoring",
        benchmark_path=BENCHMARK, records=len(rows), points_per_record=1.0,
        max_score=sum(maxima.values()), max_score_by_problem=maxima,
        by_year={y: dict(records=len(pids), max_score=sum(maxima[p] for p in pids), problem_ids=pids)
                 for y, pids in sorted(years.items())},
        normalization="For any explicitly scored selection, sum earned points AND possible points over the same retained record IDs. Divide only when the retained possible sum is positive; an empty selection has no score, not zero performance.",
        caveats=["All current Mystery Hunt records remain not_ready; denominator bookkeeping does not certify an evaluator.",
                 "The catalog mixes isolated puzzles, interactions and related answer variants; its weight sum is not an official hunt score or a count of independent tasks.",
                 "Do not rescale the old aggregate numerator onto the reduced denominator. Historical runs require per-record attribution and a separate derived result.",
                 "Per-record official total_points and existing gold weights are not changed."])


def historical_manifest_impact():
    # Inspect small ID-bearing manifests only; no completed run or result table
    # is modified, and no model-generated score is invented.
    proc = subprocess.run(["rg", "--files", "results", "output", "initial_experiments",
        "-g", "*mystery*.json", "-g", "registry.json", "-g", "!**/otc_code_audit_20260913_155144/**"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode not in (0, 1):
        raise ValueError("Historical manifest inventory failed")
    findings = []
    for name in proc.stdout.splitlines():
        path = ROOT / name
        if path.stat().st_size > 8_000_000:
            continue
        obj = read(path)
        if not isinstance(obj, dict):
            continue
        candidates = obj.get("jobs", []) if path.name == "registry.json" else [obj]
        affected = []
        for item in candidates:
            if not isinstance(item, dict) or (item.get("competition_id") or item.get("competition")) != CID:
                continue
            pids = item.get("problem_ids", [])
            overlap = set(pids) & IDS
            if overlap:
                affected.append(dict(session_id=item.get("session_id") or item.get("session") or item.get("id"),
                    excluded_ids=sorted(overlap), retained_ids=[p for p in pids if p not in IDS],
                    disposition="empty_after_exclusion_do_not_assign_zero_score" if set(pids) <= IDS else "fresh_registration_and_per_record_rescoring_required"))
        if affected:
            findings.append(dict(path=rel(path), sha256=sha(path), affected_selections=affected))
    return dict(scope="Existing small Mystery-Hunt-named JSON manifests and registry.json files in results, output and initial_experiments; not a complete score-table audit.",
                historical_files_modified=False, affected_files=findings,
                guidance="Keep original run identities and grades. Re-register future selections in a fresh output root; create separately labeled per-record score projections only for an explicitly selected historical results table.")


def prepare():
    if (ROOT / MANIFEST).exists() or (ROOT / CACHE / "plan.json").exists():
        raise ValueError("This exclusion is already prepared/applied")
    store = Store(ROOT)
    index = deepcopy(store.read("data/benchmarks/index.json"))
    benchmarks = {t["id"]: store.read(t["benchmark_path"]) for t in index["olympiads"]}
    before = benchmarks[CID]
    if set(store.read(REPAIR_REPORT)["changed_ids"]) != IDS or len(before) != 261 or index["total_records"] != 1741:
        raise ValueError("Selection no longer matches the user-approved fourteen-record batch")
    remaining, excluded = partition(before, IDS)
    if len(excluded) != 14 or any(r["evaluation"]["status"] != "not_ready" for r in excluded):
        raise ValueError("Unexpected selected record readiness")
    rubric, answers, cards, rule = [deepcopy(store.read(p)) for p in (RUBRIC, ANSWERS, SCORECARD, RULE)]
    original_ids = {r["problem_id"] for r in before}
    if set(rubric["answers"]) != original_ids or {p for p in answers if not p.startswith("_")} != original_ids:
        raise ValueError("Answer maps do not match the original active set")
    if {c["problem_id"] for c in cards["records"]} != original_ids:
        raise ValueError("Scorecards do not match the original active set")
    before_scores, after_scores = score_summary(before), score_summary(remaining)
    if (before_scores["max_score"], after_scores["max_score"]) != (261.0, 247.0):
        raise ValueError("Unexpected score change")
    archive_scores = dict(official_answer_entries={p: rubric["answers"][p] for p in sorted(IDS)},
        short_answer_entries={p: answers[p] for p in sorted(IDS)},
        scorecards=[c for c in cards["records"] if c["problem_id"] in IDS],
        excluded_max_score=14.0, before_catalog_score_summary=before_scores)
    rubric["answers"] = {p: v for p, v in rubric["answers"].items() if p not in IDS}
    rubric["coverage"].update(benchmark_records=247, mapped_records=247)
    rubric["coverage"]["limitations"] = [s.replace("Only the 261 task-bearing promoted records", "Only the 247 active task-bearing records")
                                            for s in rubric["coverage"]["limitations"]]
    rubric["coverage"]["excluded_selection_manifest"] = MANIFEST
    rubric["coverage"]["benchmark_score_summary"] = SCORES
    answers = {p: v for p, v in answers.items() if p not in IDS}
    sync_rules(CID, rule, remaining)
    rule["scoring"]["benchmark_score_basis"] = dict(scope=after_scores["scope"], active_records=247,
        active_record_weight_sum=247.0, points_per_record=1.0, score_summary_path=SCORES,
        official_hunt_total=False, scoring_readiness_unchanged=True)
    source_trees = ("data/raw/external/MIT_Mystery_Hunt", "data/raw/mystery_hunt")
    source_hashes = {rel(p): sha(p) for tree in source_trees for p in (ROOT / tree).rglob("*") if p.is_file()}
    selected_source_paths = {p for r in excluded for p in [r.get("source_file"), r.get("solution_file")]
                             if p} | {a["path"] for r in excluded for a in r.get("assets", [])}
    for cid, records in benchmarks.items():
        for row in records:
            if cid == CID and row["problem_id"] in IDS:
                continue
            used = {row.get("source_file"), row.get("solution_file")} | {a["path"] for a in row.get("assets", [])}
            if selected_source_paths & used:
                raise ValueError("Selected sources have shared active-record references; review before proceeding")
    derived, selected_hashes, retained_hashes = {}, {}, {}
    for layout in ("base", "last_exam"):
        taskcards = deepcopy(store.read(f"data/{layout}/task_cards.json"))
        manifest = deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
        old = taskcards["tasks"]
        selected = [c for c in old if c["task_id"] in {CID + "/" + p for p in IDS}]
        if len(selected) != 14:
            raise ValueError("Unexpected derived task selection")
        taskcards["tasks"] = [c for c in old if c not in selected]
        taskcards["n_tasks"] = len(taskcards["tasks"])
        manifest["files"] = [c for c in manifest["files"] if c["task_id"] not in {CID + "/" + p for p in IDS}]
        layout_index = deepcopy(store.read(f"data/{layout}/index.json"))
        layout_index["n_tasks"] = 1727
        if layout == "base":
            next(t for t in layout_index["competitions"] if t["id"] == CID)["n_tasks"] = 247
        derived.update({f"data/{layout}/task_cards.json": taskcards, f"data/{layout}/input_asset_manifest.json": manifest,
                        f"data/{layout}/index.json": layout_index})
        for card in old:
            if not card["task_id"].startswith(CID + "/"):
                continue
            target = (ROOT / f"data/{layout}" / card["source_repo_path"]).resolve()
            expected = (ROOT / f"data/{layout}/tasks/{CID}" / card["problem_id"]).resolve() if layout == "last_exam" else (ROOT / f"data/{layout}/tasks" / card["task_id"]).resolve()
            if target != expected or not target.is_dir():
                raise ValueError("Unexpected task tree location")
            bucket = selected_hashes if card["task_id"] in {CID + "/" + p for p in IDS} else retained_hashes
            bucket.update({rel(p): sha(p) for p in target.rglob("*") if p.is_file()})
    writes = {BENCHMARK: remaining, RUBRIC: rubric, ANSWERS: answers, SCORES: after_scores, RULE: rule, **derived}
    changing = set(writes) | {SCORECARD, "data/benchmarks/index.json"}
    protected = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    for tree in ("data/rules", "data/rubrics"):
        protected.extend(rel(p) for p in (ROOT / tree).rglob("*.json") if rel(p) not in changing)
    protected.extend((REPAIR_REPORT, "data/benchmarks/source_verified_record_aliases_20260912.json",
                      "data/last_exam/competitions/index.json"))
    protected.extend(rel(p) for p in (ROOT / f"data/last_exam/competitions/{CID}").rglob("*")
                     if p.is_file() and "eval" not in p.parts)
    expected_paths = set(writes) - {SCORES} | {SCORECARD, "data/benchmarks/index.json", "data/README.md",
        "data/benchmarks/README.md", "data/base/README.md", "data/last_exam/README.md",
        f"data/last_exam/competitions/{CID}/eval/evaluation.json", f"data/last_exam/competitions/{CID}/eval/scoring.md"}
    expected_paths.update(rel(p) for p in (ROOT / "data/viz").iterdir() if p.is_file())
    plan = dict(before_rows=before, remaining_rows=remaining, excluded_rows=excluded, archive_scores=archive_scores,
        writes=writes, before_index=index, protected_hashes={p: sha(ROOT / p) for p in protected},
        expected_hashes={p: sha(ROOT / p) for p in expected_paths}, source_hashes=source_hashes,
        selected_packet_hashes=selected_hashes, retained_packet_hashes=retained_hashes,
        scorecard_before=cards, historical_manifest_impact=historical_manifest_impact())
    path = ROOT / CACHE / "plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(excluding=len(excluded), remaining=247, score_before=261, score_after=247,
        preserved_source_files=len(source_hashes), archived_packet_files=len(selected_hashes),
        affected_historical_manifest_files=len(plan["historical_manifest_impact"]["affected_files"])), indent=2))


def manifest_score_checks(rows):
    scores = score_summary(rows)
    folder = ROOT / CACHE / "validation_manifests"
    folder.mkdir(parents=True, exist_ok=True)
    results = {}
    for year, info in scores["by_year"].items():
        path = folder / (year + ".json")
        path.write_text(json.dumps(dict(session_id=CID + "_" + year, competition_id=CID,
            problem_ids=info["problem_ids"], split_parts=False)), encoding="utf-8")
        loaded = load_contest_manifest(path, benchmark_root=ROOT / "data/benchmarks")
        possible = sum(t.max_score for t in loaded.tasks)
        if possible != info["max_score"] or any(t.parent_problem_id in IDS for t in loaded.tasks):
            raise ValueError("Runtime manifest denominator differs from retained gold weights")
        results[year] = dict(records=len(loaded.tasks), max_score=possible)
    stale = folder / "excluded_selection_probe.json"
    stale.write_text(json.dumps(dict(session_id="excluded_selection_probe", competition_id=CID,
        problem_ids=sorted(IDS))), encoding="utf-8")
    try:
        load_contest_manifest(stale, benchmark_root=ROOT / "data/benchmarks")
    except ValueError as error:
        if "missing from benchmark" not in str(error):
            raise
    else:
        raise ValueError("Excluded record IDs still resolve through current loader")
    return results


def verify(plan, report):
    rows = read(ROOT / BENCHMARK)
    if rows != plan["remaining_rows"] or len(rows) != 247:
        raise ValueError("Retained canonical rows changed")
    active = {r["problem_id"] for r in rows}
    if active & IDS or active | IDS != {r["problem_id"] for r in plan["before_rows"]}:
        raise ValueError("Wrong canonical set subtraction")
    for p, expected in {**plan["protected_hashes"], **plan["source_hashes"], **plan["retained_packet_hashes"]}.items():
        if sha(ROOT / p) != expected:
            raise ValueError(f"Protected file changed: {p}")
    if read(ROOT / EXCLUDED / "records.json") != plan["excluded_rows"] or read(ROOT / EXCLUDED / "scoring_snapshot.json") != plan["archive_scores"]:
        raise ValueError("Excluded records or original score entries not preserved verbatim")
    manifest = read(ROOT / MANIFEST)
    if set(manifest["excluded_ids"]) != IDS or manifest["disposition"] != "excluded_from_active_catalog_not_deleted":
        raise ValueError("Exclusion manifest membership/disposition drift")
    for p, expected in plan["selected_packet_hashes"].items():
        if (ROOT / p).exists() or sha(ROOT / report["backup"] / p) != expected:
            raise ValueError("Excluded generated file missing from reversible archive")
    for p, expected in plan["writes"].items():
        if read(ROOT / p) != expected:
            raise ValueError("Written metadata differs: " + p)
    summaries = read(ROOT / SCORES)
    if summaries != score_summary(rows) or summaries["max_score"] != 247:
        raise ValueError("Active score denominator drift")
    cards = read(ROOT / SCORECARD)
    if cards["records"] != [scorecard(r, ROOT) for r in rows]:
        raise ValueError("Scorecard membership/hash/weights drift")
    if sum(c["gold_max_score"] for c in cards["records"]) != summaries["max_score"]:
        raise ValueError("Scorecard maxima do not match active denominator")
    # Only rubric hashes may change in retained per-record scorecards.
    old_cards = {c["problem_id"]: c for c in plan["scorecard_before"]["records"]}
    for current in cards["records"]:
        old, new = deepcopy(old_cards[current["problem_id"]]), deepcopy(current)
        for c in (old, new):
            for r in c["rubrics"]:
                r.pop("sha256", None)
        if old != new:
            raise ValueError("Retained per-record scoring semantics changed")
    ids, statuses = [], Counter()
    index = read(ROOT / "data/benchmarks/index.json")
    for t in index["olympiads"]:
        records = read(ROOT / t["benchmark_path"])
        ids.extend(t["id"] + "/" + r["problem_id"] for r in records)
        statuses.update(r["evaluation"]["status"] for r in records)
        if t["problems_collected"] != len(records):
            raise ValueError("Per-track index count drift")
    if len(ids) != len(set(ids)) or len(ids) != 1727 or index["total_records"] != 1727:
        raise ValueError("Global canonical membership drift")
    for layout in ("base", "last_exam"):
        taskcards = read(ROOT / f"data/{layout}/task_cards.json")
        if ({c["task_id"] for c in taskcards["tasks"]} != set(ids)
                or len(taskcards["tasks"]) != 1727 or taskcards["n_tasks"] != 1727):
            raise ValueError("Global task catalog membership drift")
        if read(ROOT / f"data/{layout}/index.json")["n_tasks"] != 1727:
            raise ValueError("Layout index count drift")
        paths = {p.name for p in (ROOT / f"data/{layout}/tasks/{CID}").iterdir() if p.is_dir()}
        if paths != active:
            raise ValueError("Active task tree membership drift")
    if read(ROOT / f"data/last_exam/competitions/{CID}/eval/evaluation.json") != read(ROOT / RULE):
        raise ValueError("Shared hidden score rules drift")
    rule_text = "# Hidden scoring configuration\n\n" + section("Evaluation", read(ROOT / RULE))
    if (ROOT / f"data/last_exam/competitions/{CID}/eval/scoring.md").read_text(encoding="utf-8") != rule_text:
        raise ValueError("Shared score rule text drift")
    summary = read(ROOT / "data/viz/summary.json")
    if summary["n_primary_records"] != 1727 or summary["records_by_track"][CID] != 247 or summary["evaluation_status_counts"] != dict(statuses):
        raise ValueError("Visualization summary count drift")
    if statuses["not_ready"] != 702:
        raise ValueError("Unexpected readiness changes")
    years = manifest_score_checks(rows)
    return dict(active_global_records=1727, active_tracks=43, active_mystery_hunt_records=247,
        excluded_records=14, active_weight_sum=247.0, excluded_weight_sum=14.0,
        runtime_manifest_maxima=years, raw_source_files_preserved=len(plan["source_hashes"]),
        archived_generated_files=len(plan["selected_packet_hashes"]),
        retained_generated_files_unchanged=len(plan["retained_packet_hashes"]),
        other_canonical_tracks_unchanged=42, readiness_status_counts=dict(statuses),
        readiness_promotions=0, historical_scores_modified=False, live_evaluation_performed=False)


def apply():
    store = Store(ROOT)
    if (ROOT / MANIFEST).exists() or (ROOT / REPORT).exists():
        raise ValueError("Exclusion already applied")
    plan = read(ROOT / CACHE / "plan.json")
    for p, expected in {**plan["expected_hashes"], **plan["protected_hashes"], **plan["source_hashes"],
                        **plan["selected_packet_hashes"], **plan["retained_packet_hashes"]}.items():
        if sha(ROOT / p) != expected:
            raise ValueError("Concurrent change before exclusion: " + p)
    for layout in ("base", "last_exam"):
        boundary = (ROOT / f"data/{layout}/tasks/{CID}").resolve()
        for pid in IDS:
            target = (boundary / pid).resolve()
            if not target.is_relative_to(boundary) or target.parent != boundary or not target.is_dir():
                raise ValueError("Unvalidated archive target")
    report = dict(operation="user_requested_reversible_mystery_hunt_selection_exclusion", status="preparing",
        timestamp_utc=store.stamp, backup=rel(store.backup), exclusion_manifest=MANIFEST,
        excluded_ids=sorted(IDS), old_records=1741, new_records=1727,
        before_mystery_hunt_weight_sum=261.0, after_mystery_hunt_weight_sum=247.0,
        score_summary=SCORES, original_source_repair_report=REPAIR_REPORT,
        score_change_policy="Remove excluded IDs from BOTH earned and possible score membership; keep surviving one-point weights. No old result numerator is reused with a smaller denominator.")
    store.finish(report)
    try:
        store.save(EXCLUDED + "/records.json", plan["excluded_rows"])
        store.save(EXCLUDED + "/scoring_snapshot.json", plan["archive_scores"])
        store.save(EXCLUDED + "/historical_manifest_impact.json", plan["historical_manifest_impact"])
        store.save(MANIFEST, dict(schema_version="1.0", visibility="maintainer_only", disposition="excluded_from_active_catalog_not_deleted",
            reason="User requested moving the fourteen-record source-repair batch out of the main dataset after reviewing the impact.",
            invalid_source_claim=False, excluded_ids=sorted(IDS), excluded_records=EXCLUDED + "/records.json",
            scoring_snapshot=EXCLUDED + "/scoring_snapshot.json", score_summary=SCORES,
            original_source_repair_report=REPAIR_REPORT, raw_files_retained_in_place=plan["source_hashes"],
            generated_packet_backup=report["backup"], original_generated_file_hashes=plan["selected_packet_hashes"],
            restore_policy="Records, gold entries, original media and repaired packets are retained. Any future reinstatement must be explicit and regenerate active score maps, packages and counts.",
            timestamp_utc=store.stamp))
        for p, value in plan["writes"].items():
            store.save(p, value)
        new_cards = deepcopy(plan["scorecard_before"])
        new_cards["records"] = [scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in plan["remaining_rows"]]
        new_cards["active_score_summary_path"] = SCORES
        store.save(SCORECARD, new_cards)
        index = deepcopy(plan["before_index"])
        update_track_index(index, CID, plan["remaining_rows"])
        index["latest_selection_exclusion_report"] = REPORT
        manifests = index.setdefault("curated_record_exclusion_manifests", [])
        if MANIFEST not in manifests:
            manifests.append(MANIFEST)
        store.save("data/benchmarks/index.json", index)
        rule = plan["writes"][RULE]
        store.save(f"data/last_exam/competitions/{CID}/eval/evaluation.json", rule)
        store.save_text(f"data/last_exam/competitions/{CID}/eval/scoring.md", "# Hidden scoring configuration\n\n" + section("Evaluation", rule))
        for layout in ("base", "last_exam"):
            for pid in sorted(IDS):
                store.archive(f"data/{layout}/tasks/{CID}/{pid}")
            text = (ROOT / f"data/{layout}/README.md").read_text(encoding="utf-8")
            store.save_text(f"data/{layout}/README.md", text.replace("43 tracks, 1741 records", "43 tracks, 1727 records"))
        report["status"] = "updating_counts_and_visualizations"
        store.finish(report)
        benchmarks = {t["id"]: read(ROOT / t["benchmark_path"]) for t in index["olympiads"]}
        summary_and_figures(store, index, benchmarks)
        text = (ROOT / "data/README.md").read_text(encoding="utf-8")
        text = text.replace("Canonical catalog: `benchmarks/index.json` (43 tracks, 1,741 records).", "Canonical catalog: `benchmarks/index.json` (43 tracks, 1,727 records; 702 not_ready).")
        text = text.replace("The global catalog remains 43 tracks and 1,741 records", "At this repair snapshot, the global catalog contained 43 tracks and 1,741 records")
        text += ("\n## User-selected Mystery Hunt exclusion (2026-09-13)\n\n"
            "The fourteen records repaired in the preceding batch were subsequently moved out of the active catalog at the user's request. "
            "Their original rows, answers, repaired packets and source material are retained under an exclusion manifest; they are not declared invalid. "
            "Mystery Hunt now has 247 records with an unchanged one-point weight each (247 total benchmark weight, not an official whole-hunt score). "
            "The 1999 weight sum is 2 instead of 15; 2006 is 13 instead of 14. All other years and remaining per-record weights are unchanged. "
            "The answer maps, scorecards, shared scoring metadata, both task catalogs and visualizations are synchronized. "
            "Historical run results remain immutable; any selected old result table needs a separate per-record projection, not numerator-preserving rescaling.\n\n"
            f"See `{MANIFEST}`, `{SCORES}`, and `{REPORT}`. Earlier sections describe historical snapshots.\n")
        store.save_text("data/README.md", text)
        text = (ROOT / "data/benchmarks/README.md").read_text(encoding="utf-8")
        text = text.replace("user-requested restoration (1,761 records). Catalog presence does not mean", "subsequent curated exclusions (currently 1,727 records). Catalog presence does not mean")
        text = text.replace("Current catalog: 43 tracks, 1,741 records, including 723 not_ready records.", "At this cleanup snapshot: 43 tracks, 1,748 records, including 723 not_ready records; later source repairs and user-selected exclusions changed these totals.")
        text += ("\n## Current user-selected Mystery Hunt subset (2026-09-13)\n\n"
            f"Current catalog: 43 tracks, 1,727 records, including 702 not_ready. Mystery Hunt has 247 active rows. "
            f"Fourteen source-reviewed rows were reversibly excluded by user choice, not declared invalid; their manifest is `{MANIFEST}`. "
            f"The active one-point-per-record benchmark denominator is 247; full per-year membership and score bounds are in `{SCORES}`. "
            "Official full-hunt scoring, evaluator readiness, other tracks and surviving problem weights are unchanged.\n")
        store.save_text("data/benchmarks/README.md", text)
        report["validation"] = verify(plan, report)
        report["status"] = "completed_reversible_exclusion_and_score_membership_sync"
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps(dict(status=report["status"], backup=report["backup"], validation=report["validation"]), indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "apply", "verify"))
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"prepare": prepare, "apply": apply}[args.mode]()
