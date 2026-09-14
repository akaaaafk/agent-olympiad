"""Recover Dossier 2 while withholding explicitly post-meta narrative."""
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

CACHE='data/.cache/mystery_2008_dossier_20260913/'
RAW='data/raw/mystery_hunt/separated_2008_dossier_20260913/'
REPORT='data/benchmarks/mystery_2008_dossier_repair_20260913.json'
SELECTED={'mystery_hunt_00994'}
URL='https://puzzles.mit.edu/2008/dossier2.html'
CSS_URL=urljoin(URL,'css/mydossier.css')
SCRIPT_URL=urljoin(URL,'js/rollover.js')
LABEL_LINKS=['world_s_tallest_cryptic/','the_last_of_sheila/','that_ll_tichu_to_mess_with_us/','advisory_boards/','the_mystery_of_the_traditional_scavenger_hunt/','picture_store/','palimpsest/','notes_english/','no_police_record/','let_me_tell_you_a_story/','these_ain_t_no_underpants_gnomes/']


def sanitize(data):
    require(len(SCRIPT.findall(data))==1,'Answer checker drift');payload=SCRIPT.sub(b'',data)
    rollover=b'<script language="javascript" type="text/javascript" src="js/rollover.js"></script>'
    require(payload.count(rollover)==1,'Rollover script drift');payload=payload.replace(rollover,b'')
    pattern=rb'<!-- BEGIN POST-META TEXT -->.*?<!-- END POST-META TEXT -->'
    matches=re.findall(pattern,payload,re.S);require(len(matches)==1,'Post-meta boundary drift');deferred=matches[0].decode('ascii');payload=re.sub(pattern,b'',payload,flags=re.S)
    soup=BeautifulSoup(payload,'html.parser');require([a['href'] for a in soup.find_all('a')]==['index.html']+LABEL_LINKS,'Dossier navigation drift')
    home=rb'<a href="index.html">(<img [^>]+/>)</a>';require(len(re.findall(home,payload))==1,'Home marker drift');payload=re.sub(home,rb'\1',payload)
    for href in LABEL_LINKS:
        p=rb'<a href="'+re.escape(href.encode())+rb'">([^<]+)</a>';require(len(re.findall(p,payload))==1,'Task label drift')
        payload=re.sub(p,rb'<span class="archive-puzzle-label">\1</span>',payload)
    require(payload.count(b'href="css/mydossier.css"')==1,'Stylesheet drift');payload=payload.replace(b'href="css/mydossier.css"',b'href="mydossier.css"')
    for name in ('dossier_preload.shtml','dossier_list.shtml'):
        include=b'<!--#include virtual="'+name.encode()+b'" -->';require(payload.count(include)==1,'SSI marker drift');payload=payload.replace(include,b'')
    soup=BeautifulSoup(payload,'html.parser');image_paths=[t['src'] for t in soup.find_all('img')]
    require(len(image_paths)==5 and len({Path(n).name for n in image_paths})==5,'Image scope drift')
    for path in image_paths:payload=payload.replace(b'src="'+path.encode()+b'"',b'src="'+Path(path).name.encode()+b'"')
    return payload,deferred,{Path(path).name:urljoin(URL,path) for path in image_paths}


def local_css(data,html):
    soup=BeautifulSoup(html,'html.parser');removed=[]
    selectors=[f'.dossier{i}{suffix}' for i in (1,3,4,5,6,7) for suffix in ('','Right')]+['#content li.checkOff','#content li.checkOn']
    for selector in selectors:
        require(not soup.select(selector),'Unused CSS selector now matches: '+selector)
        pattern=re.escape(selector.encode())+rb'\s*\{[^}]*\}';matches=re.findall(pattern,data);require(len(matches)==1,'Unused CSS scope drift')
        removed.append(dict(selector=selector,original_rule=matches[0].decode('ascii')));data=re.sub(pattern,b'',data)
    refs=re.findall(rb'url\(([^)]+)\)',data)
    require(refs==[b'../images/header_bg.gif',b'../images/bg_page.gif',b'../images/dossier_2_folder_slice.gif',b'../images/dossier_2_folder_side_slice.gif'],'Remaining styles need review')
    deps={Path(ref.decode()).name:urljoin(CSS_URL,ref.decode()) for ref in refs}
    for ref in refs:data=data.replace(ref,Path(ref.decode()).name.encode())
    data+=b'\n.archive-puzzle-label { color: #003399; text-decoration: none; }\n'
    return data,deps,removed


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);old=next(r for r in before if r['problem_id'] in SELECTED);row=deepcopy(old);pid=row['problem_id'];source=ROOT/row['source_file']
    with ThreadPoolExecutor(max_workers=3) as pool:snapshots={s['source_url']:s for s in pool.map(download,[URL,CSS_URL,SCRIPT_URL])}
    require(source.read_bytes().replace(b'\r',b'')==(ROOT/snapshots[URL]['path']).read_bytes().replace(b'\r',b''),'Publisher source differs')
    payload,deferred,deps=sanitize(source.read_bytes());css,cssdeps,removed=local_css((ROOT/snapshots[CSS_URL]['path']).read_bytes(),payload)
    require(not (set(deps)&set(cssdeps)),'Dependency basename collision');deps.update(cssdeps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(set(deps.values())))})
    folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];copies=[]
    def add(data,name,mime):
        p=folder/name
        if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
        else:
            with p.open('xb') as out:out.write(data)
        dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
    add(payload,'puzzle.html','text/html');add(css,'mydossier.css','text/css')
    for name,url in sorted(deps.items()):
        p=ROOT/snapshots[url]['path']
        with Image.open(p) as im:im.verify()
        add(p.read_bytes(),name,'image/jpeg' if name.endswith('.jpg') else 'image/gif')
    allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed);check_css(folder/'mydossier.css',allowed)
    prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original dossier layout and image. Listed puzzle titles are labels only; other puzzles, their answers and full-hunt progression are not supplied.\n\nArchive limitation: this packet does not reproduce historical unlocks, host interaction or cross-task evaluation.'
    assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    row.update(source_url=URL,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,source_visibility='initial_dossier_only_post_meta_text_judge_only',asset_policy='Original initial narrative, labels and dossier artwork only. Explicitly post-meta text remains judge-only; no navigation, answer checking, other task answers or unlock mechanism is supplied.')
    row['evaluation']['limitations']='The two original initial narrative paragraphs and dossier image are recovered. The archive explicitly marks later narrative as post-meta; it remains in the judge-only original. Cross-task prerequisites, progression and evaluation are not reproduced. Gold and scores remain unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
    row['source_review']=deepcopy(old.get('source_review') or {})
    row['source_review'].update(batch='mystery_2008_dossier_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[URL]['path'],publisher_html_sha256=snapshots[URL]['sha256'],deferred_post_meta_section=deferred,dependency_urls=deps,unused_css_rules_removed=removed,unexecuted_rollover_snapshot=snapshots[SCRIPT_URL],task_links_preserved_as_labels=LABEL_LINKS,answers_and_scores_unchanged=True)
    provenance(row);Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots))
    print(json.dumps(dict(records=1,public_files=len(copies))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);pid=next(iter(SELECTED));dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
    p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1800','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
    require(p.returncode==0 and dest.exists(),'Render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
