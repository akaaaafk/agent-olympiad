"""Eleven original static 2010 packets, including all image-map targets."""
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
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2010_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2010_static_20260913/'
REPORT='data/benchmarks/mystery_2010_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1261,1271,1277,1278,1301,1315,1324,1343,1358,1361,1363)}
CSS_URL='https://puzzles.mit.edu/2010/styles/'
STYLE_NAMES=('puzzles.css','round1puzzles.css')


def sanitize(data):
    require(len(SCRIPT.findall(data))==1,'Answer checker drift');payload=SCRIPT.sub(b'',data)
    soup=BeautifulSoup(payload,'html.parser');header=soup.find(id='header-content');require(header and [a['href'] for a in header.find_all('a')]==['../','solution.html'],'Navigation drift')
    for key in ('back-to-round','solution'):
        pattern=rb'<a id="'+key.encode()+rb'" href="[^"]+"><img [^>]+/></a>';require(len(re.findall(pattern,payload))==1,'Navigation boundary drift');payload=re.sub(pattern,b'',payload)
    names={Path(t['href']).name for t in soup.find_all('link')};require(len(names)==1 and names<=set(STYLE_NAMES),'Stylesheet scope drift');name=next(iter(names))
    old=b'href="../../../styles/'+name.encode()+b'"';require(payload.count(old)==2,'Screen/print style drift');payload=payload.replace(old,b'href="'+name.encode()+b'"')
    return payload,name


def localize(payload,url):
    soup=BeautifulSoup(payload,'html.parser');deps={}
    for el in soup.find_all():
        if el.name=='link':continue
        for attr in ('src','href','background'):
            if not el.get(attr):continue
            path=el[attr];name=Path(path).name;require(re.fullmatch(r'[A-Za-z0-9_-]+\.(gif|jpg|png)',name),'Unreviewed dependency: '+path)
            u=urljoin(url,path);require(name not in deps or deps[name]==u,'Image basename collision');deps[name]=u
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+path.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def local_css(data):
    refs=re.findall(rb"url\('([^']+)'\)",data);require(len(refs)==len(re.findall(rb'url\(',data)),'Unreviewed CSS URL form');deps={}
    for ref in refs:
        path=ref.decode('ascii');name=Path(path).name;require(path.startswith('../images/'),'Unreviewed CSS origin');deps[name]=urljoin(CSS_URL,path);data=data.replace(ref,name.encode())
    return data,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==11,'Selection drift')
    snapshots={s['source_url']:s for s in map(download,[CSS_URL+n for n in STYLE_NAMES])};prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/'
        payload,name=sanitize((ROOT/old['source_file']).read_bytes());css,cssdeps=local_css((ROOT/snapshots[CSS_URL+name]['path']).read_bytes());payload,deps=localize(payload,url)
        require(not(set(deps)&set(cssdeps)),'CSS/image collision');deps.update(cssdeps);urls.update(deps.values());urls.add(url);prepared[pid]=(url,payload,name,css,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,cssname,css,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift: '+pid)
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(css,cssname,'text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path']
            if urljoin(url,name)==u and (source.parent/name).exists():require(sha(p)==sha(source.parent/name),'Unreviewed image mismatch: '+pid+'/'+name)
            with Image.open(p) as im:im.verify()
            add(p.read_bytes(),name,{'.gif':'image/gif','.jpg':'image/jpeg','.png':'image/png'}[Path(name).suffix])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed);check_css(folder/cssname,allowed)
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        note='The original standalone archive page, diagrams, image-map links and applicable style artwork are preserved. Historical wording, repeated names, ordering and fictional premises are not modernized. No physical enactment, cross-task state or end-to-end grading is supplied.'
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original styled task and its image links. The visual packet, including image-map regions, is not replaced by a text preview.\n\nArchive limitation: '+note
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy='Original task and explicit dependencies only. Archive navigation and answer checking removed; no supplemental answers, modern substitutions or runtime state.')
        row['evaluation']['limitations']=note+' Gold and scores unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2010_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,image_map_targets=[dict(a.attrs) for a in clean.find_all('area')],css_name=cssname,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=11,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1261:1800,1271:2800,1277:2200,1278:3000,1301:5600,1315:2000,1324:3200,1343:2400,1358:9000,1361:2400,1363:3800}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png')
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
