"""Source-image-verified, record-local PDF glyph repairs; no answer/score changes."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.repair_iol_sources_20260913 import read, sha, rel, require, POPPLER

CACHE = "data/.cache/catalog_glyph_repair_20260913"
RENDER = "tmp/pdfs/catalog_glyph_repair_20260913"
REPORT = "data/excluded/benchmark_audit_reports/catalog_glyph_repair_20260913.json"
SELECTED = {
    "iol_team": {"iol_team_2021", "iol_team_2025"},
    "arml_power": {"arml_power_spring_2022", "arml_power_spring_2024"},
    "arml_national_power": {"arml_national_power_2023"},
    "iiot": {"iiot_2021_02", "iiot_2021_08", "iiot_2023_01"},
    "pumac_power": {"pumac_power_2010", "pumac_power_2021", "pumac_power_2023"},
}
CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
PATCHES = {
    "iol_team_2021": [("\x1b", "←", 1)],
    "iol_team_2025": [("north 6 ? -\x1b", "north ↑ ↓ → ←", 1)],
    "arml_power_spring_2022": [("\x18m + n\n2\n\x19", "⌈(m + n)/2⌉", 1)],
    "arml_power_spring_2024": [("f(m, s) ≤FC(m, s) = max\n\x1a1\n3, min\n\x1a\nm\ns⌈2m/s⌉, 1 −\nm\ns⌊2m/s⌋\n\x1b\x1b", "f(m, s) ≤ FC(m, s) = max{1/3, min{m/(s⌈2m/s⌉), 1 − m/(s⌊2m/s⌋)}}", 1)],
    "arml_national_power_2023": [("\x04 log2(x)\x05", "⌊log2(x)⌋", 1), ("\x04 k 4 \x05", "⌊k/4⌋", 1), ("\x04 log2(m)\x05", "⌊log2(m)⌋", 1)],
    "iiot_2021_02": [("\x0e", "Note:", 1), ("109 + 7", "10^9 + 7", 2)],
    "iiot_2021_08": [("\x0e", "Note:", 1), ("107 + 19", "10^7 + 19", 1), ("10 7 +19", "10^7 + 19", 1)],
    "iiot_2023_01": [("\x0e", "Note:", 1), ("109 + 7", "10^9 + 7", 3)],
    "pumac_power_2010": [("\x0f", "ϵ", 4)],
    "pumac_power_2021": [("\x12", "(", 5), ("\x13", ")", 5),
        ("dTV(x, y) = max\nA⊂[d]\n\x0c\x0c\x0c\x0c\x0c\nX\nn∈A\n(xn − yn)\n\x0c\x0c\x0c\x0c\x0c = 1\n2 sup\n( dX\nk=1\nfk(xk − yk) : max\ni∈[d]\n|fi| ≤1\n)",
         "dTV(x, y) = max_{A⊂[d]} |∑_{n∈A}(x_n − y_n)| = (1/2) sup{∑_{k=1}^d f_k(x_k − y_k) : max_{i∈[d]} |f_i| ≤ 1}", 1)],
    "pumac_power_2023": [("\x12", "(", 4), ("\x13", ")", 4)],
}
REVIEWED_PAGES = {"iol_team_2021":[9], "iol_team_2025":[1], "arml_power_spring_2022":[5],
    "arml_power_spring_2024":[3], "arml_national_power_2023":[2], "iiot_2021_02":[1], "iiot_2021_08":[1],
    "iiot_2023_01":[1], "pumac_power_2010":[4], "pumac_power_2021":[11,15,17], "pumac_power_2023":[21,23]}


def repair_text(pid, text):
    require(pid in PATCHES, "No reviewed patch for record")
    for old, new, count in PATCHES[pid]:
        require(text.count(old) == count, f"Source context/count changed: {pid}: {old!r}")
        text = text.replace(old, new)
    require(not CONTROLS.search(text), "Unreviewed control remains")
    return text


def inspect():
    entries = []
    for cid, ids in SELECTED.items():
        for row in read(ROOT/f"data/benchmarks/{cid}/benchmark.json"):
            if row["problem_id"] not in ids:
                continue
            source = ROOT/row["source_file"]
            pages = []
            with pymupdf.open(source) as document:
                for n, page in enumerate(document, 1):
                    text = page.get_text()
                    matches = list(CONTROLS.finditer(text))
                    if not matches:
                        continue
                    prefix = ROOT/RENDER/row["problem_id"]
                    prefix.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run([str(POPPLER/"pdftoppm.exe"), "-f", str(n), "-l", str(n), "-r", "130", "-png", str(source), str(prefix)], check=True, capture_output=True)
                    pages.append(dict(page=n, controls=dict(Counter(str(ord(m[0])) for m in matches)),
                        contexts=[text[max(0,m.start()-70):m.start()+100] for m in matches]))
            item = dict(task_id=cid+"/"+row["problem_id"], source_file=row["source_file"], sha256=sha(source), pages=pages)
            entries.append(item)
            print(json.dumps(item, ensure_ascii=True), flush=True)
    Store(ROOT).save(CACHE+"/source_review.json", dict(records=entries))


def prepare():
    require(not (ROOT/CACHE/"plan.json").exists() and not (ROOT/REPORT).exists(), "Already prepared/applied")
    store = Store(ROOT)
    evidence = read(ROOT/CACHE/"source_review.json")["records"]
    sources = {v["task_id"]:v for v in evidence}
    writes, before_rows, changes = {}, {}, []
    for cid, ids in SELECTED.items():
        path = f"data/benchmarks/{cid}/benchmark.json"
        before_rows[cid] = deepcopy(store.read(path))
        rows = deepcopy(before_rows[cid])
        for row in rows:
            pid = row["problem_id"]
            if pid not in ids:
                continue
            source = sources[cid+"/"+pid]
            require(sha(ROOT/source["source_file"]) == source["sha256"], "Reviewed source changed")
            original = row["problem_description"]
            row["problem_description"] = repair_text(pid, original)
            changes.append(dict(task_id=cid+"/"+pid, source_file=source["source_file"], source_sha256=source["sha256"],
                pdf_pages_visually_reviewed=REVIEWED_PAGES[pid], control_characters_repaired=len(CONTROLS.findall(original)),
                replacements=[dict(before=a, after=b, occurrences=n) for a,b,n in PATCHES[pid]]))
        writes[path] = rows
    require(len(changes) == 11, "Selected membership differs")
    for layout in ("base", "last_exam"):
        cards = store.read(f"data/{layout}/task_cards.json")["tasks"]
        for card in cards:
            cid, pid = card["task_id"].split("/", 1)
            if pid not in SELECTED.get(cid, set()):
                continue
            path = f"data/{layout}/"+card["source_repo_path"]+"/base/input/problem.md"
            old = next(r for r in before_rows[cid] if r["problem_id"] == pid)
            require((ROOT/path).read_text(encoding="utf-8") == old["problem_description"]+"\n", "Pre-repair task prompt drift")
            new = next(r for r in writes[f"data/benchmarks/{cid}/benchmark.json"] if r["problem_id"] == pid)
            writes[path] = new["problem_description"]+"\n"
    # All files in affected task folders other than problem.md stay byte-identical.
    protected = {v["source_file"]:v["sha256"] for v in evidence}
    for tree in ("data/rules", "data/rubrics", "data/viz"):
        protected.update({rel(p):sha(p) for p in (ROOT/tree).rglob("*") if p.is_file()})
    for layout in ("base", "last_exam"):
        for card in read(ROOT/f"data/{layout}/task_cards.json")["tasks"]:
            cid, pid = card["task_id"].split("/",1)
            if cid in SELECTED:
                folder = ROOT/f"data/{layout}"/card["source_repo_path"]
                protected.update({rel(p):sha(p) for p in folder.rglob("*") if p.is_file() and rel(p) not in writes})
        for name in ("index.json", "task_cards.json", "input_asset_manifest.json", "README.md"):
            path = f"data/{layout}/{name}"
            protected[path] = sha(ROOT/path)
    for track in store.read("data/benchmarks/index.json")["olympiads"]:
        if track["id"] not in SELECTED:
            protected[track["benchmark_path"]] = sha(ROOT/track["benchmark_path"])
    protected["data/benchmarks/index.json"] = sha(ROOT/"data/benchmarks/index.json")
    plan = dict(before_rows=before_rows, writes=writes, changes=changes, protected_hashes=protected,
        expected_hashes={p:sha(ROOT/p) for p in writes})
    store.save(CACHE+"/plan.json", plan)
    print(json.dumps(dict(records=len(changes), changed_files=len(writes), protected_files=len(protected),
        control_characters=sum(c["control_characters_repaired"] for c in changes)), indent=2))


def verify(plan):
    for path, value in plan["writes"].items():
        actual = (ROOT/path).read_text(encoding="utf-8") if isinstance(value,str) else read(ROOT/path)
        require(actual == value, "Write readback differs: "+path)
    for path, digest in plan["protected_hashes"].items():
        require(sha(ROOT/path) == digest, "Protected file changed: "+path)
    changed = 0
    for cid, before in plan["before_rows"].items():
        after = read(ROOT/f"data/benchmarks/{cid}/benchmark.json")
        require([r["problem_id"] for r in after] == [r["problem_id"] for r in before], "Membership/order changed")
        for a,b in zip(before,after):
            expected = deepcopy(a)
            if a["problem_id"] in SELECTED[cid]:
                expected["problem_description"] = repair_text(a["problem_id"], a["problem_description"])
                changed += 1
            require(b == expected, "Out-of-scope record mutation")
    require(changed == 11, "Wrong repaired record count")
    return dict(repaired_records=11, repaired_control_characters=sum(c["control_characters_repaired"] for c in plan["changes"]),
        source_pages_visually_reviewed=sum(len(v) for v in REVIEWED_PAGES.values()), protected_files_unchanged=len(plan["protected_hashes"]),
        changed_files=len(plan["writes"]), task_prompt_copies_updated=22, membership_unchanged=True,
        original_sources_unchanged=True, answers_scores_and_readiness_unchanged=True, historical_results_modified=False)


def apply():
    require(not (ROOT/REPORT).exists(), "Already applied")
    plan = read(ROOT/CACHE/"plan.json")
    store = Store(ROOT)
    for path, digest in {**plan["expected_hashes"], **plan["protected_hashes"]}.items():
        require(sha(ROOT/path) == digest, "Concurrent change: "+path)
        if path in plan["expected_hashes"]:
            store.raw[store.path(path)] = store.path(path).read_bytes()
    report = dict(operation="source_verified_pdf_control_glyph_repair", status="preparing", backup=rel(store.backup),
        timestamp_utc=store.stamp, changes=plan["changes"])
    store.finish(report)
    try:
        for path, value in plan["writes"].items():
            store.save_text(path,value) if isinstance(value,str) else store.save(path,value)
        report["validation"] = verify(plan)
        report["status"] = "completed_prompt_only_source_verified_repairs"
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps(dict(status=report["status"], backup=report["backup"], validation=report["validation"]), indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "prepare", "apply", "verify"))
    mode = parser.parse_args().mode
    if mode == "verify":
        print(json.dumps(verify(read(ROOT/CACHE/"plan.json")), indent=2))
    else:
        {"inspect":inspect, "prepare":prepare, "apply":apply}[mode]()
