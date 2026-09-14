"""Recover the explicitly linked full Numerology puzzle, not just its example."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,sanitize,provenance,writer as static_writer

PID='mystery_hunt_00184'
CACHE='data/.cache/mystery_numerology_20260913/'
RAW='data/raw/mystery_hunt/separated_numerology_20260913/'
REPORT='data/benchmarks/mystery_numerology_repair_20260913.json'


def prepare(refresh=False):
    if (ROOT/CACHE/'plan.json').exists():
        require(refresh and not (ROOT/REPORT).exists() and sha(ROOT/PATH)==read(ROOT/CACHE/'plan.json')['expected_benchmark_sha256'], 'Already prepared/applied or canonical data changed')
    rows=read(ROOT/PATH);old=next(r for r in rows if r['problem_id']==PID);row=deepcopy(old)
    base='https://puzzles.mit.edu/2001/phase4/08/'
    names=['index.html','index2.html','gridsmall.gif','img1.gif','gridlarge.gif','img3.gif','img2.gif']
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,[urljoin(base,n) for n in names])}
    source=ROOT/old['source_file']; remote=ROOT/snapshots[base+'index.html']['path']
    require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Original example differs')
    folder=ROOT/CACHE/PID/'input';folder.mkdir(parents=True,exist_ok=True)
    copies=[];public=[];edits=[];missing=[]
    for name in names:
        snapshot=ROOT/snapshots[base+name]['path'];payload=snapshot.read_bytes()
        dest_name='puzzle.html' if name=='index.html' else name
        if name=='index.html':payload,edits=sanitize(source.read_bytes())
        elif name=='index2.html':
            require(payload.count(b'href="index.html"')==1,'Unexpected example backlink')
            require(b'<script' not in payload.lower(),'Unexpected full-page script')
            payload=payload.replace(b'href="index.html"',b'href="puzzle.html"')
        else:
            legacy=source.parent/name
            if legacy.exists():require(sha(legacy)==sha(snapshot),'Existing image differs')
            else:missing.append(name)
            with Image.open(snapshot) as im:im.verify()
        target=folder/dest_name
        if target.exists():require(target.read_bytes()==payload,'Prepared bytes differ')
        else:
            with target.open('xb') as out:out.write(payload)
        path=RAW+PID+'/input/'+dest_name
        copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=path,sha256=sha(target)))
        public.append(dict(path=path,role='agent_visible',mime_type='text/html' if name.endswith('.html') else 'image/gif',sha256=sha(target)))
    allow={p.resolve() for p in folder.iterdir()}
    main=check_html(folder/'puzzle.html',allow);full=check_html(folder/'index2.html',allow)
    require([a.get('href') for a in main.find_all('a')]==['index2.html'],'Primary link drift')
    require([a.get('href') for a in full.find_all('a')]==['puzzle.html'],'Secondary link drift')
    note='Both the example and the explicitly linked full puzzle are included. Historical trivia, hex-grid/image interpretation, original rules and end-to-end evaluation remain uncertified. No solved grid or answer is added.'
    prompt='# Numerology\n\nOpen `puzzle.html` for the worked-example page and follow its link to `index2.html` for the full puzzle. Both original hex grids and image-encoded clues are present; text extraction does not preserve their geometry.\n\nArchive limitation: '+note+'\n\n'
    prompt+='The original HTML is authoritative; no flattened text preview is supplied for this layout-dependent puzzle.'
    original_assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in original_assets):
        original_assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    row.update(source_file=RAW+PID+'/input/puzzle.html',source_url=base+'index.html',problem_description=prompt.rstrip(),
               assets=public+original_assets,source_visibility='explicit_static_packet_original_archive_judge_only',
               asset_policy='Only explicit HTML and image dependencies are public. Archive answer controls and judge references are excluded.')
    row['evaluation']['limitations']=note
    row['source_review']=dict(batch='mystery_numerology_20260913',original_source_file=old['source_file'],original_sha256=sha(source),
         publisher_html_sha256=sha(remote),publisher_snapshot=snapshots[base+'index.html']['path'],
         full_puzzle_snapshot=snapshots[base+'index2.html'],media_count=5,media_missing_from_legacy_archive=missing,
         edits=edits+[dict(reason='resolve full-page backlink to renamed example',before='href="index.html"',after='href="puzzle.html"')],
         original_content_preserved=True,answers_and_scores_unchanged=True)
    provenance(row)
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=rows,
         updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots,review={PID:row['source_review']}))
    print(json.dumps(dict(records=1,html_pages=2,images=5,public_files=7)))


def writer():
    module=static_writer();module.CACHE=CACHE;module.RAW=RAW;module.REPORT=REPORT;module.SELECTED={PID}
    return module


def render():
    folder=ROOT/CACHE/'renders';folder.mkdir(exist_ok=True)
    for name in ('puzzle.html','index2.html'):
        page=ROOT/CACHE/PID/'input'/name;dest=folder/(name+'.png')
        result=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu',
          '--disable-extensions','--no-first-run','--no-default-browser-check','--disable-background-networking','--hide-scrollbars',
          '--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),
          '--screenshot='+str(dest),'--window-size=1400,3800','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(result.returncode==0 and dest.exists(),'Render failed');print(name,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='refresh':prepare(True)
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
