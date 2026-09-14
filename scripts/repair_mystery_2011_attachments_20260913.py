"""Restore InventoryQuest's 18 unchanged text fragments and Letter Bank's grid."""
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
import pymupdf as fitz
from scripts.repair_mystery_2011_static_20260913 import sanitize,local_css,check_css,reset_snapshot,RESET_URL,RESET_REPO
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2011_attachments_20260913/'
RAW='data/raw/mystery_hunt/separated_2011_attachments_20260913/'
REPORT='data/benchmarks/mystery_2011_attachments_repair_20260913.json'
SELECTED={'mystery_hunt_01395','mystery_hunt_01398'}
MIMES={'.jpg':'image/jpeg','.png':'image/png','.txt':'text/plain','.pdf':'application/pdf'}
TEXT_SIZES=[344,1234,570,754,410,688,742,378,676,439,781,341,1085,285,633,593,1231,258]


def localize(payload,url):
    deps={};s=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in s.find_all(tag):
            path=el[attr];name=Path(path).name;require(Path(name).suffix in MIMES,'Unreviewed attachment');target=urljoin(url,path);require(name not in deps or deps[name]==target,'Collision');deps[name]=target
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+path.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==2,'Selection drift');snapshots={s['source_url']:s for s in map(reset_snapshot,(RESET_URL,RESET_REPO))};prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url);require(list(styleurls)==['reset-min.css','global.css','world.css'],'Style scope drift');payload,deps=localize(payload,url);urls.add(url);urls.update(deps.values());urls.update(styleurls.values());prepared[pid]=(url,payload,styleurls,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls-set(snapshots)))})
    styles={};urls=set()
    for pid,(url,payload,styleurls,deps) in prepared.items():
        styles[pid]={}
        for name,u in styleurls.items():
            css,links=local_css((ROOT/snapshots[u]['path']).read_bytes(),u);styles[pid][name]=css
            for n,v in links.items():require(n not in deps or deps[n]==v,'CSS/content collision');deps[n]=v
        urls.update(deps.values())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];review={}
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in styles[pid].items():add(data,name,'text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path'];data=p.read_bytes();ext=Path(name).suffix
            if ext=='.txt':
                require(len(data)==TEXT_SIZES[int(name[:2])-1] and b'???' in data,'Text fragment drift');data.decode('ascii');review[name]=dict(bytes=len(data),line_count=len(data.splitlines()),executed=False,original_bytes_preserved=True)
            elif ext=='.pdf':
                require(data.startswith(b'%PDF-'),'Not PDF')
                with fitz.open(p) as doc:require(len(doc)==1 and not doc.is_encrypted,'PDF scope drift');review[name]=dict(pages=1,original_bytes_preserved=True)
            else:
                with Image.open(p) as im:im.verify()
            if urljoin(url,'assets/'+name)==u and (source.parent/'assets'/name).exists():require(sha(p)==sha(source.parent/'assets'/name),'Legacy attachment mismatch')
            add(data,name,MIMES[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styleurls:check_css(folder/name,allowed)
        note='All 18 explicitly linked text fragments are puzzle inputs, not executable commands. Their order, repeated lines, question marks and original line endings are retained. No game state or missing words are inferred.' if pid.endswith('01395') else 'The original grid image, one-page grid PDF and all printed Across/Down letter-and-price clues are retained. The given prices are puzzle clues, not benchmark scores; no cells are filled or inferred.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` and its explicit local attachments.\n\nArchive limitation: '+note,assets=public+assets,source_visibility='explicit_attachment_packet_original_archive_judge_only',asset_policy=note)
        row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2011_attachments_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,attachment_review=review,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=2,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png')
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,2600','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed')
    p=subprocess.run([str(ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'),'-png','-r','130',str(ROOT/CACHE/'mystery_hunt_01398/input/grid.pdf'),str(out/'grid')],capture_output=True,timeout=45);require(p.returncode==0,'PDF render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
