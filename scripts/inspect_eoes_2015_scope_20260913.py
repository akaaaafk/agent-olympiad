"""Read-only source rendering; generated PNGs and text are private review aids."""
from pathlib import Path
import subprocess
import pymupdf
from scripts.repair_mystery_2001_packets_20260913 import ROOT, Store, sha

CACHE='data/.cache/eoes_2015_scope_20260913/'
SOURCES={
 'challenge1':('data/raw/eoes/euso/2015/ExpBlowingintheWind.pdf',[2,4,6,7]),
 'challenge2':('data/raw/eoes/euso/2015/tasksheet2.pdf',[2,21,23,28]),
 'additional':('data/raw/eoes/euso/2015/additionalfileschallenge1.pdf',[1,2,3,4]),
}

def main():
    out=ROOT/CACHE/'review';out.mkdir(parents=True,exist_ok=True);summary=[]
    poppler=ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'
    for key,(source,pages) in SOURCES.items():
        with pymupdf.open(ROOT/source) as doc:
            summary.append(dict(key=key,source_file=source,sha256=sha(ROOT/source),pages=len(doc),review_pages=pages))
            for page in pages:
                Store(ROOT).save_text(CACHE+f'review/{key}-{page}.txt',doc[page-1].get_text(sort=True))
                subprocess.run([str(poppler),'-f',str(page),'-l',str(page),'-singlefile','-scale-to','1500','-png',str(ROOT/source),str(out/f'{key}-{page}')],check=True,capture_output=True)
    Store(ROOT).save(CACHE+'source-review.json',summary)
    print(summary)

if __name__=='__main__':main()
