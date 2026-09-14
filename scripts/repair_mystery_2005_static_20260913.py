"""Fifteen reviewed 2005 static inputs, preserving layout and live limitations."""
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

CACHE='data/.cache/mystery_2005_static_20260913/'
RAW='data/raw/mystery_hunt/separated_2005_static_20260913/'
REPORT='data/benchmarks/mystery_2005_static_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (601,617,624,629,645,652,653,656,681,687,691,697,698,708,719)}
LIMITS={687:'The published performance requirements are supplied, but the live performance, appointment, host response and judging are not reproduced.',
        691:'The original page is only a request to call HQ for a guided-tour appointment. No host interaction, historical route or observations are reconstructed.',
        708:'The publisher supplies clue columns without a linked grid. No grid is invented from the title or solution.'}


def sanitize(data):
    require(len(SCRIPT.findall(data))==1,'Archive script count drift');data=SCRIPT.sub(b'',data)
    pattern=rb'<a href=solution\.html>solution</a>'
    require(len(re.findall(pattern,data))==1,'Solution-navigation drift')
    return re.sub(pattern,b'',data),[dict(reason='remove archive answer checker and solution-navigation control')]


def source_equal(source,remote):
    if source.name=='index.utf8_verified.html':
        expected='<meta charset="utf-8">\n'+remote.read_bytes().decode('cp1252')
        require(source.read_text(encoding='utf-8').replace('\r','')==expected.replace('\r',''),'Prior UTF-8 repair differs')
    else:require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher differs: '+str(source))


def sanitize_css(data,html):
    # Both published pages have no .black cell. The copied shared stylesheet
    # references a missing image only in this unused pseudo-element rule.
    require(not BeautifulSoup(html,'html.parser').select('.grid td.black'),'Black cells require the missing original image')
    rule=b'.grid td.black:after { content: url("black30x30.gif") ; }'
    require(data.count(rule)==1,'CSS rule drift')
    return data.replace(rule,b'/* Unused missing-image rule omitted; no matching cells in this static page. */')


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==15 and all(r['year']==2005 for r in chosen),'Selection drift')
    urls=set();media={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'].rstrip('/')+'/';urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        require([a.get('href') for a in soup.find_all('a')]==['solution.html'],'Unreviewed non-static navigation')
        refs={t['src'] for t in soup.find_all('img')};refs.update(t['href'] for t in soup.find_all('link'))
        require(all(re.fullmatch(r'[A-Za-z0-9_-]+\.(?:gif|png|css)',r) for r in refs),'Unexpected dependency')
        require(not any('url(' in t.get('style','').lower() for t in soup.find_all()),'Inline URL needs review')
        media[row['problem_id']]=sorted(refs);urls.update(urljoin(url,r) for r in refs)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url='https://puzzles.mit.edu/'+row['puzzle_url'].rstrip('/')+'/';source=ROOT/row['source_file'];remote=ROOT/snapshots[url]['path']
        source_equal(source,remote);payload,edits=sanitize(source.read_bytes());folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        add(payload,'puzzle.html','text/html')
        for ref in media[pid]:
            p=ROOT/snapshots[urljoin(url,ref)]['path'];legacy=source.parent/ref
            if legacy.is_file():require(sha(legacy)==sha(p),'Original media differs')
            if not ref.endswith('.css'):
                with Image.open(p) as im:im.verify()
            data=p.read_bytes()
            if ref.endswith('.css'):
                data=sanitize_css(data,payload)
                edits.append(dict(reason='omit an unused shared-CSS missing-image rule; no matching black cells exist',file=ref,original_sha256=sha(p),missing_publisher_url=urljoin(url,'black30x30.gif'),observed_http_status=404))
            add(data,ref,{'.css':'text/css','.png':'image/png','.gif':'image/gif'}[Path(ref).suffix])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for css in folder.glob('*.css'):check_css(css,allowed)
        note=LIMITS.get(int(pid[-5:]),'Historical rules, layout-aware interpretation and end-to-end evaluation remain uncertified.')
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the complete original page, tables, typography and images. No flattened preview replaces the puzzle layout.\n\nArchive limitation: '+note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_static_packet_original_archive_judge_only',asset_policy='Only the listed public HTML and media are contestant inputs. Solution controls, missing observations and host responses are not supplied.')
        row['evaluation']['limitations']=note+' Original gold and scores are retained, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2005_static_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=edits,media_count=len(media[pid]),answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots))
    print(json.dumps(dict(records=15,public_files=len(copies))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    heights={601:5000,617:1500,624:1500,629:2300,645:3000,652:1600,653:2200,656:6500,681:1800,687:1800,691:1000,697:8500,698:1800,708:2200,719:2400}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1600,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
