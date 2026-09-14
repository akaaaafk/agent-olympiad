"""Recover sixteen source-backed 2015 pages without archive answers or scripts."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageFont
from scripts.repair_mystery_2001_packets_20260913 import ROOT, PATH, Store, read, sha, require, download, check_html, provenance, writer as static_writer

CACHE='data/.cache/mystery_2015_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2015_static_20260913/'
REPORT='data/benchmarks/mystery_2015_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1970,1985,1995,2002,2007,2008,2035,2040,2044,2045,2062,2080,2103,2107,2109,2124)}
ORIGIN='https://puzzles.mit.edu/2015/'
MIRROR='https://web.mit.edu/puzzle/www/2015/'
URL=re.compile(rb'url\(([^)]+)\)')
QUOTES=bytes([34,39])
EXT_MIME={'.png':'image/png','.jpg':'image/jpeg','.gif':'image/gif','.eot':'application/vnd.ms-fontobject','.woff':'font/woff','.woff2':'font/woff2','.ttf':'font/ttf','.svg':'image/svg+xml'}


def snapshot(url):
    if url.startswith(ORIGIN):return download(url)
    require(url.startswith(MIRROR),'Unreviewed publisher origin: '+url)
    expected=ORIGIN+url[len(MIRROR):].lstrip('/')
    stem=hashlib.sha256(url.encode()).hexdigest();p=ROOT/CACHE/'publisher'/(stem+'.bin');meta=p.with_suffix('.json')
    if p.exists():
        d=read(meta);require(d['source_url']==url and d['final_url']==expected and sha(p)==d['sha256'],'Mirror snapshot drift');return d
    r=requests.get(url,timeout=40);r.raise_for_status();require(r.url==expected and r.content,'Unexpected publisher redirect: '+r.url)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as out:out.write(r.content)
    d=dict(source_url=url,final_url=r.url,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(r.content),content_type=r.headers.get('Content-Type'),redirects=[dict(url=h.url,status=h.status_code) for h in r.history],retrieved_at_utc=Store(ROOT).stamp)
    Store(ROOT).save(meta.relative_to(ROOT).as_posix(),d);return d


def replace_ref(data,attr,ref,name):
    found=False
    for q in (b'"',b"'"):
        old=attr.encode()+b'='+q+ref.encode()+q
        if old in data:found=True;data=data.replace(old,attr.encode()+b'='+q+name.encode()+q)
    require(found,'Reference serialization drift: '+ref);return data


def sanitize(data,url):
    soup=BeautifulSoup(data,'html.parser');scripts=soup.find_all('script')
    require([s.get('src') for s in scripts]==['https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js',MIRROR+'static/bootstrap/javascripts/bootstrap.js',None,'/checkanswer.js'],'Unreviewed scripts')
    answer=soup.select_one('.puzzle-page-header > .answer');require(answer is not None and re.fullmatch('answer_[0-9]+',answer.get('id','')) and answer.get_text(' ',strip=True)=='Answer: click here to reveal','Answer placeholder drift')
    aid=re.escape(answer['id']);gold_script=scripts[2].get_text().strip()
    grammar=r'\$\(document\)\.ready\(function\(e\) \{ \$\(\x27#'+aid+r'\x27\)\.click\(function\(e\) \{ \$\(\x27#'+aid+r'\x27\)\.text\("Answer: " \+ "[^"\r\n]*"\);\}\);\}\);'
    require(re.fullmatch(grammar,gold_script) is not None,'Answer reveal grammar drift')
    payload=re.sub(rb'<script\b[^>]*>.*?</script>',b'',data,flags=re.S|re.I)
    navs=re.findall(rb'<nav\b[^>]*>.*?</nav>',payload,re.S);require(len(navs)==1,'Navbar boundary drift')
    nav=BeautifulSoup(navs[0],'html.parser');require([a['href'] for a in nav.find_all('a')]==[MIRROR+'intro.html',MIRROR+'storylog.html','#']+[MIRROR+x for x in ('toc.html','eventschedule.html','updates.html','completelog.html','faq.html','sponsors.html','')],'Archive navbar contents drift');payload=payload.replace(navs[0],b'')
    solutions=re.findall(rb'<div class="sol"><a href="solution/">View Solution</a></div>',payload);require(len(solutions)==1,'Solution control drift');payload=payload.replace(solutions[0],b'')
    pattern=rb'<p class="answer" id="'+answer['id'].encode()+rb'"> Answer: click here to reveal</p>';require(len(re.findall(pattern,payload))==1,'Answer header serialization drift');payload=re.sub(pattern,b'',payload)
    icons=re.findall(rb'<link rel="icon"[^>]+/>',payload);require(len(icons)==1 and MIRROR.encode()+b'static/images/hunt/icon32.png' in icons[0],'Favicon drift');payload=payload.replace(icons[0],b'')
    styles={}
    for link in soup.find_all('link',rel='stylesheet'):
        ref=link['href'];require(ref.startswith(MIRROR) and ref.endswith('.css'),'Unreviewed stylesheet');name=f'style-{len(styles)}.css';styles[name]=ref;payload=replace_ref(payload,'href',ref,name)
    require(len(styles) in (3,4),'Style count drift');return payload,styles


def check_css_data(data):
    # Bootstrap's print-only attribute selector is not executable JavaScript.
    data=re.sub(rb'/\*.*?\*/',b'',data,flags=re.S).replace(b'a[href^="javascript:"]',b'a[href^="inert-qa-selector:"]')
    require(not re.search(rb'@import|expression\s*\(|behavior\s*:|javascript:|data:',data,re.I),'Active/unreviewed CSS')


def localize_css(data,url,deps):
    check_css_data(data)
    def replace(m):
        ref=m[1].strip().strip(QUOTES).decode('ascii');parts=urlsplit(ref);require(not parts.query and parts.fragment in ('','iefix','glyphicons_halflingsregular','im_fell_double_pica_scregular','griffosfontregular'),'Unreviewed CSS suffix')
        target=urljoin(url,ref.split('#')[0].rstrip('?'));require(target.startswith((ORIGIN,MIRROR)),'Unreviewed CSS origin');ext=Path(urlsplit(target).path).suffix;require(ext in EXT_MIME,'Unreviewed CSS asset type')
        if target not in deps.values():deps[f'css-{len(deps)}'+ext]=target
        name=next(n for n,u in deps.items() if u==target);suffix=('?' if '?#' in ref else '')+('#'+parts.fragment if parts.fragment else '')
        return b'url("'+(name+suffix).encode()+b'")'
    return URL.sub(replace,data)


def localize_html(data,url):
    deps={};soup=BeautifulSoup(data,'html.parser');require(not soup.find_all('a',href=True),'Unreviewed body link')
    for el in soup.find_all('img',src=True):
        ref=el['src'];target=urljoin(url,ref);name=Path(urlsplit(target).path).name
        require(target.startswith((ORIGIN,MIRROR)) and re.fullmatch(r'[A-Za-z0-9_-]+\.(gif|png|jpg)',name),'Unreviewed image');require(name not in deps or deps[name]==target,'Image basename collision')
        if name in deps:continue
        deps[name]=target;data=replace_ref(data,'src',ref,name)
    return data,deps


def localize_inline(data,url,deps):
    return re.sub(rb'(<style\b[^>]*>)(.*?)(</style>)',lambda m:m[1]+localize_css(m[2],url,deps)+m[3],data,flags=re.S)


def check_css(path,allowed):
    check_css_data(path.read_bytes());data=re.sub(rb'/\*.*?\*/',b'',path.read_bytes(),flags=re.S);require(not re.search(rb'https?://',data),'Remote CSS')
    for m in URL.finditer(data):
        ref=urlsplit(m[1].strip().strip(QUOTES).decode('ascii'));require(not ref.netloc and not ref.scheme and (path.parent/ref.path).resolve() in allowed,'Unlisted CSS dependency')


def inspect_asset(path,ext):
    data=path.read_bytes()
    if ext in ('.jpg','.png','.gif'):
        with Image.open(path) as im:
            result=dict(format=im.format,size=list(im.size),frames=getattr(im,'n_frames',1),loop=im.info.get('loop'),durations=[],disposals=[])
            for i in range(result['frames']):
                im.seek(i);im.load();result['durations'].append(im.info.get('duration'));result['disposals'].append(getattr(im,'disposal_method',None))
            return result
    if ext=='.ttf':ImageFont.truetype(str(path),16).getmask('Archive');return dict(check='FreeType font render')
    if ext in ('.woff','.woff2'):
        require(data[:4]==({'.woff':b'wOFF','.woff2':b'wOF2'}[ext]) and struct.unpack('>I',data[8:12])[0]==len(data),'WOFF header/length mismatch');return dict(check='signature and declared container length; not full font validation')
    if ext=='.eot':
        require(len(data)>82 and struct.unpack('<I',data[:4])[0]==len(data) and data[34:36]==b'LP','EOT header mismatch');return dict(check='header, magic and declared size; not full font validation')
    require(ext=='.svg','Unsupported asset')
    tree=ET.fromstring(data);require(tree.tag.endswith('svg') and not re.search(rb'<script|javascript:',data,re.I),'Active SVG')
    for el in tree.iter():
        for attr,value in el.attrib.items():
            require(not attr.rsplit('}',1)[-1].lower().startswith('on'),'SVG event handler')
            if attr.endswith('href'):require(value.startswith('#'),'External SVG reference')
    return dict(check='XML font syntax and no active or external references')


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==16,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url);payload,deps=localize_html(payload,url);styles={};cssdeps={}
        for name,target in styleurls.items():
            if target not in snapshots:snapshots[target]=snapshot(target)
            styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
        payload=localize_inline(payload,url,cssdeps);require(not(set(deps)&set(cssdeps)),'CSS/content collision');deps.update(cssdeps);urls.add(url);urls.update(deps.values());prepared[old['problem_id']]=(url,payload,styles,styleurls,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[];asset_reviews={}
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];n=int(pid[-5:]);url,payload,styles,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML differs: '+pid);folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
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
            if target not in asset_reviews:asset_reviews[target]=inspect_asset(p,ext)
            add(p.read_bytes(),name,EXT_MIME[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styles:check_css(folder/name,allowed)
        for block in clean.find_all('style'):
            check_css_data(block.get_text().encode())
            for m in URL.finditer(block.get_text().encode()):require((folder/urlsplit(m[1].strip().strip(QUOTES).decode()).path).resolve() in allowed,'Missing inline CSS asset')
        note='Only the original standalone archived body and its explicit visual dependencies are restored. Archive solution links, answer-reveal header and gold-bearing scripts, navigation and scripts are removed. Original published CSS, images and font files are preserved or mechanically relinked; original CSS font query/fragment suffixes are retained. Puzzles are not solved, historical wording is not modernized, and blank cells, geometry, colors and deliberately misspelled words are not corrected. Gold, scores, splits, license and grading/runtime readiness are unchanged and not recertified.'
        if n==1970:note+=' All eleven original GIF files are byte-preserved; all frames are decoded, including ten animations, without flattening, retiming or claiming full semantic playback review.'
        if n==2007:note+=' Dory uses apparent errata for other puzzles as its own clue content. These statements are retained only in Dory and are not applied to other records.'
        if n in (1995,2062,2080):note+=' This archived meta page contains only an instruction to call in a submarine upgrade. Other-puzzle answers, physical components and host interaction are absent; this input packet does not make the meta independently solvable.'
        if n==2045:note+=' The archived chest narrative, lid and four paper codes are retained; other round puzzles and physical locks are not reconstructed.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        title=clean.select_one('.puzzle-page-header h1').get_text(' ',strip=True);row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# '+title+'\n\nOpen `puzzle.html` for the original styled packet. Text previews do not replace visual cells, animation, colors or diagrams.\n\nArchive limitation: '+note,source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2015_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,asset_reviews=asset_reviews));print(json.dumps(dict(records=16,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1970:10200,1985:1700,1995:1500,2002:3300,2007:5800,2008:7500,2035:8400,2040:4500,2044:8000,2045:2400,2062:1500,2080:1500,2103:5000,2107:3400,2109:4400,2124:5000}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
