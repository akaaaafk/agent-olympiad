"""Read-only canonical audit: render remaining IIOT statements for source review."""
import json
from pathlib import Path
import subprocess
import sys
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.repair_iol_sources_20260913 import read,sha
POPPLER=ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'
CACHE='data/.cache/iiot_remaining_text_20260913/'

def main():
    selected=[r for r in read(ROOT/'data/benchmarks/iiot/benchmark.json') if r['year']!=2023]
    report=[];store=Store(ROOT)
    for r in selected:
        pid=r['problem_id'];source=ROOT/r['source_file'];out=ROOT/'tmp/pdfs/iiot_remaining_text_20260913'/pid;out.mkdir(parents=True,exist_ok=True)
        with pymupdf.open(source) as doc:
            pages=[p.get_text() for p in doc];report.append(dict(problem_id=pid,source_file=r['source_file'],sha256=sha(source),pages=len(pages)))
        store.save_text(CACHE+pid+'.txt','\n\n'.join('PAGE '+str(i)+'\n'+t for i,t in enumerate(pages,1)))
        if not (out/'page-1.png').exists():
            subprocess.run([str(POPPLER),'-r','100','-png',str(source),str(out/'page')],check=True,capture_output=True,timeout=45)
        print(pid,len(pages),flush=True)
    store.save(CACHE+'source_inventory.json',report)

if __name__=='__main__':main()
