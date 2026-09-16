"""Source-bound IOL 2017 emoji transcription and partial-reference repair."""
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

import pymupdf
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance, summary_and_figures
from scripts.build_data_packages import build_packages, section
from scripts.repair_iol_sources_20260913 import read, sha, rel, require, pdf_text, POPPLER
from dataset_catalog import scorecard, update_track_index

CID, PID = "iol_team", "iol_team_2017"
TASK = CID + "/" + PID
CACHE = "data/.cache/iol_emoji_20260913"
RAW = "data/raw/iol/emoji_20260913"
RENDER = "tmp/pdfs/iol_emoji_20260913"
BENCHMARK = "data/benchmarks/iol_team/benchmark.json"
CARDS = "data/rubrics/task_scorecards/iol_team.json"
RULE = "data/rules/iol_team/evaluation.json"
SCORES = "data/rubrics/iol_team_active_score_membership.json"
REFERENCE = "data/rubrics/iol_team_2017_structured_reference_v1.json"
REPORT = "data/excluded/benchmark_audit_reports/iol_emoji_repair_20260913.json"
SOURCE = "data/raw/iol/iol-2017-team-prob.en.pdf"
SOLUTION = "data/raw/iol/iol-2017-team-sol.en.pdf"
SOURCE_SHA = "fadec98495be3282049e806fb44eb652f3528585b35b41c1f8e265d46aac9c9c"
SOLUTION_SHA = "e831b2003e0c4cb7ade36cfc003f1650146ac9781485a57183f77559c14bbdfc"
LABELS = [a+b for a in "ABC" for b in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] + ["D"+b for b in "ABCDEFGHIJKLMNO"]
UNMATCHED = {59: "payung tertutup", 73: "hati biru", 79: "kacamata hitam", 81: "mulut"}


def poppler_text(path):
    return subprocess.check_output([str(POPPLER/"pdftotext.exe"), "-layout", str(path), "-"]).decode("utf-8")


def sources():
    evidence = []
    for path, count, digest in ((SOURCE, 4, SOURCE_SHA), (SOLUTION, 3, SOLUTION_SHA)):
        local = ROOT / path
        url = "https://ioling.org/booklets/" + local.name
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        require(response.content.startswith(b"%PDF-"), "Remote source is not a PDF")
        require(hashlib.sha256(response.content).hexdigest() == sha(local) == digest, "Publisher/local bytes differ")
        pages = pdf_text(local)
        require(len(pages) == count, "Unexpected page count")
        prefix = ROOT / RENDER / local.stem
        prefix.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(POPPLER/"pdftoppm.exe"), "-r", "140", "-png", str(local), str(prefix)], check=True, capture_output=True)
        Store(ROOT).save_text(rel(prefix)+".txt", "\n\n".join(pages))
        Store(ROOT).save_text(rel(prefix)+"-poppler.txt", poppler_text(local))
        evidence.append(dict(path=path, source_url=url, sha256=digest, pages=count, publisher_bytes_identical=True))
    Store(ROOT).save(CACHE+"/source_review.json", dict(sources=evidence))
    print(json.dumps(evidence, indent=2))


def descriptions(text):
    """Read only the public description page, never the solution table."""
    flattened = " ".join(text.split())
    pairs = re.findall(r"\b([A-D][A-Z])\s+([a-z][a-z -]*?)(?=\s+[A-D][A-Z]\s+|$)", flattened)
    require(len(pairs) == len(LABELS) and {p[0] for p in pairs} == set(LABELS), "Description labels differ")
    return dict(sorted(pairs))


def answer_map(text):
    pairs = [(label, int(number)) for label, number in re.findall(r"\b([A-D][A-Z])\s+.*?\b(\d{1,2})\b", text, re.S)]
    require(len(pairs) == len(LABELS) and [p[0] for p in pairs] == LABELS, "Answer labels differ")
    require(set(range(1, 88)) - {p[1] for p in pairs} == set(UNMATCHED), "Unmatched emoji differ")
    require(len({p[1] for p in pairs}) == 83, "Matched emoji count differs")
    return dict(pairs)


def reference_data():
    require(sha(ROOT/SOURCE) == SOURCE_SHA and sha(ROOT/SOLUTION) == SOLUTION_SHA, "Source edition differs")
    public = descriptions(pdf_text(ROOT/SOURCE)[1])
    independent_public = descriptions(poppler_text(ROOT/SOURCE).split("\f")[1])
    require(public == independent_public, "Independent public description extraction differs")
    native = "\n".join(pdf_text(ROOT/SOLUTION))
    independent = poppler_text(ROOT/SOLUTION)
    answers = answer_map(native)
    require(answers == answer_map(independent), "Independent answer ID extraction differs")
    for number, phrase in UNMATCHED.items():
        for text in (native, independent):
            require(re.search(re.escape(phrase)+r"\s+"+str(number)+r"\b", text), "Unmatched description differs")
    duplicates = {str(n): [label for label, value in answers.items() if value == n]
                  for n, count in Counter(answers.values()).items() if count > 1}
    ref = dict(rubric_id=Path(REFERENCE).stem, dataset=CID, visibility="judge_only", total_points=None, criteria=[],
        rubric_type="partial_official_answer_map_no_verified_weights", grading_validation_status="not_validated",
        source_file=SOLUTION, source_sha256=SOLUTION_SHA, source_url="https://ioling.org/booklets/iol-2017-team-sol.en.pdf",
        public_description_source=dict(path=SOURCE, sha256=SOURCE_SHA, pdf_page=2),
        label_to_emoji_id=answers, duplicate_description_groups=duplicates,
        unlabelled_emoji_descriptions=[dict(emoji_id=n, indonesian=phrase, solution_pdf_page=3) for n, phrase in UNMATCHED.items()],
        counts=dict(descriptions=93, numbered_emoji=87, matched_unique_emoji=83, unmatched_emoji=4),
        coverage={"a": "All 93 official label-to-ID matches recovered; multiple labels may match one emoji.",
                  "b": "All four official Indonesian descriptions recovered. Valid alternative phrasings/partial credit unverified.",
                  "c": "Official solution supplies phrase-level English glosses, not a separately enumerated word dictionary or scoring key.",
                  "d": "No explicit short-grammar answer or criterion-level scoring found in the reviewed three-page solution."},
        emoji_identity_policy="Use original numbered problem images, not extracted Unicode code points. No Unicode substitutions generated.",
        legacy_proxy=dict(path="data/rubrics/iol_team_worked_answer_100_v1.json", total_points=100, official=False, active_for_this_record=False),
        official_weights_verified=False, not_observable_from_deck=["Official part/item weights and full dictionary/grammar credit allocation"])
    return public, ref


def make_row(before):
    public, reference = reference_data()
    row = deepcopy(before)
    image_assets = []
    for page in (3, 4):
        rendered = ROOT/RENDER/f"iol-2017-team-prob.en-{page}.png"
        target = ROOT/RAW/f"input/iol_2017_emoji_page_{page}.png"
        require(rendered.exists(), "Render sources first")
        require(not target.exists() or sha(target) == sha(rendered), "Existing image differs")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(rendered, target)
        image_assets.append(dict(path=rel(target), sha256=sha(target), role="agent_visible", mime_type="image/png",
            derived_from=SOURCE, original_sha256=SOURCE_SHA, original_pdf_page=page, rendering="Poppler 26.07.0, 140 dpi, unedited full page"))
    intro = pdf_text(ROOT/SOURCE)[0].strip().replace("Aus-\ntronesian", "Austronesian").replace("!△\n", "Note: ")
    row["problem_description"] = ("Use the complete four-page original problem PDF. The two attached PNGs reproduce its numbered emoji pages 3-4 without substitutions. "
        "Emoji identity, color and shape must be read from those original images; embedded-font plain-text extraction is not a valid substitute.\n\n"
        + intro + "\n\nDescriptions transcribed from original problem page 2:\n\n"
        + "\n".join(label+" "+public[label] for label in LABELS))
    row["total_points"] = None
    row["scoring_components"] = dict(official_total_points=None, official_item_weights_verified=False,
        legacy_benchmark_proxy_points=100, legacy_proxy_enabled=False, description_count_is_not_a_score=True)
    limitations = [
        "Original emoji page images are required; plain-text font extraction corrupts glyph identity (including black versus blue heart).",
        "Official (a) label-to-ID and (b) four unmatched-emoji references recovered; do not deduplicate the 93 description labels into 83 items.",
        "The official solution gives phrase glosses but no separate full word-dictionary or short-grammar answer/marking rubric for (c)-(d).",
        "No official total, part weights or partial-credit rules recovered. The old 100-point 50/30/20 benchmark proxy is disabled for this record.",
        "Image-aware task delivery and full four-part grading have not been validated end to end."]
    e = row["evaluation"]
    e.update(status="not_ready", evaluator_id=None, rubric_path=REFERENCE, answer_key_path=REFERENCE,
        score_basis="Official points unknown; structured partial reference only. Legacy 100-point benchmark proxy disabled; 93 matches and 4 descriptions are not point weights.",
        limitations=limitations, scoring_validation_status="source_repaired_full_grading_not_validated")
    # A stale plural rubric override must not reactivate the old generic rubric.
    e.pop("rubric_paths", None)
    e.pop("rubric_reuse", None)
    reference_payload = (json.dumps(reference, ensure_ascii=False, indent=2)+"\n").encode()
    row["assets"] = [dict(path=SOURCE, sha256=SOURCE_SHA, role="agent_visible", mime_type="application/pdf"), *image_assets,
        dict(path=SOLUTION, sha256=SOLUTION_SHA, role="judge_only", mime_type="application/pdf"),
        dict(path=REFERENCE, sha256=hashlib.sha256(reference_payload).hexdigest(), role="judge_only", mime_type="application/json")]
    e["judge_assets"] = [a["path"] for a in row["assets"] if a["role"] == "judge_only"]
    row["gold_label"].update(expected_answer=None, parts=[], reference_assets=[SOLUTION, REFERENCE],
        reference_format="structured_partial_reference_and_pdf_images", grading_rubric="\n".join(limitations))
    row["source_review"] = dict(report=REPORT, official_page="https://ioling.org/problems/2017/t1/",
        original_source_preserved=True, original_solution_preserved=True, source_pages_reviewed=4, solution_pages_reviewed=3,
        source_and_answer_images_required=True, no_answerless_exclusion=True, text_extraction_not_emoji_identity=True)
    provenance(row)
    return row, reference


def check_packages(row, base):
    generated = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
    assets = {a["path"]: a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}
    for layout in ("base", "last_exam"):
        entries = [v for v in read(base/layout/"input_asset_manifest.json")["files"] if v["task_id"] == TASK]
        require(len(entries) == 3 and {v["source"]:v["sha256"] for v in entries} == assets, "Public asset membership differs")
        folder = base/layout/"tasks"/TASK/"base/input"
        names = {Path(v["staged"]).relative_to(Path("tasks")/TASK/"base/input").as_posix() for v in entries}
        require({p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} == names|generated, "Public allowlist differs")
        for entry in entries:
            require(sha(base/layout/entry["staged"]) == entry["sha256"], "Copied public bytes differ")
        require((folder/"problem.md").read_text(encoding="utf-8") == row["problem_description"]+"\n", "Prompt readback differs")
        for name in generated:
            text = (folder/name).read_text(encoding="utf-8")
            require(not any(t in text for t in ("team-sol", "data/rubrics/", "label_to_emoji_id", "payung tertutup", "hati biru")), "Hidden reference leaked")
        if layout == "last_exam":
            ref = read(folder.parent.parent/"eval/reference.json")
            require(ref["evaluation"] == row["evaluation"] and ref["solution_file"] == SOLUTION, "Hidden evaluation differs")


def prepare():
    store = Store(ROOT)
    require(not (ROOT/REPORT).exists() and not (ROOT/CACHE/"plan.json").exists(), "Already prepared/applied")
    visual = read(ROOT/CACHE/"visual_review.json")
    require(visual["source_sha256"] == SOURCE_SHA and visual["solution_sha256"] == SOLUTION_SHA and visual["pages_reviewed"] == 7, "Visual review differs")
    before = deepcopy(store.read(BENCHMARK))
    index = deepcopy(store.read("data/benchmarks/index.json"))
    require(len(before) == 18 and index["total_records"] == 1720, "Catalog starting point differs")
    selected = next(r for r in before if r["problem_id"] == PID)
    row, reference = make_row(selected)
    rows = [row if r["problem_id"] == PID else r for r in deepcopy(before)]
    rules = {k:deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    scoring = rules["evaluation"]["scoring"]
    scoring["evaluation_status_counts"] = dict(Counter(r["evaluation"]["status"] for r in rows))
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
    update_track_index(index, CID, rows)
    index["latest_source_repair_report"] = REPORT
    writes["data/benchmarks/index.json"] = index
    stage = ROOT/CACHE/"stage"
    require(not stage.exists(), "Stage already exists")
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
    for tree in ("data/raw/iol", "data/rules", "data/rubrics"):
        protected.update({rel(p):sha(p) for p in (ROOT/tree).rglob("*") if p.is_file() and rel(p) not in writes})
    for track in index["olympiads"]:
        if track["id"] != CID:
            protected[track["benchmark_path"]] = sha(ROOT/track["benchmark_path"])
    folder = ROOT/f"data/last_exam/competitions/{CID}"
    protected.update({rel(p):sha(p) for p in folder.rglob("*") if p.is_file() and "eval" not in p.parts})
    for path in ("data/base/index.json", "data/last_exam/index.json", "data/last_exam/competitions/index.json", "data/base/README.md", "data/last_exam/README.md", "output/pdf/iol_2011_initial.pdf"):
        protected[path] = sha(ROOT/path)
    expected = set(writes)|{"data/README.md", "data/benchmarks/README.md", f"data/last_exam/competitions/{CID}/eval/evaluation.json", f"data/last_exam/competitions/{CID}/eval/scoring.md"}
    expected.update(rel(p) for p in (ROOT/"data/viz").iterdir() if p.is_file())
    plan = dict(before_rows=before, rows=rows, prior_cards=prior_cards, writes=writes, targets=targets, old_tasks=old_tasks, protected_hashes=protected,
        expected_hashes={p:sha(ROOT/p) for p in expected if (ROOT/p).exists()}, new_paths=[p for p in expected if not (ROOT/p).exists()],
        stage_hashes={rel(p):sha(p) for p in stage.rglob("*") if p.is_file()})
    check_packages(row, stage)
    store.save(CACHE+"/plan.json", plan)
    print(json.dumps(dict(selected_year=2017, status_counts=scoring["evaluation_status_counts"], protected_files=len(protected), archived_task_dirs=len(targets)), indent=2))


def verify(plan, report):
    for path, digest in plan["protected_hashes"].items():
        require(sha(ROOT/path) == digest, "Protected bytes changed: "+path)
    for path, value in plan["writes"].items():
        require(read(ROOT/path) == value, "Metadata readback differs: "+path)
    rows = read(ROOT/BENCHMARK)
    row = next(r for r in rows if r["problem_id"] == PID)
    require([r for r in rows if r["problem_id"] != PID] == [r for r in plan["before_rows"] if r["problem_id"] != PID], "Unrelated IOL row changed")
    cards = read(ROOT/CARDS)["records"]
    require([c for c in cards if c["problem_id"] != PID] == [c for c in plan["prior_cards"] if c["problem_id"] != PID], "Unrelated scorecard changed")
    card = next(c for c in cards if c["problem_id"] == PID)
    require(card == scorecard(row, ROOT), "Selected scorecard differs")
    require(card["evaluation_status"] == "not_ready" and card["evaluator_id"] is None and not card["numeric_rubric_available"] and card["gold_max_score"] is None, "Unvalidated points/readiness restored")
    for asset in row["assets"]:
        require(sha(ROOT/asset["path"]) == asset["sha256"], "Asset bytes differ")
    require(read(ROOT/REFERENCE) == reference_data()[1], "Independent reference reconstruction differs")
    for page in (3, 4):
        require(sha(ROOT/RAW/f"input/iol_2017_emoji_page_{page}.png") == sha(ROOT/RENDER/f"iol-2017-team-prob.en-{page}.png"), "Rendered page changed")
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
    all_ids, statuses = [], Counter()
    for track in index["olympiads"]:
        data = read(ROOT/track["benchmark_path"])
        require(len(data) == track["problems_collected"], "Track count mismatch")
        all_ids += [track["id"]+"/"+r["problem_id"] for r in data]
        statuses.update(r["evaluation"]["status"] for r in data)
    require(len(all_ids) == len(set(all_ids)) == index["total_records"] == 1720, "Global membership mismatch")
    for layout in ("base", "last_exam"):
        derived = read(ROOT/f"data/{layout}/task_cards.json")
        require(derived["n_tasks"] == len(derived["tasks"]) == 1720 and {c["task_id"] for c in derived["tasks"]} == set(all_ids), "Derived membership mismatch")
    summary = read(ROOT/"data/viz/summary.json")
    require(summary["n_primary_records"] == 1720 and summary["evaluation_status_counts"] == dict(statuses), "Summary mismatch")
    require(dict(statuses) == dict(ready=661, not_ready=706, ready_with_limitations=193, remote_judge_ready=158, sample_tests_ready=2), "Unexpected readiness delta")
    return dict(active_tracks=43, active_records=1720, active_iol_records=18, no_years_excluded=True, repaired_years=[2017],
        iol_status_counts=dict(Counter(r["evaluation"]["status"] for r in rows)), global_status_counts=dict(statuses),
        official_label_matches=93, matched_unique_emoji=83, unmatched_emoji_descriptions=4, public_original_page_images=2,
        official_score_unknown=True, old_proxy_disabled=True, source_pages_visually_reviewed=7,
        unchanged_iol_rows_and_scorecards=17, other_tracks_unchanged=42, protected_files_unchanged=len(plan["protected_hashes"]),
        archived_generated_files=len(plan["old_tasks"]), historical_results_modified=False, end_to_end_runtime_or_grading_validated=False)


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
    report = dict(operation="iol_2017_emoji_input_and_partial_reference_repair", status="preparing", backup=rel(store.backup), timestamp_utc=store.stamp)
    store.finish(report)
    try:
        for path, value in plan["writes"].items():
            store.save(path, value)
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
        index = plan["writes"]["data/benchmarks/index.json"]
        summary_and_figures(store, index, {t["id"]:read(ROOT/t["benchmark_path"]) for t in index["olympiads"]})
        for path in ("data/README.md", "data/benchmarks/README.md"):
            text = store.raw[store.path(path)].decode("utf-8-sig")
            text = text.replace("(43 tracks, 1,720 records; 705 not_ready)", "(43 tracks, 1,720 records; 706 not_ready)")
            text = text.replace("Current catalog: 43 tracks, 1,720 records, including 705 not_ready.", "At the prior IOL follow-up snapshot: 43 tracks, 1,720 records, including 705 not_ready.")
            text += ("\n## IOL 2017 emoji repair (2026-09-13)\n\nCurrent catalog: 43 tracks, 1,720 records, including 706 not_ready. "
                "IOL remains at 18 years (8 ready, 1 ready_with_limitations, 9 not_ready); no years were excluded. "
                "2017 now has clean public descriptions and two original-page PNGs; judge-only structured references preserve all 93 matches and four unmatched-emoji descriptions. "
                "Its old 100-point generic proxy is disabled, official weights remain unknown, and status is not_ready pending full dictionary/grammar scoring and image-aware runtime validation. "
                f"Original PDFs and historical results are preserved. See `{REPORT}` and `docs/from_zhongzheng/iol-emoji-repair-20260913.md`.\n")
            store.save_text(path, text)
        report["validation"] = verify(plan, report)
        report["new_task_file_hashes"] = {rel(p):sha(p) for layout in ("base", "last_exam") for p in (ROOT/"data"/layout/"tasks"/CID/PID).rglob("*") if p.is_file()}
        report["status"] = "completed_source_repair_partial_reference_and_score_sync"
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
        {"sources": sources, "prepare": prepare, "apply": apply}[mode]()
