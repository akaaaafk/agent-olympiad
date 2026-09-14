"""Restore thirteen reviewed static pages with pinned, offline-compiled LESS."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageFont
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2013_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2013_static_20260913/'
REPORT='data/benchmarks/mystery_2013_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1684,1686,1687,1689,1702,1727,1775,1802,1807,1810,1820,1821,1824)}
ORIGIN='https://puzzles.mit.edu/2013/coinheist.com/'
FONT_CSS={'https://fonts.googleapis.com/css?family='+q for q in ('Crete+Round:400,400italic','Cantarell:400,700,400italic','Kaushan+Script')}
FONT_FAMILIES={'creteround','cantarell','kaushanscript'}
URL=re.compile(rb'url\(([^)]+)\)')
MISSING_TILE=ORIGIN+'feynman/gptile.jpg'
UNUSED_EVIL=ORIGIN+'get_smart/evilfg.png'
SCRIPTS=re.compile(rb'<script\b[^>]*>.*?</script>',re.S|re.I)
spec=importlib.util.spec_from_file_location('_mystery2013_font_transport',ROOT/'scripts/repair_mystery_2012_static_20260913.py');font_transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(font_transport);font_transport.CACHE=CACHE;font_transport.FONT_CSS=FONT_CSS;font_transport.FONT_FAMILIES=FONT_FAMILIES


def snapshot(url):
    if url==ORIGIN+'oceans_11/oceans_11.js':
        # The publisher really serves an empty JavaScript file, not a redirect.
        p=ROOT/CACHE/'publisher/oceans-empty.js';meta=p.with_suffix('.json')
        if p.exists():
            d=read(meta);require(p.stat().st_size==0 and sha(p)==d['sha256'],'Empty script drift');return d
        r=requests.get(url,timeout=25);r.raise_for_status();require(r.url==url and r.content==b'' and r.headers.get('Content-Type')=='application/javascript','Empty source drift');p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb'):pass
        d=dict(source_url=url,final_url=r.url,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=0,retrieved_at_utc=Store(ROOT).stamp);Store(ROOT).save(meta.relative_to(ROOT).as_posix(),d);return d
    if url.startswith(ORIGIN):return download(url)
    return font_transport.snapshot(url)


def compile_less(data):
    require(not re.search(rb'@import|`|javascript:|expression\s*\(',data,re.I),'Unreviewed active/imported LESS')
    result=subprocess.run(['node',str(ROOT/'scripts/compile_mystery_2013_less_20260913.cjs')],input=data,capture_output=True,timeout=15);require(result.returncode==0,'LESS compile failed: '+result.stderr.decode());return result.stdout


def missing_tile_evidence(url=MISSING_TILE):
    require(url in (MISSING_TILE,UNUSED_EVIL),'Unreviewed missing dependency')
    path=ROOT/CACHE/('publisher/missing-feynman-tile.json' if url==MISSING_TILE else 'publisher/missing-unused-evil.json')
    if path.exists():
        d=read(path);require(d['source_url']==url and d['http_status']==404,'Missing tile evidence drift');return d
    r=requests.get(url,timeout=25);require(r.url==url and r.status_code==404,'Missing tile status changed; review source again')
    d=dict(source_url=url,http_status=404,retrieved_at_utc=Store(ROOT).stamp,response_sha256=hashlib.sha256(r.content).hexdigest(),scope='Page body decoration only; #content retains its separate opaque white background. Historical tile appearance is not recovered.' if url==MISSING_TILE else 'Only #evilbg and #evilbar1 rules reference this asset; both IDs are absent from the selected static pages.',treatment='Only the exact failed background URL is replaced by none; the source fallback color and all other CSS are unchanged.')
    Store(ROOT).save(path.relative_to(ROOT).as_posix(),d);return d


def sanitize(data,url,n):
    comment=rb'<!-- \[if lt IE 8\]>.*?<!\[endif\]-->';matches=re.findall(comment,data,re.S);require(len(matches)==1 and b'http://ie7-js.googlecode.com/svn/version/2.0(beta3)/IE8.js' in matches[0],'Legacy IE comment drift');payload=re.sub(comment,b'',data,flags=re.S)
    soup=BeautifulSoup(payload,'html.parser');scripts=soup.find_all('script');expected=['https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js','../../static/js/less-1.3.0.min.js','../../static/js/fixie-nav.js']+(['../sneakers.js'] if n>=1807 else ['../oceans_11.js'] if n==1775 else [])+['/checkanswer.js'];require([x.get('src') for x in scripts]==expected,'Unreviewed page script');payload=SCRIPTS.sub(b'',payload)
    navpat=rb'<div id="fixie-nav">.*?</div>\s*</div>';navs=re.findall(navpat,payload,re.S);require(len(navs)==1,'Nav boundary drift');nav=BeautifulSoup(navs[0],'html.parser');require([a['href'] for a in nav.find_all('a')]==['../../index.html','../../index.html#notes','../../notes/eventlist/index.html','answer/index.html','../../contact_hq/index.html'],'Nav contents drift');payload=payload.replace(navs[0],b'')
    marker=(b'<span class="answer">Q.E.D.</span>' if n<1700 else b'<span class="answer">-- Solved</span>' if n in (1702,1712,1719,1727) else b'<span class="answer">Solved</span>' if n==1775 else b'<span class="answer"><span>Solved: </span></span>' if n==1802 else b'<span class="answer"> [SOLVED]</span>');require(payload.count(marker)==1,'Archive solved marker drift');payload=payload.replace(marker,b'')
    for ref in ['../index.html','../stratosphere/index.html','../treasure_island/index.html','../caesars_palace/index.html','../aria/index.html','../excalibur/index.html','../luxor/index.html','index.html#']:
        payload=payload.replace(('href="'+ref+'"').encode(),('data-archive-href="'+ref+'"').encode())
    styles={}
    for i,l in enumerate(soup.find_all('link')):
        ref=l['href'];target=urljoin(url,ref);target='https://'+target[7:] if target.startswith('http://fonts.googleapis.com/') else target;require(target.startswith(ORIGIN) or target in FONT_CSS,'Unreviewed style origin');name=f'style-{i}.css';styles[name]=target
        for q in (b'"',b"'"):payload=payload.replace(b'href='+q+ref.encode()+q,b'href='+q+name.encode()+q)
    payload=payload.replace(b'rel="stylesheet/less"',b'rel="stylesheet"').replace(b'type="text/less"',b'type="text/css"');return payload,styles


def localize_css(data,url,deps):
    require(not re.search(rb'@import|`|expression\s*\(|javascript:',data,re.I),'Unreviewed CSS')
    if url==ORIGIN+'feynman/feynman.less':
        token=b"background: #eeeeee url('gptile.jpg') repeat;";require(data.count(token)==1,'Feynman decoration rule drift');data=data.replace(token,b'background: #eeeeee none repeat;')
    if url==ORIGIN+'get_smart/get_smart.less':
        token=b"background-image: url('evilfg.png');";require(data.count(token)==2,'Unused Evil rules drift');data=data.replace(token,b'background-image: none;')
    def replace(m):
        target=urljoin(url,m[1].strip(b'\'"').decode('ascii'));require(target.startswith(ORIGIN) or target.startswith('https://fonts.gstatic.com/s/'),'Unreviewed CSS URL');ext=Path(urlparse(target).path).suffix;require(ext in ('.png','.jpg','.gif','.ttf'),'Unsupported CSS asset')
        if target not in deps.values():deps[f'css-{len(deps)}'+ext]=target
        name=next(n for n,u in deps.items() if u==target);return b'url("'+name.encode()+b'")'
    return URL.sub(replace,data)


def localize_html(payload,url):
    deps={};s=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in s.find_all(tag,attrs={attr:True}):
            ref=el[attr];name=Path(ref).name;require(re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|gif)',name),'Unexpected static attachment: '+ref);target=urljoin(url,ref);require(target.startswith(ORIGIN),'Image outside archive');require(name not in deps or deps[name]==target,'Image collision');deps[name]=target
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+ref.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def localize_inline(payload,url,deps):
    # Work within style blocks only. Original invalid // declaration comments stay.
    return re.sub(rb'(<style\b[^>]*>)(.*?)(</style>)',lambda m:m[1]+localize_css(m[2],url,deps)+m[3],payload,flags=re.S)


def check_css(path,allowed):
    data=re.sub(rb'/\*.*?\*/',b'',path.read_bytes(),flags=re.S);require(not re.search(rb'@import|javascript:|expression\(|https?://',data,re.I),'Active/remote CSS')
    for m in URL.finditer(data):require((path.parent/m[1].strip(b'\'"').decode('ascii')).resolve() in allowed,'Missing CSS dependency')


def packet_title(clean):
    content=clean.find(id='content');heading=clean.find(class_='header') or content.find(class_='window-title') or content.find(['h1','h2'])
    return heading.get_text(' ',strip=True).rstrip(':') if heading else clean.title.get_text().removesuffix(' -- COINHEIST')


def correct_prepared_title():
    require(not (ROOT/REPORT).exists(),'Cannot amend an applied plan');plan=read(ROOT/CACHE/'plan.json');changed=[]
    for u in plan['updates']:
        r=u['after'];clean=BeautifulSoup((ROOT/CACHE/r['problem_id']/'input/puzzle.html').read_bytes(),'html.parser');old,rest=r['problem_description'].split('\n',1);new='# '+packet_title(clean)
        if old!=new:
            require(r['problem_id']=='mystery_hunt_01727' and old=="# Agent 13's Bleater Feed" and new=='# Travels With Charlie','Unexpected title change');r['problem_description']=new+'\n'+rest;changed.append(r['problem_id'])
    require(changed==['mystery_hunt_01727'],'Title already corrected or drift');Store(ROOT).save(CACHE+'plan.json',plan)


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==13,'Selection drift');snapshots={};prepared={};urls=set();missing=[missing_tile_evidence(),missing_tile_evidence(UNUSED_EVIL)]
    for old in chosen:
        pid=old['problem_id'];n=int(pid[-5:]);url='https://puzzles.mit.edu/'+old['puzzle_url'];payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url,n);payload,deps=localize_html(payload,url);styles={};cssdeps={}
        require(not BeautifulSoup(payload,'html.parser').select('#evilbg, #evilbar1'),'Unused Evil selector became active')
        for name,target in styleurls.items():
            if target not in snapshots:snapshots[target]=snapshot(target)
            data=(ROOT/snapshots[target]['path']).read_bytes()
            if target.endswith('.less'):data=compile_less(data)
            styles[name]=localize_css(data,target,cssdeps)
        payload=localize_inline(payload,url,cssdeps);require(not(set(deps)&set(cssdeps)),'CSS/content collision');deps.update(cssdeps)
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlparse(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        urls.add(url);urls.update(deps.values());prepared[pid]=(url,payload,styles,styleurls,deps)
    urls.update([ORIGIN+'sneakers/sneakers.js',ORIGIN+'oceans_11/oceans_11.js'])
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];url,payload,styles,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML differs: '+pid);folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared byte drift')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in styles.items():add(data,name,'text/css')
        for name,target in sorted(deps.items()):
            p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
            if ext in ('.jpg','.png','.gif'):
                with Image.open(p) as im:im.verify()
            elif ext=='.ttf':ImageFont.truetype(str(p),16).getmask('Archive')
            add(p.read_bytes(),name,{'.jpg':'image/jpeg','.png':'image/png','.gif':'image/gif','.ttf':'font/ttf','.txt':'text/plain'}[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styles:check_css(folder/name,allowed)
        for block in clean.find_all('style'):
            for m in URL.finditer(block.get_text().encode()):require((folder/m[1].strip(b'\'"').decode()).resolve() in allowed,'Missing inline CSS asset')
        note='Only the original static standalone body, layout and explicitly linked images are restored. Archive Q.E.D./Solved header markers, status counters, solution navigation and scripts are removed; other navigation is inert. Original LESS is compiled offline using version 1.3.0, with imports and JavaScript expressions disabled. CSS image links and font dependencies are local; the archive League Gothic bytes are preserved, while source-named Google font binaries are current snapshots, not certified historical versions. Historical travel times, fictional advice, cipher text and repeated visual cells are not corrected or modernized. Calling Bingo retains only its listed other-puzzle titles and enumeration; no other answers or unlock states are injected. Federal Reserve retains only its archived fictional server notice; no real bank, puzzle server or terminal commands are contacted or executed. Gold, scores and grading/runtime readiness are unchanged and not recertified.'
        if '/feynman/' in url:note+=' The publisher returns 404 for the page-wide gptile.jpg decoration; its failed URL is replaced by none, preserving the original grey fallback and separate white clue background. Historical decorative appearance is not recovered.'
        if '/get_smart/' in url:note+=' The shared stylesheet also references missing evilfg.png only under #evilbg and #evilbar1, neither present in this packet; those unused image declarations are set to none.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        title=packet_title(clean);row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# '+title+'\n\nOpen `puzzle.html` for the original styled packet and image links. Text previews do not replace blank cells, diagrams, symbols or feed ordering.\n\nArchive limitation: '+note,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2013_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,less_version='1.3.0',font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    tool='data/.cache/mystery_2013_static_20260913/less_tool/package-lock.json';Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,unavailable_dependencies=missing,less_tool_lock=dict(path=tool,sha256=sha(ROOT/tool))));print(json.dumps(dict(records=13,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1684:2800,1686:3400,1687:5400,1689:8000,1702:1700,1727:30000,1775:4600,1802:6200,1807:7400,1810:1400,1820:1700,1821:4600,1824:4200}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='correct-prepared-title':correct_prepared_title()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
