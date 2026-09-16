"""Restore sample-table boundaries and math typography from 20 reviewed PDF pages."""
from copy import deepcopy
import argparse
import json
import re
from scripts.repair_remaining_prompt_text_20260913 import ROOT,Store,Editor,read,sha,rel,require

CACHE="data/.cache/iiot_2023_text_20260913"
REPORT="data/excluded/benchmark_audit_reports/iiot_2023_text_repair_20260913.json"
SAMPLES={
    1:[("5\n2 3 0\n2 2 1\n4 1 1\n100 100 100\n100000 100000 1", "1\n12\n0\n105481704\n600000")],
    2:[("60 4\n4 60\n3 6\n5 42\n2 15","10 45"),
       ("30 5\n1000000000 30\n1000000000 30\n1000000000 30\n1000000000 30\n1000000000 30","5000000000 0")],
    3:[("3 6\nare\nmere\nana\noare\ncinestie\nnimeni\nanaana\nplebi\nnusestie","3\n-1\n4")],
    4:[("4\n10 4 8 7","23"),("10\n5 4 18 11 19 14 21 7 0 10","114")],
    5:[("6\n3 6 6 6 6 6\n5 1 1 1 1\n5\n4 2 2\n2 4 2\n1 1 1\n4 3 2\n4 3 1","6\n6\n3\n6\n6"),
       ("10\n5 10 1 1 2 5 9 8 2 9\n8 2 7 9 5 1 1 8 5\n10\n10 3 2\n1 4 2\n6 8 1\n3 4 2\n2 9 2\n9 7 2\n3 3 1\n6 4 4\n5 5 1\n3 8 1","9\n5\n8\n9\n8\n8\n1\n5\n2\n10")],
    6:[("3\n8 0 7\n5 6 9\n1 7 9","7")],
    7:[("3 6 2\n1 2 3\n1 5\n1 2 1 5\n2 1 2 4","5\n9")],
    8:[("2 3","-1"),("4 3","3\n0 0 0\n1 2 0\n1 2 2\n1 1 2")],
    9:[("3 1\n1 2 4\n2 3 5","18"),("4 2\n1 2 10\n2 3 10\n2 4 11","41")],
}
# Header first, then subtask order. These are colors visible in the original,
# not numerical scoring weights or a new difficulty scale.
BOOKS={1:[5,1,1,2,3,3,5,5],2:[2,1,1,1,1,2],3:[5,1,1,5,5],
       4:[1,1,1,1,1],5:[5,1,3,4,5,4,5,4,5],6:[5,1,2,5,5,5],
       7:[5,1,3,3,3,4,4,5],8:[2,1,1,2,2],9:[3,1,2,2,3]}


def repair(number,text):
    e=Editor(text)
    e.rep("III ((( OOO TTT +++ III ))) ;;;", "[IIOT logo]")
    icon="ὖE"*5
    require(e.text.count(icon)==len(BOOKS[number]),"Book indicator count drift")
    for orange in BOOKS[number]:
        after=f"[book indicator: {orange} orange, {5-orange} grey]"
        e.text=e.text.replace(icon,after,1)
        e.changes.append(dict(before=icon,after=after))
    samples="\n\nExamples\n\n"+"\n\n".join(
        f"Sample {i} input:\n```text\n{a}\n```\n\nSample {i} output:\n```text\n{b}\n```"
        for i,(a,b) in enumerate(SAMPLES[number],1))+"\n\n"
    e.rx(r"Examples? input output .*?(?=Explanation)", samples)
    if number==3:
        e.rep("2·105", "2·10^5",2)
        e.rep("4·105", "4·10^5")
        e.rep("at most 106", "at most 10^6")
        e.rep("ei = chr (( ord(si) +ord(ti) ) mod 26 )", "e_i = chr((ord(s_i) + ord(t_i)) mod 26)")
        e.rep("ei = chr (( ord(si) +ord(ti mod|t|) ) mod 26 )", "e_i = chr((ord(s_i) + ord(t_{i mod |t|})) mod 26)")
    elif number==5:
        e.text += "\n\nSource note: the fifth query in sample 1 has k=1, but the printed explanation calls its answer the second largest. Both original statements are retained; no unpublished erratum is assumed."
    elif number==6:
        e.rep("ai,j≤ 109", "ai,j≤ 10^9")
        e.rep("becomes this: 6 9 7 9", "becomes this:\n```text\n6 9\n7 9\n```\n")
    elif number==7:
        e.rx(r"\(0,0\) \(0,1\).*?(?=Figure 2:)",
             "[Figure 2 diagram: three bidirectional rings i=0,1,2, each with j=0,...,5 and cyclic edges j↔(j+1) mod 6. Ring-edge costs are 1, 2, 3 respectively. Radial edges (0,j)↔(1,j) cost 1 and (1,j)↔(2,j) cost 5 for every j. There is no (0,j)↔(2,j) edge.] ")
        e.rep("(Aq, Bq)̸= (Cq, Dq)", "(Aq, Bq) ≠ (Cq, Dq)")
    elif number==8:
        e.rep("Figure 1: All the pieces avaiable to Tommaso.",
              "Figure 1: All the pieces avaiable to Tommaso.\n[Diagram transcription: seven tetrominoes, with # occupied and . empty; rows are separated by /.]\nO: ##/##; I: #/#/#/#; S: .##/##.; Z: ##./.##; L: #./#./##; J: .#/.#/##; T: ###/.#.\n")
    elif number==9:
        e.rep("ci≤106", "ci≤10^6",2)
        e.rep("ai̸= bi", "ai ≠ bi")
    require("ὖE" not in e.text,"Unreviewed icon remains")
    return e


def prepare():
    require(not (ROOT/CACHE/"plan.json").exists(),"Already prepared")
    store=Store(ROOT); path="data/benchmarks/iiot/benchmark.json"
    rows=read(ROOT/path); before=deepcopy(rows); protected={}; changes=[]; selected={}
    for row in rows:
        if row.get("year")!=2023: continue
        pid=row["problem_id"]; number=int(pid[-2:]); edit=repair(number,row["problem_description"])
        row["problem_description"]=edit.text; selected[pid]=row
        for a in row["assets"]: protected[a["path"]]=sha(ROOT/a["path"])
        changes.append(dict(task_id="iiot/"+pid, source_file=row["source_file"], source_sha256=sha(ROOT/row["source_file"]),
                            reviewed_pages=list(range(1,4 if number in (5,7) else 3)), edits=edit.changes,
                            samples=len(SAMPLES[number])))
    require(len(selected)==9,"Selection drift")
    writes={path:rows}
    for layout in ("base","last_exam"):
        for card in read(ROOT/f"data/{layout}/task_cards.json")["tasks"]:
            pid=card["task_id"].split("/",1)[1]
            if pid not in selected: continue
            folder=ROOT/f"data/{layout}"/card["source_repo_path"]; prompt=rel(folder/"base/input/problem.md")
            old=next(r for r in before if r["problem_id"]==pid)["problem_description"]
            require((ROOT/prompt).read_text(encoding="utf-8")==old+"\n","Prompt drift")
            writes[prompt]=selected[pid]["problem_description"]+"\n"
            protected.update({rel(f):sha(f) for f in folder.rglob("*") if f.is_file() and rel(f)!=prompt})
        for name in ("task_cards.json","input_asset_manifest.json","index.json","README.md"):
            p=f"data/{layout}/{name}"; protected[p]=sha(ROOT/p)
    for tree in ("data/rules","data/rubrics","data/viz"):
        protected.update({rel(f):sha(f) for f in (ROOT/tree).rglob("*") if f.is_file()})
    for track in read(ROOT/"data/benchmarks/index.json")["olympiads"]:
        p=track["benchmark_path"]
        if p!=path: protected[p]=sha(ROOT/p)
    protected["data/benchmarks/index.json"]=sha(ROOT/"data/benchmarks/index.json")
    store.save(CACHE+"/plan.json",dict(writes=writes,before_rows=before,changes=changes,protected=protected,
               expected={p:sha(ROOT/p) for p in writes}))
    print(json.dumps(dict(records=9,files=len(writes),sample_pairs=sum(len(v) for v in SAMPLES.values()))))


def verify(plan):
    for p,v in plan["writes"].items():
        require(((ROOT/p).read_text(encoding="utf-8") if isinstance(v,str) else read(ROOT/p))==v,"Write drift: "+p)
    for p,h in plan["protected"].items(): require(sha(ROOT/p)==h,"Protected drift: "+p)
    expected=deepcopy(plan["before_rows"])
    for row in expected:
        if row.get("year")==2023: row["problem_description"]=repair(int(row["problem_id"][-2:]),row["problem_description"]).text
    require(expected==read(ROOT/"data/benchmarks/iiot/benchmark.json"),"Non-prompt changes")
    return dict(records=9,content_files=19,sample_pairs=14,reviewed_pages=20,
                protected_files_unchanged=len(plan["protected"]),sources_tests_scores_readiness_unchanged=True)


def apply():
    require(not (ROOT/REPORT).exists(),"Already applied")
    plan=read(ROOT/CACHE/"plan.json")
    for p,h in {**plan["expected"],**plan["protected"]}.items(): require(sha(ROOT/p)==h,"Concurrent edit: "+p)
    store=Store(ROOT)
    report=dict(operation="source_verified_iiot_2023_sample_and_math_repair",backup=rel(store.backup),
                changes=plan["changes"],status="preparing")
    store.finish(report)
    for p,v in plan["writes"].items(): store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    report.update(status="completed",validation=verify(plan))
    store.save(REPORT,report); store.finish(report)
    print(json.dumps(report["validation"]))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("mode",choices=("prepare","apply","verify")); mode=parser.parse_args().mode
    if mode=="verify": print(json.dumps(verify(read(ROOT/CACHE/"plan.json"))))
    else: {"prepare":prepare,"apply":apply}[mode]()
