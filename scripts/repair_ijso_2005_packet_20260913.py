"""Separate IJSO 2005 practical pages and transcribe printed point allocations.

This does not recover answers, measurements, answer sheets, or an executable
grader. Only the 2005 row and its derived projections are replaced.
"""
from __future__ import annotations

import argparse
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
from scripts.repair_data_catalog import Store, provenance
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard

CID = "ijso_practical"
PID = "ijso_practical_2005_team_practical_2005"
TASK = CID + "/" + PID
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
ORIGINAL = "data/raw/ijso/2005/recovered_20260913/experiment.pdf"
SOURCE_URL = "https://www.ijso.com.br/downloads/provas/2005/2005.pdf"
SOURCE_SHA = "ebba0db4802a4bcc1d3c78d30960c9c6d76e7b7992e4c429bc1a5d6e2b8eb369"
CACHE = "tmp/pdfs/ijso_2005_repair_20260913"
RAW = "data/raw/ijso/2005/separated_20260913"
PUBLIC = RAW + "/input/ijso_2005_experimental.pdf"
DELIVERY = "output/pdf/ijso_2005_experimental.pdf"
RUBRIC = "data/rubrics/ijso_practical_2005_printed_points_v1.json"
SCORECARDS = f"data/rubrics/task_scorecards/{CID}.json"
REPORT = "data/excluded/benchmark_audit_reports/ijso_2005_packet_repair_20260913.json"
MANIFEST = RAW + "/manifest.json"
RULE = f"data/rules/{CID}/evaluation.json"
PAGES = list(range(7, 15))
GENERATED = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
FORBIDDEN = ("TEST COMPETITION", "THEORETICAL EXAMINATION", "data/rubrics/", "recovered_20260913")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def extract_allocations(pages):
    """Extract weights from exact section boundaries, not all booklet numbers."""
    require(len(pages) == 8, "Expected exactly eight experimental pages")
    require("Maximum points for problem is 20" in " ".join(pages[0].split()), "20-point header missing")
    practical = "\n".join(pages[:4])
    expected_parts = {"I-2": [1, 1.5], "I-3": [1, 1.5], "I-4": [0.5],
                      "II-2": [1, 1.5], "II-3": [0.5],
                      "III-3": [1, 1.5], "III-4": [0.5]}
    starts = list(re.finditer(r"(?m)^[ \t]*(I{1,3}-\d+)[ \t]*(?:\n|(?=[A-Za-z]))", practical))
    found, criteria = {}, []
    for i, match in enumerate(starts):
        key = match[1]
        chunk = practical[match.end():starts[i + 1].start() if i + 1 < len(starts) else len(practical)]
        # A following section heading has a subtotal, not an extra task weight.
        chunk = re.split(r"Experiment-I{1,3}\s*:", chunk)[0]
        points = [float(n) for n in re.findall(r"\((\d+(?:\.\d+)?)\s+points?\)", chunk)]
        if not points:
            continue
        require(key not in found, "Duplicate practical item")
        found[key] = points
        source_page = 10 if key.startswith("I-") else 11
        for j, point in enumerate(points):
            component = ("measurements" if j == 0 else "plot") if len(points) == 2 else "conclusion_choice"
            criteria.append(dict(id=key + "." + component, name=key + " " + component,
                max_score=point, source_page=source_page, section=key.split("-")[0],
                description="Printed point allocation only; no marking reference or experimental observations are supplied.",
                requires_original_measurements=True,
                answer_sheet_choices_missing=(component == "conclusion_choice")))
    require(found == expected_parts, f"Practical point map differs: {found}")
    question_text = "\n".join(pages[4:])
    starts = list(re.finditer(r"(?m)^[ \t]*(\d+)\.[ \t]*(?:\n|(?=[A-Za-z]))", question_text))
    require([int(m[1]) for m in starts] == list(range(1, 16)), "Question IDs differ from 1-15")
    for i, match in enumerate(starts):
        number = int(match[1])
        chunk = question_text[match.end():starts[i + 1].start() if i + 1 < len(starts) else len(question_text)]
        points = [float(n) for n in re.findall(r"\((\d+(?:\.\d+)?)\s+points?\)", chunk)]
        expected = 0.75 if number in (1, 2) else 1 if number == 3 else 0.5
        require(points == [expected], f"Question {number} printed points differ: {points}")
        criteria.append(dict(id=f"E-{number}", name=f"Question {number}", max_score=expected,
            source_page=12 if number <= 3 else 13 if number <= 7 else 14 if number <= 12 else 15,
            section="E", description="Printed multiple-choice question weight; official correct option has not been recovered.",
            answer_key_available=False))
    totals = {key: sum(c["max_score"] for c in criteria if c["section"] == key) for key in ("I", "II", "III", "E")}
    require(totals == {"I": 5.5, "II": 3, "III": 3, "E": 8.5}, "Section totals differ")
    require(len(criteria) == 26 and sum(totals.values()) == 20, "Point coverage differs")
    return dict(total_points=20, section_totals=totals, criteria=criteria)


def check_pdf(path):
    with pymupdf.open(ROOT / ORIGINAL) as original, pymupdf.open(path) as public:
        require(len(original) == 24 and len(public) == 8, "Unexpected page count")
        for i, source in enumerate(PAGES):
            require(public[i].get_text() == original[source].get_text(), "Page text changed")
            before = original[source].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
            after = public[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
            require((before.width, before.height, before.samples) == (after.width, after.height, after.samples), "Page pixels changed")
        require(not public.embfile_count() and not public.get_toc(), "Unexpected hidden document content")
        require(not any(list(p.annots()) or p.get_links() or list(p.widgets()) for p in public), "Unexpected document annotations")
        text = "\n".join(p.get_text() for p in public)
        require(not any(x in text for x in FORBIDDEN), "Other-round material in public PDF")
        return extract_allocations([p.get_text() for p in public])


def check_packages(row, directory):
    for layout in ("base", "last_exam"):
        folder = directory / layout / "tasks" / CID / PID / "base/input"
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
        require(actual == GENERATED | {Path(PUBLIC).name}, "Public file allowlist differs")
        require(digest(folder / Path(PUBLIC).name) == row["assets"][0]["sha256"], "Public PDF copy differs")
        for name in GENERATED:
            text = (folder / name).read_text(encoding="utf-8")
            require(not any(x in text for x in FORBIDDEN), "Non-task material exposed")
        require((folder / "problem.md").read_text(encoding="utf-8") == row["problem_description"] + "\n", "Prompt differs")
        cards = read(directory / layout / "task_cards.json")["tasks"]
        selected = [c for c in cards if c["task_id"] == TASK]
        require(len(selected) == 1, "Task card membership differs")
        card = selected[0]
        listing = card["input_files"] if layout == "base" else card["input"]["files"]
        prefix = "input/" if layout == "base" else "base/input/"
        require({f["path"].removeprefix(prefix) for f in listing} == actual, "Card input list differs")
        if layout == "base":
            require(card["evaluation"] == row["evaluation"], "Base evaluation projection differs")
        else:
            ref = read(folder.parent.parent / "eval/reference.json")
            require(ref["evaluation"] == row["evaluation"] and not ref["has_gold_answer"] and not ref["solution_file"], "Hidden reference differs")
    return 2


def prepare():
    store = Store(ROOT)
    require(not (ROOT / REPORT).exists(), "Already applied; use verify")
    require(digest(ROOT / ORIGINAL) == SOURCE_SHA, "Local source changed")
    response = requests.get(SOURCE_URL, timeout=45)
    response.raise_for_status()
    require(hashlib.sha256(response.content).hexdigest() == SOURCE_SHA, "Publisher bytes differ")
    prepared = ROOT / CACHE / "prepared.pdf"
    require(not prepared.exists(), "Prepared PDF already exists")
    prepared.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(ROOT / ORIGINAL) as original:
        require(len(original) == 24, "Unexpected original page count")
        require("TEST COMPETITION" in original[0].get_text() and "THEORETICAL EXAMINATION" in original[15].get_text(), "Round boundaries differ")
        with pymupdf.open() as public:
            public.insert_pdf(original, from_page=7, to_page=14)
            public.set_metadata(dict(title="IJSO 2005 Experimental Examination", subject="Unmodified original booklet pages 8-15; other rounds omitted"))
            public.save(prepared, garbage=4, deflate=True)
    allocations = check_pdf(prepared)
    poppler = ROOT / "data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin"
    # Independently confirm every printed allocation using Poppler extraction.
    independently = subprocess.check_output([str(poppler / "pdftotext.exe"), "-layout", str(prepared), "-"]).decode("utf-8")
    independent_pages = independently.split("\f")
    if not independent_pages[-1].strip():
        independent_pages.pop()
    require(extract_allocations(independent_pages) == allocations, "Independent point extraction differs")
    renders = ROOT / CACHE / "renders"
    renders.mkdir()
    subprocess.run([str(poppler / "pdftoppm.exe"), "-r", "105", "-png", str(prepared), str(renders / "page")], check=True)
    rows = deepcopy(store.read(BENCHMARK))
    matches = [r for r in rows if r["problem_id"] == PID]
    require(len(matches) == 1 and len(rows) == 20, "Unexpected canonical membership")
    row = matches[0]
    before = deepcopy(row)
    limitations = [
        "Only experimental booklet pages 8-15 are contestant input; the complete 24-page archive is preserved outside contestant input.",
        "Printed allocations sum to 20 points (5.5 + 3 + 3 + 8.5). They are not a recovered answer key or a validated grading rubric.",
        "Original measured observations and an edition-specific marking packet remain unavailable; no measurements or correct options are invented.",
        "Separately referenced answer sheets have not been recovered, including the conclusion choices for I-4, II-3 and III-4.",
        "The existing three-agent roster is retained as a benchmark adaptation; historical team equivalence and physical execution are not validated.",
    ]
    basis = "2005 experimental booklet page 8 declares 20 points; pages 10-15 specify 26 weighted components totaling 20. Printed point allocation only, with official marking and observations still unavailable."
    with pymupdf.open(prepared) as public:
        prompt = ("IJSO 2005 experimental examination, 10 December 2005.\n\n"
            "Use only the attached eight-page experimental packet, preserved from original booklet pages 8-15. "
            "Its figures and mathematical layout are authoritative. The printed maximum is 20 points. "
            "Original experimental observations and separately referenced answer sheets are unavailable; "
            "do not fabricate observations or assume missing conclusion choices.\n\n"
            + "\n\n".join(p.get_text() for p in public))
    row.update(source_file=PUBLIC, total_points=20, problem_description=prompt,
        source_visibility="experimental_section_only", source_review=dict(
            original_file=ORIGINAL, source_sha256=SOURCE_SHA, publisher_bytes_verified=True,
            contestant_source_pages=[p + 1 for p in PAGES], other_round_pages=list(range(1, 8)) + list(range(16, 25)),
            manifest_path=MANIFEST, page_content_unmodified=True, point_allocation_verified=True,
            answer_key_recovered=False, observed_data_recovered=False))
    row["assets"] = [dict(path=PUBLIC, mime_type="application/pdf", role="agent_visible", sha256=digest(prepared),
                          source_url=SOURCE_URL, source_pages=list(range(8, 16)))]
    # Keep the mixed-round archive in provenance, not as an active attachment.
    row["evaluation"].update(rubric_path=RUBRIC, score_basis=basis, limitations=limitations,
        scoring_validation_status="printed_weights_only_not_executable_grading", status="not_ready", evaluator_id=None)
    row["evaluation"]["superseded_rubric_reuse"] = row["evaluation"].pop("rubric_reuse")
    row["evaluation"]["source_repair"].update(packet_section_separated=True, point_allocation_verified=True,
        scoring_validated=False, latest_report=REPORT)
    provenance(row)
    row["provenance"]["original_archive"] = dict(path=ORIGINAL, sha256=SOURCE_SHA, visibility="maintainer_only",
        preserved_in_place=True, reason="Complete source booklet includes other competition rounds.")
    rubric = dict(rubric_id="ijso_practical_2005_printed_points_v1", dataset=CID,
        title="IJSO 2005 experiment - printed point allocation, not a recovered marking scheme",
        visibility="judge_only", rubric_type="printed_point_allocation_only", grading_validation_status="not_validated",
        total_points=20, criteria=allocations["criteria"], section_totals=allocations["section_totals"],
        answer_key_available=False, observed_data_available=False, source_file=ORIGINAL,
        source_sha256=SOURCE_SHA, source_url=SOURCE_URL, limitations=limitations,
        not_observable_from_deck=["Original physical measurements and laboratory execution"])
    rules = {k: deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    scoring = rules["evaluation"]["scoring"]
    scoring.setdefault("record_rubric_overrides", {})[PID] = RUBRIC
    scoring.setdefault("record_evaluator_overrides", {})[PID] = None
    scoring.setdefault("record_score_basis_overrides", {})[PID] = dict(max_score=20, basis=basis, status="printed_weights_only_not_ready")
    writes = {BENCHMARK: rows, RUBRIC: rubric, RULE: rules["evaluation"]}
    tracked = list(writes) + [SCORECARDS, "data/benchmarks/index.json"]
    tracked += [f"data/{layout}/{name}.json" for layout in ("base", "last_exam") for name in ("task_cards", "input_asset_manifest")]
    originals = {relative(p): digest(p) for p in (ROOT / "data/raw/ijso").rglob("*") if p.is_file()}
    plan = dict(before_row=before, after_row=row, writes=writes, rules=rules, allocations=allocations,
        expected_hashes={p: digest(ROOT / p) for p in tracked if (ROOT / p).exists()},
        original_hashes=originals, prepared_sha256=digest(prepared), publisher_verified_sha256=SOURCE_SHA)
    store.save(CACHE + "/plan.json", plan)
    print(json.dumps(dict(pages=8, criteria=26, total_points=20, section_totals=allocations["section_totals"],
        unchanged_page_pixels=True, independent_point_extraction_matched=True, prepared_sha256=digest(prepared)), indent=2))


def verify(plan, report):
    for name, sha in {**plan["original_hashes"], **report["preserved_hashes"]}.items():
        require(digest(ROOT / name) == sha, f"Protected file changed: {name}")
    for name, value in plan["writes"].items():
        require(read(ROOT / name) == value, f"Readback differs: {name}")
    row = plan["after_row"]
    for key in ("problem_id", "year", "team_size", "split", "license", "status", "gold_label"):
        require(row[key] == plan["before_row"][key], f"Protected field changed: {key}")
    require(row["evaluation"]["status"] == "not_ready" and row["evaluation"]["evaluator_id"] is None, "Unexpected promotion")
    require(check_pdf(ROOT / PUBLIC) == plan["allocations"], "PDF/point verification differs")
    require(digest(ROOT / PUBLIC) == plan["prepared_sha256"] == digest(ROOT / DELIVERY), "Final PDF differs from reviewed version")
    require(read(ROOT / CACHE / "visual_review.json")["sha256"] == plan["prepared_sha256"], "Visual review hash differs")
    require(row["total_points"] == read(ROOT / RUBRIC)["total_points"] == 20, "Score denominator differs")
    cards = read(ROOT / SCORECARDS)["records"]
    require(next(c for c in cards if c["problem_id"] == PID) == scorecard(row, ROOT), "Scorecard differs")
    require(stable([c for c in cards if c["problem_id"] != PID]) == report["other_scorecards_hash"], "Other scorecards changed")
    for layout in ("base", "last_exam"):
        for filename, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            data = read(ROOT / f"data/{layout}/{filename}")[key]
            require(stable([x for x in data if x["task_id"] != TASK]) == report["other_derived_hashes"][layout + "/" + filename], "Other derived entries changed")
            if key == "tasks":
                require(len(data) == 1727 and len({x["task_id"] for x in data}) == 1727, "Global generated membership differs")
            else:
                ours = [x for x in data if x["task_id"] == TASK]
                require(len(ours) == 1 and ours[0]["sha256"] == plan["prepared_sha256"], "Input manifest differs")
    require(check_packages(row, ROOT / "data") == 2, "Package validation failed")
    rule = read(ROOT / RULE)
    require(read(ROOT / f"data/last_exam/competitions/{CID}/eval/evaluation.json") == rule, "Shared hidden rules differ")
    require(read(ROOT / "data/benchmarks/index.json")["total_records"] == 1727, "Canonical count changed")
    for name, sha in report["replaced_task_hashes"].items():
        require(digest(ROOT / report["backup"] / name) == sha, "Archived task file differs")
    return dict(global_records=1727, changed_records=1, preserved_same_track_records=19,
        preserved_other_tracks=42, original_ijso_files_unchanged=len(plan["original_hashes"]),
        public_pages=8, omitted_other_round_pages=16, page_pixel_differences=0,
        source_anchored_points=20, printed_components=26, readiness_promotions=0,
        answer_key_invented=False, measurements_invented=False, copied_assets_checked=2,
        grading_performed=False)


def apply():
    store = Store(ROOT)
    require(not (ROOT / REPORT).exists(), "Already applied; use verify")
    plan = store.read(CACHE + "/plan.json")
    review = store.read(CACHE + "/visual_review.json")
    require(review["sha256"] == plan["prepared_sha256"] and review["pages_reviewed"] == list(range(1, 9)), "Missing complete visual review")
    for name, sha in {**plan["expected_hashes"], **plan["original_hashes"]}.items():
        require(digest(ROOT / name) == sha, f"File changed during review: {name}")
        if name.endswith(".json") and name in plan["expected_hashes"]:
            store.read(name)
    prepared = ROOT / CACHE / "prepared.pdf"
    require(digest(prepared) == plan["prepared_sha256"], "Prepared PDF changed")
    require(check_pdf(prepared) == plan["allocations"], "Prepared point map changed")
    require(not any((ROOT / p).exists() for p in (PUBLIC, DELIVERY, MANIFEST)), "Output destination occupied")
    index = deepcopy(store.read("data/benchmarks/index.json"))
    track = next(t for t in index["olympiads"] if t["id"] == CID)
    preserved = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    changed = {BENCHMARK, RULE, SCORECARDS, RUBRIC}
    for folder in ("data/rules", "data/rubrics"):
        preserved += [relative(p) for p in (ROOT / folder).rglob("*.json") if relative(p) not in changed]
    replaced = {}
    for layout in ("base", "last_exam"):
        for folder in (ROOT / f"data/{layout}/tasks/{CID}").iterdir():
            for path in folder.rglob("*"):
                if path.is_file():
                    if folder.name == PID:
                        replaced[relative(path)] = digest(path)
                    else:
                        preserved.append(relative(path))
    for path in (ROOT / f"data/last_exam/competitions/{CID}").rglob("*"):
        if path.is_file() and path.parent.name != "eval":
            preserved.append(relative(path))
    cards = deepcopy(store.read(SCORECARDS))
    report = dict(operation="ijso_2005_experimental_packet_and_printed_points_repair", status="preparing",
        backup=relative(store.backup), preserved_hashes={p: digest(ROOT / p) for p in preserved},
        replaced_task_hashes=replaced, other_derived_hashes={},
        other_scorecards_hash=stable([c for c in cards["records"] if c["problem_id"] != PID]),
        visual_review=review, source_pages=list(range(8, 16)), previous_generic_rubric_points=40,
        corrected_edition_printed_points=20, original_archive_preserved_in_place=True)
    catalogs = {}
    for layout in ("base", "last_exam"):
        for filename, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            name = f"data/{layout}/{filename}"
            catalogs[name] = deepcopy(store.read(name))
            report["other_derived_hashes"][layout + "/" + filename] = stable([x for x in catalogs[name][key] if x["task_id"] != TASK])
    store.finish(report)
    try:
        for name in (PUBLIC, DELIVERY):
            target = store.path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(prepared, target)
            store.changes.append(dict(path=name, before_sha256=None, after_sha256=digest(target)))
        stage = store.path(CACHE + "/packages_" + store.stamp)
        build_packages(ROOT, stage, {"olympiads": [track]}, {CID: [plan["after_row"]]}, {CID: plan["rules"]}, store.sha)
        check_packages(plan["after_row"], stage)
        for name, value in plan["writes"].items():
            store.save(name, value)
        cards["records"] = [scorecard(plan["after_row"], ROOT) if c["problem_id"] == PID else c for c in cards["records"]]
        store.save(SCORECARDS, cards)
        index["latest_source_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        store.save(MANIFEST, dict(visibility="maintainer_only", original_file=ORIGINAL, original_sha256=SOURCE_SHA,
            publisher_verified_sha256=SOURCE_SHA, source_url=SOURCE_URL, original_preserved=True,
            contestant_file=PUBLIC, contestant_sha256=plan["prepared_sha256"],
            source_pages=list(range(8, 16)), omitted_other_round_pages=list(range(1, 8)) + list(range(16, 25)),
            page_pixels_unchanged=True, visual_review=review, printed_point_rubric=RUBRIC,
            backup=relative(store.backup), scoring_readiness="not_ready"))
        for layout in ("base", "last_exam"):
            name = f"data/{layout}/tasks/{CID}/{PID}"
            require(store.path(name).is_relative_to(store.path(f"data/{layout}/tasks/{CID}")), "Unsafe task archive target")
            expected_tree = {p: sha for p, sha in replaced.items() if p.startswith(name + "/")}
            actual_tree = {relative(p): digest(p) for p in store.path(name).rglob("*") if p.is_file()}
            require(actual_tree == expected_tree, "Task files changed before recoverable replacement")
            store.archive(name)
            shutil.copytree(stage / layout / "tasks" / CID / PID, store.path(name))
            for filename, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
                name = f"data/{layout}/{filename}"
                fresh = read(stage / layout / filename)[key]
                require(all(x["task_id"] == TASK for x in fresh), "Staged non-target entries")
                old = catalogs[name]
                if key == "tasks":
                    require(len(fresh) == 1, "Unexpected staged card count")
                    old[key] = [fresh[0] if x["task_id"] == TASK else x for x in old[key]]
                else:
                    old[key] = [x for x in old[key] if x["task_id"] != TASK] + fresh
                store.save(name, old)
        for filename in ("evaluation.json", "scoring.md"):
            source = stage / "last_exam/competitions" / CID / "eval" / filename
            store.save_text(f"data/last_exam/competitions/{CID}/eval/{filename}", source.read_text(encoding="utf-8"))
        report["validation"] = verify(plan, report)
        report["status"] = "completed_packet_and_point_repair_readiness_deferred"
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
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"prepare": prepare, "apply": apply}[args.mode]()
