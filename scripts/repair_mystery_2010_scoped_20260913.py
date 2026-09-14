"""Recover five 2010 initial pages without inventing host actions or past state."""
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
from scripts.repair_mystery_2010_static_20260913 import sanitize as static_html,localize,local_css,CSS_URL,STYLE_NAMES
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2010_scoped_20260913/'
RAW='data/raw/mystery_hunt/separated_2010_scoped_20260913/'
REPORT='data/benchmarks/mystery_2010_scoped_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1266,1307,1313,1337,1377)}
LIMITS={1266:'Only the common original appointment instructions are initial input. Physical rooms, timed attempts, host assignment and delivery are not implemented; this is not a playable reconstruction.',
1307:'The original clues and diagram are preserved. Historical location, car and time-sensitive context are not recreated or replaced with current facts.',
1313:'Only the explicit round page and its two images are recovered. Other task names and image-map coordinates remain visible but their navigation is inactive. No additional note, other task answers or unlock state is supplied.',
1337:'The original January 2010 letter and all historical arcade scores are retained as clues, not replaced with modern leaderboards. Historical solvability is not certified.',
1377:'The original movie assignment instructions, including its published dummy response, are preserved. Organizer assignment, uploads, email, calls and physical performance are not implemented or performed.'}


def sanitize(data,n):
    if n==1313:
        require(data.count(b'href="../../styles/puzzles.css"')==2,'Round style drift');data=data.replace(b'href="../../styles/puzzles.css"',b'href="../../../styles/puzzles.css"')
    payload,name=static_html(data);deferred=None
    if n==1266:
        boundary=rb'<hr\s*/>\s*<br\s*/>\s*<p>Team members were directed to the private dining rooms.*?(?=</div><!--end of id="page-content"-->)'
        found=re.findall(boundary,payload,re.S);require(len(found)==1 and b'Word based nanohunts' in found[0] and b'Physical based nanohunts' in found[0],'Nanohunt boundary drift')
        deferred=found[0].decode('utf-8');payload=payload.replace(found[0],b'')
    if n==1313:
        soup=BeautifulSoup(payload,'html.parser');areas=soup.find_all('area');require(len(areas)==11,'Round map drift')
        for area in areas:
            target=area['href'];require(re.fullmatch(r'[a-z0-9_%]+/',target),'Unreviewed round link');token=('href="'+target+'"').encode();require(payload.count(token)==1,'Round link collision');payload=payload.replace(token,('data-archive-href="'+target+'"').encode())
    inline=re.findall(rb'url\([^)]*\)',payload)
    require(inline==([b"url('1952_top.jpg')"] if n==1313 else []),'Unreviewed inline CSS dependency')
    return payload,name,deferred


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==5,'Selection drift')
    snapshots={s['source_url']:s for s in map(download,[CSS_URL+n for n in STYLE_NAMES])};prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];n=int(pid[-5:]);url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/'
        payload,name,deferred=sanitize((ROOT/old['source_file']).read_bytes(),n);css,cssdeps=local_css((ROOT/snapshots[CSS_URL+name]['path']).read_bytes());payload,deps=localize(payload,url)
        if n==1313:deps['1952_top.jpg']=url+'1952_top.jpg'
        require(not(set(deps)&set(cssdeps)),'CSS/image collision');deps.update(cssdeps);private={}
        if n==1266:private={name:url+name for name in ('nanohunts_cubes.gif','nanohunts_cubes_th.gif')}
        urls.update(deps.values());urls.update(private.values());urls.add(url);prepared[pid]=(url,payload,name,css,deps,private,deferred)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];n=int(pid[-5:]);url,payload,cssname,css,deps,private,deferred=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift: '+pid)
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);new_assets=[]
        def add(data,name,mime,role='agent_visible'):
            sub='input' if role=='agent_visible' else 'judge';p=ROOT/CACHE/pid/sub/name;p.parent.mkdir(exist_ok=True)
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/'+sub+'/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));new_assets.append(dict(path=dest,role=role,mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(css,cssname,'text/css')
        for role,links in (('agent_visible',deps),('judge_only',private)):
            for name,u in sorted(links.items()):
                p=ROOT/snapshots[u]['path']
                if urljoin(url,name)==u and (source.parent/name).exists():require(sha(p)==sha(source.parent/name),'Unreviewed image mismatch')
                with Image.open(p) as im:im.verify()
                add(p.read_bytes(),name,{'.gif':'image/gif','.jpg':'image/jpeg','.png':'image/png'}[Path(name).suffix],role)
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed);check_css(folder/cssname,allowed)
        if n==1313:require((folder/'1952_top.jpg').resolve() in allowed,'Missing inline background')
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        note=LIMITS[n];prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original initial page and explicit local images.\n\nArchive limitation: '+note
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=new_assets+assets,source_visibility='explicit_initial_scope_original_archive_judge_only',asset_policy=note)
        row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2010_scoped_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,judge_dependency_urls=private,deferred_section=deferred,css_name=cssname,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots);Store(ROOT).save(CACHE+'plan.json',plan);print(json.dumps(dict(records=5,roles=writer().copy_role_counts(plan),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');height=4000 if pid.endswith('01337') else 1600
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
