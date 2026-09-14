"""Seven reviewed 2002 static pages and their exact published image dependencies."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2002_packets_20260913/'
RAW='data/raw/mystery_hunt/separated_2002_20260913/'
REPORT='data/benchmarks/mystery_2002_packets_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (196,199,201,203,215,220,226)}
LIMITS={196:'The source requires historical physical planet displays and local observations, which are not recreated.',
        226:'The maze requires seven other puzzle answers in a separately determined order. Those answers and ordering are not inserted into the initial packet.'}


def sanitize(data):
    edits=[]
    pattern=rb'<script type="module" src="/checkanswer\.js"></script>'
    require(len(re.findall(pattern,data))==1,'Unexpected script count')
    data=re.sub(pattern,b'',data);edits.append(dict(reason='remove archive answer-check script'))
    pattern=rb'<a\s+href="\.\./index\.html"\s*>(.*?)</a>'
    require(len(re.findall(pattern,data,re.I|re.S))==1,'Unexpected navigation anchor')
    data=re.sub(pattern,lambda m:m[1],data,flags=re.I|re.S);edits.append(dict(reason='remove round-navigation anchor tags, preserve its visible label'))
    for source in re.findall(rb'src="(\.\./\.\./images/[^"/]+\.gif)"',data):
        name=source.rsplit(b'/',1)[1]
        data=data.replace(b'src="'+source+b'"',b'src="'+name+b'"')
        edits.append(dict(reason='localize identical publisher header image',before=source.decode(),after=name.decode()))
    return data,edits


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==7 and all(r['year']==2002 for r in chosen),'Selection drift')
    urls=set();media={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'];urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        refs=[t['src'] for t in soup.find_all('img')]
        require(len({Path(s).name for s in refs})==len(refs),'Image filename collision')
        require(all(re.fullmatch(r'(?:../../images/|\./)?[A-Za-z0-9_]+\.gif',s) for s in refs),'Unreviewed image source')
        media[row['problem_id']]=refs;urls.update(urljoin(url,s) for s in refs)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    copies=[];updates=[];review={}
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];source=ROOT/row['source_file'];url='https://puzzles.mit.edu/'+row['puzzle_url']
        remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher markup differs: '+pid)
        payload,edits=sanitize(source.read_bytes());folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True)
        public=[];missing=[]
        def save_new(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared file differs')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name
            copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        save_new(payload,'puzzle.html','text/html')
        for ref in media[pid]:
            name=Path(ref).name;downloaded=ROOT/snapshots[urljoin(url,ref)]['path']
            local=source.parent/name
            if local.exists():require(sha(local)==sha(downloaded),'Existing image differs')
            else:missing.append(ref)
            with Image.open(downloaded) as im:im.verify()
            save_new(downloaded.read_bytes(),name,'image/gif')
        clean=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
        note=LIMITS.get(int(pid[-5:]),'Historical rules, image/layout interpretation and answer-mechanism equivalence remain uncertified.')
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the complete source page and its images. Layout, color, music notation, cipher spelling and letter case remain as published; a flattened text preview is not a substitute.\n\nArchive limitation: '+note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_static_packet_original_archive_judge_only',
            asset_policy='Only allowlisted original HTML/media are public; archive answer controls, round navigation and judge references are excluded.')
        row['evaluation']['limitations']='Static source page and images recovered; legacy gold and end-to-end evaluator are not recertified. '+note
        row['source_review']=dict(batch='mystery_2002_packets_20260913',original_source_file=old['source_file'],original_sha256=sha(source),
              publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),comparison='Same original markup after removing CR bytes.',
              edits=edits,media_count=len(media[pid]),media_missing_from_legacy_archive=missing,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row));review[pid]=row['source_review']
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,
        updates=updates,copies=copies,publisher_snapshots=snapshots,review=review))
    print(json.dumps(dict(records=7,public_files=len(copies),publisher_files=len(snapshots),image_copies=sum(map(len,media.values())))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    folder=ROOT/CACHE/'renders';folder.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        height=6500 if pid.endswith('00220') else 4600 if pid.endswith('00199') else 2500
        dest=folder/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions',
             '--no-first-run','--no-default-browser-check','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
             '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),
             '--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
