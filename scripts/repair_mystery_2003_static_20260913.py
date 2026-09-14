"""Nine bounded 2003 static packets, retaining verified answer-variant metadata."""
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
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2003_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2003_static_20260913/'
REPORT='data/benchmarks/mystery_2003_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (356,358,371,377,405,408,409,412,457)}
LIMITS={405:'Historical physical water fixtures and the visit suggested in the source are not reproduced.',
        408:'This is the retained untrained answer variant; it must not be counted as an independent puzzle from the trained variant.',
        409:'This is the retained trained answer variant, requiring the hunt-specific answer-switching context. That context is not invented or supplied from the gold.',
        412:'The colored originals and folding directions are supplied, but physical construction and spatial grading are not implemented.'}
SCRIPT=re.compile(rb'<script\b(?=[^>]*\bsrc="/checkanswer\.js")(?=[^>]*\btype="module")[^>]*>\s*</script>',re.I)


def sanitize(data):
    edits=[];count=len(SCRIPT.findall(data));require(count in (1,2),'Unexpected archive script count')
    data=SCRIPT.sub(b'',data);edits.append(dict(reason='remove archive answer checker',count=count))
    pattern=rb'<a\b[^>]*href="\.\./\.\./solutions/[^"/]+\.html"[^>]*>\s*\(Solution\)\s*</a>'
    require(len(re.findall(pattern,data,re.I|re.S))==1,'Unexpected solution-navigation anchor')
    data=re.sub(pattern,b'',data,flags=re.I|re.S);edits.append(dict(reason='remove archive solution link and label'))
    pattern=rb'<a\b[^>]*href="index\.html"[^>]*>\s*Back to the index\s*</a>'
    require(len(re.findall(pattern,data,re.I|re.S))==1,'Unexpected index navigation')
    data=re.sub(pattern,b'',data,flags=re.I|re.S);edits.append(dict(reason='remove archive index navigation'))
    pattern=rb'((?:src|href)=["\'])images/([^"\']+)(["\'])'
    for m in re.finditer(pattern,data,re.I):edits.append(dict(reason='localize identical image',before='images/'+m[2].decode(),after=m[2].decode()))
    data=re.sub(pattern,lambda m:m[1]+m[2]+m[3],data,flags=re.I)
    return data,edits


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==9 and all(r['year']==2003 for r in chosen),'Selection drift')
    urls=set();media={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'];urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        refs={t['src'] for t in soup.find_all('img')}
        refs.update(t['href'] for t in soup.find_all('a') if t.get('href','').startswith('images/'))
        require(all(re.fullmatch(r'images/[A-Za-z0-9_-]+\.(?:jpg|gif|png)',r) for r in refs),'Unreviewed image reference')
        media[row['problem_id']]=sorted(refs);urls.update(urljoin(url,r) for r in refs)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    copies=[];updates=[];review={}
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];source=ROOT/row['source_file'];url='https://puzzles.mit.edu/'+row['puzzle_url']
        remote=ROOT/snapshots[url]['path']
        require(SCRIPT.sub(b'',source.read_bytes()).replace(b'\r',b'')==SCRIPT.sub(b'',remote.read_bytes()).replace(b'\r',b''),'Publisher content differs: '+pid)
        payload,edits=sanitize(source.read_bytes());folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True)
        public=[];missing=[]
        def save_new(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name
            copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        save_new(payload,'puzzle.html','text/html')
        for ref in media[pid]:
            name=Path(ref).name;downloaded=ROOT/snapshots[urljoin(url,ref)]['path']
            candidates=[p for p in (source.parent/ref,source.parent/name) if p.is_file()]
            for local in candidates:require(sha(local)==sha(downloaded),'Existing image differs')
            if not candidates:missing.append(ref)
            with Image.open(downloaded) as im:im.verify()
            mime={'.jpg':'image/jpeg','.png':'image/png','.gif':'image/gif'}[Path(name).suffix]
            save_new(downloaded.read_bytes(),name,mime)
        clean=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
        note=LIMITS.get(int(pid[-5:]),'Historical rules, image/layout interpretation and end-to-end evaluation remain uncertified.')
        # Do not expose answer-variant identities or infer a solving method from
        # judge-side metadata in the contestant's short navigation prompt.
        public_note='Historical rules, image/layout interpretation and end-to-end evaluation remain uncertified.' if pid.endswith(('00408','00409')) else note
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the complete original page and its images. Linked full-size color sheets, where present, are included. No flattened preview replaces their spacing, ordering or visual presentation.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
             source_visibility='explicit_static_packet_original_archive_judge_only',
             asset_policy='Only explicit HTML/media are public; archive solution links, answer-checking scripts and index navigation are excluded.')
        row['evaluation']['limitations']='Static page/media recovered; no gold or evaluator recertification. '+note+' Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2003_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),
             publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),
             comparison='Source equals publisher after removing CR and archive answer-check script copies only.',
             edits=edits,media_count=len(media[pid]),media_missing_from_legacy_archive=missing,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row));review[pid]=row['source_review']
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,
        updates=updates,copies=copies,publisher_snapshots=snapshots,review=review,
        deferred_records=[r['problem_id'] for r in before if r['year']==2003 and r['problem_id'] not in SELECTED]))
    print(json.dumps(dict(records=9,public_files=len(copies),publisher_files=len(snapshots),image_copies=sum(map(len,media.values())))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        height=11000 if pid.endswith('00457') else 7500 if pid.endswith(('00405','00412')) else 5000
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions',
          '--no-first-run','--no-default-browser-check','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
          '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1600,'+str(height),
          '--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
