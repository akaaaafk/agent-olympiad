"""Recover thirteen static 2012 inputs without cross-task state or answer edits."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageFont
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2012_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2012_static_20260913/'
REPORT='data/benchmarks/mystery_2012_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1546,1566,1591,1603,1610,1640,1642,1645,1647,1651,1659,1666,1667)}
FONT_QUERIES=('Coustard|Nothing+You+Could+Do|Buenard:700','Abril+Fatface','Alice|Inconsolata&subset=latin,latin-ext','Abril+Fatface|Alice&subset=latin,latin-ext')
FONT_CSS={'https://fonts.googleapis.com/css?family='+q for q in FONT_QUERIES}
FONT_FAMILIES={'abrilfatface','alice','inconsolata','buenard','coustard','nothingyoucoulddo'}
IMPORT=re.compile(rb'@import\s+(?:url\(([^)]+)\)|[\'"]([^\'"]+)[\'"])\s*;')
URL=re.compile(rb'url\(([^)]+)\)')
SCRIPTS=re.compile(rb'<script\b[^>]*>.*?</script>',re.S|re.I)


def snapshot(url):
    if url.startswith('https://puzzles.mit.edu/2012/puzzles/'):return download(url)
    parts=urlparse(url)
    font=parts.netloc=='fonts.gstatic.com' and re.fullmatch(r'/s/('+'|'.join(sorted(FONT_FAMILIES))+r')/v\d+/[A-Za-z0-9_-]+\.ttf',parts.path)
    license_url=url.startswith('https://raw.githubusercontent.com/google/fonts/main/ofl/') and parts.path.split('/')[-2] in FONT_FAMILIES and parts.path.endswith('/OFL.txt')
    require(url in FONT_CSS or font or license_url,'Unreviewed external dependency: '+url)
    p=ROOT/CACHE/'publisher'/(hashlib.sha256(url.encode()).hexdigest()+'.bin');meta=p.with_suffix('.json')
    if p.exists():
        d=read(meta);require(d['source_url']==url and sha(p)==d['sha256'],'Snapshot drift');return d
    response=requests.get(url,timeout=30);response.raise_for_status();require(urlparse(response.url).netloc==parts.netloc,'Unexpected redirect');data=response.content
    if url in FONT_CSS:require(data.startswith(b'@font-face {') and b'<html' not in data.lower(),'Invalid font CSS')
    elif font:require(data[:4]==b'\x00\x01\x00\x00','Invalid TrueType signature')
    else:require(b'SIL OPEN FONT LICENSE' in data,'Invalid font license')
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as out:out.write(data)
    if font:ImageFont.truetype(str(p),16).getmask('Archive')
    d=dict(source_url=url,final_url=response.url,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(data),retrieved_at_utc=Store(ROOT).stamp)
    Store(ROOT).save(meta.relative_to(ROOT).as_posix(),d);return d


def sanitize(data,url):
    soup=BeautifulSoup(data,'html.parser');scripts=soup.find_all('script');show=soup.find(id='show-title') is not None;letter=soup.find(id='banner') is not None
    require(len(scripts)==(7 if show else 4 if letter else 5),'Script count drift')
    srcs=[];inlines=[]
    for el in scripts:
        if el.has_attr('src'):srcs.append(el['src'])
        else:inlines.append(el.get_text())
    require(sorted(srcs)==sorted(['../../points.js','../../shortcuts.js','/checkanswer.js']+([] if letter else ['../../guess.js'])+(['../../release.js'] if show else [])),'Script sources drift')
    require(len(inlines)==(2 if show else 1),'Inline count drift')
    assignments=inlines[0].strip()
    require(re.fullmatch(r'this.depth="../../";\s*this.up_title="[^"\n]+";\s*'+('' if letter else r'this.puzzlehash="[a-f0-9]{56}";'),assignments),'Unreviewed inline initialization')
    if show:
        require(''.join(inlines[1].split())=='''var linkpath=this.puzzle_link_map[this.puzzlehash];if(linkpath){var link=document.getElementById("link");link.innerHTML='<a href="../../'+linkpath+'/"><img src="../../'+linkpath+'/icon-large.png"></a>';}'''.replace(' ',''),'Release script drift')
    payload=SCRIPTS.sub(b'',data)
    favicon=re.compile(rb'<link rel="shortcut icon" href="../../favicon.ico"\s*/>')
    require(len(favicon.findall(payload))==1,'Favicon drift');payload=favicon.sub(b'',payload)
    navs=[a for a in soup.find_all('a',href=True) if a['href'] in ('../','../../','../..')]
    require(len(navs)==(2 if show else 1 if letter else 3),'Navigation count drift')
    for ref in {a['href'] for a in navs}:
        token=('href="'+ref+'"').encode();payload=payload.replace(token,('data-archive-href="'+ref+'"').encode())
    styles={}
    for i,link in enumerate(soup.find_all('link',rel='stylesheet')):
        ref=link['href'];require(ref in ('../style.css','style.css','../../subpage.css'),'Unreviewed stylesheet');name=f'style-{i}.css';styles[name]=urljoin(url,ref)
        for q in (b'"',b"'"):payload=payload.replace(b'href='+q+ref.encode()+q,b'href='+q+name.encode()+q)
    require(not re.search(rb'url\(',payload),'Unreviewed inline URL')
    return payload,styles


def localize(payload,url):
    deps={};soup=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in soup.find_all(tag,attrs={attr:True}):
            ref=el[attr];name=Path(ref).name;require(re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|gif)',name),'Unreviewed image: '+ref);target=urljoin(url,ref);require(target.startswith('https://puzzles.mit.edu/2012/puzzles/'),'Image outside archive');require(name not in deps or deps[name]==target,'Image collision');deps[name]=target
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+ref.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def css_ref(ref,url):
    target=urljoin(url,ref.strip(b'\'"').decode('ascii'))
    if target.startswith('http://fonts.googleapis.com/'):target='https://'+target[7:]
    require(target.startswith('https://puzzles.mit.edu/2012/puzzles/') or target in FONT_CSS or target.startswith('https://fonts.gstatic.com/s/'),'Unreviewed CSS dependency: '+target)
    return target


def css_graph(styleurls,snapshots):
    names={u:n for n,u in styleurls.items()};styles={};deps={};pending=list(names)
    while pending:
        url=pending.pop(0)
        if url not in snapshots:snapshots[url]=snapshot(url)
        data=(ROOT/snapshots[url]['path']).read_bytes();require(b'<html' not in data.lower(),'HTML masquerading as CSS');imports=list(IMPORT.finditer(data))
        require(len(imports)==len(re.findall(rb'@import',data)),'Unsupported import syntax')
        for m in reversed(imports):
            target=css_ref(m[1] or m[2],url)
            if target not in names:names[target]=f'style-{len(names)}.css';pending.append(target)
            data=data[:m.start()]+b'@import "'+names[target].encode()+b'";'+data[m.end():]
        def replace(m):
            target=css_ref(m[1],url)
            if target not in deps.values():
                ext=Path(urlparse(target).path).suffix;require(ext in ('.jpg','.png','.gif','.ttf'),'Unreviewed CSS asset');name=f'css-{len(deps)}'+ext;deps[name]=target
            name=next(n for n,u in deps.items() if u==target)
            return b'url("'+name.encode()+b'")'
        data=URL.sub(replace,data);styles[names[url]]=data
    return styles,deps,{n:u for u,n in names.items()}


def check_css(path,allowed):
    data=path.read_bytes();plain=re.sub(rb'/\*.*?\*/',b'',data,flags=re.S)
    require(not re.search(rb'expression\(|javascript:|https?://|<script',plain,re.I),'Active/remote CSS')
    imports=list(IMPORT.finditer(plain));require(len(imports)==len(re.findall(rb'@import',plain)),'Unsupported import')
    refs=[(m[1] or m[2]).strip(b'\'"') for m in imports]+[m[1].strip(b'\'"') for m in URL.finditer(plain)]
    for ref in refs:require((path.parent/ref.decode('ascii')).resolve() in allowed,'Missing CSS dependency')


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==13,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        require(not any(a['role']=='agent_visible' for a in old['assets']),'Previously public');url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url);payload,deps=localize(payload,url);styles,cssdeps,allstyles=css_graph(styleurls,snapshots);require(not(set(deps)&set(cssdeps)),'Asset collision');deps.update(cssdeps);licenses={}
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlparse(target).path.split('/')[2];name=family+'-OFL.txt';licenses[name]='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        deps.update(licenses);prepared[old['problem_id']]=(url,payload,styles,styleurls,allstyles,deps);urls.add(url);urls.update(deps.values())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];url,payload,styles,styleurls,allstyles,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML differs: '+pid);folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared data drift')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in styles.items():add(data,name,'text/css')
        for name,target in sorted(deps.items()):
            p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
            if ext in ('.png','.jpg','.gif'):
                with Image.open(p) as im:im.verify()
            elif ext=='.ttf':ImageFont.truetype(str(p),16).getmask('Archive')
            add(p.read_bytes(),name,{'.png':'image/png','.jpg':'image/jpeg','.gif':'image/gif','.ttf':'font/ttf','.txt':'text/plain'}[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styles:check_css(folder/name,allowed)
        note='Original standalone text, blank patterns, image order and explicitly linked full-size images are preserved. Cross-task navigation is inert; archive release, points and answer-checking scripts are removed. Original CSS cascade and image bytes are retained with local URL rewrites. The originally named Google Fonts families are snapshotted from their current publisher service; these binaries are not certified as the historical 2012 revisions. Contemporary font license notices accompany those dependencies, not the puzzle license. Historical place clues, fictional letters and cross-puzzle instructions are not modernized or completed with other answers. Shared-page answer variants remain distinct; scores and readiness are unchanged, not recertified.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the styled original packet and explicitly linked images. Text previews do not replace visual clues or blank cells.\n\nArchive limitation: '+note,assets=public+assets,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy=note)
        row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2012_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,all_stylesheet_urls=allstyles,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=13,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1546:8500,1566:2300,1591:3400,1603:1200,1610:2600,1640:10000,1642:4500,1645:1600,1647:4200,1651:5000,1659:2600,1666:2700,1667:2700}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
