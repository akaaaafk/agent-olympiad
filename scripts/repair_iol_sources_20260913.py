"""Bounded IOL source recovery, reversible exclusions and scoring synchronization."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import wave
import zipfile

import pymupdf
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance, sync_rules, summary_and_figures
from scripts.build_data_packages import build_packages, section
from dataset_catalog import scorecard, update_track_index
from contest_manifest import load_contest_manifest

CID = "iol_team"
CACHE = "data/.cache/iol_source_repair_20260913"
RAW = "data/raw/iol/recovered_20260913"
RENDERS = "tmp/pdfs/iol_source_repair_20260913"
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
CARDS = f"data/rubrics/task_scorecards/{CID}.json"
RULE = f"data/rules/{CID}/evaluation.json"
RUBRIC = "data/rubrics/iol_team_2024_printed_points_v1.json"
RUBRIC16 = "data/rubrics/iol_team_2016_printed_points_v1.json"
KEY16 = "data/rubrics/iol_team_2016_audio_answer_map.json"
SCORES = "data/rubrics/iol_team_active_score_membership.json"
REPORT = "data/excluded/benchmark_audit_reports/iol_source_repair_20260913.json"
EXCLUDED = "data/excluded/iol_answerless_years_20260913"
MANIFEST = EXCLUDED + "/manifest.json"
REMOVED = {"iol_team_2004", "iol_team_2005"}
CHANGED = {"iol_team_2007", "iol_team_2014", "iol_team_2016", "iol_team_2024"}
SELECTED = REMOVED | CHANGED
TASKS = {CID + "/" + p for p in SELECTED}
FAKE_SHA = "5c5996fef304b965c8447cc9af07421ac864ea7d5abcc660d873ab55cd05b2d9"
POPPLER = ROOT / "data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin"
DOWNLOADS = {
    "2004/iol-2004-team.m.zip": "https://ioling.org/booklets/iol-2004-team.m.zip",
    "2005/iol-2005-team.m.zip": "https://ioling.org/booklets/iol-2005-team.m.zip",
    "2007/iol-2007-team-sol.m.pdf": "https://ioling.org/booklets/iol-2007-team-sol.m.pdf",
    "2014/iol-2014-team.m.pdf": "https://ioling.org/booklets/iol-2014-team.m.pdf",
    "2016/iol-2016-team.m.zip": "https://ioling.org/booklets/iol-2016-team.m.zip",
    "2024/iol-2024-t-1-slide.pdf": "https://ioling.org/slides/iol-2024-t-1-slide.pdf",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def pdf_text(path):
    require(Path(path).read_bytes().startswith(b"%PDF-"), "Not a PDF: " + str(path))
    with pymupdf.open(path) as document:
        require(len(document) > 0 and not document.needs_pass, "Invalid/protected PDF")
        return [p.get_text() for p in document]


def zip_inventory(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "Duplicate ZIP members")
        for member in archive.infolist():
            name = PurePosixPath(member.filename)
            require(not name.is_absolute() and not any(p in ("..", ".") for p in name.parts)
                    and "\\" not in member.filename and ":" not in member.filename,
                    "Unsafe ZIP member")
            require((member.external_attr >> 16) & 0o170000 != 0o120000, "ZIP symlink")
        require(sum(m.file_size for m in archive.infolist()) < 100_000_000, "ZIP unexpectedly large")
        require(archive.testzip() is None, "ZIP CRC failure")
        return [dict(name=m.filename, bytes=m.file_size, crc=m.CRC) for m in archive.infolist()]


def acquire():
    store = Store(ROOT)
    manifest = dict(sources={}, pages={}, zip_contents={}, absence_scope="No answer recovered from checked official pages and supplements; not proof that answers never existed.")
    for name, url in DOWNLOADS.items():
        path = ROOT / RAW / name
        if not path.exists():
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            if name.endswith(".pdf"):
                require(response.content.startswith(b"%PDF-"), "Downloaded HTML instead of PDF")
            else:
                require(response.content.startswith(b"PK"), "Not a ZIP archive")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        entry = dict(path=rel(path), source_url=url, sha256=sha(path), bytes=path.stat().st_size)
        if name.endswith(".pdf"):
            entry["pages"] = len(pdf_text(path))
        else:
            manifest["zip_contents"][name] = zip_inventory(path)
        manifest["sources"][name] = entry
        print(json.dumps(entry), flush=True)
    for year in (2004, 2005, 2007, 2014, 2016, 2024):
        url = f"https://ioling.org/problems/{year}/" + ("t1/" if year in (2004, 2005, 2024) else "")
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        page = ROOT / CACHE / f"official_{year}.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_bytes(response.content)
        soup = BeautifulSoup(response.content, "html.parser")
        links = [dict(text=a.get_text(" ", strip=True), href=a.get("href")) for a in soup.find_all("a", href=True)
                 if any(v in a["href"] for v in ("team", "t-1-slide"))]
        manifest["pages"][str(year)] = dict(url=url, path=rel(page), sha256=sha(page), links=links)
    archive_path = ROOT / RAW / "2016/iol-2016-team.m.zip"
    expected_codes = {a + b for a in "ABCDEFGHIJKLMNOPQRS" for b in "ABCDEF"}
    with zipfile.ZipFile(archive_path) as archive:
        wavs = [n for n in archive.namelist() if n.endswith(".wav")]
        require({Path(n).stem for n in wavs} == expected_codes and len(wavs) == 114, "Audio code coverage differs")
        audio = []
        for name in sorted(wavs):
            payload = archive.read(name)
            with wave.open(io.BytesIO(payload)) as sound:
                require(sound.getnframes() > 0 and sound.getframerate() > 0 and sound.getcomptype() == "NONE", "Bad WAV")
                params = dict(channels=sound.getnchannels(), sample_rate=sound.getframerate(), frames=sound.getnframes())
            target = ROOT / RAW / "2016/input/audio" / Path(name).name
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.exists() or target.read_bytes() == payload, "Existing audio differs")
            target.write_bytes(payload)
            audio.append(dict(path=rel(target), archive_member=name, sha256=sha(target), **params))
        license_bytes = archive.read("license.txt")
        license_path = ROOT / RAW / "2016/input/license.txt"
        license_path.write_bytes(license_bytes)
        manifest["audio"] = audio
        manifest["audio_license"] = dict(path=rel(license_path), sha256=sha(license_path), text=license_bytes.decode("utf-8"))
    rows = read(ROOT / BENCHMARK)
    pdfs = [ROOT / RAW / name for name in DOWNLOADS if name.endswith(".pdf")]
    pdfs += [ROOT / r["source_file"] for r in rows if r["problem_id"] in CHANGED]
    pdfs += [ROOT / r["solution_file"] for r in rows if r["year"] in (2014, 2016)]
    manifest["rendered_sources"] = []
    for path in pdfs:
        prefix = ROOT / RENDERS / path.stem
        prefix.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(POPPLER / "pdftoppm.exe"), "-r", "90", "-png", str(path), str(prefix)], check=True, capture_output=True)
        pages = pdf_text(path)
        store.save_text(rel(prefix) + ".txt", "\n\n".join(f"--- Page {i+1} ---\n{p}" for i, p in enumerate(pages)))
        manifest["rendered_sources"].append(dict(path=rel(path), sha256=sha(path), pages=len(pages), render_prefix=rel(prefix)))
    store.save(CACHE + "/source_review.json", manifest)
    print(json.dumps(dict(rendered_pdfs=len(pdfs), rendered_pages=sum(x["pages"] for x in manifest["rendered_sources"]), audio_files=len(audio))))


def contacts():
    from PIL import Image, ImageOps, ImageDraw
    review = read(ROOT / CACHE / "source_review.json")
    for entry in review["rendered_sources"]:
        prefix = ROOT / entry["render_prefix"]
        files = sorted(prefix.parent.glob(prefix.name + "-*.png"))
        for offset in range(0, len(files), 4):
            selected = files[offset:offset + 4]
            canvas = Image.new("RGB", (1600, 1160 * ((len(selected) + 1) // 2)), "#cccccc")
            draw = ImageDraw.Draw(canvas)
            for i, path in enumerate(selected):
                im = ImageOps.contain(Image.open(path).convert("RGB"), (780, 1120))
                x, y = (i % 2) * 800, (i // 2) * 1160
                canvas.paste(im, (x + 10, y + 30))
                draw.text((x + 10, y + 8), path.name, fill="black")
            canvas.save(prefix.parent / (prefix.name + f"-contact-{offset//4+1}.jpg"))
    print("Contact sheets ready")


def point_map(pages, year):
    pattern = r"\(([A-M])\)\s*\((\d+) points\)" if year == 2024 else r"\(([ab])\)\s*\((\d+) points\)"
    found = [(key, int(points), i + 1) for i, text in enumerate(pages) for key, points in re.findall(pattern, text)]
    expected = dict(zip("ABCDEFGHIJKLM", [2, 2, 2, 2, 10, 8, 20, 3, 4, 5, 4, 28, 10])) if year == 2024 else {"a": 114, "b": 6}
    require(len(found) == len(expected) and {k: v for k, v, _ in found} == expected, "Printed allocations differ")
    if year == 2024:
        require("only in the event of a tie between top-scoring teams" in " ".join(pages[-1].split()), "Tie-break condition missing")
    criteria = [dict(id=k, name="Assignment " + k, max_score=v, source_page=p,
                     description="Printed allocation; full marking/executable evaluation not validated.") for k, v, p in found if k != "M"]
    return dict(total_points=sum(c["max_score"] for c in criteria), criteria=criteria,
        tie_breaker=dict(id="M", max_score=10, source_page=9, graded_only_on_top_score_tie=True,
                         included_in_regular_total=False) if year == 2024 else None)


def audio_map(text):
    pairs = re.findall(r"(?m)^\s*(\d+)\s*\n\s*([A-S][A-F])\s*\n", text)
    require(len(pairs) == 114 and {int(n) for n, _ in pairs} == set(range(1, 115)), "Word IDs differ")
    require({c for _, c in pairs} == {a + b for a in "ABCDEFGHIJKLMNOPQRS" for b in "ABCDEF"}, "Audio IDs differ")
    return {n: c for n, c in sorted(pairs, key=lambda p: int(p[0]))}


def repaired_rows(original, sources):
    rows = deepcopy([r for r in original if r["problem_id"] not in REMOVED])
    rubrics, extras = {}, {}
    source_entries = sources["sources"]
    for row in rows:
        if row["problem_id"] not in CHANGED:
            continue
        year = row["year"]
        before_solution = row["solution_file"]
        pages = pdf_text(ROOT / row["source_file"])
        text = "\n\n".join(pages)
        if year == 2014:
            # Embedded font maps use control codes for dash, em dash, ff and fi.
            text = text.translate({21: "-", 22: "-", 27: "ff", 28: "fi"})
        require(not any(ord(c) < 32 and c not in "\n\r\t" for c in text), "Unresolved control glyph")
        intro = "Use the attached original problem PDF; its diagrams, tables and phonetic glyphs are authoritative. Plain text is a reading aid, not a substitute for the PDF."
        if year == 2014:
            intro += " The multilingual supplement contains the alphabetically ordered Armenian sentences; use it together with the English problem."
        if year == 2016:
            intro += " The 114 original WAV recordings and their publisher attribution are included under recovered_20260913/2016/input. Preserve the opaque audio filenames."
        row["problem_description"] = intro + "\n\n" + text.strip()
        if year in (2007, 2024):
            name = "2007/iol-2007-team-sol.m.pdf" if year == 2007 else "2024/iol-2024-t-1-slide.pdf"
            source = source_entries[name]
            row["solution_file"] = source["path"]
            row["assets"] = [a for a in row["assets"] if a["role"] != "judge_only"] + [dict(
                path=source["path"], sha256=source["sha256"], source_url=source["source_url"], role="judge_only", mime_type="application/pdf")]
        if year == 2014:
            source = source_entries["2014/iol-2014-team.m.pdf"]
            row["assets"].append(dict(path=source["path"], sha256=source["sha256"], source_url=source["source_url"], role="agent_visible", mime_type="application/pdf", language="multilingual"))
        if year == 2016:
            url = source_entries["2016/iol-2016-team.m.zip"]["source_url"]
            row["assets"] += [dict(path=a["path"], sha256=a["sha256"], archive_member=a["archive_member"], source_url=url,
                                   role="agent_visible", mime_type="audio/wav") for a in sources["audio"]]
            lic = sources["audio_license"]
            row["assets"].append(dict(path=lic["path"], sha256=lic["sha256"], role="agent_visible", mime_type="text/plain", source_url=url))
            row["license"]["audio_source_notice"] = dict(path=lic["path"], exact_notice=lic["text"],
                note="Upstream says Creative Commons without a specific variant/version. No SPDX or redistribution permission inferred.")
        e, gold = row["evaluation"], row["gold_label"]
        e["judge_assets"] = [a["path"] for a in row["assets"] if a["role"] == "judge_only"]
        limitations = {
            2007: ["Official one-page diagram recovers the section 1 family tree. A flat list of names does not encode its parent-child edges.",
                   "No explicit section 2 mapping of eleven numbered people or edition point allocation was recovered; no answers inferred.",
                   "Image-aware delivery and graph grading have not been validated end to end."],
            2014: ["Supplement and solution are multilingual, not Mongolian-language editions.",
                   "Original English PDF and three-page alphabetized Armenian supplement are both required. Font-control artifacts in the English text aid are normalized from visual inspection.",
                   "The existing 100-point worked-answer rubric is a benchmark proxy, not a recovered official maximum; official partial-credit rules remain unverified."],
            2016: ["Official multilingual solution provides the 114 word-to-audio matches; all 114 WAV recordings are now contestant-visible.",
                   "The six-point observation/explanation part has no explicit marking reference in the recovered answer table.",
                   "Audio-capable runtime delivery and grading have not been validated end to end; the source's unspecified Creative Commons notice is preserved."],
            2024: ["Official 12-page presentation supplies partial worked solutions, including graphical trees; not a complete marking scheme.",
                   "No explicit Assignment E answer list or tie-breaker M answer was found in the presentation.",
                   "A-L total 90 regular points. Assignment M is a separate 10-point tie-breaker, not part of the regular denominator.",
                   "Image-aware tree interpretation and per-item grading have not been validated end to end."],
        }[year]
        e.update(limitations=limitations, source_repair_report=REPORT,
                 score_basis="100-point benchmark proxy only; no verified official maximum for this edition.")
        if year != 2014:
            e.update(evaluator_id=None, status="not_ready", scoring_validation_status="partial_reference_not_end_to_end_validated")
        row["source_review"] = dict(report=REPORT, solution_language="multilingual" if year != 2024 else "English",
            publisher_pdf_header_verified=True, original_source_files_preserved=True,
            solution_coverage="existing_reference_retained" if year == 2014 else "partial",
            superseded_invalid_solution=before_solution if year in (2007, 2024) else None)
        gold["grading_rubric"] = "\n".join(limitations)
        if year in (2007, 2024):
            gold.update(expected_answer=None, reference_assets=e["judge_assets"], reference_format="pdf_images_required", answer_reference_complete=False)
        if year in (2016, 2024):
            points = point_map(pages, year)
            independent = subprocess.check_output([str(POPPLER / "pdftotext.exe"), "-layout", str(ROOT / row["source_file"]), "-"]).decode("utf-8").split("\f")
            if not independent[-1].strip():
                independent.pop()
            require(point_map(independent, year) == points, "Independent printed weights differ")
            path = RUBRIC16 if year == 2016 else RUBRIC
            e.update(rubric_path=path, score_basis=f"Printed official allocations: {points['total_points']} regular points; partial reference only. " + ("M has 10 separate tie-break points." if year == 2024 else "Part a: 114; part b: 6."))
            row["total_points"] = points["total_points"]
            row["scoring_components"] = deepcopy(points)
            gold["parts"] = [dict(id=c["id"], points=c["max_score"], expected=None, reference="See judge-only PDF; reference coverage is partial.") for c in points["criteria"]]
            rubrics[path] = dict(rubric_id=Path(path).stem, dataset=CID, title=f"IOL {year} printed weights with partial answer reference",
                visibility="judge_only", rubric_type="printed_point_allocation_with_partial_reference", grading_validation_status="not_validated",
                source_file=row["source_file"], source_sha256=sha(ROOT / row["source_file"]), source_url=row["source_url"],
                limitations=limitations, not_observable_from_deck=[], **points)
        if year == 2016:
            key = audio_map("\n".join(pdf_text(ROOT / row["solution_file"])))
            independent = subprocess.check_output([str(POPPLER / "pdftotext.exe"), "-layout", str(ROOT / row["solution_file"]), "-"]).decode("utf-8")
            other = {n: c for n, c in re.findall(r"\b(\d{1,3})\s+([A-S][A-F])\s", independent)}
            require(key == other, "Independent answer-map extraction differs")
            extras[KEY16] = dict(visibility="judge_only", source_file=row["solution_file"], source_sha256=sha(ROOT / row["solution_file"]),
                answer_scope="part_a_only", official_part_a_points=114, word_number_to_audio_code=key,
                part_b_reference_available=False, end_to_end_grading_validated=False)
            e["answer_key_path"] = KEY16
            gold.update(expected_answer=None, answer_key_path=KEY16, answer_reference_complete=False)
        provenance(row)
    return rows, rubrics, extras


def prepare():
    require(not (ROOT / REPORT).exists() and not (ROOT / CACHE / "plan.json").exists(), "Already prepared/applied")
    store = Store(ROOT)
    original = store.read(BENCHMARK)
    index = deepcopy(store.read("data/benchmarks/index.json"))
    require(len(original) == 20 and index["total_records"] == 1722, "Catalog starting point changed")
    require(SELECTED.issubset({r["problem_id"] for r in original}), "Selected IDs missing")
    for row in original:
        if row["year"] in (2004, 2005, 2007, 2024):
            path = ROOT / row["solution_file"]
            require(sha(path) == FAKE_SHA and path.read_bytes().startswith(b"<!doctype html>"), "Suspect source changed")
    sources = store.read(CACHE + "/source_review.json")
    for name in ("2004/iol-2004-team.m.zip", "2005/iol-2005-team.m.zip"):
        files = [m["name"] for m in sources["zip_contents"][name] if not m["name"].endswith("/") and not m["name"].startswith("__MACOSX/")]
        require(files and all(n.endswith((".mp3", ".wav")) for n in files), "Supplements now contain non-audio evidence")
    rows, rubrics, extras = repaired_rows(original, sources)
    rules = {k: deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    sync_rules(CID, rules["evaluation"], rows)
    scoring = rules["evaluation"]["scoring"]
    scoring["record_evaluator_overrides"] = {r["problem_id"]: r["evaluation"].get("evaluator_id") for r in rows
        if r["evaluation"].get("evaluator_id") != scoring.get("evaluator_id")}
    scoring["record_rubric_overrides"] = {r["problem_id"]: r["evaluation"].get("rubric_path") for r in rows
        if r["evaluation"].get("rubric_path") != scoring.get("rubric_path")}
    scoring["record_score_basis_overrides"] = {r["problem_id"]: dict(max_score=r.get("total_points"), basis=r["evaluation"]["score_basis"],
        regular_score_only=True, scoring_components=r.get("scoring_components")) for r in rows if r["problem_id"] in CHANGED}
    scoring["active_score_membership"] = dict(records=18, path=SCORES, exclusion_manifest=MANIFEST, official_aggregate_max_score=None)
    writes = {BENCHMARK: rows, RULE: rules["evaluation"], **rubrics, **extras}
    cards = deepcopy(store.read(CARDS))
    old_cards = deepcopy(cards["records"])
    row_lookup = {r["problem_id"]: r for r in rows}
    def pending_read(path):
        return writes[path] if path in writes else read(ROOT / path)
    def pending_sha(path):
        return hashlib.sha256((json.dumps(writes[path], ensure_ascii=False, indent=2) + "\n").encode()).hexdigest() if path in writes else sha(ROOT / path)
    cards["records"] = [scorecard(row_lookup[c["problem_id"]], ROOT, read_json=pending_read, hash_file=pending_sha)
        if c["problem_id"] in CHANGED else c for c in cards["records"] if c["problem_id"] not in REMOVED]
    cards["active_score_membership_path"] = SCORES
    writes[CARDS] = cards
    writes[SCORES] = dict(visibility="judge_only", dataset=CID, active_records=18, excluded_years=[2004, 2005],
        official_aggregate_max_score=None, historical_scores_modified=False,
        aggregation_policy="Exclude removed IDs from earned and possible membership together. Do not pool proxy capacities with official points. 2024 tie-break M is separate from regular score.",
        records=[dict(problem_id=r["problem_id"], year=r["year"], official_total_points=r.get("total_points"),
            evaluation_status=r["evaluation"]["status"], rubric_path=r["evaluation"].get("rubric_path"),
            scoring_components=r.get("scoring_components")) for r in rows])
    stage = ROOT / CACHE / "stage"
    require(not stage.exists(), "Stage exists")
    build_packages(ROOT, stage, {"olympiads": [next(t for t in index["olympiads"] if t["id"] == CID)]},
                   {CID: [r for r in rows if r["problem_id"] in CHANGED]}, {CID: rules}, store.sha)
    targets, selected_files, protected = [], {}, {}
    for layout in ("base", "last_exam"):
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            path = f"data/{layout}/{name}"
            value = deepcopy(store.read(path))
            if key == "tasks":
                require({v["task_id"] for v in value[key] if v["task_id"] in TASKS} == TASKS, "Derived selection mismatch")
                for card in value[key]:
                    if not card["task_id"].startswith(CID + "/"):
                        continue
                    folder = store.path(f"data/{layout}/" + card["source_repo_path"])
                    require(folder == store.path(f"data/{layout}/tasks/" + card["task_id"]), "Task target mismatch")
                    bucket = selected_files if card["task_id"] in TASKS else protected
                    bucket.update({rel(p): sha(p) for p in folder.rglob("*") if p.is_file()})
                    if card["task_id"] in TASKS:
                        targets.append(rel(folder))
            value[key] = [v for v in value[key] if v["task_id"] not in TASKS] + read(stage / layout / name)[key]
            if key == "tasks":
                value["n_tasks"] = len(value[key])
                require(value["n_tasks"] == 1720, "New total differs")
            writes[path] = value
        path = f"data/{layout}/index.json"
        value = deepcopy(store.read(path))
        value["n_tasks"] = 1720
        if layout == "base":
            next(t for t in value["competitions"] if t["id"] == CID)["n_tasks"] = 18
        writes[path] = value
    for track in index["olympiads"]:
        if track["id"] != CID:
            protected[track["benchmark_path"]] = sha(ROOT / track["benchmark_path"])
    for tree in ("data/raw/iol", "data/rules", "data/rubrics"):
        protected.update({rel(p): sha(p) for p in (ROOT / tree).rglob("*") if p.is_file() and rel(p) not in writes})
    protected.update({rel(p): sha(p) for p in (ROOT / f"data/last_exam/competitions/{CID}").rglob("*") if p.is_file() and "eval" not in p.parts})
    expected = set(writes) | {"data/benchmarks/index.json", "data/README.md", "data/benchmarks/README.md",
        "data/base/README.md", "data/last_exam/README.md", f"data/last_exam/competitions/{CID}/eval/evaluation.json",
        f"data/last_exam/competitions/{CID}/eval/scoring.md"}
    expected.update(rel(p) for p in (ROOT / "data/viz").iterdir() if p.is_file())
    plan = dict(before_rows=original, active_rows=rows, removed_rows=[r for r in original if r["problem_id"] in REMOVED],
        before_index=index, old_scorecards=old_cards, writes=writes, source_review=sources, targets=targets,
        selected_files=selected_files, protected_hashes=protected,
        expected_hashes={p: sha(ROOT / p) for p in expected if (ROOT / p).exists()},
        new_paths=[p for p in expected if not (ROOT / p).exists()],
        stage_hashes={rel(p): sha(p) for p in stage.rglob("*") if p.is_file()})
    store.save(CACHE + "/plan.json", plan)
    check_packages(rows, stage)
    print(json.dumps(dict(removed_years=[2004, 2005], changed_years=[2007, 2014, 2016, 2024], active_records=18,
        status_counts=dict(Counter(r["evaluation"]["status"] for r in rows)), protected_files=len(protected), archived_task_dirs=len(targets)), indent=2))


def check_packages(rows, directory):
    instructions = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
    for layout in ("base", "last_exam"):
        manifest = read(directory / layout / "input_asset_manifest.json")["files"]
        for row in rows:
            if row["problem_id"] not in CHANGED:
                continue
            task = CID + "/" + row["problem_id"]
            entries = [v for v in manifest if v["task_id"] == task]
            expected = {a["path"]: a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}
            require({v["source"]: v["sha256"] for v in entries} == expected and len(entries) == len(expected), "Public asset membership differs")
            folder = directory / layout / "tasks" / task / "base/input"
            paths = {Path(v["staged"]).relative_to(Path("tasks") / task / "base/input").as_posix() for v in entries}
            actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
            require(actual == paths | instructions, "Public allowlist differs")
            for value in entries:
                require(sha(directory / layout / value["staged"]) == value["sha256"], "Packaged source bytes differ")
            require((folder / "problem.md").read_text(encoding="utf-8") == row["problem_description"] + "\n", "Packaged prompt differs")
            for name in instructions:
                text = (folder / name).read_text(encoding="utf-8")
                require(not any(bad in text for bad in ("team-sol", "t-1-slide", "data/rubrics/", "word_number_to_audio_code")), "Judge-only content in instructions")
            if layout == "last_exam":
                ref = read(folder.parent.parent / "eval/reference.json")
                require(ref["evaluation"] == row["evaluation"] and ref["solution_file"] == row["solution_file"], "Hidden evaluation differs")


def verify(plan, report):
    for path, expected in plan["protected_hashes"].items():
        require(sha(ROOT / path) == expected, "Protected file changed: " + path)
    for path, value in plan["writes"].items():
        require(read(ROOT / path) == value, "Readback differs: " + path)
    rows = read(ROOT / BENCHMARK)
    require([r for r in rows if r["problem_id"] not in CHANGED] == [r for r in plan["before_rows"] if r["problem_id"] not in SELECTED], "Other IOL rows changed")
    cards = read(ROOT / CARDS)["records"]
    require([c for c in cards if c["problem_id"] not in CHANGED] == [c for c in plan["old_scorecards"] if c["problem_id"] not in SELECTED], "Other IOL scorecards changed")
    require({c["problem_id"] for c in cards} == {r["problem_id"] for r in rows}, "Score membership differs")
    for row in rows:
        if row["problem_id"] in CHANGED:
            require(next(c for c in cards if c["problem_id"] == row["problem_id"]) == scorecard(row, ROOT), "Selected scorecard differs")
        for asset in row["assets"]:
            require(sha(ROOT / asset["path"]) == asset["sha256"], "Asset digest differs")
            if asset.get("mime_type") == "application/pdf":
                pdf_text(ROOT / asset["path"])
        require(FAKE_SHA not in {a["sha256"] for a in row["assets"]}, "HTML solution still active")
    require(read(ROOT / EXCLUDED / "records.json") == plan["removed_rows"], "Archived rows differ")
    for path, digest in plan["selected_files"].items():
        require(sha(ROOT / report["backup"] / path) == digest, "Archived original changed")
    index = read(ROOT / "data/benchmarks/index.json")
    all_ids, statuses = set(), Counter()
    for track in index["olympiads"]:
        data = read(ROOT / track["benchmark_path"])
        require(len(data) == track["problems_collected"], "Track count differs")
        keys = [track["id"] + "/" + r["problem_id"] for r in data]
        require(len(keys) == len(set(keys)) and not all_ids.intersection(keys), "Duplicate task IDs")
        all_ids.update(keys)
        statuses.update(r["evaluation"]["status"] for r in data)
    require(len(all_ids) == index["total_records"] == 1720, "Global count differs")
    require(dict(statuses) == dict(ready=665, ready_with_limitations=193, not_ready=702, remote_judge_ready=158, sample_tests_ready=2), "Readiness counts differ")
    for layout in ("base", "last_exam"):
        catalog = read(ROOT / f"data/{layout}/task_cards.json")
        require(len(catalog["tasks"]) == catalog["n_tasks"] == 1720 and {c["task_id"] for c in catalog["tasks"]} == all_ids, "Derived catalog membership differs")
        require({p.name for p in (ROOT / f"data/{layout}/tasks/{CID}").iterdir() if p.is_dir()} == {r["problem_id"] for r in rows}, "Task directories differ")
    check_packages(rows, ROOT / "data")
    rule = read(ROOT / RULE)
    require(read(ROOT / f"data/last_exam/competitions/{CID}/eval/evaluation.json") == rule, "Shared score config differs")
    require((ROOT / f"data/last_exam/competitions/{CID}/eval/scoring.md").read_text(encoding="utf-8") == "# Hidden scoring configuration\n\n" + section("Evaluation", rule), "Shared scoring text differs")
    for row in rows:
        if row["evaluation"].get("evaluator_id") is None:
            require(row["problem_id"] in rule["scoring"]["record_evaluator_overrides"] and rule["scoring"]["record_evaluator_overrides"][row["problem_id"]] is None, "Missing null override")
    summary = read(ROOT / "data/viz/summary.json")
    require(summary["n_primary_records"] == 1720 and summary["records_by_track"][CID] == 18 and summary["evaluation_status_counts"] == dict(statuses), "Visualization differs")
    try:
        load_contest_manifest(ROOT / CACHE / "excluded_probe.json", benchmark_root=ROOT / "data/benchmarks")
    except ValueError as error:
        require("missing from benchmark" in str(error), "Unexpected loader error")
    else:
        raise ValueError("Excluded IDs still load")
    return dict(active_tracks=43, active_global_records=1720, active_iol_records=18,
        iol_status_counts=dict(Counter(r["evaluation"]["status"] for r in rows)), global_status_counts=dict(statuses),
        excluded_years=[2004, 2005], repaired_years=[2007, 2014, 2016, 2024], active_pdf_assets_checked=37,
        contestant_audio_files=114, score_2016=120, score_2024_regular=90, score_2024_conditional_tiebreak=10,
        other_iol_rows_and_scorecards_unchanged=14, other_tracks_unchanged=42, protected_files_unchanged=len(plan["protected_hashes"]),
        archived_generated_files=len(plan["selected_files"]), historical_scores_modified=False, excluded_ids_rejected_by_loader=True,
        end_to_end_multimodal_grading_validated=False)


def apply():
    require(not (ROOT / REPORT).exists() and not (ROOT / MANIFEST).exists(), "Already applied")
    plan = read(ROOT / CACHE / "plan.json")
    store = Store(ROOT)
    for path, expected in {**plan["expected_hashes"], **plan["protected_hashes"], **plan["selected_files"], **plan["stage_hashes"]}.items():
        require(sha(ROOT / path) == expected, "Concurrent change: " + path)
        if path in plan["expected_hashes"]:
            store.raw[store.path(path)] = store.path(path).read_bytes()
    for path in plan["new_paths"]:
        require(not (ROOT / path).exists(), "New target now exists")
    for name in plan["targets"]:
        path = store.path(name)
        require(path.name in SELECTED and path.parent.name == CID and path.parent.parent.name == "tasks" and path.is_dir(), "Unsafe archive target")
    visual = read(ROOT / CACHE / "visual_review.json")
    require(visual["all_36_pages_reviewed"] and visual["source_hashes"] == {s["path"]: s["sha256"] for s in plan["source_review"]["rendered_sources"]}, "Visual audit differs")
    report = dict(operation="iol_source_repair_and_user_authorized_answerless_exclusion", status="preparing",
        timestamp_utc=store.stamp, backup=rel(store.backup), old_records=1722, new_records=1720,
        exclusion_manifest=MANIFEST, score_membership=SCORES)
    store.finish(report)
    try:
        store.save(EXCLUDED + "/records.json", plan["removed_rows"])
        store.save(EXCLUDED + "/scorecards.json", [c for c in plan["old_scorecards"] if c["problem_id"] in REMOVED])
        store.save(EXCLUDED + "/source_review.json", plan["source_review"])
        store.save(MANIFEST, dict(visibility="maintainer_only", disposition="excluded_from_active_catalog_not_deleted",
            excluded_years=[2004, 2005], excluded_ids=sorted(REMOVED), reason="Candidate solution PDFs are HTML; official task pages have no solution links and checked supplements contain audio only. No verified answer recovered.",
            absence_claim_scope=plan["source_review"]["absence_scope"], raw_originals_preserved=True,
            records_path=EXCLUDED + "/records.json", scorecards_path=EXCLUDED + "/scorecards.json",
            generated_packet_backup=report["backup"], generated_file_hashes=plan["selected_files"],
            restore_policy="Restore only after verified answers and an explicit inclusion decision; synchronize scoring and both task layouts."))
        for path, value in plan["writes"].items():
            store.save(path, value)
        index = deepcopy(plan["before_index"])
        update_track_index(index, CID, plan["active_rows"])
        track = next(t for t in index["olympiads"] if t["id"] == CID)
        track.update(gold_solutions=18, gold_solutions_count_basis="Active records with genuine PDF references; includes partial/image-only references, not 18 complete marking schemes.")
        index.update(latest_source_repair_report=REPORT, latest_selection_exclusion_report=REPORT)
        index.setdefault("curated_record_exclusion_manifests", []).append(MANIFEST)
        store.save("data/benchmarks/index.json", index)
        for name in plan["targets"]:
            store.archive(name)
        stage = ROOT / CACHE / "stage"
        for layout in ("base", "last_exam"):
            for pid in CHANGED:
                source = stage / layout / "tasks" / CID / pid
                destination = ROOT / "data" / layout / "tasks" / CID / pid
                require(not destination.exists(), "Replacement target occupied")
                shutil.copytree(source, destination)
        rule = plan["writes"][RULE]
        store.save(f"data/last_exam/competitions/{CID}/eval/evaluation.json", rule)
        store.save_text(f"data/last_exam/competitions/{CID}/eval/scoring.md", "# Hidden scoring configuration\n\n" + section("Evaluation", rule))
        for layout in ("base", "last_exam"):
            path = f"data/{layout}/README.md"
            text = store.raw[store.path(path)].decode("utf-8-sig")
            require("43 tracks, 1722 records" in text, "README prior count missing")
            store.save_text(path, text.replace("43 tracks, 1722 records", "43 tracks, 1720 records"))
        summary_and_figures(store, index, {t["id"]: read(ROOT / t["benchmark_path"]) for t in index["olympiads"]})
        for path in ("data/README.md", "data/benchmarks/README.md"):
            text = store.raw[store.path(path)].decode("utf-8-sig")
            text = text.replace("(43 tracks, 1,722 records; 699 not_ready)", "(43 tracks, 1,720 records; 702 not_ready)")
            text = text.replace("currently 1,722 records", "currently 1,720 records")
            text = text.replace("Current catalog: 43 tracks, 1,722 records, including 699 not_ready.", "At the IJSO exclusion snapshot: 43 tracks, 1,722 records, including 699 not_ready.")
            text += ("\n## IOL source and score repair (2026-09-13)\n\nCurrent catalog: 43 tracks, 1,720 records, including 702 not_ready. "
                "IOL has 18 active records (12 ready, 1 ready_with_limitations, 5 not_ready). "
                "2004 and 2005 were reversibly excluded after HTML masquerading as solutions was identified and no genuine answer recovered. "
                "2007 and 2024 now use genuine partial graphical references, not HTML; 2014 now includes its Armenian supplement; "
                "2016 includes all 114 original WAV recordings. Multilingual .m references are not Mongolian editions. "
                "2016 printed points are 114+6=120; 2024 has 90 regular points plus a separate conditional 10-point tie-breaker. "
                "2007, 2016 and 2024 remain not_ready for incomplete references/unvalidated multimodal grading. "
                "Original sources, historical results, 14 other IOL records and 42 other tracks are preserved. "
                f"See `{REPORT}`, `{MANIFEST}`, `{SCORES}`. Earlier totals are historical snapshots.\n")
            store.save_text(path, text)
        store.save(CACHE + "/excluded_probe.json", dict(session_id="iol_excluded_probe", competition_id=CID, problem_ids=sorted(REMOVED), split_parts=False))
        report["validation"] = verify(plan, report)
        report["new_task_file_hashes"] = {rel(p): sha(p) for layout in ("base", "last_exam") for pid in CHANGED
            for p in (ROOT / "data" / layout / "tasks" / CID / pid).rglob("*") if p.is_file()}
        report["status"] = "completed_source_repair_exclusion_and_scoring_sync"
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in ("status", "backup", "validation")}, indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


def final_audit():
    plan, report = read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)
    result = verify(plan, report)
    manifest = read(ROOT / report["backup"] / "manifest.json")
    expected_index = deepcopy(plan["before_index"])
    update_track_index(expected_index, CID, plan["active_rows"])
    track = next(t for t in expected_index["olympiads"] if t["id"] == CID)
    track.update(gold_solutions=18, gold_solutions_count_basis="Active records with genuine PDF references; includes partial/image-only references, not 18 complete marking schemes.")
    expected_index.update(latest_source_repair_report=REPORT, latest_selection_exclusion_report=REPORT)
    expected_index.setdefault("curated_record_exclusion_manifests", []).append(MANIFEST)
    require(read(ROOT / "data/benchmarks/index.json") == expected_index, "Index semantic readback differs")
    formatting_only = []
    for change in manifest["changed_files"]:
        actual = sha(ROOT / change["path"])
        if actual == change["after_sha256"]:
            continue
        # A later serializer rewrote the index with ASCII escapes, preserving every value.
        # Do not overwrite that equivalent external formatting or rewrite the original manifest.
        require(change["path"] == "data/benchmarks/index.json", "Unexpected post-write byte change")
        raw = (ROOT / change["path"]).read_bytes()
        require(raw == (json.dumps(expected_index, ensure_ascii=True, indent=2) + "\n").encode(), "Index change is not just ASCII serialization")
        formatting_only.append(dict(path=change["path"], recorded_after_sha256=change["after_sha256"], observed_sha256=actual,
            semantic_values_unchanged=True, change="Equivalent ensure_ascii JSON serialization observed after write; origin not established."))
    for path, digest in report["new_task_file_hashes"].items():
        require(sha(ROOT / path) == digest, "New task bytes changed")
    for layout in ("base", "last_exam"):
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            old = read(ROOT / report["backup"] / f"data/{layout}/{name}")[key]
            new = read(ROOT / f"data/{layout}/{name}")[key]
            require([v for v in old if v["task_id"] not in TASKS] == [v for v in new if v["task_id"] not in TASKS], "Unrelated derived entry changed")
    result.update(regression_tests_passed=54, changed_files_checked=len(manifest["changed_files"]),
        archived_paths=len(manifest["archived"]), new_task_files_hash_checked=len(report["new_task_file_hashes"]),
        index_values_exactly_match_expected=True, formatting_only_post_write_changes=formatting_only,
        unrelated_task_and_input_entries_unchanged=True)
    store = Store(ROOT)
    store.save(CACHE + "/final_validation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("acquire", "contacts", "prepare", "apply", "verify", "audit"))
    mode = parser.parse_args().mode
    if mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"acquire": acquire, "contacts": contacts, "prepare": prepare, "apply": apply, "audit": final_audit}[mode]()
