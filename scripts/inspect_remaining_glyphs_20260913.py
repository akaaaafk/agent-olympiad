"""Render original pages and retain extraction evidence for the remaining glyph queue."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import sys
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.repair_iol_sources_20260913 import POPPLER, read, sha, rel

CACHE = "data/.cache/remaining_glyphs_20260913"
RENDER = "tmp/pdfs/remaining_glyphs_20260913"
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
PAGES = {
    "eoes_EOES2025_Task1_TaskSheet-final": [10,11,15,16,17,18,19,20,21],
    "eoes_EOES2025_Task2_TaskSheet_final": [4,5,6,7,8,9,10,11,12,13,14,15],
    "eoes_EUSO_I_2004_TaskB": list(range(2,10)),
    "eoes_TEST2 final version English": [5,9,13],
    "eoes_P1Tasks": [8],
    "eoes_additionalfileschallenge1": [1,2,3,4],
    "iiot_2021_05": [1,2,3],
}


def main():
    store = Store(ROOT)
    tasks, sources = [], []
    for cid in ("eoes", "iiot"):
        for row in read(ROOT/f"data/benchmarks/{cid}/benchmark.json"):
            pid=row["problem_id"]
            if pid not in PAGES: continue
            source = ROOT/row["source_file"]
            entries=[]
            with pymupdf.open(source) as document:
                for n in PAGES[pid]:
                    if n>len(document): continue
                    page=document[n-1]
                    prefix=ROOT/RENDER/pid/"page"
                    prefix.parent.mkdir(parents=True,exist_ok=True)
                    tasks.append([str(POPPLER/"pdftoppm.exe"),"-f",str(n),"-l",str(n),"-r","115","-png",str(source),str(prefix)])
                    entries.append(dict(page=n,text=page.get_text(),spans=[s for b in page.get_text("dict")["blocks"] if "lines" in b for line in b["lines"] for s in line["spans"]]))
            sources.append(dict(task_id=cid+"/"+pid,source_file=row["source_file"],sha256=sha(source),pages=entries))
    store.save(CACHE+"/source_review.json",dict(records=sources))
    def render(args):
        subprocess.run(args,check=True,capture_output=True)
        print(json.dumps(dict(source=args[-2],page=args[2])),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(render,tasks))
    print(json.dumps(dict(sources=len(sources),rendered_pages=len(tasks))))


if __name__ == "__main__": main()
