"""Restore nine explicitly static 2016 inputs with conservative source isolation."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from scripts.repair_mystery_2015_static_20260913 import EXT_MIME,URL,QUOTES,replace_ref,check_css,check_css_data,inspect_asset
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2016_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2016_static_20260913/'
REPORT='data/benchmarks/mystery_2016_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (2166,2197,2200,2205,2218,2220,2241,2258,2262)}
ORIGIN='https://puzzles.mit.edu/2016/'
FONT_CSS={'https://fonts.googleapis.com/css?family='+q for q in ('Montserrat:400,700','Alegreya+Sans:400,300,700')}
FONT_FAMILIES={'montserrat','alegreyasans'}
spec=importlib.util.spec_from_file_location('_mystery2016_fonts',ROOT/'scripts/repair_mystery_2012_static_20260913.py');font_transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(font_transport);font_transport.CACHE=CACHE;font_transport.FONT_CSS=FONT_CSS;font_transport.FONT_FAMILIES=FONT_FAMILIES
FONT_REPAIRS={ORIGIN+'static/stylesheets/bootstrap/fonts/bootstrap/glyphicons-halflings-regular.'+e:ORIGIN+'static/bootstrap/fonts/bootstrap/glyphicons-halflings-regular.'+e for e in ('eot','woff','ttf','svg')}
LOGO_REPAIRS={ORIGIN+'static/images/huntception.png':ORIGIN+'static/spoilr/images/huntception.png'}


def snapshot(url):return download(url) if url.startswith(ORIGIN) else font_transport.snapshot(url)


def failed_font_paths():
    path=ROOT/CACHE/'failed-font-paths.json'
    if path.exists():return read(path)
    rows=[]
    for old,new in FONT_REPAIRS.items():
        r=requests.get(old,timeout=25);require(r.url==old and r.status_code==404,'Font path status changed; review again');rows.append(dict(source_url=old,http_status=404,recovered_url=new,response_sha256=hashlib.sha256(r.content).hexdigest(),retrieved_at_utc=Store(ROOT).stamp))
    Store(ROOT).save(path.relative_to(ROOT).as_posix(),rows);return rows


def failed_logo_path():
    path=ROOT/CACHE/'failed-logo-path.json'
    if path.exists():return read(path)
    old,new=next(iter(LOGO_REPAIRS.items()));r=requests.get(old,timeout=25);require(r.url==old and r.status_code==404,'Logo status changed; review again');d=dict(source_url=old,http_status=404,recovered_url=new,response_sha256=hashlib.sha256(r.content).hexdigest(),retrieved_at_utc=Store(ROOT).stamp,scope='Only stylesheet rules for removed archive navigation refer to this logo; it is not puzzle clue content.');Store(ROOT).save(path.relative_to(ROOT).as_posix(),d);return d


def sanitize(data,url):
    comment=b'<!--<script src="../..//code.jquery.com/ui/1.11.2/jquery-ui.js"></script>-->';require(data.count(comment)==1,'Commented UI script drift');payload=data.replace(comment,b'');soup=BeautifulSoup(payload,'html.parser');scripts=soup.find_all('script');require([s.get('src') for s in scripts]==['https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js','../../static/bootstrap/javascript/bootstrap.js',None,'/checkanswer.js'],'Unreviewed script sources')
    expected='''$(document).ready(function(){ $.getJSON('../../sheep.json').done(function(data) { $('span.current-sheep').html(data.sheep); $('span.next-update').html(data.update); }); $("#nextupdate").hover(function(){ $('#navtooltip').addClass('hover'); }, function(){ $('#navtooltip').removeClass('hover'); }); });''';require(''.join(scripts[2].get_text().split())==''.join(expected.split()),'Archive status script drift');payload=re.sub(rb'<script\b[^>]*>.*?</script>',b'',payload,flags=re.S|re.I)
    navs=re.findall(rb'<nav\b[^>]*>.*?</nav>',payload,re.S);require(len(navs)==1,'Nav boundary drift');nav=BeautifulSoup(navs[0],'html.parser');require([a['href'] for a in nav.find_all('a')]==['index.html','#','../../toc.html','../../faq.html','solution/','../../'],'Nav contents drift');payload=payload.replace(navs[0],b'')
    back=soup.select('a.back-to-round');require(len(back)==1 and back[0]['href'].startswith('../../round/'),'Round navigation drift');ref=back[0]['href'];payload=payload.replace(('href="'+ref+'"').encode(),('data-archive-href="'+ref+'"').encode())
    credit=soup.select('.footer a')
    if credit:
        require(len(credit)==1 and credit[0]['href']=='http://www.ahc.com/' and credit[0].parent.get_text(' ',strip=True)=='Puzzle artwork designed and produced by ahc.com','Artwork attribution drift');payload=payload.replace(b'href="http://www.ahc.com/"',b'data-archive-href="http://www.ahc.com/"')
    favicon=b'<link rel="icon" href="../../static/hunt/images/icon32.png" type="image/x-icon" />';require(payload.count(favicon)==1,'Icon drift');payload=payload.replace(favicon,b'');require(not soup.select('.header .answer'),'Unexpected answer header')
    styles={}
    for link in soup.find_all('link',rel='stylesheet'):
        ref=link['href'];target=urljoin(url,ref);require(target.startswith(ORIGIN) or target in FONT_CSS,'Unreviewed style');name=f'style-{len(styles)}.css';styles[name]=target;payload=replace_ref(payload,'href',ref,name)
    require(len(styles) in (5,6),'Style count drift');return payload,styles


def localize_css(data,url,deps):
    check_css_data(data)
    def replace(m):
        ref=m[1].strip().strip(QUOTES).decode('ascii');parts=urlsplit(ref);require(not parts.query and parts.fragment in ('','iefix','glyphicons_halflingsregular'),'CSS suffix drift');target=urljoin(url,ref.split('#')[0].rstrip('?'));target=FONT_REPAIRS.get(target,LOGO_REPAIRS.get(target,target));require(target.startswith(ORIGIN) or target.startswith('https://fonts.gstatic.com/s/'),'Unreviewed CSS origin');ext=Path(urlsplit(target).path).suffix;require(ext in EXT_MIME,'CSS type drift')
        if target not in deps.values():deps[f'css-{len(deps)}'+ext]=target
        name=next(n for n,u in deps.items() if u==target);suffix=('?' if '?#' in ref else '')+('#'+parts.fragment if parts.fragment else '');return b'url("'+(name+suffix).encode()+b'")'
    return URL.sub(replace,data)


def localize_html(data,url):
    deps={};seen=set();soup=BeautifulSoup(data,'html.parser')
    for tag,attr in [('img','src'),('image','src'),('a','href')]:
        for el in soup.find_all(tag,attrs={attr:True}):
            ref=el[attr];target=urljoin(url,ref);name=Path(urlsplit(target).path).name;require(target.startswith(ORIGIN) and re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg)',name),'Unreviewed static attachment');require(name not in deps or deps[name]==target,'Image collision');deps[name]=target
            if (attr,ref) not in seen:data=replace_ref(data,attr,ref,name);seen.add((attr,ref))
    return data,deps


def localize_inline(data,url,deps):return re.sub(rb'(<style\b[^>]*>)(.*?)(</style>)',lambda m:m[1]+localize_css(m[2],url,deps)+m[3],data,flags=re.S)


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==9,'Selection drift');snapshots={};prepared={};urls=set();failures=failed_font_paths();logo_failure=failed_logo_path()
    for old in chosen:
        url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url);payload,deps=localize_html(payload,url);styles={};cssdeps={}
        for name,target in styleurls.items():
            if target not in snapshots:snapshots[target]=snapshot(target)
            styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
        payload=localize_inline(payload,url,cssdeps);require(not(set(cssdeps)&set(deps)),'CSS collision');deps.update(cssdeps)
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlsplit(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        urls.add(url);urls.update(deps.values());prepared[old['problem_id']]=(url,payload,styles,styleurls,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[];reviews={}
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];n=int(pid[-5:]);url,payload,styles,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift: '+pid);folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared drift')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in styles.items():add(data,name,'text/css')
        for name,target in sorted(deps.items()):
            p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
            if ext=='.txt':require(b'SIL OPEN FONT LICENSE' in p.read_bytes(),'Font license drift')
            elif target not in reviews:reviews[target]=inspect_asset(p,ext)
            add(p.read_bytes(),name,EXT_MIME[ext] if ext!='.txt' else 'text/plain')
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for p in folder.glob('*.css'):check_css(p,allowed)
        for block in clean.find_all('style'):
            check_css_data(block.get_text().encode());require(not URL.search(block.get_text().encode()),'Unexpected inline image')
        note='Only original static standalone content and explicitly linked images are restored. Archive solution navigation, shared sheep/status requests and scripts are removed; round-return navigation and the artwork-credit hyperlink are inert, with attribution wording retained. Original geometry, blank cells, symbols, letter case, repeated clues and historical wording remain unchanged. Four broken Bootstrap font paths are corrected to the existing same-year publisher files; original source bytes and the four 404 responses are retained privately. Source-named Google font binaries are current snapshots with their OFL texts, not certified historical font versions. Local system font fallbacks are not bundled. Gold, total points, splits, license and grading/runtime readiness are unchanged and not recertified.'
        note+=' The stylesheet also points its unused archive-logo rule at a missing path; the original logo survives in the same-year spoilr/images directory and is preserved locally, without restoring archive navigation.'
        if n==2220:note+=' The original large linked image is preserved at 16290 by 4720 pixels; no compressed thumbnail or retyped grid replaces it.'
        if n==2241:note+=' The original team-size-dependent map coverage and field-inhibitor rules are preserved as task content, not converted into benchmark scoring or a fabricated fixed team size. Physical object eligibility and live host verification are still missing; no objects are collected and no host is contacted.'
        if n==2166:note+=' Multiple-choice alternatives and their letter tags remain in original order; game spoilers in question wording are not treated as benchmark-answer disclosure.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        title=clean.select_one('.header h2').get_text(' ',strip=True);row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# '+title+'\n\nOpen `puzzle.html` with the explicitly linked full-resolution images. Text previews do not replace diagrams, subscripts, colors or blank cells.\n\nArchive limitation: '+note,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2016_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,asset_reviews=reviews,failed_font_paths=failures,failed_logo_path=logo_failure));print(json.dumps(dict(records=9,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={2166:2600,2197:2600,2200:3500,2205:1900,2218:3800,2220:1200,2241:4000,2258:1500,2262:3200}
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
