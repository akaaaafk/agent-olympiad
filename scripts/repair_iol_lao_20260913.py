"""Recover IOL 2012 judge linkage and preserve the Lao/phonetic image data."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"src"))
from scripts.repair_data_catalog import Store, provenance
from scripts.build_data_packages import build_packages, section
from scripts.repair_iol_sources_20260913 import read, sha, rel, require, pdf_text, POPPLER
from dataset_catalog import scorecard

CID, PID = "iol_team", "iol_team_2012"
TASK = CID+"/"+PID
CACHE = "data/.cache/iol_lao_20260913"
RAW = "data/raw/iol/lao_20260913"
RENDER = "tmp/pdfs/iol_lao_20260913"
BENCHMARK = "data/benchmarks/iol_team/benchmark.json"
CARDS = "data/rubrics/task_scorecards/iol_team.json"
RULE = "data/rules/iol_team/evaluation.json"
SCORES = "data/rubrics/iol_team_active_score_membership.json"
REFERENCE = "data/rubrics/iol_team_2012_structured_reference_v1.json"
REPORT = "data/excluded/benchmark_audit_reports/iol_lao_repair_20260913.json"
SOURCE = "data/raw/iol/iol-2012-team-prob.en.pdf"
SOLUTION = "data/raw/iol/iol-2012-team-sol.en.pdf"
SOURCE_SHA = "61fcd5cb329a1f5cb80699f1ecb5da02638f08b8bcd586984a90fe06c76fafaa"
SOLUTION_SHA = "70b95c0b3c3bc4d7533f3ef459f3db398c5110f7ec714473a4534739d00124e8"
INPUT_IMAGE = RAW+"/input/iol_2012_lao_problem.png"
JUDGE_IMAGE = RAW+"/judge/iol_2012_lao_solution.png"


def poppler_text(path):
    return subprocess.check_output([str(POPPLER/"pdftotext.exe"), "-layout", str(path), "-"]).decode("utf-8")


def sources():
    entries = []
    for path, digest in ((SOURCE, SOURCE_SHA), (SOLUTION, SOLUTION_SHA)):
        local = ROOT/path
        url = "https://ioling.org/booklets/"+local.name
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        require(response.content.startswith(b"%PDF-"), "Publisher response is not PDF")
        require(hashlib.sha256(response.content).hexdigest() == sha(local) == digest, "Publisher/local edition differs")
        pages = pdf_text(local)
        require(len(pages) == 1, "Unexpected page count")
        prefix = ROOT/RENDER/local.stem
        prefix.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(POPPLER/"pdftoppm.exe"), "-r", "220", "-png", str(local), str(prefix)], check=True, capture_output=True)
        Store(ROOT).save_text(rel(prefix)+".txt", pages[0])
        Store(ROOT).save_text(rel(prefix)+"-poppler.txt", poppler_text(local))
        entries.append(dict(path=path, sha256=digest, pages=1, source_url=url, publisher_bytes_identical=True,
            rendered_page=rel(prefix)+"-1.png", rendered_sha256=sha(Path(str(prefix)+"-1.png"))))
    Store(ROOT).save(CACHE+"/source_review.json", dict(sources=entries))
    print(json.dumps(entries, indent=2))


def country_map(text):
    """Parse country names only; pronunciation typography is not text-safe."""
    pairs = [(int(n), " ".join(name.split())) for n, name in re.findall(r"\b(\d{1,2})\.\s+([A-Za-z ()]+?)\s*\[", text)]
    require(len(pairs) == 57 and {n for n, _ in pairs} == set(range(1, 58)), "Country ID membership differs")
    return {str(n):name for n, name in sorted(pairs)}


def reference_data():
    require(sha(ROOT/SOURCE) == SOURCE_SHA and sha(ROOT/SOLUTION) == SOLUTION_SHA, "Source edition differs")
    countries = country_map(pdf_text(ROOT/SOLUTION)[0])
    require(countries == country_map(poppler_text(ROOT/SOLUTION)), "Independent country extraction differs")
    return dict(rubric_id=Path(REFERENCE).stem, dataset=CID, visibility="judge_only", rubric_type="official_answer_map_without_verified_weights",
        total_points=None, criteria=[], source_file=SOLUTION, source_sha256=SOLUTION_SHA,
        source_url="https://ioling.org/booklets/iol-2012-team-sol.en.pdf", country_names_by_id=countries,
        pronunciation_reference=dict(format="original_page_image_required", source_file=SOLUTION, source_sha256=SOLUTION_SHA,
            image_file=JUDGE_IMAGE, image_sha256=sha(ROOT/JUDGE_IMAGE), original_pdf_page=1, covers_ids=list(range(1,58)),
            text_transcription_verified=False, instruction="Read the original rendered phonetic symbols, diacritics and superscripts; do not grade against flattened text extraction."),
        coverage={"a":"Official country identifications for all 57 numbered entries, independently parsed and visually checked.",
                  "b":"Official pronunciation references for all 57 entries preserved in the PDF and unedited page image; no text-safe pronunciation key asserted."},
        official_weights_verified=False, grading_validation_status="not_validated",
        legacy_proxy=dict(path="data/rubrics/iol_team_worked_answer_100_v1.json", total_points=100, official=False, active_for_this_record=False),
        not_observable_from_deck=["Official overall/part/item point allocation", "Acceptable alternative country names and pronunciation variants; partial-credit rules"])


def make_row(before):
    row = deepcopy(before)
    evidence = read(ROOT/CACHE/"source_review.json")["sources"]
    visual = read(ROOT/CACHE/"visual_review.json")
    require(visual["source_sha256"] == SOURCE_SHA and visual["solution_sha256"] == SOLUTION_SHA and visual["pages_reviewed"] == 2, "Visual review differs")
    images = []
    for item, target, role in zip(evidence, (INPUT_IMAGE, JUDGE_IMAGE), ("agent_visible", "judge_only")):
        require(sha(ROOT/item["path"]) == item["sha256"] and sha(ROOT/item["rendered_page"]) == item["rendered_sha256"], "Reviewed source/render changed")
        destination = ROOT/target
        require(not destination.exists() or sha(destination) == item["rendered_sha256"], "Existing image differs")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(ROOT/item["rendered_page"], destination)
        images.append(dict(path=target, sha256=sha(destination), mime_type="image/png", role=role,
            derived_from=item["path"], original_sha256=item["sha256"], original_pdf_page=1,
            rendering="Poppler 26.07.0, 220 dpi, unedited full page"))
    reference = reference_data()
    reference_hash = hashlib.sha256((json.dumps(reference, ensure_ascii=False, indent=2)+"\n").encode()).hexdigest()
    row["problem_description"] = ("Use the complete original IOL 2012 problem PDF and its attached full-page image (lao_20260913/input/iol_2012_lao_problem.png). "
        "All 57 numbered Lao country names are image data and are missing from plain-text extraction. Preserve their original numbering, script and diacritics. "
        "For each entry, answer both (a) country identification and (b) your best guess at the pronunciation of its Lao name. "
        "The image, not an inferred Unicode transcription, is the authoritative input.\n\n"+pdf_text(ROOT/SOURCE)[0].strip())
    row["assets"] = [dict(path=SOURCE, sha256=SOURCE_SHA, mime_type="application/pdf", role="agent_visible"), images[0],
        dict(path=SOLUTION, sha256=SOLUTION_SHA, mime_type="application/pdf", role="judge_only"), images[1],
        dict(path=REFERENCE, sha256=reference_hash, mime_type="application/json", role="judge_only")]
    row["total_points"] = None
    row["scoring_components"] = dict(official_total_points=None, official_item_weights_verified=False,
        legacy_benchmark_proxy_points=100, legacy_proxy_enabled=False, item_count_is_not_a_score=True)
    limitations = [
        "All 57 Lao input forms are present in the original problem image but absent from plain-text extraction.",
        "Official country names and pronunciation references for all 57 entries are present; the solution PDF, rendered page and country map are now linked as judge-only assets.",
        "Flattened pronunciation extraction loses or moves superscripts/diacritics. Only the original page images are authoritative; no Unicode pronunciation key is asserted.",
        "Official total, part/item weights, acceptable variants and partial-credit rules remain unverified. The old 100-point 50/30/20 benchmark proxy is disabled for this record.",
        "Image-aware task delivery and pronunciation grading have not been validated end to end; keep not_ready."]
    evaluation = row["evaluation"]
    evaluation.update(evaluator_id=None, status="not_ready", rubric_path=REFERENCE, answer_key_path=REFERENCE,
        judge_assets=[a["path"] for a in row["assets"] if a["role"] == "judge_only"], limitations=limitations,
        score_basis="Official points unknown; 57 entries and two requested outputs per entry are not point weights. Legacy 100-point benchmark proxy disabled.",
        scoring_validation_status="source_repaired_pronunciation_grading_not_validated")
    evaluation.pop("rubric_paths", None)
    evaluation.pop("rubric_reuse", None)
    row["gold_label"].update(expected_answer=None, parts=[], reference_assets=[SOLUTION, JUDGE_IMAGE, REFERENCE],
        reference_format="structured_country_map_and_original_pronunciation_image", grading_rubric="\n".join(limitations))
    row["source_review"] = dict(report=REPORT, official_page="https://ioling.org/problems/2012/t1/",
        original_source_preserved=True, original_solution_preserved=True, publisher_bytes_identical=True,
        source_pages_reviewed=1, solution_pages_reviewed=1, country_ids_verified=57, no_answerless_exclusion=True)
    row["packet_review"] = dict(status="present_visual_verified", reviewed_on="2026-09-13",
        input_requirement="Original Lao page images required; all 57 written forms are omitted by text extraction.", source_image=INPUT_IMAGE)
    provenance(row)
    return row, reference


def check_packages(row, base):
    generated = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
    public = {a["path"]:a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}
    countries = reference_data()["country_names_by_id"]
    forbidden = ["team-sol", "/judge/", "data/rubrics/", "country_names_by_id", *countries.values()]
    for layout in ("base", "last_exam"):
        entries = [v for v in read(base/layout/"input_asset_manifest.json")["files"] if v["task_id"] == TASK]
        require(len(entries) == 2 and {v["source"]:v["sha256"] for v in entries} == public, "Public asset membership differs")
        folder = base/layout/"tasks"/TASK/"base/input"
        names = {Path(v["staged"]).relative_to(Path("tasks")/TASK/"base/input").as_posix() for v in entries}
        require({p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} == names|generated, "Public allowlist differs")
        for v in entries:
            require(sha(base/layout/v["staged"]) == v["sha256"], "Copied public bytes differ")
        require((folder/"problem.md").read_text(encoding="utf-8") == row["problem_description"]+"\n", "Prompt readback differs")
        for name in generated:
            text = (folder/name).read_text(encoding="utf-8")
            require(not any(term in text for term in forbidden), "Judge country/reference leaked: "+name)
        if layout == "last_exam":
            reference = read(folder.parent.parent/"eval/reference.json")
            require(reference["evaluation"] == row["evaluation"] and reference["solution_file"] == SOLUTION, "Hidden reference differs")


def prepare():
    require(not (ROOT/REPORT).exists() and not (ROOT/CACHE/"plan.json").exists(), "Already prepared/applied")
    store = Store(ROOT)
    before = deepcopy(store.read(BENCHMARK))
    index = deepcopy(store.read("data/benchmarks/index.json"))
    require(len(before) == 18 and index["total_records"] == 1720, "Catalog starting point differs")
    original = next(r for r in before if r["problem_id"] == PID)
    require(original["evaluation"]["status"] == "not_ready", "Selected record status changed")
    row, reference = make_row(original)
    rows = [row if r["problem_id"] == PID else r for r in deepcopy(before)]
    rules = {k:deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    scoring = rules["evaluation"]["scoring"]
    require(scoring["evaluation_status_counts"] == dict(Counter(r["evaluation"]["status"] for r in rows)), "Status counts differ")
    scoring.setdefault("record_evaluator_overrides", {})[PID] = None
    scoring.setdefault("record_rubric_overrides", {})[PID] = REFERENCE
    scoring.setdefault("record_score_basis_overrides", {})[PID] = dict(max_score=None, basis=row["evaluation"]["score_basis"], grading_validation_status="not_ready")
    writes = {BENCHMARK:rows, RULE:rules["evaluation"], REFERENCE:reference}
    cards = deepcopy(store.read(CARDS))
    prior_cards = deepcopy(cards["records"])
    def pending_read(path):
        return writes[path] if path in writes else read(ROOT/path)
    def pending_sha(path):
        return hashlib.sha256((json.dumps(writes[path], ensure_ascii=False, indent=2)+"\n").encode()).hexdigest() if path in writes else sha(ROOT/path)
    cards["records"] = [scorecard(row, ROOT, read_json=pending_read, hash_file=pending_sha) if c["problem_id"] == PID else c for c in cards["records"]]
    writes[CARDS] = cards
    membership = deepcopy(store.read(SCORES))
    item = next(v for v in membership["records"] if v["problem_id"] == PID)
    item.update(official_total_points=None, evaluation_status="not_ready", rubric_path=REFERENCE, scoring_components=row["scoring_components"])
    writes[SCORES] = membership
    index["latest_source_repair_report"] = REPORT
    writes["data/benchmarks/index.json"] = index
    stage = ROOT/CACHE/"stage"
    require(not stage.exists(), "Stage occupied")
    build_packages(ROOT, stage, {"olympiads":[next(t for t in index["olympiads"] if t["id"] == CID)]}, {CID:[row]}, {CID:rules}, store.sha)
    targets, old_tasks, protected = [], {}, {}
    for layout in ("base", "last_exam"):
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            path = f"data/{layout}/{name}"
            value = deepcopy(store.read(path))
            if key == "tasks":
                for card in value[key]:
                    if not card["task_id"].startswith(CID+"/"):
                        continue
                    folder = store.path(f"data/{layout}/"+card["source_repo_path"])
                    require(folder == store.path(f"data/{layout}/tasks/"+card["task_id"]), "Task path differs")
                    bucket = old_tasks if card["task_id"] == TASK else protected
                    bucket.update({rel(p):sha(p) for p in folder.rglob("*") if p.is_file()})
                    if card["task_id"] == TASK:
                        targets.append(rel(folder))
            replacement = read(stage/layout/name)[key]
            require({v["task_id"] for v in replacement} == {TASK}, "Staged membership differs")
            if key == "tasks":
                require(len(replacement) == 1, "Duplicate staged task")
                value[key] = [replacement[0] if v["task_id"] == TASK else v for v in value[key]]
            else:
                value[key] = [v for v in value[key] if v["task_id"] != TASK]+replacement
            writes[path] = value
    require(len(targets) == 2, "Unexpected archive count")
    for tree in ("data/raw/iol", "data/rules", "data/rubrics", "data/viz"):
        protected.update({rel(p):sha(p) for p in (ROOT/tree).rglob("*") if p.is_file() and rel(p) not in writes})
    for track in index["olympiads"]:
        if track["id"] != CID:
            protected[track["benchmark_path"]] = sha(ROOT/track["benchmark_path"])
    folder = ROOT/f"data/last_exam/competitions/{CID}"
    protected.update({rel(p):sha(p) for p in folder.rglob("*") if p.is_file() and "eval" not in p.parts})
    for path in ("data/base/index.json", "data/last_exam/index.json", "data/last_exam/competitions/index.json", "data/base/README.md", "data/last_exam/README.md", "output/pdf/iol_2011_initial.pdf"):
        protected[path] = sha(ROOT/path)
    for path in ("data/README.md", "data/benchmarks/README.md"):
        value = store.path(path).read_text(encoding="utf-8-sig")
        value += ("\n## IOL 2012 Lao reference repair (2026-09-13)\n\n2012 is retained: the official solution contains all 57 country identifications and pronunciations. "
            "The empty judge-assets link is repaired, the public input now includes the original Lao page image, and the judge-only reference includes a 57-country ID map and the original pronunciation image. "
            "Flattened phonetic text is no longer treated as gold. Official weights remain unknown; the old 100-point proxy is disabled. "
            "2012 remains not_ready pending image-aware delivery and pronunciation grading. Catalog membership and readiness counts are unchanged (43 tracks, 1,720 records; IOL 18 years; 706 not_ready globally). "
            f"See `{REPORT}` and `docs/from_zhongzheng/iol-lao-repair-20260913.md`.\n")
        writes[path] = value
    expected = set(writes)|{f"data/last_exam/competitions/{CID}/eval/evaluation.json", f"data/last_exam/competitions/{CID}/eval/scoring.md"}
    plan = dict(before_rows=before, rows=rows, prior_cards=prior_cards, writes=writes, targets=targets, old_tasks=old_tasks, protected_hashes=protected,
        expected_hashes={p:sha(ROOT/p) for p in expected if (ROOT/p).exists()}, new_paths=[p for p in expected if not (ROOT/p).exists()],
        stage_hashes={rel(p):sha(p) for p in stage.rglob("*") if p.is_file()})
    check_packages(row, stage)
    store.save(CACHE+"/plan.json", plan)
    print(json.dumps(dict(selected_year=2012, status_counts=scoring["evaluation_status_counts"], protected_files=len(protected), archived_task_dirs=2), indent=2))


def verify(plan, report):
    for path, digest in plan["protected_hashes"].items():
        require(sha(ROOT/path) == digest, "Protected bytes changed: "+path)
    for path, value in plan["writes"].items():
        actual = (ROOT/path).read_text(encoding="utf-8-sig") if isinstance(value, str) else read(ROOT/path)
        require(actual == value, "Metadata readback differs: "+path)
    rows = read(ROOT/BENCHMARK)
    row = next(r for r in rows if r["problem_id"] == PID)
    require([r for r in rows if r["problem_id"] != PID] == [r for r in plan["before_rows"] if r["problem_id"] != PID], "Unrelated IOL row changed")
    cards = read(ROOT/CARDS)["records"]
    require([c for c in cards if c["problem_id"] != PID] == [c for c in plan["prior_cards"] if c["problem_id"] != PID], "Unrelated scorecard changed")
    card = next(c for c in cards if c["problem_id"] == PID)
    require(card == scorecard(row, ROOT), "Scorecard projection differs")
    require(card["evaluator_id"] is None and card["evaluation_status"] == "not_ready" and not card["numeric_rubric_available"] and card["gold_max_score"] is None, "Unverified score/readiness restored")
    require(read(ROOT/REFERENCE) == reference_data(), "Independent reference reconstruction differs")
    for asset in row["assets"]:
        require(sha(ROOT/asset["path"]) == asset["sha256"], "Asset hash differs")
    for path, digest in plan["old_tasks"].items():
        require(sha(ROOT/report["backup"]/path) == digest, "Archived task differs")
    check_packages(row, ROOT/"data")
    for layout in ("base", "last_exam"):
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            before = read(ROOT/report["backup"]/f"data/{layout}/{name}")[key]
            after = read(ROOT/f"data/{layout}/{name}")[key]
            require([v for v in before if v["task_id"] != TASK] == [v for v in after if v["task_id"] != TASK], "Unrelated derived entries changed")
    rule = read(ROOT/RULE)
    require(read(ROOT/f"data/last_exam/competitions/{CID}/eval/evaluation.json") == rule, "Shared evaluation differs")
    require((ROOT/f"data/last_exam/competitions/{CID}/eval/scoring.md").read_text(encoding="utf-8") == "# Hidden scoring configuration\n\n"+section("Evaluation", rule), "Shared scoring text differs")
    index = read(ROOT/"data/benchmarks/index.json")
    all_ids, all_rows, statuses = [], [], Counter()
    for track in index["olympiads"]:
        data = read(ROOT/track["benchmark_path"])
        require(len(data) == track["problems_collected"], "Track count mismatch")
        all_ids += [track["id"]+"/"+r["problem_id"] for r in data]
        all_rows.extend(data)
        statuses.update(r["evaluation"]["status"] for r in data)
    require(len(all_ids) == len(set(all_ids)) == index["total_records"] == 1720, "Global membership mismatch")
    for layout in ("base", "last_exam"):
        derived = read(ROOT/f"data/{layout}/task_cards.json")
        require(derived["n_tasks"] == len(derived["tasks"]) == 1720 and {c["task_id"] for c in derived["tasks"]} == set(all_ids), "Derived membership mismatch")
    summary = read(ROOT/"data/viz/summary.json")
    require(summary["n_primary_records"] == 1720 and summary["evaluation_status_counts"] == dict(statuses), "Summary mismatch")
    require(summary["record_status_primary"] == dict(Counter(r["status"] for r in all_rows)), "Record-status summary mismatch")
    require(dict(statuses) == dict(ready=661, not_ready=706, ready_with_limitations=193, remote_judge_ready=158, sample_tests_ready=2), "Unexpected readiness change")
    return dict(active_tracks=43, active_records=1720, active_iol_records=18, no_years_excluded=True, repaired_years=[2012],
        iol_status_counts=dict(Counter(r["evaluation"]["status"] for r in rows)), global_status_counts=dict(statuses),
        country_ids_verified=57, official_pronunciation_rows_present=57, judge_link_recovered=True,
        source_pages_visually_reviewed=2, public_page_images=1, judge_page_images=1, official_score_unknown=True, old_proxy_disabled=True,
        unchanged_iol_rows_and_scorecards=17, other_tracks_unchanged=42, protected_files_unchanged=len(plan["protected_hashes"]),
        archived_generated_files=len(plan["old_tasks"]), visualization_bytes_unchanged=True, historical_results_modified=False,
        end_to_end_runtime_or_grading_validated=False)


def apply():
    require(not (ROOT/REPORT).exists(), "Already applied")
    plan = read(ROOT/CACHE/"plan.json")
    store = Store(ROOT)
    for path, digest in {**plan["protected_hashes"], **plan["expected_hashes"], **plan["old_tasks"], **plan["stage_hashes"]}.items():
        require(sha(ROOT/path) == digest, "Concurrent change: "+path)
        if path in plan["expected_hashes"]:
            store.raw[store.path(path)] = store.path(path).read_bytes()
    for path in plan["new_paths"]:
        require(not (ROOT/path).exists(), "New target occupied")
    for name in plan["targets"]:
        target = store.path(name)
        require(target.name == PID and target.parent.name == CID and target.parent.parent.name == "tasks" and target.is_dir(), "Unsafe archive target")
    report = dict(operation="iol_2012_lao_judge_link_and_image_reference_repair", status="preparing", backup=rel(store.backup), timestamp_utc=store.stamp)
    store.finish(report)
    try:
        for path, value in plan["writes"].items():
            store.save_text(path, value) if isinstance(value, str) else store.save(path, value)
        for name in plan["targets"]:
            require({rel(p):sha(p) for p in store.path(name).rglob("*") if p.is_file()} == {p:h for p,h in plan["old_tasks"].items() if p.startswith(name+"/")}, "Task changed before archival")
            store.archive(name)
        for layout in ("base", "last_exam"):
            destination = ROOT/"data"/layout/"tasks"/CID/PID
            require(not destination.exists(), "Replacement target occupied")
            shutil.copytree(ROOT/CACHE/"stage"/layout/"tasks"/CID/PID, destination)
        rule = plan["writes"][RULE]
        store.save(f"data/last_exam/competitions/{CID}/eval/evaluation.json", rule)
        store.save_text(f"data/last_exam/competitions/{CID}/eval/scoring.md", "# Hidden scoring configuration\n\n"+section("Evaluation", rule))
        report["validation"] = verify(plan, report)
        report["new_task_file_hashes"] = {rel(p):sha(p) for layout in ("base", "last_exam") for p in (ROOT/"data"/layout/"tasks"/CID/PID).rglob("*") if p.is_file()}
        report["status"] = "completed_judge_link_image_reference_and_score_sync"
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps({k:report[k] for k in ("status", "backup", "validation")}, indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("sources", "prepare", "apply", "verify"))
    mode = parser.parse_args().mode
    if mode == "verify":
        print(json.dumps(verify(read(ROOT/CACHE/"plan.json"), read(ROOT/REPORT)), indent=2))
    else:
        {"sources":sources, "prepare":prepare, "apply":apply}[mode]()
