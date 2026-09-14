"""Recover original music and enforce the explicit post-food handout boundary."""
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
from scripts.repair_mystery_2006_static_20260913 import sanitize,css_packet,check_css
from scripts.repair_mystery_linked_archives_20260913 import inspect_audio
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2006_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2006_media_20260913/'
REPORT='data/benchmarks/mystery_2006_media_repair_20260913.json'
SELECTED={'mystery_hunt_00766','mystery_hunt_00833'}
FILES={766:{'header.jpg'},833:{'header.jpg','picture.jpg','picturebig.jpg',*[f'{i}.mp3' for i in range(1,6)]}}
LIMITS={766:'Only the initial cooking assignment is provided. The original archive explicitly releases fortunes after delivery of food; that later handout is judge-only. Physical delivery, acceptance and staged release are not implemented.',
        833:'Five original audio files and the original images are byte-preserved. MPEG frame structure is checked; audio has not been decoded, listened to, transcribed or semantically certified.'}


def initial_html(data,n):
    payload,edits=sanitize(data);deferred=None
    if n==766:
        pattern=rb'<p><hr></p>\s*<p><i>\.\.\.and after teams brought us food, yo, they were given seven\s+fortune cookies with the following fortunes:</i></p>\s*<p><img src="fortunes.png" alt="fortunes"></p>'
        matches=re.findall(pattern,payload,re.S);require(len(matches)==1,'Post-food handout boundary drift')
        deferred=matches[0].decode('ascii');payload=re.sub(pattern,b'',payload,flags=re.S)
        edits.append(dict(reason='exclude the explicitly post-delivery fortune handout from initial input'))
    return payload,edits,deferred


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==2,'Selection drift')
    baseurls={r['problem_id']:'https://puzzles.mit.edu/'+r['puzzle_url'].rstrip('/')+'/' for r in chosen}
    urls={u for url in baseurls.values() for u in (url,urljoin(url,'../puzzle.css'))}
    for pid,url in baseurls.items():urls.update(urljoin(url,n) for n in FILES[int(pid[-5:])])
    urls.add(baseurls['mystery_hunt_00766']+'fortunes.png')
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    csses={};deps={}
    for pid,url in baseurls.items():
        css_url=urljoin(url,'../puzzle.css');css,refs=css_packet((ROOT/snapshots[css_url]['path']).read_bytes());csses[pid]=css
        deps[pid]={n:urljoin(url,n) for n in FILES[int(pid[-5:])]}
        for ref,name in refs.items():require(name not in deps[pid],'CSS basename collision');deps[pid][name]=urljoin(css_url,ref)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted({u for d in deps.values() for u in d.values()}-set(snapshots)))})
    copies=[];updates=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];n=int(pid[-5:]);url=baseurls[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher source differs')
        payload,edits,deferred=initial_html(source.read_bytes(),n);soup=BeautifulSoup(payload,'html.parser')
        require({t['src'] for t in soup.find_all('img')}|{a['href'] for a in soup.find_all('a')}==FILES[n],'Unreviewed page reference')
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);new_assets=[];audio={}
        def add(data,name,mime,role='agent_visible'):
            sub='input' if role=='agent_visible' else 'judge';target=ROOT/CACHE/pid/sub/name;target.parent.mkdir(exist_ok=True)
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/'+sub+'/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            new_assets.append(dict(path=dest,role=role,mime_type=mime,sha256=sha(target)))
        add(payload,'puzzle.html','text/html');add(csses[pid],'puzzle.css','text/css')
        for name,u in sorted(deps[pid].items()):
            p=ROOT/snapshots[u]['path']
            if name.endswith('.mp3'):audio[name]=inspect_audio(p,'audio/mpeg');mime='audio/mpeg'
            else:
                with Image.open(p) as im:im.verify()
                mime='image/jpeg' if name.endswith('.jpg') else 'image/png'
            if urljoin(url,name)==u and (source.parent/name).is_file():require(sha(source.parent/name)==sha(p),'Legacy attachment differs')
            add(p.read_bytes(),name,mime)
        if n==766:
            p=ROOT/snapshots[url+'fortunes.png']['path']
            with Image.open(p) as im:im.verify()
            add(p.read_bytes(),'fortunes.png','image/png','judge_only')
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed);check_css(folder/'puzzle.css',allowed)
        public_note='Only the original initial cooking assignment is provided. Physical delivery and host interaction are not reproduced.' if n==766 else LIMITS[n]
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` and its explicit local attachments for original layout and media.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=new_assets+assets,
            source_visibility='explicit_initial_packet_later_handout_judge_only',asset_policy='Only explicit public initial materials are released. Conditional later handouts, original archive controls and judge references remain unavailable; historical host behavior is not synthesized.')
        row['evaluation']['limitations']=LIMITS[n]+' Gold and scores remain unchanged and uncertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2006_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=edits,deferred_section=deferred,audio_structure=audio,dependency_urls=deps[pid],stylesheet_publisher=snapshots[urljoin(url,'../puzzle.css')],answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots)
    Store(ROOT).save(CACHE+'plan.json',plan);print(json.dumps(dict(records=2,copied_files=len(copies),roles=writer().copy_role_counts(plan))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1800','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
