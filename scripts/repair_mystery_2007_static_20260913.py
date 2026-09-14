"""Fourteen original 2007 static packets; preserve symbols, layouts and fiction."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
import hashlib
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2003_static_20260913 import SCRIPT
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2007_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2007_static_20260913/'
REPORT='data/benchmarks/mystery_2007_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (869,871,882,887,913,926,929,930,941,946,948,956,960,961)}
CSS_URL='https://puzzles.mit.edu/2007/styles/'
CSS_IMAGES={f'http://web.mit.edu/puzzle/www/07/images/{name}':'https://puzzles.mit.edu/2007/images/'+name for name in ('flame-border.jpg','red-gradient.png')}
SYMBOLS={'sq-fill.png','sq-empty.png','circle-empty.png'}
SPIRAL_HASHES=('d45701c453b1e974ffaa933e85efac3a5a669ff80b6a0fea418ad42e14c302b9','d60bebe2c200083989ef1777dded8947b05bc9c10732e54ea66eeb0bfce94f69')


def sanitize(data):
    require(len(SCRIPT.findall(data))==1,'Archive script drift');payload=SCRIPT.sub(b'',data)
    nav=BeautifulSoup(payload,'html.parser').find(id='nav');require(nav and [a['href'] for a in nav.find_all('a')]==['../','answer/'],'Navigation drift')
    pattern=rb'(<div id="nav">).*?(</div>)';require(len(re.findall(pattern,payload,re.S))==1,'Navigation boundary drift')
    payload=re.sub(pattern,rb'\1\2',payload,flags=re.S)
    for name in ('puzzle.css','print.css'):
        old=b'href="../../styles/'+name.encode()+b'"';require(payload.count(old)==1,'Stylesheet drift');payload=payload.replace(old,b'href="'+name.encode()+b'"')
    for name in SYMBOLS:payload=payload.replace(b'"../../images/'+name.encode()+b'"',b'"'+name.encode()+b'"')
    return payload


def local_css(data):
    refs=re.findall(rb'url\(([^)]+)\)',data);require(refs==[u.encode() for u in CSS_IMAGES],'Unexpected CSS dependency')
    for u in CSS_IMAGES:data=data.replace(u.encode(),Path(u).name.encode())
    return data


def publisher_download(url):
    if url not in CSS_IMAGES:return download(url)
    response=requests.get(url,timeout=20);response.raise_for_status()
    expected=CSS_IMAGES[url];require(response.url==expected,'Historical CSS redirect changed')
    snapshot=download(expected);require(hashlib.sha256(response.content).hexdigest()==snapshot['sha256'],'Redirected bytes differ')
    return dict(snapshot,source_url=url,verified_redirect_chain=[r.url for r in response.history]+[response.url])


def prepare(refresh=False):
    if (ROOT/CACHE/'plan.json').exists():
        require(refresh and not (ROOT/REPORT).exists() and sha(ROOT/PATH)==read(ROOT/CACHE/'plan.json')['expected_benchmark_sha256'],'Prepared or canonical state changed')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==14,'Selection drift')
    baseurls={r['problem_id']:'https://puzzles.mit.edu/'+r['puzzle_url'].rstrip('/')+'/' for r in chosen}
    urls=set(baseurls.values())|{CSS_URL+n for n in ('puzzle.css','print.css')}|set(CSS_IMAGES)|set(CSS_IMAGES.values())
    deps={};prepared={}
    for row in chosen:
        pid=row['problem_id'];url=baseurls[pid];payload=sanitize((ROOT/row['source_file']).read_bytes());prepared[pid]=payload
        soup=BeautifulSoup(payload,'html.parser');require(not soup.find_all('a'),'Unreviewed linked material')
        names={im['src'] for im in soup.find_all('img')};require(all(re.fullmatch(r'[A-Za-z0-9_-]+\.(?:jpg|png|gif)',n) for n in names),'Unreviewed image path')
        deps[pid]={n:urljoin(url,'../../images/'+n if n in SYMBOLS else n) for n in names}
        for u in CSS_IMAGES.values():require(Path(u).name not in deps[pid],'Image basename collision');deps[pid][Path(u).name]=u
        urls.update(deps[pid].values())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(publisher_download,sorted(urls))}
    for old,new in CSS_IMAGES.items():require(snapshots[old]['final_url']==new and snapshots[old]['sha256']==snapshots[new]['sha256'],'Historical CSS redirect differs')
    css=local_css((ROOT/snapshots[CSS_URL+'puzzle.css']['path']).read_bytes());print_css=(ROOT/snapshots[CSS_URL+'print.css']['path']).read_bytes()
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url=baseurls[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher source drift: '+pid)
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];conflicts=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared file differs')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(prepared[pid],'puzzle.html','text/html');add(css,'puzzle.css','text/css');add(print_css,'print.css','text/css')
        for name,u in sorted(deps[pid].items()):
            p=ROOT/snapshots[u]['path']
            if urljoin(url,name)==u and (source.parent/name).is_file() and sha(p)!=sha(source.parent/name):
                require(pid=='mystery_hunt_00930' and name=='spiral.png' and (sha(source.parent/name),sha(p))==SPIRAL_HASHES,'Unreviewed legacy image mismatch')
                conflicts.append(dict(path=(source.parent/name).relative_to(ROOT).as_posix(),original_sha256=sha(source.parent/name),publisher_sha256=sha(p),reason='Legacy file is a 472x419 colored navigation spiral; the explicit official puzzle URL supplies the 1798x1867 numbered blank spiral grid. Preserve the legacy original judge-only.'))
            with Image.open(p) as im:im.verify()
            add(p.read_bytes(),name,{'.jpg':'image/jpeg','.png':'image/png','.gif':'image/gif'}[Path(name).suffix])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
        note='The original 2007 clues, visual marks and wording are preserved. Historical facts are not modernized; image/layout-aware interpretation and end-to-end evaluation remain uncertified.'
        public_note=note
        if pid.endswith('00926'):note+=' The counterfactual sports accounts and printed dates are puzzle content, not corrected to real-world results.'
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original styled puzzle, figures and marked positions. No text-only preview replaces the visual layout.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        for c in conflicts:
            if not any(a['path']==c['path'] for a in assets):assets.append(dict(path=c['path'],role='judge_only',mime_type='image/png',sha256=c['original_sha256']))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy='Only the explicit public HTML, styles and images are initial materials. Archive navigation and solution checking are removed; no other task answers or runtime state are supplied.')
        row['evaluation']['limitations']=note+' Gold and scores are unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2007_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=['remove only archive navigation contents and answer checker','localize explicit style and symbol-image URLs without changing body content','follow publisher historical CSS image redirects and retain byte-identical images'],legacy_image_conflicts=conflicts,dependency_urls=deps[pid],css_redirects={u:snapshots[u] for u in CSS_IMAGES},answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots))
    print(json.dumps(dict(records=14,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    heights={869:10000,871:2000,882:5000,887:6000,913:3000,926:6500,929:4000,930:3500,941:2000,946:6000,948:6000,956:1800,960:2200,961:4000}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='refresh':prepare(True)
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
