"""Restore six image/layout-dependent 2009 packets without source execution."""
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

CACHE='data/.cache/mystery_2009_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2009_static_20260913/'
REPORT='data/benchmarks/mystery_2009_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1150,1151,1152,1180,1189,1206)}
CSS_URL='https://puzzles.mit.edu/2009/styles/'
STYLE_NAMES=('puzzle.css','print.css','puzzle-page-images.css')


def sanitize(data):
    require(len(SCRIPT.findall(data))==1,'Answer checker drift');payload=SCRIPT.sub(b'',data)
    soup=BeautifulSoup(payload,'html.parser');header=soup.find(id='header');require(header is not None,'Missing header')
    for cls in ('solution','check_answer'):
        nodes=header.find_all('div',class_=cls);require(len(nodes)==(1 if cls=='solution' else int('reverse_dimension' not in soup.body['class'])),'Navigation shape drift')
        if nodes:
            require(len(nodes[0].find_all('a'))==1 and nodes[0].get_text(strip=True)=='','Navigation includes task text')
            p=rb'<div class="'+cls.encode()+rb'">[^\r\n]*?</div>';require(len(re.findall(p,payload))==1,'Navigation boundary drift');payload=re.sub(p,b'',payload)
    pattern=rb'(<div class="planet">)<a href="[^"]+">(<img [^>]+/>)</a>(</div>)'
    require(len(re.findall(pattern,payload))==1,'Planet link boundary drift');payload=re.sub(pattern,rb'\1\2\3',payload)
    for name in ('puzzle.css','print.css'):
        token=b'href="../../../styles/'+name.encode()+b'"';require(payload.count(token)==1,'Style link drift');payload=payload.replace(token,b'href="'+name.encode()+b'"')
    return payload


def styles(main,images,payload):
    """Inline the original import in cascade order, omit only unmatched image rules."""
    soup=BeautifulSoup(payload,'html.parser');removed=[];kept=[]
    pattern=rb'(body\.[a-z0-9_]+(?:\.[a-z0-9_]+)? \.puzzle-id-image div)\s*\{\s*background: url\(([^)]+)\);\s*\}'
    require(len(re.findall(pattern,images))==len(re.findall(rb'url\(',images)),'Unreviewed image stylesheet grammar')
    def choose(match):
        selector=match[1].decode('ascii')
        if soup.select(selector):kept.append(selector);return match[0]
        removed.append(selector);return b''
    images=re.sub(pattern,choose,images)
    token=b'@import url("puzzle-page-images.css");';require(main.count(token)==1,'CSS import drift');data=main.replace(token,images)
    refs=re.findall(rb'url\(([^)]+)\)',data);deps={}
    for ref in refs:
        path=ref.decode('ascii');name=Path(path).name;url=urljoin(CSS_URL,path)
        require(name not in deps or deps[name]==url,'Style basename collision');deps[name]=url;data=data.replace(ref,name.encode())
    return data,deps,dict(retained_image_selectors=kept,omitted_unmatched_image_selectors=removed,import_inlined_in_original_cascade_order=True)


def localize(payload,url):
    soup=BeautifulSoup(payload,'html.parser');deps={}
    for tag,attr in [('img','src'),('a','href')]:
        for el in soup.find_all(tag):
            path=el[attr];name=Path(path).name
            require(re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|gif)',name),'Unreviewed image link: '+path)
            target=urljoin(url,path);require(name not in deps or deps[name]==target,'Image basename collision');deps[name]=target
            for quote in (b'"',b"'"):
                payload=payload.replace(attr.encode()+b'='+quote+path.encode()+quote,attr.encode()+b'='+quote+name.encode()+quote)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==6,'Selection drift')
    snapshots={s['source_url']:s for s in map(download,[CSS_URL+n for n in STYLE_NAMES])}
    main=(ROOT/snapshots[CSS_URL+'puzzle.css']['path']).read_bytes();images=(ROOT/snapshots[CSS_URL+'puzzle-page-images.css']['path']).read_bytes()
    prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/'
        payload=sanitize((ROOT/old['source_file']).read_bytes());css,cssdeps,review=styles(main,images,payload);payload,deps=localize(payload,url)
        require(not (set(deps)&set(cssdeps)),'CSS/HTML collision');deps.update(cssdeps);urls.update(deps.values());urls.add(url)
        prepared[pid]=(url,payload,css,deps,review)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,css,deps,review=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher source drift: '+pid)
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(css,'puzzle.css','text/css');add((ROOT/snapshots[CSS_URL+'print.css']['path']).read_bytes(),'print.css','text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path']
            if urljoin(url,name)==u and (source.parent/name).exists():require(sha(p)==sha(source.parent/name),'Unreviewed legacy image mismatch: '+pid+'/'+name)
            with Image.open(p) as im:im.verify()
            add(p.read_bytes(),name,{'.png':'image/png','.jpg':'image/jpeg','.gif':'image/gif'}[Path(name).suffix])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        note='The original standalone archive packet is restored, including explicit full-size image links and applicable header artwork. Historic wording, symbols, dimensions and source groupings remain unchanged. Full-hunt progression, cross-task evaluation and image-aware grading are not reproduced.'
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original styled task. Explicit image links open original full-size files; a text preview does not replace the visual packet.\n\nArchive limitation: '+note
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy='Original initial HTML, matching styles and explicit images only; archive navigation and answer checking removed. No other task answers or runtime state supplied.')
        row['evaluation']['limitations']=note+' Gold and scores unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2009_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,style_review=review,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=6,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1150:4600,1151:1700,1152:5400,1180:6500,1189:5800,1206:2400}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
