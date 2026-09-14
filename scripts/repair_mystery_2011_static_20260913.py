"""Restore sixteen 2011 static inputs, original styles and legitimate variants."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2003_static_20260913 import SCRIPT
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2011_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2011_static_20260913/'
REPORT='data/benchmarks/mystery_2011_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1402,1408,1410,1418,1429,1431,1432,1446,1454,1486,1491,1496,1501,1520,1521,1523)}
RESET_OLD='http://yui.yahooapis.com/3.2.0/build/cssreset/reset-min.css'
RESET_URL='https://yui-s.yahooapis.com/3.2.0/build/cssreset/reset-min.css'
RESET_REPO='https://raw.githubusercontent.com/yui/yui3/v3.2.0/build/cssreset/reset-min.css'


def reset_snapshot(url):
    require(url in (RESET_URL,RESET_REPO),'Unreviewed reset origin');p=ROOT/CACHE/'publisher'/(hashlib.sha256(url.encode()).hexdigest()+'.css');meta=p.with_suffix('.json')
    if p.exists():
        d=read(meta);require(d['source_url']==url and sha(p)==d['sha256'],'Reset snapshot drift');return d
    r=requests.get(url,timeout=30);r.raise_for_status();require(r.url==url and b'html{color:#000;background:#FFF;}' in r.content,'Unexpected reset CSS');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(r.content)
    d=dict(source_url=url,final_url=r.url,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(r.content),retrieved_at_utc=Store(ROOT).stamp);Store(ROOT).save(meta.relative_to(ROOT).as_posix(),d);return d


def sanitize(data,url):
    require(len(SCRIPT.findall(data))==1,'Checker drift');payload=SCRIPT.sub(b'',data)
    pattern=rb'<div id="puzzletopbar">.*?<script type="text/javascript" src="../../assets/points.js"></script>\s*</div>'
    navs=re.findall(pattern,payload,re.S);require(len(navs)==1,'Navigation boundary drift');nav=BeautifulSoup(navs[0],'html.parser');require(len(nav.find_all('a'))==9 and nav.find('a',title='View solution') is not None,'Navigation contents drift');payload=payload.replace(navs[0],b'')
    s=BeautifulSoup(payload,'html.parser');require(not s.find_all('script'),'Unreviewed active content');styles={}
    for link in s.find_all('link'):
        ref=link['href'];name=Path(ref).name;target=RESET_URL if ref==RESET_OLD else urljoin(url,ref);require(name not in styles and (target.startswith('https://puzzles.mit.edu/2011/puzzles/') or target==RESET_URL),'Unreviewed style');styles[name]=target;token=('href="'+ref+'"').encode();require(payload.count(token)==1,'Style link collision');payload=payload.replace(token,('href="'+name+'"').encode())
    require(list(styles)[:3]==['reset-min.css','global.css','world.css'],'Stylesheet order drift');require(not re.search(rb'url\(',payload),'Unreviewed inline dependency')
    return payload,styles


def local_css(data,url):
    deps={}
    for ref in re.findall(rb'url\(([^)]+)\)',data):
        path=ref.strip(b'\'"').decode('ascii');require(path.startswith('../images/'),'Unreviewed CSS dependency');name=Path(path).name;target=urljoin(url,path);require(name not in deps or deps[name]==target,'CSS image collision');deps[name]=target;data=data.replace(ref,name.encode())
    return data,deps


def check_css(path,allowed):
    # Copyright notices contain an informational URL, not a network dependency.
    data=re.sub(r'/\*.*?\*/','',path.read_text(encoding='ascii'),flags=re.S)
    require(not re.search(r'@import|expression\(|javascript:|https?://',data,re.I),'Active/remote CSS')
    for name in re.findall(r'url\([\'\"]?([^\)\'\"]+)',data):require((path.parent/name).resolve() in allowed,'Missing CSS image')


def localize(payload,url):
    deps={};s=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in s.find_all(tag):
            path=el[attr];name=Path(path).name;require(re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|gif)',name),'Unreviewed asset');target=urljoin(url,path);require(name not in deps or deps[name]==target,'Image collision');deps[name]=target
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+path.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==16,'Selection drift');snapshots={s['source_url']:s for s in map(reset_snapshot,(RESET_URL,RESET_REPO))}
    reset=(ROOT/snapshots[RESET_URL]['path']).read_bytes();repo=(ROOT/snapshots[RESET_REPO]['path']).read_bytes();require(re.sub(rb'/\*.*?\*/\s*',b'',reset,flags=re.S)==repo,'Same-version reset CSS mismatch');prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url);payload,deps=localize(payload,url);prepared[pid]=(url,payload,styleurls,deps);urls.add(url);urls.update(styleurls.values());urls.update(deps.values())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls-set(snapshots)))})
    styles={};cssdeps={};urls=set()
    for pid,(url,payload,styleurls,deps) in prepared.items():
        styles[pid]={};cssdeps[pid]={}
        for name,u in styleurls.items():
            css,links=local_css((ROOT/snapshots[u]['path']).read_bytes(),u);styles[pid][name]=css
            for n,v in links.items():require(n not in cssdeps[pid] or cssdeps[pid][n]==v,'Cross-style image collision');cssdeps[pid][n]=v
        require(not (set(deps)&set(cssdeps[pid])),'CSS/content basename collision');deps.update(cssdeps[pid]);urls.update(deps.values())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift: '+pid)
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in styles[pid].items():add(data,name,'text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path']
            for legacy in (source.parent/name,source.parent/'assets'/name):
                if urljoin(url,'assets/'+name)==u and legacy.exists():require(sha(p)==sha(legacy),'Legacy image mismatch')
            with Image.open(p) as im:im.verify()
            add(p.read_bytes(),name,{'.gif':'image/gif','.jpg':'image/jpeg','.png':'image/png'}[Path(name).suffix])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styleurls:check_css(folder/name,allowed)
        note='Original standalone text, layout, diagrams, repeated entries and published worked examples are preserved. The exact YUI 3.2.0 reset is recovered from its publisher and checked against the same official release. Archive navigation, answer checking and points scripts are removed. Historical claims are not modernized; shared-page answer variants are not merged and host or cross-task protocols are not reconstructed.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original styled visual packet and linked images. A text preview does not replace the diagrams or blank cells.\n\nArchive limitation: '+note,assets=public+assets,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy=note)
        row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2011_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,reset_version='3.2.0',reset_publisher_css_matches_official_release_without_license_comment=True,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=16,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1402:5500,1408:1800,1410:2700,1418:4700,1429:9000,1431:1300,1432:1300,1446:6200,1454:2500,1486:1800,1491:3400,1496:2100,1501:2200,1520:18000,1521:2200,1523:2200}
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
