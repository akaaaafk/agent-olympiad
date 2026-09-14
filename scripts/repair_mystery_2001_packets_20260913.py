"""Explicit 12-record, static-page 2001 recovery, preserving unsolved live dependencies."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import difflib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2000_packets_20260913 import ROOT,PATH,Store,download,check_html,sha,read,require,provenance

CACHE='data/.cache/mystery_2001_packets_20260913/'
RAW='data/raw/mystery_hunt/separated_2001_20260913/'
REPORT='data/benchmarks/mystery_2001_packets_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (136,137,140,144,147,155,160,165,166,169,179,185)}
LIMITS={
 144:'The page is only an invitation to a live headquarters appointment. The original performance, host interaction and observations are absent.',
 165:'The first office must be supplied by a live host; 2001 office-door texts and physical route observations are absent. The starting room and later observations are not inferred.',
 169:'Names may depend on historical affiliations. Current affiliations are not substituted for the 2001 context.',
}


def sanitize(data):
    pattern=rb'<script type="module" src="/checkanswer\.js"></script>'
    matches=list(re.finditer(pattern,data,re.I))
    require(len(matches)==1,'Unexpected archive script count')
    return re.sub(pattern,b'',data,flags=re.I),[dict(reason='archive answer-checking script',removed=matches[0][0].decode('ascii'))]


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    store=Store(ROOT); before=read(ROOT/PATH); chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==12 and all(r['year']==2001 for r in chosen),'Selection drift')
    urls=set(); media={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url']; urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        require(not soup.find_all(['a','form','iframe','object','embed','link']),'Unreviewed linked/dynamic dependency')
        names=[t['src'] for t in soup.find_all('img')]
        require(len(set(names))==len(names) and all(re.fullmatch(r'[A-Za-z0-9]+\.(?:gif|jpg)',n) for n in names),'Unexpected media names')
        media[row['problem_id']]=names; urls.update(urljoin(url,n) for n in names)
    with ThreadPoolExecutor(max_workers=4) as pool: snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    updates=[];copies=[];review={}
    def copy_new(source,dest):
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists(): require(sha(source)==sha(dest),'Existing cache file differs')
        else:
            with dest.open('xb') as out,source.open('rb') as inp: shutil.copyfileobj(inp,out)
    for old in chosen:
        row=deepcopy(old); pid=row['problem_id']; url='https://puzzles.mit.edu/'+row['puzzle_url']
        original=ROOT/row['source_file']; remote=ROOT/snapshots[url]['path']
        legacy=original.with_name('index.html') if original.name=='index.utf8_verified.html' else original
        # The two previously repaired archives have one legacy replacement glyph
        # each (blank NBSP cell / e-acute in seance). Compare their already-repaired
        # text to the publisher, never mistake the damaged legacy bytes for gold.
        if original!=legacy:
            expected=remote.read_bytes().decode('cp1252').replace('charset=iso-8859-1','charset=utf-8').replace('\r','')
            require(original.read_bytes().decode('utf-8').replace('\r','')==expected,'Prior encoding repair differs')
        else:
            require(legacy.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML differs from original archive: '+pid)
        payload,edits=sanitize(original.read_bytes())
        prepared=ROOT/CACHE/pid/'input/puzzle.html'; prepared.parent.mkdir(parents=True,exist_ok=True)
        if prepared.exists(): require(prepared.read_bytes()==payload,'Prepared HTML differs')
        else:
            with prepared.open('xb') as out: out.write(payload)
        public=[]
        def add(source,name,mime):
            dest=RAW+pid+'/input/'+name
            copies.append(dict(source=source.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(source)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(source)))
        add(prepared,'puzzle.html','text/html')
        missing=[]
        for name in media[pid]:
            remote_image=ROOT/snapshots[urljoin(url,name)]['path']; legacy_image=original.parent/name
            if legacy_image.exists(): require(sha(legacy_image)==sha(remote_image),'Publisher image differs')
            else: missing.append(name)
            with Image.open(remote_image) as im: im.verify()
            local=prepared.parent/name; copy_new(remote_image,local)
            add(local,name,'image/gif' if name.endswith('.gif') else 'image/jpeg')
        clean=check_html(prepared,{p.resolve() for p in prepared.parent.iterdir()})
        note=LIMITS.get(int(pid[-5:]),'Historical rules, answer-mechanism semantics and image/layout-aware evaluation remain uncertified.')
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original table, image and monospace layout. The auxiliary text below is not a layout replacement.\n\nArchive limitation: '+note+'\n\n## Source text (layout is in puzzle.html)\n\n'
        prompt+=clean.body.get_text('\n',strip=True).replace('\r\n','\n').replace('\r','\n')
        assets=deepcopy(row['assets'])
        if not any(a['path']==row['source_file'] for a in assets):
            assets.append(dict(path=row['source_file'],role='judge_only',mime_type='text/html',sha256=sha(original)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
             source_visibility='explicit_static_packet_original_archive_judge_only',
             asset_policy='Only explicit agent_visible HTML/media are contestant inputs. Archive controls and judge references are excluded. No live interaction or missing observations are synthesized.')
        row['evaluation']['limitations']='Static source page/media recovered; legacy gold and evaluator equivalence are not recertified. '+note
        row['source_review']=dict(batch='mystery_2001_packets_20260913',original_source_file=old['source_file'],
             original_sha256=sha(original),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),
             legacy_source_file=legacy.relative_to(ROOT).as_posix(),legacy_source_sha256=sha(legacy),
             comparison='Publisher equals current source after removing CR and, for the two previously corrected UTF-8 files, decoding the publisher as cp1252 and changing only its charset declaration. Legacy damaged bytes are preserved separately.',
             edits=edits,media_count=len(media[pid]),media_missing_from_legacy_archive=missing,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row));review[pid]=row['source_review']
    store.save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,
               updates=updates,copies=copies,review=review,publisher_snapshots=snapshots,
               deferred_records={
                 'mystery_hunt_00138':'Original dead title image and post-2010 substituted link need historical source review.',
                 'mystery_hunt_00177':'Periodically updated table has unresolved release timing.',
                 'mystery_hunt_00182':'Windows 9x executable needs isolated compatibility/security/runtime work; it is not executed.',
                 'mystery_hunt_00184':'Example page links to a separate full puzzle; secondary page/media still require source review.'}))
    print(json.dumps(dict(records=12,public_files=len(copies),publisher_files=len(snapshots),media=sum(map(len,media.values())))))


def writer():
    # Isolate the existing bounded packet writer so importing this module never
    # reconfigures the frozen 2000 regression module in the same process.
    spec=importlib.util.spec_from_file_location('_mystery_2001_bounded_writer',ROOT/'scripts/repair_mystery_2000_packets_20260913.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.CACHE=CACHE; module.RAW=RAW; module.REPORT=REPORT; module.SELECTED=SELECTED
    return module


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        height=6500 if pid.endswith(('00147','00179')) else 4500 if pid.endswith(('00155','00165')) else 3600 if pid.endswith(('00166','00185')) else 2500
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions',
             '--no-first-run','--no-default-browser-check','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
             '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),
             '--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed'); print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='diff':
        for row in read(ROOT/PATH):
            if row['problem_id'] not in SELECTED: continue
            local=ROOT/row['source_file']; local=local.with_name('index.html') if local.name=='index.utf8_verified.html' else local
            remote=ROOT/download('https://puzzles.mit.edu/'+row['puzzle_url'])['path']
            a=local.read_bytes().replace(b'\r',b'').decode('latin-1').splitlines(); b=remote.read_bytes().replace(b'\r',b'').decode('latin-1').splitlines()
            if a!=b:
                print(row['problem_id'])
                print('\n'.join(difflib.unified_diff(a,b,n=2))[:9000])
    elif mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
