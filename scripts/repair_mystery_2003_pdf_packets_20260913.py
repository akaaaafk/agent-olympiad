"""Recover three explicitly linked 2003 PDF packets without executing PostScript."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pymupdf as fitz
from PIL import Image
from scripts.repair_mystery_2003_static_20260913 import SCRIPT,sanitize
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2003_pdf_packets_20260913/'
RAW='data/raw/mystery_hunt/separated_2003_pdf_20260913/'
REPORT='data/benchmarks/mystery_2003_pdf_packets_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (368,373,398)}
FILES={368:['4_9.pdf','4_9.ps'],373:['5_2.pdf','5_2.ps'],398:['datasheet.pdf']+[f'schematics-{n}.pdf' for n in range(1,6)]}
MIME={'.pdf':'application/pdf','.ps':'application/postscript','.jpg':'image/jpeg'}
POPPLER=ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==3 and all(r['year']==2003 for r in chosen),'Selection drift')
    urls=set();refs={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'];urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        images=[t['src'] for t in soup.find_all('img')]
        require(len(images)==2 and all(x.startswith('images/') and x.endswith('.jpg') for x in images),'Image drift')
        linked=[a['href'] for a in soup.find_all('a') if a.get('href','').endswith(('.pdf','.ps'))]
        require(linked==FILES[int(row['problem_id'][-5:])],'Attachment drift')
        refs[row['problem_id']]=images+linked;urls.update(urljoin(url,r) for r in images+linked)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    updates=[];copies=[];pdfs=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];source=ROOT/row['source_file'];url='https://puzzles.mit.edu/'+row['puzzle_url']
        remote=ROOT/snapshots[url]['path']
        require(SCRIPT.sub(b'',source.read_bytes()).replace(b'\r',b'')==SCRIPT.sub(b'',remote.read_bytes()).replace(b'\r',b''),'Publisher HTML differs')
        payload,edits=sanitize(source.read_bytes());folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True)
        public=[]
        def add(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name
            copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
            return target
        add(payload,'puzzle.html','text/html')
        for ref in refs[pid]:
            name=Path(ref).name;original=ROOT/snapshots[urljoin(url,ref)]['path'];data=original.read_bytes();suffix=Path(name).suffix
            for local in (source.parent/ref,source.parent/name):
                if local.is_file():require(sha(local)==sha(original),'Legacy attachment differs')
            if suffix=='.pdf':
                require(data.startswith(b'%PDF-'),'Not PDF')
                with fitz.open(stream=data,filetype='pdf') as doc:
                    require(not doc.is_encrypted and len(doc)>0,'Unreadable PDF')
                    # Inspect object dictionaries, not only the byte header.
                    objects='\n'.join(doc.xref_object(n) for n in range(1,doc.xref_length()))
                    require(not any(k in objects for k in ('/JavaScript','/Launch','/EmbeddedFile','/RichMedia','/OpenAction')),'Active PDF dependency')
                    pdfs.append(dict(problem_id=pid,name=name,pages=len(doc),sha256=sha(original)))
            elif suffix=='.ps':
                # Antiphony uses the valid minimal %! header, not DSC %!PS.
                # Its publisher labels it obfuscated; preserve, never execute.
                require(data.startswith(b'%!'),'Not PostScript')
            else:
                with Image.open(original) as im:im.verify()
            add(data,name,MIME[suffix])
        clean=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
        note='The original PDFs are the complete static puzzle materials. PostScript alternatives, where present, are archived as inert source files and were not executed. Historical rules and visual/spatial grading remain uncertified.'
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` and its linked PDF files. Their original page geometry, notation and images are preserved; no flattened preview replaces them.\n\nArchive limitation: '+note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_static_packet_original_archive_judge_only',
            asset_policy='Only explicit HTML/PDF/media and inert PostScript alternatives are public; solution links, archive scripts and index navigation are excluded. No source program was executed.')
        row['evaluation']['limitations']='Static PDF packet recovered; no gold or evaluator recertification. '+note+' Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2003_pdf_packets_20260913',original_source_file=old['source_file'],original_sha256=sha(source),
            publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=edits,
            attachment_names=refs[pid],pdfs=[p for p in pdfs if p['problem_id']==pid],postscript_executed=False,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,pdf_inventory=pdfs))
    print(json.dumps(dict(records=3,public_files=len(copies),pdfs=pdfs),indent=2))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    plan=read(ROOT/CACHE/'plan.json')
    for p in plan['pdf_inventory']:
        out=ROOT/'tmp/pdfs/mystery_2003_pdf_20260913'/p['problem_id']/Path(p['name']).stem;out.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(POPPLER),'-r','100','-png',str(ROOT/CACHE/p['problem_id']/'input'/p['name']),str(out/'page')],check=True,capture_output=True,timeout=45)
        require(len(list(out.glob('page-*.png')))==p['pages'],'Render count differs')
        print(p['problem_id'],p['name'],p['pages'],flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
