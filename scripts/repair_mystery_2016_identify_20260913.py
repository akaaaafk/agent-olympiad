"""Restore static clue images and literal TeX using a deliberately narrow MathML projection."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2016_static_20260913 import ORIGIN,EXT_MIME,sanitize as common_sanitize,localize_css,localize_inline,snapshot,check_css,inspect_asset,replace_ref
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2016_identify_20260913/'
RAW='data/raw/mystery_hunt/separated_2016_identify_20260913/'
REPORT='data/benchmarks/mystery_2016_identify_repair_20260913.json'
SELECTED={'mystery_hunt_02174'}
PAGE=ORIGIN+'puzzle/identify_sort_index_solve/'
UPSTREAM='https://raw.githubusercontent.com/mathjax/MathJax/2.6.0/MathJax.js'
UPSTREAM_SHA='ecc42ce8f9a2d60610535602d20dcb2d48e1bd145c4e4e095155d401dc0d150f'
ARCHIVE_JS_SHA='877078e3049eb88e4d909ad79b634544fbbc86251fe85ef5ac6e904789facc32'
TEX=re.compile(rb'\\\((.*?)\\\)',re.S)


def library_evidence():
    path=ROOT/CACHE/'upstream-MathJax.js';meta=ROOT/CACHE/'upstream-MathJax.json'
    if not path.exists():
        r=requests.get(UPSTREAM,timeout=30);r.raise_for_status();require(r.url==UPSTREAM and hashlib.sha256(r.content).hexdigest()==UPSTREAM_SHA,'Upstream version drift');path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as out:out.write(r.content)
        Store(ROOT).save(meta.relative_to(ROOT).as_posix(),dict(source_url=UPSTREAM,final_url=r.url,path=path.relative_to(ROOT).as_posix(),sha256=UPSTREAM_SHA,bytes=len(r.content),retrieved_at_utc=Store(ROOT).stamp))
    a=path.read_bytes();s=snapshot(PAGE+'puzzle.js');b=(ROOT/s['path']).read_bytes();require(sha(path)==UPSTREAM_SHA and sha(ROOT/s['path'])==ARCHIVE_JS_SHA,'Library hash drift');require(b.count(br'\../../')==5 and b.replace(br'\../../',br'\./')==a,'Archive script is not the reviewed MathJax library');return read(meta),s


def mathml(tex):
    # Only this source's finite grammar: integers, A/BB, two arrow commands,
    # parentheses, punctuation and explicitly braced superscripts. No evaluation.
    tokens=re.findall(r'\\(?:uparrow|rightarrow)|\d+|BB|A|[{}^()=!,\.]',tex);require(''.join(tokens)==re.sub(r'\s+','',tex),'Unreviewed TeX token');pos=0
    def sequence(end=None):
        nonlocal pos
        out=[]
        while pos<len(tokens) and tokens[pos]!=end:
            t=tokens[pos];pos+=1
            if t=='^':
                require(out and pos<len(tokens) and tokens[pos]=='{','Unbraced exponent');pos+=1;power=sequence('}');out[-1]='<msup>'+out[-1]+power+'</msup>';continue
            if t in ('{','('):
                inner=sequence('}' if t=='{' else ')');node=inner if t=='{' else '<mrow><mo>(</mo>'+inner+'<mo>)</mo></mrow>'
            elif t.isdigit():node='<mn>'+t+'</mn>'
            elif t in ('A','BB'):node=''.join('<mi>'+letter+'</mi>' for letter in t)
            elif t in ('\\uparrow','\\rightarrow'):node='<mo>'+('↑' if t=='\\uparrow' else '→')+'</mo>'
            else:require(t in '=!,.','Unexpected closing token');node='<mo>'+t+'</mo>'
            out.append(node)
        if end is not None:require(pos<len(tokens) and tokens[pos]==end,'Unbalanced TeX');pos+=1
        return '<mrow>'+''.join(out)+'</mrow>'
    body=sequence();require(pos==len(tokens),'Unparsed TeX');return ('<math xmlns="http://www.w3.org/1998/Math/MathML"><semantics>'+body+'<annotation encoding="application/x-tex">'+escape(tex)+'</annotation></semantics></math>').encode('utf-8')


def sanitize(data,url):
    for s in (b"<script src='https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'></script>",b'<script src="puzzle.js"></script>'):
        require(data.count(s)==1,'Math library tag drift');data=data.replace(s,b'')
    payload,styles=common_sanitize(data,url);require(len(TEX.findall(payload))==29,'Formula count drift');payload=TEX.sub(lambda m:mathml(m[1].decode('ascii')),payload);return payload,styles


def localize_html(payload,url):
    deps={};seen=set()
    for img in BeautifulSoup(payload,'html.parser').find_all('img'):
        ref=img['src'];target=urljoin(url,ref);name=Path(urlsplit(target).path).name;require(target.startswith(ORIGIN) and re.fullmatch(r'[A-Za-z0-9_-]+\.(jpg|png|gif)',name),'Image scope drift');require(name not in deps or deps[name]==target,'Image collision');deps[name]=target
        if ref not in seen:payload=replace_ref(payload,'src',ref,name);seen.add(ref)
    require({n for n in deps if re.fullmatch(r'a\d+\.jpg',n)}=={f'a{n:02}.jpg' for n in range(1,30)},'Clue image set drift');return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==1,'Selection drift');old=chosen[0];row=deepcopy(old);pid=old['problem_id'];source=ROOT/old['source_file'];upstream,archived=library_evidence();payload,styleurls=sanitize(source.read_bytes(),PAGE);payload,deps=localize_html(payload,PAGE);styles={};cssdeps={};snapshots={UPSTREAM:upstream,PAGE+'puzzle.js':archived}
    for name,target in styleurls.items():snapshots[target]=snapshot(target);styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
    payload=localize_inline(payload,PAGE,cssdeps);require(not(set(deps)&set(cssdeps)),'CSS collision');deps.update(cssdeps)
    for target in list(cssdeps.values()):
        if target.startswith('https://fonts.gstatic.com/'):
            family=urlsplit(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(({PAGE}|set(deps.values()))-set(snapshots)))})
    remote=ROOT/snapshots[PAGE]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);copies=[];public=[];reviews={}
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
        if ext=='.txt':require(b'SIL OPEN FONT LICENSE' in p.read_bytes(),'Font license drift');mime='text/plain'
        else:reviews[target]=inspect_asset(p,ext);mime=EXT_MIME[ext]
        add(p.read_bytes(),name,mime)
    allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
    for p in folder.glob('*.css'):check_css(p,allowed)
    note='The original 29-row image-and-formula table is static. Its puzzle.js is MathJax 2.6.0 with five archive-rewritten regular expressions; no puzzle-specific state logic was found by exact comparison to the pinned upstream library after reversing those five substitutions. Neither script is executed or exposed. All 29 literal TeX fragments are mechanically projected to native MathML, preserving their original TeX in annotations, without calculating, sorting, simplifying or answering. Native mathematical font metrics are not certified identical to historical MathJax. Original image bytes, GIF frames, row order, example labels, blank answer line, capitalization and historical number descriptions remain. Archive solution navigation and sheep/status scripts are removed; round navigation is inert. Same-year CSS repairs follow the static batch; current source-named Google fonts include OFL texts, not certified 2016 binaries. Gold, total points, splits, license and grading/runtime readiness are unchanged and not recertified.'
    assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    row.update(source_url=PAGE,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# identify, SORT, index, solve\n\nOpen `puzzle.html` for all original images and formulas. The mathematical expressions are displayed natively; their original TeX remains in the HTML annotations.\n\nArchive limitation: '+note,source_visibility='static_mathml_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2016_identify_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[PAGE]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row)
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots,asset_reviews=reviews,tex_fragments=[s.decode('ascii') for s in TEX.findall(source.read_bytes())]));print(json.dumps(dict(records=1,public_files=len(copies),publisher_files=len(snapshots),formulas=29)))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def correct_prepared_bb():
    require(not (ROOT/REPORT).exists(),'Applied plan is frozen');plan=read(ROOT/CACHE/'plan.json');p=ROOT/CACHE/'mystery_hunt_02174/input/puzzle.html';data=p.read_text(encoding='utf-8');require(data.count('<mi>BB</mi>')==3,'Prepared BB count drift');st=Store(ROOT);st.save_text(p.relative_to(ROOT).as_posix(),data.replace('<mi>BB</mi>','<mi>B</mi><mi>B</mi>'));digest=sha(p)
    for c in plan['copies']:
        if c['source']==p.relative_to(ROOT).as_posix():c['sha256']=digest
    for a in plan['updates'][0]['after']['assets']:
        if a['path']==RAW+'mystery_hunt_02174/input/puzzle.html':a['sha256']=digest
    st.save(CACHE+'plan.json',plan)


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);page=ROOT/CACHE/'mystery_hunt_02174/input/puzzle.html';dest=out/'identify.png';p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1600,6000','--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed')
    with Image.open(dest) as im:
        for y in range(0,4000,1000):im.crop((250,y,1400,y+1000)).save(out/f'identify-{y}.png')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='correct-prepared-bb':correct_prepared_bb()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
