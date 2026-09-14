"""Restore phase-one Charity Work and unchanged opaque Hyperextensions inputs."""
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
from scripts.repair_mystery_2003_static_20260913 import SCRIPT
from scripts.repair_mystery_2009_static_20260913 import sanitize as static_html,styles,CSS_URL,STYLE_NAMES
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2009_attachments_20260913/'
RAW='data/raw/mystery_hunt/separated_2009_attachments_20260913/'
REPORT='data/benchmarks/mystery_2009_attachments_repair_20260913.json'
SELECTED={'mystery_hunt_01112','mystery_hunt_01157'}
OPAQUE={f'file.{i:03}' for i in range(1,23)}
OPAQUE_SIZES=[6814,45528,250,1144576,5605,1613,236,1020,869,107501,410,1241,11202,3774,1097,215856,68154,740,10240,113,71,110451]


def sanitize(data,pid):
    if pid.endswith('01157'):return static_html(data)
    require(len(SCRIPT.findall(data))==1,'Answer checker drift');payload=SCRIPT.sub(b'',data)
    scripts=re.findall(rb'<script type="text/javascript">.*?</script>',payload,re.S)
    require(len(scripts)==1 and b'function unhide(divID)' in scripts[0] and scripts[0].count(b'function ')==1,'Unhide script drift');payload=payload.replace(scripts[0],b'')
    for cls in ('solution','check_answer'):
        p=rb'<div class="'+cls.encode()+rb'">[^\r\n]*?</div>';require(len(re.findall(p,payload))==1,'Navigation boundary drift');payload=re.sub(p,b'',payload)
    token=b'href="../../../styles/puzzle.css"';require(payload.count(token)==1,'Style link drift');payload=payload.replace(token,b'href="puzzle.css"')
    forms=re.findall(rb'<form>.*?</form>',payload,re.S);require(len(forms)==1,'Form boundary drift')
    form=BeautifulSoup(forms[0],'html.parser');require([(x.get('type'),x.get('name')) for x in form.find_all('input')]==[('hidden','last_phase'),('text','verify'),('button','submit')],'Initial form scope drift')
    require(form.find('input',attrs={'name':'last_phase'})['value']=='1','Not initial phase')
    passive=forms[0].replace(b'<form>',b'<div class="archive-verification">').replace(b'</form>',b'<span> (archived control; inactive)</span></div>')
    actions=re.findall(rb" onclick='[^']+'",passive);require(len(actions)==1,'Action boundary drift');passive=passive.replace(actions[0],b'').replace(b'<input ',b'<input disabled ')
    payload=payload.replace(forms[0],passive);require(not BeautifulSoup(payload,'html.parser').find_all('script'),'Unreviewed script remains')
    return payload


def localize(payload,url):
    deps={};soup=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in soup.find_all(tag):
            path=el[attr];name=Path(path).name;require(Path(name).suffix in ('.png','.jpg') or name in OPAQUE,'Unreviewed attachment')
            u=urljoin(url,path);require(name not in deps or deps[name]==u,'Dependency collision');deps[name]=u
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+path.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==2,'Selection drift')
    snapshots={s['source_url']:s for s in map(download,[CSS_URL+n for n in STYLE_NAMES])};main=(ROOT/snapshots[CSS_URL+'puzzle.css']['path']).read_bytes();images=(ROOT/snapshots[CSS_URL+'puzzle-page-images.css']['path']).read_bytes();prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/'
        payload=sanitize((ROOT/old['source_file']).read_bytes(),pid);css,cssdeps,review=styles(main,images,payload);payload,deps=localize(payload,url)
        require(not(set(deps)&set(cssdeps)),'CSS collision');deps.update(cssdeps);urls.update(deps.values());urls.add(url);prepared[pid]=(url,payload,css,deps,review)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,css,deps,review=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift')
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];opaque_review={}
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(css,'puzzle.css','text/css')
        if pid.endswith('01157'):add((ROOT/snapshots[CSS_URL+'print.css']['path']).read_bytes(),'print.css','text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path'];data=p.read_bytes()
            if urljoin(url,name)==u and (source.parent/name).exists():require(sha(p)==sha(source.parent/name),'Unreviewed legacy attachment mismatch')
            if name in OPAQUE:
                require(len(data)==OPAQUE_SIZES[int(name[-3:])-1],'Opaque source-size drift');mime='application/octet-stream';opaque_review[name]=dict(bytes=len(data),header_hex=data[:16].hex(),sha256=sha(p),executed=False,unpacked=False,format_interpretation_added_to_public_packet=False)
            else:
                with Image.open(p) as im:im.verify()
                mime='image/png' if name.endswith('.png') else 'image/jpeg'
            add(data,name,mime)
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in ('puzzle.css','print.css'):
            if (folder/name).exists():check_css(folder/name,allowed)
        if pid.endswith('01112'):
            note='Only the original first-stage instructions and 32 explicitly linked Plutonian sheets are restored. The archived verification controls are inactive. Later-stage pages and their release/verification mechanism are not included or inferred; this is not a complete playable reconstruction.'
        else:
            note='All 22 explicitly linked original files retain their opaque names and bytes. No filename extensions are inferred, no code or shortcuts are executed, and no contents are unpacked or replaced with interpreted outputs. Source recovery does not certify file safety, interpretation or executable evaluation.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original layout and explicit local inputs.\n\nArchive limitation: '+note,assets=public+assets,source_visibility='explicit_initial_attachments_original_archive_judge_only',asset_policy=note)
        row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2009_attachments_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,style_review=review,opaque_review=opaque_review,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=2,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');height=2600 if pid.endswith('01112') else 1000
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
