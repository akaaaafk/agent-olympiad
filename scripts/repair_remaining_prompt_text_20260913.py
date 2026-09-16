"""Visually verified EOES/IIOT prompt corrections; original packets remain authoritative."""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.repair_iol_sources_20260913 import read, sha, rel, require
from scripts.inspect_remaining_glyphs_20260913 import PAGES, CONTROL

CACHE="data/.cache/remaining_glyphs_20260913"
REPORT="data/excluded/benchmark_audit_reports/remaining_prompt_repair_20260913.json"

class Editor:
    def __init__(self,text): self.text=text; self.changes=[]
    def rx(self,pattern,new,count=1):
        found=list(re.finditer(pattern,self.text,re.S))
        require(len(found)==count,f"Expected {count}, got {len(found)}: {pattern!r}")
        self.changes.extend(dict(before=m.group(),after=new) for m in found)
        self.text=re.sub(pattern,lambda m:new,self.text,flags=re.S)
    def rep(self,old,new,count=1): self.rx(re.escape(old),new,count)
    def all(self,old,new):
        count=self.text.count(old)
        require(count>0,f"Missing reviewed token {old!r}")
        self.rep(old,new,count)


def task1(text):
    e=Editor(text)
    e.rx(r"\x01\x02.*?\x12(?:\t|\))", "IO_3^−(aq) + 5I^−(aq) + 6H^+(aq) → 3I_2(aq) + 3H_2O(l)",3)
    e.rx(r"2\x14\x15.*?\x01\x11 \(\x07\x08 \)","2Fe^{3+}(aq) + 2I^−(aq) → 2Fe^{2+}(aq) + I_2(aq)")
    e.rx(r"\x01\x11 \x06.*?\x16\x17\x02\x18.*?\x06\x07\x08\t", "I_2(aq) + 2S_2O_3^{2−}(aq) → 2I^−(aq) + S_4O_6^{2−}(aq)")
    e.rep("form free iodine. \n \n", "form free iodine.\nI^−(aq) + 3ClO^−(aq) → IO_3^−(aq) + 3Cl^−(aq)\n\n")
    for old,new in [("\x19\n\x1a","n_1"),("\x19\x1a","n_1"),("\x19\x11","n_2"),("\x1b\x1a","α_1"),("\x1b\x11","α_2"),("\x1b*","α_i"),("\x19air","n_air")]: e.all(old,new)
    e.all(", \x1f ,\x06-\t","Y = Y(X)")
    e.all("\x06-*, ,*)","(X_i, Y_i)")
    for old,new in [("\x19","n"),("\x1b","α"),("\x1f","="),("\x06","("),("\t",")"),("$","d"),("&","y")]: e.all(old,new)
    e.rx(r"%(?=\s*(?:exact|\(cm\)))","x",8)
    e.rep("(%, y)","(x, y)",2)
    e.rep("(the index \n ) indicates", "(the index i indicates")
    e.rep("and + is outer width", "and w is outer width")
    e.rep("Figure 3.1. The propagation", "Snell's law: n_1 sin(α_1) = n_2 sin(α_2).\nFigure 3.1. The propagation")
    e.rep(" (3. 1) ", "d(α; n) = w sin(α) / sqrt(n^2 − sin^2(α))  (3.1) ")
    e.rep("\n(3.2)  ","\nsin(α_i) sqrt(w^2 + d_i^2) = n d_i  (3.2)  ")
    e.rep("\n(3.3)  ","\nX_i = d_i; Y_i = sin(α_i) sqrt(w^2 + d_i^2)  (3.3)  ")
    e.rep("\n (3.4)  ","\nY_i = n X_i  (3.4)  ")
    e.rep("\uf0fd","☒")
    e.rep("n_1and","n_1 and",2)
    return e


def task2(text):
    e=Editor(text)
    # Floating equation glyph runs are removed, then placed beside their own
    # printed equation numbers. No unlabeled solution or measured data is added.
    e.rx(r"\x01CV = \x05\x06\x07 \x08\tBL\s+\tCV\s+\x0c", "")
    e.rx(r"\[CV \] = \x01CV\s+\x14 ∙ \x05 =\s*\x05\x06\x07 \x16\tBL\s+\tCV\s+\x17\s+\x14 ∙ \x05", "")
    e.rx(r"\x05\x18 \x19\s*\[CV \]\x1a\s*\[CV \]0\s*\x1c = −\r′\x1a", "")
    e.rx(r"\x05\x18 \x19\[CV \]\x1a.{0,250}?− \x05\x18 \x1d\x010\x1e", "")
    e.rep("\x05\x18 \x1d\x01\x1a\x1e = \x05\x18 \x1d\x010\x1e − \r′\x1a", "")
    e.rep("\r′ = \r[OH −]", "")
    for number,formula in {
        2:"A_CV = log(U_BL / U_CV)",
        3:"[CV] = A_CV / (ε · l) = log(U_BL / U_CV) / (ε · l)",
        4:"ln([CV]_t / [CV]_0) = −k′t",
        5:"k′ = k[OH^−]",
        6:"ln([CV]_t / [CV]_0) = ln((A_t / (ε · l)) / (A_0 / (ε · l))) = ln(A_t / A_0) = ln(A_t) − ln(A_0)",
        7:"ln(A_t) = ln(A_0) − k′t",
    }.items(): e.rx(r"(?<=\n) +\("+str(number)+r"\)",formula+f"  ({number})")
    e.rep("\t\x1f !!!!!","mean(U_BL)",2)
    e.rep('"# \x1d$%\x1e',"ln(A_t)")
    e.rep("\x05\x18 \x1d\x01&\x1e","ln(A_t)")
    e.rep("solu\x1eon","solution")
    for old,new in [("omiJed","omitted"),("equaKons","equations"),("reacKon","reaction"),
                    ("PlasKc","Plastic"),("shaU","shaft"),("mulKple","multiple"),
                    ("calcula.ons","calculations"),("calcula.on","calculation"),
                    ("reac.on","reaction"),("s.cker","sticker")]: e.all(old,new)
    e.rep("(\x1d\x1a\x1e = (\x1d0\x1e *+,&", "θ(t) = θ(0) exp(−γt)")
    e.rep(". = 2230\n\x07", "T = 2π sqrt(R/g)")
    e.rep("ln (\x1d\x1a\x1e = ln (\x1d0\x1e − - \x1a", "ln θ(t) = ln θ(0) − γt")
    e.rep("- = 7\n \n8 ,", "γ = C L/m,")
    e.rx(r"/9\s+:⎯⎯< /9.*?/CBD ,9", "L_i → L_i m_0/m_i = L_i m_0/(m_0 + m_{i,paper}) = L_{ren,i}")
    e.rx(r"- = \x08 7\n6=\n\x0c \x19/9.*?\x0c /CBD ,9", "γ = (C/m_0)(L_i m_0/(m_0 + m_{i,paper})) = (C/m_0)L_{ren,i}")
    # Ordinary punctuation also encodes math glyphs in this one source section.
    start=e.text.index("Problem 2. Velocity and Drag")
    end=e.text.index("Problem 3.",start)
    p=Editor(e.text[start:end])
    for old,new in [("displacement ( decreases","displacement θ decreases"),("displace ment ( without","displacement θ without"),
                    ("((0)","θ(0)"),("time \x1a = 0","time t = 0"),("( \x04 0","θ = 0"),
                    ("angle \n( comment","angle θ comment"),("angle ( ln  ()","angle (ln θ)"),
                    ("Period . is","Period T is"),("period . of","period T of"),("p eriod .,","period T,"),
                    ("length 0,","length R,"),("where 0 is","where R is"),("\x07","g"),
                    ("and - is","and γ is"),("constant -).","constant γ)."),("constants - for","constants γ for"),
                    ("factor - to","factor γ to"),("constant - is","constant γ is"),("of - as","of γ as"),
                    ("slope '–-'","slope '−γ'"),("mass 6 of","mass m of"),("on 6,","on m,"),
                    ("6\n0 is","m_0 is"),("where 7 is","where C is"),("constant 7 and","constant C and")]: p.all(old,new)
    # Replace only the source's standalone L glyphs, never division operators
    # in the repaired equations or the m/s unit.
    l_pattern=r"/(?=\s|[),]|ren)"
    p.rx(l_pattern,"L",len(re.findall(l_pattern,p.text)))
    p.rep("m/s 2","m/s^2")
    p.rep("L\nE","L_i")
    p.rep("Lren, E","L_{ren,i}")
    p.rep("L\nren, E","L_{ren,i}")
    e.changes.extend(p.changes)
    e.text=e.text[:start]+p.text+e.text[end:]
    return e


def repair(pid,text):
    if pid=="eoes_EOES2025_Task1_TaskSheet-final": e=task1(text)
    elif pid=="eoes_EOES2025_Task2_TaskSheet_final": e=task2(text)
    else:
        e=Editor(text)
        if pid=="eoes_EUSO_I_2004_TaskB":
            for n in range(8): e.rep(chr(20+n),f"[PDF page {n+2}]")
        elif pid=="eoes_TEST2 final version English":
            e.rep("\x01","▪",5); e.rep("\x02","→",3)
        elif pid=="eoes_P1Tasks":
            e.rep("24 \x01h","24 h [spacing glyph is unreadable in the original PDF]")
        elif pid=="eoes_additionalfileschallenge1":
            e.rx(r"(?m)^(?:CHALLENGE 1|Challenge 1 Task A)[^\n]*", "Challenge 1 Task A [original header contains unreadable glyphs]",4)
            e.text += "\n\nSource-page guide: PDF page 1 contains the crayfish diagram with labels 1-13 and regions A/B; page 2 contains the blank Function table with rows 1-19; pages 3 and 4 contain two differently sized outline drawings. Read all four original pages; this text preview does not replace their geometry."
        elif pid=="iiot_2021_05":
            e.rep("0≤Ti≤109", "0≤Ti≤10^9")
            e.rep("III ((( OOO TTT +++ III ))) ;;;", "IIOT")
            e.rep("ὖE"*5,"[five-book difficulty indicator; see original colors]",7)
            e.rx(r"Examples input.txt output.txt.*? Explanation ", """Examples

Sample 1 input:
```text
5 2
3 10
4 1
3 5
-1 20
3 2
```
Sample 1 output: `5`

Sample 2 input:
```text
7 2
1 10
-1 1
3 10
1 3
1 7
0 7
5 9
```
Sample 2 output: `14`

Explanation """)
            e.rep("0\x1a\x1a10 0 11 25 3\x1a\x1a20 0 42", "[First example diagram: root 3; edges 3→0, 3→4, 3→2, 4→1. Durations: task 0 = 10, task 1 = 1, task 2 = 5, task 3 = 20, task 4 = 2 hours. Tasks 0 and 3 are skipped, so their durations become 0.]")
            e.rep("0\x1a\x1a10 0 11 210 33 47 5\x017 0 69", "[Second example diagram: root 1; edges 1→0, 1→3, 1→4, 0→5, 3→2, 5→6. Durations: task 0 = 10, task 1 = 1, task 2 = 10, task 3 = 3, task 4 = 7, task 5 = 7, task 6 = 9 hours. Tasks 0 and 5 are skipped, so their durations become 0.]")
        else: raise ValueError(pid)
    require(not CONTROL.search(e.text),"Unreviewed control remains: "+pid)
    return e


def verify(plan):
    for path,value in plan["writes"].items():
        actual=(ROOT/path).read_text(encoding="utf-8") if isinstance(value,str) else read(ROOT/path)
        require(actual==value,"Write mismatch: "+path)
    for path,h in plan["protected"].items(): require(sha(ROOT/path)==h,"Protected file changed: "+path)
    for cid,before in plan["before_rows"].items():
        after=read(ROOT/f"data/benchmarks/{cid}/benchmark.json")
        require(len(before)==len(after),"Membership changed")
        for a,b in zip(before,after):
            c=deepcopy(a)
            if a["problem_id"] in PAGES: c["problem_description"]=repair(a["problem_id"],a["problem_description"]).text
            require(c==b,"Non-prompt mutation")
    return dict(records=7,control_characters_repaired=sum(v["controls_before"] for v in plan["changes"]),
                content_files=len(plan["writes"]),task_prompt_copies=14,protected_files_unchanged=len(plan["protected"]),
                original_sources_unchanged=True,answers_scores_readiness_unchanged=True)


def prepare():
    require(not (ROOT/CACHE/"plan.json").exists(),"Already prepared")
    evidence={r["task_id"]:r for r in read(ROOT/CACHE/"source_review.json")["records"]}
    store=Store(ROOT); writes={}; before_rows={}; changes=[]; protected={}
    for cid in ("eoes","iiot"):
        path=f"data/benchmarks/{cid}/benchmark.json"
        before_rows[cid]=deepcopy(store.read(path)); rows=deepcopy(before_rows[cid])
        for row in rows:
            pid=row["problem_id"]
            if pid not in PAGES: continue
            ev=evidence[cid+"/"+pid]
            require(sha(ROOT/ev["source_file"])==ev["sha256"],"Reviewed source changed")
            for a in row["assets"]: protected[a["path"]]=sha(ROOT/a["path"])
            edit=repair(pid,row["problem_description"])
            changes.append(dict(task_id=cid+"/"+pid,source_file=ev["source_file"],source_sha256=ev["sha256"],
                                reviewed_pages=PAGES[pid],controls_before=len(CONTROL.findall(row["problem_description"])),edits=edit.changes))
            row["problem_description"]=edit.text
        writes[path]=rows
    for layout in ("base","last_exam"):
        cards=read(ROOT/f"data/{layout}/task_cards.json")["tasks"]
        for card in cards:
            cid,pid=card["task_id"].split("/",1)
            if pid not in PAGES: continue
            folder=ROOT/f"data/{layout}"/card["source_repo_path"]
            p=rel(folder/"base/input/problem.md")
            before=next(r for r in before_rows[cid] if r["problem_id"]==pid)["problem_description"]
            require((ROOT/p).read_text(encoding="utf-8")== (before+"\n").replace("\r\n","\n").replace("\r","\n"),"Existing prompt drift")
            writes[p]=next(r for r in writes[f"data/benchmarks/{cid}/benchmark.json"] if r["problem_id"]==pid)["problem_description"]+"\n"
            protected.update({rel(f):sha(f) for f in folder.rglob("*") if f.is_file() and rel(f)!=p})
        for name in ("task_cards.json","input_asset_manifest.json","index.json","README.md"):
            p=f"data/{layout}/{name}"; protected[p]=sha(ROOT/p)
    for tree in ("data/rules","data/rubrics","data/viz"):
        protected.update({rel(f):sha(f) for f in (ROOT/tree).rglob("*") if f.is_file()})
    for t in store.read("data/benchmarks/index.json")["olympiads"]:
        if t["benchmark_path"] not in writes: protected[t["benchmark_path"]]=sha(ROOT/t["benchmark_path"])
    protected["data/benchmarks/index.json"]=sha(ROOT/"data/benchmarks/index.json")
    require(len(changes)==7,"Unexpected selection")
    plan=dict(writes=writes,before_rows=before_rows,changes=changes,protected=protected,expected={p:sha(ROOT/p) for p in writes})
    store.save(CACHE+"/plan.json",plan)
    print(json.dumps(dict(records=7,files=len(writes),controls=sum(v["controls_before"] for v in changes))))


def apply():
    require(not (ROOT/REPORT).exists(),"Already applied")
    plan=read(ROOT/CACHE/"plan.json"); store=Store(ROOT)
    for path,h in {**plan["expected"],**plan["protected"]}.items(): require(sha(ROOT/path)==h,"Concurrent change: "+path)
    report=dict(operation="source_verified_eoes_iiot_prompt_repair",backup=rel(store.backup),changes=plan["changes"],status="preparing")
    store.finish(report)
    for p,v in plan["writes"].items(): store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    report.update(status="completed",validation=verify(plan))
    store.save(REPORT,report); store.finish(report)
    print(json.dumps(dict(backup=report["backup"],validation=report["validation"]),indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("mode",choices=("prepare","apply","verify","preview")); mode=parser.parse_args().mode
    if mode=="preview":
        for cid in ("eoes","iiot"):
            for row in read(ROOT/f"data/benchmarks/{cid}/benchmark.json"):
                if row["problem_id"] in PAGES:
                    edit=repair(row["problem_id"],row["problem_description"])
                    Store(ROOT).save_text(CACHE+"/previews/"+row["problem_id"]+".md",edit.text)
                    print(json.dumps(dict(id=row["problem_id"],edits=len(edit.changes)),ensure_ascii=True))
    elif mode=="verify": print(json.dumps(verify(read(ROOT/CACHE/"plan.json"))))
    else: {"prepare":prepare,"apply":apply}[mode]()
