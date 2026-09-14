"""Restore four static page boundaries without releasing other rooms or late hints."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2003_static_20260913 import SCRIPT,sanitize as static_sanitize
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2003_scoped_20260913/'
RAW='data/raw/mystery_hunt/separated_2003_scoped_20260913/'
REPORT='data/benchmarks/mystery_2003_scoped_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (384,431,433,451)}
LIMITS={384:'Only the section meta page and its original grid are supplied. Eight linked puzzle titles are retained as text; their tasks and prior answers are not injected. The historical meta context remains unresolved.',
        431:'Only this room page is supplied. Original exit labels remain as inert text. Other rooms, shortcut solutions and navigation state are not included.',
        433:'Only this room page is supplied. Original exit labels remain as inert text. Other rooms, shortcut solutions and navigation state are not included.',
        451:'The publisher labels a deck-order clarification Saturday evening. That later note is retained in the judge-only original, not initial input. Initial deck variation and a timed-release mechanism remain unresolved.'}


def sanitize(data,pid):
    edits=[];late=None
    def sub(pattern,replacement,count,reason):
        nonlocal data
        matches=list(re.finditer(pattern,data,re.I|re.S));require(len(matches)==count,'Unexpected '+reason)
        edits.append(dict(reason=reason,count=count,removed=[m[0].decode('ascii') for m in matches]))
        data=re.sub(pattern,replacement,data,flags=re.I|re.S)
    n=int(pid[-5:])
    if n==451:
        data,edits=static_sanitize(data)
        pattern=rb'<strong>Saturday evening note:.*?</strong>'
        found=re.findall(pattern,data,re.I|re.S);require(len(found)==1,'Late note drift');late=found[0].decode('ascii')
        sub(pattern,b'',1,'defer explicitly later Saturday evening note')
    else:
        require(len(SCRIPT.findall(data))==1,'Script count differs');data=SCRIPT.sub(b'',data)
        edits.append(dict(reason='remove archive answer checker',count=1))
        if n==384:
            sub(rb'<a\b[^>]*href="\.\./\.\./solutions/m5\.html"[^>]*>\(Meta-puzzle solution\)</a>',b'',1,'remove meta solution navigation')
            sub(rb'<a\b[^>]*href="5_[1-8]\.html"[^>]*>(.*?)</a>',rb'\1',8,'make other-puzzle navigation inert, preserve labels')
            sub(rb'<a\b[^>]*href="\.\./index\.html"[^>]*>Back to the index</a>',b'',1,'remove archive index navigation')
            data=re.sub(rb'(src=")images/([^"/]+)(")',rb'\1\2\3',data)
            edits.append(dict(reason='localize same-byte header/footer images'))
        else:
            sub(rb'<a\b[^>]*href="\.\./\.\./\.\./solutions/[^"/]+\.html"[^>]*>\(Solution\)</a>',b'',1,'remove room solution navigation')
            sub(rb'\(<a\b[^>]*href="\.\./\.\./\.\./solutions/all-r\.html"[^>]*>Shortcuts</a>\)',b'',1,'remove shortcut solution navigation')
            sub(rb'<a\b[^>]*href\s*=\s*"\.\./[0-9]_[0-9]{3}/index\.html"[^>]*>(.*?)</a>',rb'\1',4,'make exits inert, preserve labels')
    return data,edits,late


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==4 and all(r['year']==2003 for r in chosen),'Selection drift')
    urls=set();refs={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'];urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        refs[row['problem_id']]=[t['src'] for t in soup.find_all('img')]
        require(all(re.fullmatch(r'images/(?:head|foot)[5t]\.jpg',n) for n in refs[row['problem_id']]),'Image drift')
        urls.update(urljoin(url,r) for r in refs[row['problem_id']])
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];source=ROOT/row['source_file'];url='https://puzzles.mit.edu/'+row['puzzle_url'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher differs')
        payload,edits,late=sanitize(source.read_bytes(),pid);folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True)
        public=[]
        def add(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        add(payload,'puzzle.html','text/html')
        for ref in refs[pid]:
            p=ROOT/snapshots[urljoin(url,ref)]['path']
            for local in (source.parent/ref,source.parent/Path(ref).name):
                if local.is_file():require(sha(local)==sha(p),'Original image differs')
            with Image.open(p) as im:im.verify()
            add(p.read_bytes(),Path(ref).name,'image/jpeg')
        clean=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()});n=int(pid[-5:]);note=LIMITS[n]
        # Do not promote information about the contents of a later hint into
        # an initial clue. Detailed deferred-scope evidence stays judge-side.
        public_note='This is an initial-page reconstruction. Later publisher additions are not initial input; historical materials and timed delivery remain unresolved.' if n==451 else note
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the source layout. Grid cells, blank lengths, marked positions and original instructions are not flattened into a text preview.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_initial_page_original_archive_judge_only',asset_policy='Only the explicit initial page/media are public. Other tasks/rooms, solution shortcuts and explicitly later notes are not initial input.')
        row['evaluation']['limitations']=note+' No gold or evaluator recertification. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2003_scoped_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=edits,
            deferred_section=late,initial_scope_note=note,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots))
    print(json.dumps(dict(records=4,public_files=len(copies))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        width=4100 if pid.endswith('00451') else 1600
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(out/(pid+'.png')),'--window-size='+str(width)+',2000','--virtual-time-budget=1000',(ROOT/CACHE/pid/'input/puzzle.html').as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and (out/(pid+'.png')).exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
