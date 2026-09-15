"""Second, visually checked EOES pass for glyph errors missed by the C0 scan."""
from copy import deepcopy
import argparse
import json
import re
from scripts.repair_remaining_prompt_text_20260913 import Editor, ROOT, Store, read, sha, rel, require

PID = "eoes_EOES2025_Task2_TaskSheet_final"
CACHE = "data/.cache/eoes_biology_text_20260913"
REPORT = "data/benchmarks/eoes_biology_text_repair_20260913.json"


def repair(text):
    e = Editor(text)
    e.rx(r"(?<=model, that says: \n).*?(?=\nIf we assume)",
         "Q_10 = [k(t_2) / k(t_1)]^(10 °C / (t_2 − t_1))\n ")
    e.rep("0 2nN N = ×", "N = N_0 × 2^n")
    for a, b in [("protecKng", "protecting"), ("plasKc", "plastic"),
                 ("boJle", "bottle"), ("soluKon", "solution"), ("Klt", "tilt"),
                 ("aBer", "after"), ("unKl", "until"), ("examinaCon", "examination"),
                 ("objecKve", "objective"), ("cuveCe", "cuvette"),
                 ("concentra.on", "concentration"), ("nota.on", "notation"),
                 ("solu.ons", "solutions"), ("tra.ons", "trations")]:
        e.all(a, b)
    return e


def prepare():
    require(not (ROOT/CACHE/"plan.json").exists(), "Already prepared")
    store = Store(ROOT)
    path = "data/benchmarks/eoes/benchmark.json"
    rows = read(ROOT/path)
    before = deepcopy(rows)
    row = next(r for r in rows if r["problem_id"] == PID)
    edit = repair(row["problem_description"])
    old = row["problem_description"]
    row["problem_description"] = edit.text
    writes = {path: rows}
    protected = {a["path"]: sha(ROOT/a["path"]) for a in row["assets"]}
    for layout in ("base", "last_exam"):
        cards = read(ROOT/f"data/{layout}/task_cards.json")["tasks"]
        card = next(c for c in cards if c["task_id"] == "eoes/"+PID)
        folder = ROOT/f"data/{layout}"/card["source_repo_path"]
        prompt = rel(folder/"base/input/problem.md")
        require((ROOT/prompt).read_text(encoding="utf-8") == old+"\n", "Prompt drift")
        writes[prompt] = edit.text+"\n"
        protected.update({rel(f): sha(f) for f in folder.rglob("*") if f.is_file() and rel(f) != prompt})
        for name in ("task_cards.json", "input_asset_manifest.json", "index.json", "README.md"):
            f = f"data/{layout}/{name}"
            protected[f] = sha(ROOT/f)
    for tree in ("data/rules", "data/rubrics", "data/viz"):
        protected.update({rel(f): sha(f) for f in (ROOT/tree).rglob("*") if f.is_file()})
    for track in read(ROOT/"data/benchmarks/index.json")["olympiads"]:
        p = track["benchmark_path"]
        if p != path: protected[p] = sha(ROOT/p)
    protected["data/benchmarks/index.json"] = sha(ROOT/"data/benchmarks/index.json")
    plan = dict(writes=writes, before_rows=before, edits=edit.changes,
                expected={p: sha(ROOT/p) for p in writes}, protected=protected,
                task_id="eoes/"+PID, source_file=row["source_file"], source_sha256=sha(ROOT/row["source_file"]),
                reviewed_pages=[9,16,17,18,19,20,21,22],
                review="Full source pages visually checked; restore printed formulas and specific font-mapped words, without adding measured values or solved answers.")
    store.save(CACHE+"/plan.json", plan)
    print(json.dumps(dict(edits=len(edit.changes), files=len(writes))))


def verify(plan):
    for p, v in plan["writes"].items():
        require(((ROOT/p).read_text(encoding="utf-8") if isinstance(v, str) else read(ROOT/p)) == v, "Write drift: "+p)
    for p, h in plan["protected"].items(): require(sha(ROOT/p) == h, "Protected drift: "+p)
    expected = deepcopy(plan["before_rows"])
    row = next(r for r in expected if r["problem_id"] == PID)
    row["problem_description"] = repair(row["problem_description"]).text
    require(expected == read(ROOT/"data/benchmarks/eoes/benchmark.json"), "Non-prompt changes")
    return dict(records=1, content_files=3, reviewed_pages=8,
                protected_files_unchanged=len(plan["protected"]), sources_answers_scores_readiness_unchanged=True)


def apply():
    require(not (ROOT/REPORT).exists(), "Already applied")
    plan = read(ROOT/CACHE/"plan.json")
    for p, h in {**plan["expected"], **plan["protected"]}.items(): require(sha(ROOT/p) == h, "Concurrent edit: "+p)
    store = Store(ROOT)
    report = dict(operation="source_verified_eoes_biology_and_chemistry_text", backup=rel(store.backup),
                  task_id=plan["task_id"], source_file=plan["source_file"], source_sha256=plan["source_sha256"],
                  reviewed_pages=plan["reviewed_pages"], edits=plan["edits"], status="preparing")
    store.finish(report)
    for p, v in plan["writes"].items(): store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    report.update(status="completed", validation=verify(plan))
    store.save(REPORT, report)
    store.finish(report)
    print(json.dumps(report["validation"]))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "apply", "verify"))
    mode=parser.parse_args().mode
    if mode == "verify": print(json.dumps(verify(read(ROOT/CACHE/"plan.json"))))
    else: {"prepare": prepare, "apply": apply}[mode]()
