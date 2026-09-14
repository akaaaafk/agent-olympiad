"""Restore two complete 2004 packets previously represented by a single subpage."""
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
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer
from scripts.repair_mystery_hunt_sources_20260913 import check_css

CACHE='data/.cache/mystery_2004_packets_20260913/'
RAW='data/raw/mystery_hunt/separated_2004_20260913/'
REPORT='data/benchmarks/mystery_2004_packets_repair_20260913.json'
SELECTED={'mystery_hunt_00529','mystery_hunt_00586'}
PAGES={529:[f'{n}.html' for n in range(1,7)],586:[n+'.html' for n in ('your','every','_answer','is','an','integral','part')]}
MIME={'.html':'text/html','.css':'text/css','.jpg':'image/jpeg','.gif':'image/gif','.png':'image/png'}


def sanitize_root(data):
    edits=[]
    for pattern,replacement,reason in (
        (rb'<script type="module" src="/checkanswer\.js"></script>',b'','remove archive answer checker'),
        (rb'<a href="\.\./">\(back to the map\)</a>',b'','remove map navigation'),
        (rb'<a href="answer\.html">\s*<img[^>]*alt="Check Answer"[^>]*>\s*</a>',b'','remove exact answer.html control, not _answer.html'),
        (rb'href="\.\./(mh04-[0-9]+\.css)"',rb'href="\1"','localize unchanged stylesheet')):
        found=re.findall(pattern,data,re.I|re.S);require(len(found)==1,'Root markup drift: '+reason)
        data=re.sub(pattern,replacement,data,flags=re.I|re.S);edits.append(dict(reason=reason,count=1))
    return data,edits


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==2 and all(r['year']==2004 for r in chosen),'Selection drift')
    snapshots={};requests={}
    for r in chosen:
        pid=r['problem_id'];base='https://puzzles.mit.edu/'+r['puzzle_url'];n=int(pid[-5:]);requests[pid]={'puzzle.html':base}
        for name in PAGES[n]:requests[pid][name]=base+name
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted({u for d in requests.values() for u in d.values()}))})
    for r in chosen:
        pid=r['problem_id'];base='https://puzzles.mit.edu/'+r['puzzle_url']
        for name,url in list(requests[pid].items()):
            data=(ROOT/snapshots[url]['path']).read_bytes()
            if name=='puzzle.html':data=sanitize_root(data)[0]
            soup=BeautifulSoup(data,'html.parser')
            if name!='puzzle.html':require(not soup.find_all(['a','script','link','form','iframe','object','embed']),'Unexpected subpage dependency')
            for t in soup.find_all(['img','link']):
                ref=t.get('src') or t.get('href');require(re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:jpg|gif|png|css)',ref),'Unreviewed media path')
                full=urljoin(url,('../' if ref.endswith('.css') else '')+ref)
                require(ref not in requests[pid] or requests[pid][ref]==full,'Name collision');requests[pid][ref]=full
    missing=sorted({u for d in requests.values() for u in d.values()}-snapshots.keys())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,missing)})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];n=int(pid[-5:]);source=ROOT/row['source_file'];base='https://puzzles.mit.edu/'+row['puzzle_url']
        # The old selected subpage and the old root are preserved and checked
        # against their actual publisher counterparts, not compared to each other.
        require(source.read_bytes().replace(b'\r',b'')==(ROOT/snapshots[base+source.name]['path']).read_bytes().replace(b'\r',b''),'Old source differs')
        require(source.with_name('index.html').read_bytes().replace(b'\r',b'')==(ROOT/snapshots[base]['path']).read_bytes().replace(b'\r',b''),'Original root differs')
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];edits=[];missing_original=[]
        for name,url in requests[pid].items():
            snap=ROOT/snapshots[url]['path'];data=snap.read_bytes();suffix=Path(name).suffix
            original=source.parent/('index.html' if name=='puzzle.html' else name)
            if original.is_file():
                if suffix in ('.html','.css'):require(original.read_bytes().replace(b'\r',b'')==data.replace(b'\r',b''),'Legacy text differs: '+name)
                else:require(sha(original)==sha(snap),'Legacy media differs: '+name)
            else:missing_original.append(name)
            if name=='puzzle.html':data,edits=sanitize_root(data)
            if suffix in ('.jpg','.gif','.png'):
                with Image.open(snap) as im:im.verify()
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=MIME[suffix],sha256=sha(target)))
        allowed={p.resolve() for p in folder.iterdir()}
        for p in folder.glob('*.html'):check_html(p,allowed)
        for p in folder.glob('*.css'):check_css(p,allowed)
        clean=check_html(folder/'puzzle.html',allowed)
        note='The six linked chapters and the root page-number clues are now supplied together. Historical references and image-aware evaluation remain uncertified.' if n==529 else 'The seven linked store problems and their diagrams are now supplied together. The source filename _answer.html is a puzzle, not the solution page answer.html. Historical context and evaluation remain uncertified.'
        # Do not explain the filename sequence or other latent solving clues.
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html`, the original entry point, and follow its local links for the complete puzzle. All original subpages, styles and referenced images are included. No flattened preview replaces their layout.\n\nArchive limitation: Historical references, multi-page interpretation and end-to-end evaluation remain uncertified.'
        assets=deepcopy(old['assets'])
        for p in (source,source.with_name('index.html')):
            rel=p.relative_to(ROOT).as_posix()
            if not any(a['path']==rel for a in assets):assets.append(dict(path=rel,role='judge_only',mime_type='text/html',sha256=sha(p)))
        row.update(source_url=base,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_complete_static_packet_original_archive_judge_only',asset_policy='Only exact original root/subpage/media dependencies are public; the answer.html control, answer checker and map navigation are excluded. No solution is copied.')
        row['evaluation']['limitations']=note+' No legacy gold or score recertification. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2004_packets_20260913',original_source_file=old['source_file'],original_sha256=sha(source),
            original_root_file=source.with_name('index.html').relative_to(ROOT).as_posix(),original_root_sha256=sha(source.with_name('index.html')),
            publisher_snapshot=snapshots[base]['path'],publisher_html_sha256=sha(ROOT/snapshots[base]['path']),edits=edits,
            recovered_subpages=PAGES[n],files_missing_from_legacy_archive=missing_original,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,source_map=requests))
    print(json.dumps(dict(records=2,public_files=len(copies),html_pages=sum(c['destination'].endswith('.html') for c in copies))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    for pid in sorted(SELECTED):
        out=ROOT/CACHE/'renders'/pid;out.mkdir(parents=True,exist_ok=True)
        for page in (ROOT/CACHE/pid/'input').glob('*.html'):
            height=3300 if pid.endswith('00529') and page.stem!='puzzle' else 1600
            p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
                '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(out/(page.stem+'.png')),'--window-size=1600,'+str(height),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
            require(p.returncode==0 and (out/(page.stem+'.png')).exists(),'Render failed');print(pid,page.name,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
