"""Read-only full active-catalog audit; write evidence reports, never source data."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"src"))
from scripts.repair_data_catalog import Store
from dataset_catalog import scorecard

CACHE = "data/.cache/all_data_audit_20260913"


def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))


def audit(label, layouts=("base", "last_exam")):
    digests, checked_pdfs, issues, review, records, tracks = {}, set(), [], [], {}, []
    def digest(path):
        p = (ROOT/path).resolve()
        if p not in digests:
            with p.open("rb") as stream:
                digests[p] = hashlib.file_digest(stream, "sha256").hexdigest()
        return digests[p]
    def add(kind, task, **detail):
        issues.append(dict(kind=kind, task=task, **detail))
    def check_path(path, task, field):
        if not isinstance(path, str) or not path:
            return False
        p = (ROOT/path).resolve()
        if not p.is_relative_to(ROOT):
            add("path_outside_repo", task, field=field, path=path)
            return False
        # Several packet/CTF tracks intentionally use a source directory and
        # declare concrete input/judge files separately in assets.
        if field == "source_file" and p.is_dir():
            return True
        if not p.is_file():
            add("missing_file", task, field=field, path=path)
            return False
        if p.suffix.lower() == ".pdf" and p not in checked_pdfs:
            checked_pdfs.add(p)
            with p.open("rb") as stream:
                header = stream.read(1024)
            if b"%PDF-" not in header:
                add("invalid_pdf_header", task, path=path, header=repr(header[:60]))
        return True
    index = read("data/benchmarks/index.json")
    statuses, splits, licenses = Counter(), Counter(), Counter()
    for track in index["olympiads"]:
        cid = track["id"]
        rows = read(track["benchmark_path"])
        cards_path = f"data/rubrics/task_scorecards/{cid}.json"
        cards = read(cards_path)["records"] if (ROOT/cards_path).is_file() else []
        cardmap = {c["problem_id"]:c for c in cards}
        if len(rows) != track["problems_collected"]:
            add("track_count_mismatch", cid, expected=len(rows), actual=track["problems_collected"])
        if Counter(c["problem_id"] for c in cards) != Counter(r["problem_id"] for r in rows):
            add("scorecard_membership_mismatch", cid)
        local_statuses = Counter(r.get("evaluation", {}).get("status") for r in rows)
        if dict(local_statuses) != track.get("evaluation_status_counts"):
            add("track_readiness_count_mismatch", cid, expected=dict(local_statuses), actual=track.get("evaluation_status_counts"))
        tracks.append(dict(id=cid, records=len(rows), statuses=dict(local_statuses),
            unknown_official_points=sum(r.get("total_points") is None for r in rows),
            limitations=[dict(problem_id=r["problem_id"], status=r.get("evaluation", {}).get("status"),
                limitations=r.get("evaluation", {}).get("limitations")) for r in rows if r.get("evaluation", {}).get("status") != "ready"]))
        rule_path = f"data/rules/{cid}/evaluation.json"
        rule = read(rule_path)
        overrides = rule.get("scoring", {}).get("record_evaluator_overrides", {})
        for row in rows:
            task = cid+"/"+row["problem_id"]
            if task in records:
                add("duplicate_task_id", task)
            records[task] = row
            e, assets = row.get("evaluation", {}), row.get("assets", [])
            statuses[e.get("status")] += 1
            splits[row.get("split")] += 1
            licenses[row.get("license", {}).get("status")] += 1
            for field in ("split", "license", "provenance", "eval_unit", "problem_description"):
                if not row.get(field):
                    add("missing_metadata", task, field=field)
            prompt = row.get("problem_description", "")
            controls = sorted({ord(ch) for ch in prompt if ord(ch) < 32 and ch not in "\t\r\n"})
            if controls:
                review.append(dict(kind="prompt_control_characters", task=task, status=e.get("status"), codepoints=controls))
            if "\ufffd" in prompt:
                review.append(dict(kind="prompt_replacement_character", task=task, status=e.get("status"), count=prompt.count("\ufffd")))
            assetmap = {a["path"]:a for a in assets}
            if len(assetmap) != len(assets):
                add("duplicate_asset_path", task)
            public_hashes, hidden_hashes = set(), set()
            for a in assets:
                if a.get("role") not in ("agent_visible", "judge_only", "maintainer_only"):
                    add("unknown_asset_role", task, path=a["path"], role=a.get("role"))
                if check_path(a["path"], task, "asset"):
                    actual = digest(a["path"])
                    if actual != a.get("sha256"):
                        add("asset_hash_mismatch", task, path=a["path"], expected=a.get("sha256"), actual=actual)
                    if a.get("role") == "agent_visible":
                        public_hashes.add(actual)
                    elif a.get("role") == "judge_only":
                        hidden_hashes.add(actual)
            if public_hashes & hidden_hashes:
                review.append(dict(kind="same_bytes_public_and_judge", task=task, sha256=sorted(public_hashes & hidden_hashes)))
            for field in ("source_file", "solution_file"):
                if row.get(field):
                    check_path(row[field], task, field)
            for field in ("rubric_path", "answer_key_path"):
                if e.get(field):
                    check_path(e[field], task, field)
            for path in e.get("rubric_paths", []):
                check_path(path, task, "rubric_paths")
            for path in e.get("judge_assets", []):
                check_path(path, task, "judge_assets")
                if path in assetmap and assetmap[path].get("role") == "agent_visible":
                    add("judge_asset_marked_public", task, path=path)
            if e.get("status") == "ready" and not e.get("evaluator_id"):
                add("ready_without_evaluator", task)
            if row["problem_id"] in overrides and overrides[row["problem_id"]] != e.get("evaluator_id"):
                add("rule_evaluator_override_mismatch", task, row=e.get("evaluator_id"), override=overrides[row["problem_id"]])
            try:
                expected_card = scorecard(row, ROOT, read_json=read, hash_file=digest)
                if cardmap.get(row["problem_id"]) != expected_card:
                    add("scorecard_drift", task, differing_fields=[k for k in expected_card if expected_card[k] != cardmap.get(row["problem_id"], {}).get(k)])
            except (ValueError, TypeError, KeyError, OSError) as error:
                add("scorecard_projection_error", task, error=str(error))
            gold = row.get("gold_label", {})
            answer = gold.get("expected_answer")
            if isinstance(answer, str) and len(answer.strip()) >= 20 and answer.strip() in prompt:
                review.append(dict(kind="long_gold_in_prompt", task=task, answer_length=len(answer.strip()), status=e.get("status")))
            weighted = [p for p in gold.get("parts", []) if p.get("expected")]
            if weighted and isinstance(row.get("total_points"), (int, float)):
                points = sum(float(p.get("points", 1)) for p in weighted)
                if abs(points-row["total_points"]) > 1e-6:
                    review.append(dict(kind="declared_total_vs_gold_weights", task=task, declared=row["total_points"], weighted_total=points, status=e.get("status")))
        print(json.dumps(dict(track=cid, records=len(rows), issues_so_far=len(issues), review_candidates=len(review))), flush=True)
    if len(records) != index["total_records"]:
        add("global_record_count_mismatch", "catalog", expected=len(records), actual=index["total_records"])
    # Verify both actual derived layouts, not only their metadata manifests.
    for layout in layouts:
        cards = read(f"data/{layout}/task_cards.json")
        if Counter(v["task_id"] for v in cards["tasks"]) != Counter(records.keys()) or cards["n_tasks"] != len(records):
            add("derived_membership_mismatch", layout)
        manifests = defaultdict(list)
        for entry in read(f"data/{layout}/input_asset_manifest.json")["files"]:
            manifests[entry["task_id"]].append(entry)
            source, staged = entry["source"], f"data/{layout}/"+entry["staged"]
            if entry["task_id"] not in records:
                add("orphan_asset_manifest", layout, task_id=entry["task_id"])
            if check_path(staged, entry["task_id"], "staged_asset") and digest(staged) != entry["sha256"]:
                add("staged_asset_hash_mismatch", entry["task_id"], layout=layout, path=staged)
        for card in cards["tasks"]:
            task = card["task_id"]
            if task not in records:
                continue
            row = records[task]
            folder = ROOT/f"data/{layout}"/card["source_repo_path"]
            prompt_path = folder/"base/input/problem.md"
            expected_prompt = (row["problem_description"]+"\n").replace("\r\n", "\n").replace("\r", "\n")
            if not prompt_path.is_file() or prompt_path.read_text(encoding="utf-8") != expected_prompt:
                add("derived_prompt_drift", task, layout=layout)
            if layout == "base" and card.get("evaluation") != row["evaluation"]:
                add("derived_evaluation_drift", task, layout=layout)
            public = {a["path"]:a["sha256"] for a in row.get("assets", []) if a.get("role") == "agent_visible"}
            actual = {v["source"]:v["sha256"] for v in manifests[task]}
            if public != actual or len(public) != len(manifests[task]):
                add("derived_public_membership_drift", task, layout=layout, expected=len(public), actual=len(manifests[task]))
            expected_files = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
            for entry in manifests[task]:
                expected_files.add((ROOT/f"data/{layout}"/entry["staged"]).relative_to(folder/"base/input").as_posix())
            actual_files = {p.relative_to(folder/"base/input").as_posix() for p in (folder/"base/input").rglob("*") if p.is_file()}
            if expected_files != actual_files:
                add("unexpected_public_files", task, layout=layout, extra=sorted(actual_files-expected_files), missing=sorted(expected_files-actual_files))
            if layout == "last_exam":
                ref = read((folder/"eval/reference.json").relative_to(ROOT))
                if ref.get("evaluation") != row["evaluation"] or ref.get("solution_file") != row.get("solution_file"):
                    add("derived_hidden_reference_drift", task)
        print(json.dumps(dict(layout=layout, checked_tasks=len(cards["tasks"]), issues_so_far=len(issues))), flush=True)
    summary = read("data/viz/summary.json")
    for field, expected in (("n_primary_records", len(records)), ("evaluation_status_counts", dict(statuses)), ("split_counts", dict(splits)), ("license_status_counts", dict(licenses))):
        if summary[field] != expected:
            add("summary_drift", "catalog", field=field, expected=expected, actual=summary[field])
    report = dict(audited_at_utc=datetime.now(timezone.utc).isoformat(), label=label,
        scope="All active canonical records, declared assets and scorecards; no contest/runtime execution or universal semantic certification.",
        audited_layouts=list(layouts),
        active_tracks=len(tracks), active_records=len(records), status_counts=dict(statuses), split_counts=dict(splits), license_counts=dict(licenses),
        unique_files_hashed=len(digests), declared_pdfs_header_checked=len(checked_pdfs),
        issue_counts=dict(Counter(i["kind"] for i in issues)), review_candidate_counts=dict(Counter(i["kind"] for i in review)),
        issues=issues, review_candidates=review, tracks=tracks,
        source_snapshot={t["benchmark_path"]:digest(t["benchmark_path"]) for t in index["olympiads"]})
    Store(ROOT).save(CACHE+f"/{label}.json", report)
    print(json.dumps({k:report[k] for k in ("active_tracks", "active_records", "status_counts", "unique_files_hashed", "declared_pdfs_header_checked", "issue_counts", "review_candidate_counts")}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label", choices=("before", "after"))
    parser.add_argument('--report-dir', type=Path, help='Fresh output directory; preserve previous audit evidence.')
    args = parser.parse_args()
    if args.report_dir:
        destination = (ROOT / args.report_dir).resolve()
        if not destination.is_relative_to(ROOT / 'output'):
            raise ValueError('Fresh audit reports must be under output')
        if (destination / (args.label+'.json')).exists():
            raise FileExistsError('Use a fresh audit report directory')
        CACHE = destination.relative_to(ROOT).as_posix()
    report = audit(args.label)
    sys.exit(bool(report['issues']))
