"""IOL 2011 staged disclosure, 2019 videos and 2022 printed scoring repair."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

import pymupdf
import requests
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance, summary_and_figures
from scripts.build_data_packages import build_packages, section
from scripts.repair_iol_sources_20260913 import read, sha, rel, stable, require, pdf_text, zip_inventory, POPPLER
from dataset_catalog import scorecard, update_track_index

CID = "iol_team"
YEARS = {2011, 2019, 2022}
IDS = {f"iol_team_{y}" for y in YEARS}
TASKS = {CID + "/" + p for p in IDS}
CACHE = "data/.cache/iol_followup_20260913"
RAW = "data/raw/iol/followup_20260913"
RENDER = "tmp/pdfs/iol_followup_20260913"
BENCHMARK = "data/benchmarks/iol_team/benchmark.json"
CARDS = "data/rubrics/task_scorecards/iol_team.json"
RULE = "data/rules/iol_team/evaluation.json"
SCORES = "data/rubrics/iol_team_active_score_membership.json"
RUBRIC = "data/rubrics/iol_team_2022_printed_points_v1.json"
RELEASE = RAW + "/2011/release_manifest.json"
REPORT = "data/benchmarks/iol_followup_repair_20260913.json"
VIDEO_URL = "https://ioling.org/booklets/iol-2019-team.m.zip"
VIDEO_ZIP = RAW + "/2019/iol-2019-team.m.zip"
INITIAL = RAW + "/2011/input/iol_2011_initial.pdf"
FORBIDDEN = ["Distribute at 30 minutes", "Distribute at 60 minutes", "Distribute at 90 minutes",
             "Distribute at 120 minutes", "Distribute at 150 minutes", "One of the deleted words is jarau",
             "A syllable is guru if and only if", "Each line describes the metre"]


def render_sources():
    store = Store(ROOT)
    rows = [r for r in read(ROOT / BENCHMARK) if r["year"] in YEARS]
    entries = []
    for row in rows:
        for key in ("source_file", "solution_file"):
            path = ROOT / row[key]
            pages = pdf_text(path)
            prefix = ROOT / RENDER / path.stem
            prefix.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(POPPLER / "pdftoppm.exe"), "-r", "100", "-png", str(path), str(prefix)], check=True, capture_output=True)
            store.save_text(rel(prefix) + ".txt", "\n\n".join(f"--- Page {i+1} ---\n{p}" for i, p in enumerate(pages)))
            files = sorted(prefix.parent.glob(prefix.name + "-*.png"))
            for offset in range(0, len(files), 4):
                selected = files[offset:offset+4]
                canvas = Image.new("RGB", (1700, 1240 * ((len(selected)+1)//2)), "#dddddd")
                draw = ImageDraw.Draw(canvas)
                for i, file in enumerate(selected):
                    image = ImageOps.contain(Image.open(file).convert("RGB"), (825, 1200))
                    x, y = (i%2)*850, (i//2)*1240
                    canvas.paste(image, (x+10, y+30))
                    draw.text((x+10,y+8), file.name, fill="black")
                canvas.save(prefix.parent / (prefix.name + f"-contact-{offset//4+1}.jpg"))
            entries.append(dict(path=row[key], sha256=sha(path), pages=len(pages)))
    zip_path = ROOT / VIDEO_ZIP
    if not zip_path.exists():
        response = requests.get(VIDEO_URL, timeout=60)
        response.raise_for_status()
        require(response.content.startswith(b"PK"), "Not a ZIP")
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(response.content)
    inventory = zip_inventory(zip_path)
    evidence = dict(rendered_sources=entries, video_source=dict(url=VIDEO_URL, path=VIDEO_ZIP, sha256=sha(zip_path), members=inventory))
    store.save(CACHE + "/source_review.json", evidence)
    print(json.dumps(evidence, indent=2))


def split_phases():
    """Run only after source review and the PDF-authoring operation marker."""
    source = ROOT / "data/raw/iol/iol-2011-team-prob.en-gb.pdf"
    pages = pdf_text(source)
    require(len(pages) == 7, "Unexpected 2011 packet length")
    require([int(re.search(r"Distribute at (\d+) minutes", t)[1]) for t in pages[1:]] == [0,30,60,90,120,150], "Release schedule differs")
    selections = [(INITIAL, [0,1], 0)]
    outputs = []
    with pymupdf.open(source) as original:
        for name, indices, minute in selections:
            destination = ROOT / name
            require(not destination.exists(), "Output already exists")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with pymupdf.open() as part:
                for i in indices:
                    part.insert_pdf(original, from_page=i, to_page=i)
                part.save(destination, garbage=4, deflate=True)
            with pymupdf.open(destination) as part:
                require(len(part) == len(indices) and not part.embfile_count(), "Wrong extracted PDF structure")
                for page, original_index in zip(part, indices):
                    before = original[original_index].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5), alpha=False)
                    after = page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5), alpha=False)
                    require(page.get_text() == original[original_index].get_text() and before.samples == after.samples, "Extracted content changed")
            render_prefix = ROOT / RENDER / destination.stem
            subprocess.run([str(POPPLER / "pdftoppm.exe"), "-r", "100", "-png", str(destination), str(render_prefix)], check=True, capture_output=True)
            outputs.append(dict(path=name, sha256=sha(destination), original_pages=[i+1 for i in indices], release_minute=minute,
                current_visibility="agent_visible" if minute==0 else "judge_only", reason="Timed runtime release is not implemented; withheld material must not enter initial input."))
    withheld = [dict(path=rel(source), sha256=sha(source), original_pages=[i+3], release_minute=m,
        current_visibility="judge_only", extraction_required_at_runtime=True) for i,m in enumerate((30,60,90,120,150))]
    delivery = ROOT / "output/pdf/iol_2011_initial.pdf"
    delivery.parent.mkdir(parents=True, exist_ok=True)
    require(not delivery.exists(), "Delivery file exists")
    shutil.copy2(ROOT / INITIAL, delivery)
    Store(ROOT).save(RELEASE, dict(visibility="maintainer_only", original_source=rel(source), original_sha256=sha(source),
        outputs=outputs, withheld_page_releases=withheld, snapshots_minutes=[30,60,90,120,150,180], final_solution_release_minute=180,
        runtime_release_implemented=False, scoring_time_dependence_not_recovered=True, source_pages_content_unmodified=True))
    print(json.dumps(outputs, indent=2))


def recover_videos():
    sys.path.insert(0, str(ROOT / "data/.cache/iol_video_deps"))
    from imageio_ffmpeg import get_ffmpeg_exe
    executable = get_ffmpeg_exe()
    expected = {4,7,9,11,13,14,16,20,22,23,26,27,28,36,38,39,44,48}
    entries = zip_inventory(ROOT / VIDEO_ZIP)
    require({int(Path(e["name"]).stem) for e in entries} == expected and len(entries) == 18, "Video membership differs")
    records = []
    canvas = Image.new("RGB", (1200, 300*6), "white")
    draw = ImageDraw.Draw(canvas)
    with zipfile.ZipFile(ROOT / VIDEO_ZIP) as archive:
        for i, item in enumerate(sorted(entries, key=lambda e:int(Path(e["name"]).stem))):
            data = archive.read(item["name"])
            require(data[:4] == b"RIFF" and data[8:12] == b"AVI ", "Not an AVI")
            path = ROOT / RAW / "2019/input/videos" / item["name"]
            path.parent.mkdir(parents=True, exist_ok=True)
            require(not path.exists() or path.read_bytes() == data, "Existing video differs")
            path.write_bytes(data)
            decoded = subprocess.run([executable,"-hide_banner","-v","error","-xerror","-i",str(path),"-f","null","-"], capture_output=True, timeout=30)
            require(decoded.returncode == 0 and not decoded.stderr.strip(), "Video decode error: " + decoded.stderr.decode(errors="replace"))
            jpeg = ROOT / RENDER / f"video_{path.stem}.jpg"
            subprocess.run([executable,"-hide_banner","-v","error","-i",str(path),"-vf","thumbnail=100","-frames:v","1","-y",str(jpeg)],check=True,capture_output=True,timeout=30)
            image = ImageOps.contain(Image.open(jpeg).convert("RGB"),(390,265))
            x,y=(i%3)*400,(i//3)*300
            canvas.paste(image,(x+5,y+30))
            draw.text((x+5,y+8),"Official example "+path.stem,fill="black")
            records.append(dict(path=rel(path), sha256=sha(path), source_url=VIDEO_URL, archive_member=item["name"],
                example_id=int(path.stem), full_decode_passed=True, mime_type="video/x-msvideo", role="agent_visible"))
    canvas.save(ROOT / RENDER / "video_contact.jpg")
    Store(ROOT).save(CACHE + "/video_manifest.json", dict(source_zip=VIDEO_ZIP, source_sha256=sha(ROOT / VIDEO_ZIP), videos=records,
        validation="All 18 original AVIs decoded in full without errors; thumbnails for semantic spot-check. No transcoding of canonical assets."))
    print(json.dumps(dict(videos=len(records), full_decode_passed=True)))


def printed_2022(pages):
    parts = [(part, int(points), i+1) for i,text in enumerate(pages) for part,points in re.findall(r"Part (I{1,3}|IV)\s*\((\d+) points\)",text)]
    require(parts == [("I",25,2),("II",25,6),("III",25,8),("IV",25,9)], "2022 printed part allocation differs")
    return [dict(id=part, name="Part "+part, max_score=points, source_pdf_page=page,
        description="Official part subtotal only; within-part partial-credit weights have not been recovered.") for part,points,page in parts]


def make_rows(before):
    rows = deepcopy(before)
    release = read(ROOT / RELEASE)
    videos = read(ROOT / CACHE / "video_manifest.json")["videos"]
    rubric = None
    for row in rows:
        if row["problem_id"] not in IDS:
            continue
        year, e, gold = row["year"], row["evaluation"], row["gold_label"]
        original_source = row["source_file"]
        limitations = {
            2011: ["Only original pages 1-2 belong in initial input. Pages 3-7 disclose cumulative hints at 30/60/90/120/150 minutes.",
                   "Timed hint release and six answer snapshots are not implemented; do not treat this as a validated single-shot contest.",
                   "The 100-point rubric remains a benchmark proxy, not recovered official phase-dependent scoring."],
            2019: ["All 18 official example videos are restored unchanged; their overlaid symbols/scores correspond to given examples 1-48, not answers 49-77.",
                   "Symbolic gymnastics notation in both problem and solution is lost in plain-text extraction. PDF images and video-capable delivery/grading remain unvalidated.",
                   "Gymnastics difficulty marks such as 0.2/0.4 are values to infer, not IOL item weights. The 100-point rubric is a proxy, not an official maximum."],
            2022: ["Printed Parts I-IV each carry 25 points, totaling 100. The previous generic accuracy/method/coverage split is not the official allocation.",
                   "Parts I and III require the Manchu script. Embedded font extraction corrupts its glyphs; original PDF images are authoritative for problem and answers.",
                   "Within-part partial credit and image/script-aware delivery/grading have not been validated. Printed subtotals alone do not make an executable official grader."],
        }[year]
        e.update(status="not_ready", evaluator_id=None, limitations=limitations, source_repair_report=REPORT,
            scoring_validation_status="source_repaired_runtime_and_grading_not_validated")
        if year == 2011:
            row["source_file"] = INITIAL
            row["assets"] = [dict(path=INITIAL,sha256=sha(ROOT/INITIAL),mime_type="application/pdf",role="agent_visible",source_pages=[1,2])]
            row["assets"] += [dict(path=p,sha256=sha(ROOT/p),mime_type="application/pdf",role="judge_only") for p in (original_source,row["solution_file"])]
            row["staged_release"] = dict(manifest_path=RELEASE, implemented=False, initial_source_pages=[1,2],
                hint_release_minutes=[30,60,90,120,150], answer_snapshot_minutes=[30,60,90,120,150,180])
            text = "\n\n".join(pdf_text(ROOT/INITIAL))
            require(not any(term in text for term in FORBIDDEN), "Future hint leaked into initial PDF")
            row["problem_description"] = "IOL 2011 initial packet only (original pages 1-2). Use the attached PDF for metre, macra and layout. This record requires timed hint releases; the current runtime has not implemented that protocol.\n\n" + text.strip()
            e["score_basis"] = "100-point benchmark proxy only. Official timed-release/snapshot scoring and maximum remain unverified."
        elif year == 2019:
            row["assets"] += [{k:v for k,v in a.items() if k != "full_decode_passed"} for a in videos]
            row["problem_description"] = ("Use all five pages of the attached original problem PDF, including its symbolic notation, together with the 18 official example AVIs under followup_20260913/2019/input/videos. "
                "Video filenames identify given examples 1-48. Complete all missing notation, difficulty marks and descriptions for entries 49-77. "
                "If multiple answers are possible, preserve the original instruction to supply two maximally different valid alternatives. "
                "A plain-text transcript omits essential symbols and is not a substitute for the attached PDF.")
            e["score_basis"] = "100-point benchmark proxy only; official IOL item weights/maximum unverified. Gymnastics marks are task answer values, not evaluation weights."
            gold.update(expected_answer=None, parts=[], reference_assets=[row["solution_file"]], reference_format="pdf_images_required")
        else:
            pages = pdf_text(ROOT/original_source)
            criteria = printed_2022(pages)
            independent = subprocess.check_output([str(POPPLER/"pdftotext.exe"),"-layout",str(ROOT/original_source),"-"]).decode("utf-8").split("\f")
            if not independent[-1].strip():
                independent.pop()
            require(printed_2022(independent) == criteria, "Independent 2022 allocation differs")
            row["total_points"] = 100
            row["scoring_components"] = dict(total_points=100, part_totals={c["id"]:c["max_score"] for c in criteria}, within_part_weights_verified=False)
            row["problem_description"] = ("Use the complete attached ten-page IOL 2022 Manchu packet. PDF page 1 is the blank answer sheet; pages 2-10 contain the problem. "
                "Parts I, II, III and IV each carry 25 points (100 total). Answer every subtask (a)-(h), including native-script answers where requested. "
                "The Manchu script, diagrams and layout in the original PDF are authoritative: the embedded-font plain-text extraction is corrupted and must not replace the original pages.")
            e.update(rubric_path=RUBRIC,score_basis="Official printed part subtotals: I=25, II=25, III=25, IV=25; maximum 100. Within-part partial credit unverified.")
            rubric = dict(rubric_id=Path(RUBRIC).stem,dataset=CID,visibility="judge_only",title="IOL 2022 official printed part subtotals",
                total_points=100,criteria=criteria,source_file=original_source,source_sha256=sha(ROOT/original_source),
                source_url=row["source_url"],rubric_type="printed_part_subtotals",grading_validation_status="not_validated",limitations=limitations,
                not_observable_from_deck=[],within_part_weights_verified=False)
            gold.update(expected_answer=None,parts=[dict(id=c["id"],points=25,expected=None,reference=row["solution_file"]) for c in criteria],
                reference_assets=[row["solution_file"]],reference_format="pdf_images_required")
        e["judge_assets"] = [a["path"] for a in row["assets"] if a["role"] == "judge_only"]
        gold["grading_rubric"] = "\n".join(limitations)
        row["source_review"] = dict(report=REPORT,original_source_preserved=original_source,
            checked_solution_file=row["solution_file"],source_and_answer_images_required=True,no_answerless_exclusion=True)
        provenance(row)
    return rows, rubric


def check_packages(rows, base):
    generated = {"problem.md","task_sop.md","input_environment_spec.md","ground_rules.md","collaboration.md"}
    for layout in ("base","last_exam"):
        entries = read(base/layout/"input_asset_manifest.json")["files"]
        for row in rows:
            if row["problem_id"] not in IDS:
                continue
            task = CID+"/"+row["problem_id"]
            values = [v for v in entries if v["task_id"] == task]
            assets = {a["path"]:a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}
            require(len(values)==len(assets) and {v["source"]:v["sha256"] for v in values}==assets,"Public asset membership differs")
            folder = base/layout/"tasks"/task/"base/input"
            names = {Path(v["staged"]).relative_to(Path("tasks")/task/"base/input").as_posix() for v in values}
            require({p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} == names|generated,"Public allowlist differs")
            for value in values:
                require(sha(base/layout/value["staged"]) == value["sha256"],"Copied public bytes differ")
            require((folder/"problem.md").read_text(encoding="utf-8") == row["problem_description"]+"\n","Prompt readback differs")
            for name in generated:
                text = (folder/name).read_text(encoding="utf-8")
                require(not any(t in text for t in ("team-sol","data/rubrics/","release_manifest.json")),"Hidden reference leaked")
                if row["year"] == 2011:
                    require(not any(t in text for t in FORBIDDEN),"Future hint leaked")
            if layout == "last_exam":
                ref = read(folder.parent.parent/"eval/reference.json")
                require(ref["evaluation"] == row["evaluation"] and ref["solution_file"]==row["solution_file"],"Hidden reference differs")


def prepare():
    store = Store(ROOT)
    require(not (ROOT/REPORT).exists() and not (ROOT/CACHE/"plan.json").exists(),"Already prepared/applied")
    before = deepcopy(store.read(BENCHMARK))
    index = deepcopy(store.read("data/benchmarks/index.json"))
    require(len(before)==18 and index["total_records"]==1720,"Catalog starting point differs")
    require({r["problem_id"] for r in before if r["year"] in YEARS}==IDS,"Selected IDs differ")
    rows,rubric = make_rows(before)
    rules = {k:deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition","collaboration","evaluation")}
    scoring = rules["evaluation"]["scoring"]
    scoring["evaluation_status_counts"] = dict(Counter(r["evaluation"]["status"] for r in rows))
    for row in rows:
        if row["problem_id"] not in IDS:
            continue
        pid = row["problem_id"]
        scoring.setdefault("record_evaluator_overrides",{})[pid] = None
        scoring.setdefault("record_rubric_overrides",{})[pid] = row["evaluation"]["rubric_path"]
        scoring.setdefault("record_score_basis_overrides",{})[pid] = dict(max_score=row.get("total_points"),basis=row["evaluation"]["score_basis"],
            grading_validation_status="not_ready")
    writes = {BENCHMARK:rows,RULE:rules["evaluation"],RUBRIC:rubric}
    cards = deepcopy(store.read(CARDS))
    prior_cards = deepcopy(cards["records"])
    lookup = {r["problem_id"]:r for r in rows}
    def pending_read(path):
        return writes[path] if path in writes else read(ROOT/path)
    def pending_sha(path):
        return hashlib.sha256((json.dumps(writes[path],ensure_ascii=False,indent=2)+"\n").encode()).hexdigest() if path in writes else sha(ROOT/path)
    cards["records"] = [scorecard(lookup[c["problem_id"]],ROOT,read_json=pending_read,hash_file=pending_sha) if c["problem_id"] in IDS else c for c in cards["records"]]
    writes[CARDS] = cards
    membership = deepcopy(store.read(SCORES))
    for item in membership["records"]:
        if item["problem_id"] in IDS:
            row = lookup[item["problem_id"]]
            item.update(official_total_points=row.get("total_points"),evaluation_status=row["evaluation"]["status"],
                rubric_path=row["evaluation"]["rubric_path"],scoring_components=row.get("scoring_components"))
    writes[SCORES] = membership
    update_track_index(index,CID,rows)
    index["latest_source_repair_report"] = REPORT
    writes["data/benchmarks/index.json"] = index
    stage = ROOT/CACHE/"stage"
    require(not stage.exists(),"Stage already exists")
    build_packages(ROOT,stage,{"olympiads":[next(t for t in index["olympiads"] if t["id"]==CID)]},
        {CID:[r for r in rows if r["problem_id"] in IDS]},{CID:rules},store.sha)
    targets,old_tasks,protected = [],{},{}
    for layout in ("base","last_exam"):
        for name,key in (("task_cards.json","tasks"),("input_asset_manifest.json","files")):
            path = f"data/{layout}/{name}"
            value = deepcopy(store.read(path))
            if key=="tasks":
                for card in value[key]:
                    if not card["task_id"].startswith(CID+"/"):
                        continue
                    folder = store.path(f"data/{layout}/"+card["source_repo_path"])
                    require(folder==store.path(f"data/{layout}/tasks/"+card["task_id"]),"Task path differs")
                    bucket = old_tasks if card["task_id"] in TASKS else protected
                    bucket.update({rel(p):sha(p) for p in folder.rglob("*") if p.is_file()})
                    if card["task_id"] in TASKS:
                        targets.append(rel(folder))
            replacement = read(stage/layout/name)[key]
            if key=="tasks":
                mapping={v["task_id"]:v for v in replacement}
                require(set(mapping)==TASKS,"Staged task IDs differ")
                value[key]=[mapping.get(v["task_id"],v) for v in value[key]]
            else:
                value[key]=[v for v in value[key] if v["task_id"] not in TASKS]+replacement
            writes[path]=value
    require(len(targets)==6,"Unexpected archive count")
    for tree in ("data/raw/iol","data/rules","data/rubrics"):
        protected.update({rel(p):sha(p) for p in (ROOT/tree).rglob("*") if p.is_file() and rel(p) not in writes})
    for track in index["olympiads"]:
        if track["id"] != CID:
            protected[track["benchmark_path"]]=sha(ROOT/track["benchmark_path"])
    for tree in (f"data/last_exam/competitions/{CID}",):
        protected.update({rel(p):sha(p) for p in (ROOT/tree).rglob("*") if p.is_file() and "eval" not in p.parts})
    protected.update({p:sha(ROOT/p) for p in ("data/base/index.json","data/last_exam/index.json","data/last_exam/competitions/index.json",
        "data/base/README.md","data/last_exam/README.md","output/pdf/iol_2011_initial.pdf")})
    expected = set(writes)|{"data/README.md","data/benchmarks/README.md",f"data/last_exam/competitions/{CID}/eval/evaluation.json",f"data/last_exam/competitions/{CID}/eval/scoring.md"}
    expected.update(rel(p) for p in (ROOT/"data/viz").iterdir() if p.is_file())
    plan=dict(before_rows=before,rows=rows,prior_cards=prior_cards,writes=writes,targets=targets,old_tasks=old_tasks,protected_hashes=protected,
        expected_hashes={p:sha(ROOT/p) for p in expected if (ROOT/p).exists()},new_paths=[p for p in expected if not (ROOT/p).exists()],
        stage_hashes={rel(p):sha(p) for p in stage.rglob("*") if p.is_file()})
    check_packages(rows,stage)
    store.save(CACHE+"/plan.json",plan)
    print(json.dumps(dict(selected_years=sorted(YEARS),status_counts=scoring["evaluation_status_counts"],protected_files=len(protected),archived_task_dirs=len(targets)),indent=2))


def verify(plan,report):
    for path,digest in plan["protected_hashes"].items():
        require(sha(ROOT/path)==digest,"Protected bytes changed: "+path)
    for path,value in plan["writes"].items():
        require(read(ROOT/path)==value,"Metadata readback differs: "+path)
    rows=read(ROOT/BENCHMARK)
    require([r for r in rows if r["problem_id"] not in IDS]==[r for r in plan["before_rows"] if r["problem_id"] not in IDS],"Unrelated IOL row changed")
    current_cards=read(ROOT/CARDS)["records"]
    require([c for c in current_cards if c["problem_id"] not in IDS]==[c for c in plan["prior_cards"] if c["problem_id"] not in IDS],"Unrelated scorecard changed")
    for row in rows:
        if row["problem_id"] in IDS:
            require(next(c for c in current_cards if c["problem_id"]==row["problem_id"])==scorecard(row,ROOT),"Selected scorecard differs")
            require(row["evaluation"]["status"]=="not_ready" and row["evaluation"]["evaluator_id"] is None,"Unvalidated record promoted")
        for asset in row["assets"]:
            require(sha(ROOT/asset["path"])==asset["sha256"],"Asset bytes changed")
            if asset["mime_type"]=="application/pdf":
                pdf_text(ROOT/asset["path"])
    for path,digest in plan["old_tasks"].items():
        require(sha(ROOT/report["backup"]/path)==digest,"Archived task differs")
    check_packages(rows,ROOT/"data")
    for layout in ("base","last_exam"):
        for name,key in (("task_cards.json","tasks"),("input_asset_manifest.json","files")):
            before=read(ROOT/report["backup"]/f"data/{layout}/{name}")[key]
            after=read(ROOT/f"data/{layout}/{name}")[key]
            require([v for v in before if v["task_id"] not in TASKS]==[v for v in after if v["task_id"] not in TASKS],"Unrelated catalog entries changed")
    rule=read(ROOT/RULE)
    require(read(ROOT/f"data/last_exam/competitions/{CID}/eval/evaluation.json")==rule,"Shared evaluation differs")
    require((ROOT/f"data/last_exam/competitions/{CID}/eval/scoring.md").read_text(encoding="utf-8")=="# Hidden scoring configuration\n\n"+section("Evaluation",rule),"Shared scoring text differs")
    index=read(ROOT/"data/benchmarks/index.json")
    all_ids,statuses=[],Counter()
    for track in index["olympiads"]:
        data=read(ROOT/track["benchmark_path"])
        require(len(data)==track["problems_collected"],"Track count mismatch")
        all_ids += [track["id"]+"/"+r["problem_id"] for r in data]
        statuses.update(r["evaluation"]["status"] for r in data)
    require(len(all_ids)==len(set(all_ids))==index["total_records"]==1720,"Global membership mismatch")
    for layout in ("base","last_exam"):
        cards=read(ROOT/f"data/{layout}/task_cards.json")
        require(cards["n_tasks"]==len(cards["tasks"])==1720 and {c["task_id"] for c in cards["tasks"]}==set(all_ids),"Derived membership mismatch")
    summary=read(ROOT/"data/viz/summary.json")
    require(summary["n_primary_records"]==1720 and summary["evaluation_status_counts"]==dict(statuses),"Summary mismatch")
    require(dict(statuses)==dict(ready=662,not_ready=705,ready_with_limitations=193,remote_judge_ready=158,sample_tests_ready=2),"Unexpected readiness delta")
    source=ROOT/"data/raw/iol/iol-2011-team-prob.en-gb.pdf"
    with pymupdf.open(source) as original,pymupdf.open(ROOT/INITIAL) as initial:
        require(len(initial)==2 and not initial.embfile_count() and not initial.get_toc(),"Unexpected initial PDF contents")
        require(not any(t in "\n".join(p.get_text() for p in initial) for t in FORBIDDEN),"Hint disclosure")
        for i,p in enumerate(initial):
            a=original[i].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
            b=p.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
            require((a.width,a.height,a.samples)==(b.width,b.height,b.samples),"Initial page pixels differ")
    require(sha(ROOT/INITIAL)==sha(ROOT/"output/pdf/iol_2011_initial.pdf"),"Delivery PDF differs")
    return dict(active_tracks=43,active_records=1720,active_iol_records=18,no_years_excluded=True,
        repaired_years=sorted(YEARS),iol_status_counts=dict(Counter(r["evaluation"]["status"] for r in rows)),global_status_counts=dict(statuses),
        public_2011_pages=[1,2],future_hint_pages_withheld=[3,4,5,6,7],new_videos=18,all_videos_decoded=True,
        official_2022_points=100,official_2022_part_points=[25,25,25,25],unchanged_iol_rows_and_scorecards=15,
        other_tracks_unchanged=42,protected_files_unchanged=len(plan["protected_hashes"]),archived_generated_files=len(plan["old_tasks"]),
        source_pdfs_visually_reviewed=6,source_pages_visually_reviewed=29,initial_pdf_page_pixels_identical=True,
        historical_results_modified=False,end_to_end_runtime_or_grading_validated=False)


def apply():
    require(not (ROOT/REPORT).exists(),"Already applied")
    plan=read(ROOT/CACHE/"plan.json")
    store=Store(ROOT)
    for path,digest in {**plan["protected_hashes"],**plan["expected_hashes"],**plan["old_tasks"],**plan["stage_hashes"]}.items():
        require(sha(ROOT/path)==digest,"Concurrent change: "+path)
        if path in plan["expected_hashes"]:
            store.raw[store.path(path)]=store.path(path).read_bytes()
    for path in plan["new_paths"]:
        require(not (ROOT/path).exists(),"New target occupied")
    visual=read(ROOT/CACHE/"visual_review.json")
    require(visual["source_pages_reviewed"]==29 and visual["initial_sha256"]==sha(ROOT/INITIAL),"Visual review differs")
    for name in plan["targets"]:
        target=store.path(name)
        require(target.name in IDS and target.parent.name==CID and target.parent.parent.name=="tasks" and target.is_dir(),"Unsafe archive target")
    report=dict(operation="iol_staged_disclosure_video_and_printed_score_repair",status="preparing",backup=rel(store.backup),timestamp_utc=store.stamp)
    store.finish(report)
    try:
        for path,value in plan["writes"].items():
            store.save(path,value)
        for name in plan["targets"]:
            require({rel(p):sha(p) for p in store.path(name).rglob("*") if p.is_file()}=={p:h for p,h in plan["old_tasks"].items() if p.startswith(name+"/")},"Task changed before archival")
            store.archive(name)
        stage=ROOT/CACHE/"stage"
        for layout in ("base","last_exam"):
            for pid in IDS:
                destination=ROOT/"data"/layout/"tasks"/CID/pid
                require(not destination.exists(),"Replacement target occupied")
                shutil.copytree(stage/layout/"tasks"/CID/pid,destination)
        rule=plan["writes"][RULE]
        store.save(f"data/last_exam/competitions/{CID}/eval/evaluation.json",rule)
        store.save_text(f"data/last_exam/competitions/{CID}/eval/scoring.md","# Hidden scoring configuration\n\n"+section("Evaluation",rule))
        index=plan["writes"]["data/benchmarks/index.json"]
        summary_and_figures(store,index,{t["id"]:read(ROOT/t["benchmark_path"]) for t in index["olympiads"]})
        for path in ("data/README.md","data/benchmarks/README.md"):
            text=store.raw[store.path(path)].decode("utf-8-sig")
            text=text.replace("(43 tracks, 1,720 records; 702 not_ready)","(43 tracks, 1,720 records; 705 not_ready)")
            text=text.replace("Current catalog: 43 tracks, 1,720 records, including 702 not_ready.","At the first IOL repair snapshot: 43 tracks, 1,720 records, including 702 not_ready.")
            text += ("\n## IOL follow-up source repair (2026-09-13)\n\nCurrent catalog: 43 tracks, 1,720 records, including 705 not_ready. "
                "IOL still has 18 years (9 ready, 1 ready_with_limitations, 8 not_ready); no years were excluded in this batch. "
                "2011 initial input now contains only original pages 1-2; five later hint releases remain withheld in the preserved archive. "
                "2019 now includes all 18 official example AVIs. 2022 now has official part subtotals of 25+25+25+25=100, "
                "not the generic 50/30/20 proxy split. All three records are not_ready pending timed-release or image/video/script-aware "
                "runtime and grading validation. Original references and historical results are preserved. "
                f"See `{REPORT}` and `docs/from_zhongzheng/iol-followup-repair-20260913.md`.\n")
            store.save_text(path,text)
        report["validation"]=verify(plan,report)
        report["new_task_file_hashes"]={rel(p):sha(p) for layout in ("base","last_exam") for pid in IDS
            for p in (ROOT/"data"/layout/"tasks"/CID/pid).rglob("*") if p.is_file()}
        report["status"]="completed_source_isolation_media_recovery_and_score_sync"
        store.save(REPORT,report)
        store.finish(report)
        print(json.dumps({k:report[k] for k in ("status","backup","validation")},indent=2))
    except Exception as error:
        report.update(status="interrupted",error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("sources", "split", "videos", "prepare", "apply", "verify"))
    mode=parser.parse_args().mode
    if mode=="verify":
        print(json.dumps(verify(read(ROOT/CACHE/"plan.json"),read(ROOT/REPORT)),indent=2))
    else:
        {"sources": render_sources, "split": split_phases, "videos": recover_videos,"prepare":prepare,"apply":apply}[mode]()
