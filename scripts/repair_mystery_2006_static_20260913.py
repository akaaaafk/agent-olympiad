"""Eleven 2006 static source packets with city styles and explicit image links."""
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

CACHE='data/.cache/mystery_2006_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2006_static_20260913/'
REPORT='data/benchmarks/mystery_2006_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (743,757,760,778,791,793,805,810,836,843,847)}
NAV=['../','../../','answer/','answer/solution.html']
LIMITS={791:'Biographical clues are preserved as fictionalized 2006 puzzle text, not corrected to current biographies.',
        805:'The page is an invitation to call headquarters. The original appointment, exhibits, host interaction and observations are not reproduced.',
        810:'Original monospace descriptions and pager marks are preserved; historical software context is not replaced or executed.',
        843:'The original legality warning and all linked photographs are preserved. Historical physical surroundings and observations are not reconstructed.'}


def sanitize(data):
    require(len(SCRIPT.findall(data))==1,'Archive script count drift');payload=SCRIPT.sub(b'',data)
    soup=BeautifulSoup(payload,'html.parser');nav=soup.find('div',id='nav')
    require(nav and [a.get('href') for a in nav.find_all('a')]==NAV,'Navigation scope drift')
    pattern=rb'(<div id="nav">).*?(</div>)'
    require(len(re.findall(pattern,payload,re.S))==1,'Navigation container drift')
    # Keep the 32px navigation background/layout, remove only its controls.
    payload=re.sub(pattern,rb'\1\2',payload,flags=re.S)
    require(payload.count(b'href="../puzzle.css"')==1,'Stylesheet drift');payload=payload.replace(b'href="../puzzle.css"',b'href="puzzle.css"')
    if b'src="../shadow.jpg"' in payload:
        require(payload.count(b'src="../shadow.jpg"')==1,'Shadow image drift');payload=payload.replace(b'src="../shadow.jpg"',b'src="shadow.jpg"')
    return payload,[dict(reason='remove archive navigation controls and answer checker; retain styled header bar'),dict(reason='localize city stylesheet and same-byte shadow image')]


def css_packet(data):
    text=data.decode('ascii');refs=re.findall(r'url\([\'"]?([^\)\'\"]+)',text)
    require(refs in (['../logo.png'],['../logo.png','ground.jpg'],['../logo.png','header.jpg']),'CSS dependencies need review')
    if 'header.jpg' in refs:
        # Washington's shared background URL is 404. Both selected pages cover
        # that exact 615x240 header box with their own opaque 615x240 JPEG.
        require(text.count('background: url(header.jpg);')==1,'Background rule drift')
        text=text.replace('background: url(header.jpg);','/* Missing shared background is covered by the original opaque title image. */');refs.remove('header.jpg')
    replacements={r:('city-header.jpg' if r=='header.jpg' else Path(r).name) for r in refs}
    for old,new in replacements.items():text=text.replace('url('+old+')','url('+new+')')
    return text.encode('ascii'),replacements


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==11 and all(r['year']==2006 for r in chosen),'Selection drift')
    baseurls={r['problem_id']:'https://puzzles.mit.edu/'+r['puzzle_url'].rstrip('/')+'/' for r in chosen}
    urls={u for url in baseurls.values() for u in (url,urljoin(url,'../puzzle.css'))}
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    prepared={};deps={};csses={}
    for row in chosen:
        pid=row['problem_id'];url=baseurls[pid];source=ROOT/row['source_file'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher source drift: '+pid)
        payload,edits=sanitize(source.read_bytes());prepared[pid]=(payload,edits);soup=BeautifulSoup(payload,'html.parser')
        references={t['src'] for t in soup.find_all('img')};references.update(a['href'] for a in soup.find_all('a'))
        require(all(re.fullmatch(r'[A-Za-z0-9_-]+\.(?:jpg|gif|png)',r) for r in references),'Unreviewed non-image link')
        deps[pid]={ref:urljoin(url,'../shadow.jpg' if ref=='shadow.jpg' else ref) for ref in references}
        css_url=urljoin(url,'../puzzle.css');css,cssrefs=css_packet((ROOT/snapshots[css_url]['path']).read_bytes());csses[pid]=css
        for ref,name in cssrefs.items():
            u=urljoin(css_url,ref);require(name not in deps[pid] or deps[pid][name]==u,'Asset basename collision');deps[pid][name]=u
    urls={u for d in deps.values() for u in d.values()}-set(snapshots)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    copies=[];updates=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url=baseurls[pid];source=ROOT/row['source_file'];payload,edits=prepared[pid];folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        add(payload,'puzzle.html','text/html');add(csses[pid],'puzzle.css','text/css')
        for name,u in sorted(deps[pid].items()):
            p=ROOT/snapshots[u]['path']
            # Only compare legacy siblings when the URL really denotes that sibling.
            if urljoin(url,name)==u and (source.parent/name).is_file():require(sha(source.parent/name)==sha(p),'Legacy media differs')
            with Image.open(p) as im:
                if '/washington/' in url and name=='header.jpg':require(im.size==(615,240) and im.mode=='RGB','Opaque header coverage changed')
                im.verify()
            add(p.read_bytes(),name,{'.jpg':'image/jpeg','.png':'image/png','.gif':'image/gif'}[Path(name).suffix])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed);check_css(folder/'puzzle.css',allowed)
        note=LIMITS.get(int(pid[-5:]),'Historical rules, visual interpretation and end-to-end evaluation remain uncertified.')
        if '/washington/' in url:edits.append(dict(reason='omit 404 shared CSS background covered by the exact-size opaque original title JPEG',missing_url=urljoin(url,'../header.jpg'),observed_http_status=404,title_image_size=[615,240]))
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original styled page and images. Explicit full-size image links are included; no flattened preview replaces spacing, colors or marked positions.\n\nArchive limitation: '+note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy='Only explicit public HTML/styles/images are initial inputs. Archive map, answer checker and solution navigation are unavailable. Historical host responses are not synthesized.')
        row['evaluation']['limitations']=note+' Gold and scores are retained, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2006_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=snapshots[url]['sha256'],edits=edits,dependency_urls=deps[pid],stylesheet_publisher=snapshots[urljoin(url,'../puzzle.css')],answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots))
    print(json.dumps(dict(records=11,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    heights={743:1600,757:3000,760:3400,778:1600,791:2200,793:8000,805:1400,810:7000,836:1600,843:1800,847:1600}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
