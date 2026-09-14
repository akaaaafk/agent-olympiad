"""Recover remaining 2005 attachments and separate the live performers' script."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urljoin
import pymupdf as fitz
from bs4 import BeautifulSoup
from scripts.repair_mystery_2005_static_20260913 import sanitize,source_equal
from scripts.repair_mystery_linked_archives_20260913 import inspect_audio
from scripts.repair_mystery_2003_pdf_packets_20260913 import POPPLER
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2005_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2005_media_20260913/'
REPORT='data/benchmarks/mystery_2005_media_repair_20260913.json'
FILES={605:['axtogrind.mp3'],612:[],628:['lscpuzzle.pdf'],686:['reflecting pool.pdf'],715:['trivial pursuit.pdf']}
SELECTED={f'mystery_hunt_{n:05}' for n in FILES}
LIMITS={605:'The original audio file is byte-preserved and structurally checked, not transcribed or semantically certified.',
        612:'Only the pre-event invitation is initial input. The archive also contains casting, performer cues and a musical script; those remain in the judge-only original. The live event and a staged delivery mechanism are not reconstructed.',
        628:'The published pre-screening handout is included. The film itself, screening environment and viewer observations are not supplied or inferred.',
        686:'The original one-page visual puzzle is preserved. Layout-aware interpretation and evaluation remain uncertified.',
        715:'The original one-page puzzle, its colors and photograph are preserved. Time-sensitive facts must be interpreted in the 2005 setting; no modern facts or answers are substituted.'}


def initial_html(data,n):
    payload,edits=sanitize(data);deferred=None
    if n==612:
        pattern=rb'<pre>\s*NIGHTCLUB MEDLEY \(Lounge Singer Puzzle\).*?</pre>'
        matches=re.findall(pattern,payload,re.S);require(len(matches)==1,'Performer-script boundary drift');deferred=matches[0].decode('ascii')
        payload=re.sub(pattern,b'',payload,flags=re.S);edits.append(dict(reason='keep casting and performer-only script out of initial invitation',section='NIGHTCLUB MEDLEY (Lounge Singer Puzzle)'))
    return payload,edits,deferred


def audio_structure(path):
    data=path.read_bytes();require(data[:6]==b'ID3\x04\x00\x40','Unexpected ID3 header')
    require(all(b<128 for b in data[6:10]),'Invalid synchsafe length')
    tag_end=10+sum(data[6+i]<<(7*(3-i)) for i in range(4));start=tag_end
    while start<len(data) and data[start]==0:start+=1
    require(tag_end==45 and start==462,'Audio prefix drift')
    result=inspect_audio(SimpleNamespace(read_bytes=lambda:data[start:]),'audio/mpeg')
    result.update(id3_bytes=tag_end,zero_padding_bytes=start-tag_end,original_prefix_preserved=True)
    return result


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==5,'Selection drift');urls=set()
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'].rstrip('/')+'/';urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser');links=[a['href'] for a in soup.find_all('a') if a.get('href')!='solution.html']
        require(links==FILES[int(row['problem_id'][-5:])] and not soup.find_all(['img','link','iframe','embed','object']),'Attachment drift')
        urls.update(urljoin(url,ref) for ref in links)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    updates=[];copies=[];pdfs=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];n=int(pid[-5:]);source=ROOT/row['source_file'];url='https://puzzles.mit.edu/'+row['puzzle_url'].rstrip('/')+'/';remote=ROOT/snapshots[url]['path']
        source_equal(source,remote);payload,edits,deferred=initial_html(source.read_bytes(),n);folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];audio={}
        def add(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        add(payload,'puzzle.html','text/html')
        for ref in FILES[n]:
            p=ROOT/snapshots[urljoin(url,ref)]['path'];data=p.read_bytes();legacy=source.parent/ref
            if legacy.is_file():require(sha(legacy)==sha(p),'Legacy attachment differs')
            if ref.endswith('.pdf'):
                require(data.startswith(b'%PDF-'),'Not PDF')
                with fitz.open(stream=data,filetype='pdf') as doc:
                    require(not doc.is_encrypted and len(doc)>0,'Unreadable PDF');objects='\n'.join(doc.xref_object(i) for i in range(1,doc.xref_length()))
                    require(not any(k in objects for k in ('/JavaScript','/Launch','/EmbeddedFile','/RichMedia','/OpenAction')),'Active PDF dependency')
                    pdfs.append(dict(problem_id=pid,name=ref,pages=len(doc),sha256=sha(p)))
                mime='application/pdf'
            else:audio[ref]=audio_structure(p);mime='audio/mpeg'
            add(data,ref,mime)
        clean=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
        note=LIMITS[n]
        public_note='Only the original pre-event invitation is provided. Live performance, observations and host interaction remain unresolved.' if n==612 else note
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` and its explicit attachments for original layout and media. No text preview replaces their colors, marks, spacing or timing.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_initial_packet_original_archive_judge_only',asset_policy='Only explicit public puzzle materials are initial inputs. Archive solution controls and performer-only scripts are not released. No film, historical observations or host responses are synthesized.')
        row['evaluation']['limitations']=note+' Gold and scores are retained, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2005_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=edits,deferred_performer_section=deferred,audio_structure=audio,pdfs=[p for p in pdfs if p['problem_id']==pid],answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,pdf_inventory=pdfs))
    print(json.dumps(dict(records=5,public_files=len(copies),pdfs=pdfs)))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1800','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed')
    for pdf in read(ROOT/CACHE/'plan.json')['pdf_inventory']:
        folder=ROOT/'tmp/pdfs/mystery_2005_media_20260913'/pdf['problem_id'];folder.mkdir(parents=True,exist_ok=True)
        p=subprocess.run([str(POPPLER),'-scale-to','1600','-png',str(ROOT/CACHE/pdf['problem_id']/'input'/pdf['name']),str(folder/'page')],capture_output=True,timeout=45)
        require(p.returncode==0,'PDF render failed');print(pdf['problem_id'],pdf['pages'],flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
