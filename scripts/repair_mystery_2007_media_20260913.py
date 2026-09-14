"""Restore 2007 original handouts and audio; isolate conditional second parts."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
import pymupdf as fitz
from scripts.repair_mystery_2007_static_20260913 import sanitize,local_css,CSS_URL,CSS_IMAGES,publisher_download
from scripts.repair_mystery_linked_archives_20260913 import inspect_audio
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2007_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2007_media_20260913/'
REPORT='data/benchmarks/mystery_2007_media_repair_20260913.json'
FILES={868:{f'image-{i}.jpg' for i in range(10)},874:{'map.jpg'},896:{'Finance4Revised0.jpg','playlist.mp3'},916:{'Hell4Handout.pdf'},918:{'pages.pdf'}}
DEFERRED={868:'Crime8Handout.pdf',874:'Gov8RevisedHandout.pdf'}
SELECTED={f'mystery_hunt_{n:05}' for n in FILES}
INDEX='https://puzzles.mit.edu/2007/puzzles/'
HANDOUT='https://puzzles.mit.edu/2007/handouts/Hell4Handout.pdf'
LIMITS={868:'The initial photo assignment and ten reference photos are provided. The explicitly post-completion Part II handout remains judge-only. Live photo judging, discretionary bonuses and staged delivery are not reproduced.',
        874:'The initial restaurant clue and its original map are preserved. The PDF explicitly obtained by asking at the correct restaurant remains judge-only. No visit, historical observations, phone call or later release is synthesized.',
        896:'The original image and complete downloaded MP3 bytes are preserved. MPEG frame boundaries and ID3 wrappers are checked; audio content and historical completeness have not been listened to or semantically certified.',
        916:'The official index co-lists this task page and its original one-page handout. Both are collected as a standalone archival packet; their availability within full-hunt progression is not asserted or reproduced.',
        918:'All eight original PDF pages are retained in their original order. Printed book metadata and copyright notices are puzzle content, not evidence of dataset licensing. Evaluation remains uncertified.'}


def initial_html(data,n):
    payload=sanitize(data);deferred=None
    if n in DEFERRED:
        pattern=rb'<p(?: class="c3")?>\(In the Hunt, [^<]*<a\s+href="'+DEFERRED[n].encode()+rb'">handout</a>\.\)</p>'
        matches=re.findall(pattern,payload,re.S);require(len(matches)==1,'Conditional handout boundary drift')
        deferred=matches[0].decode('ascii');payload=re.sub(pattern,b'',payload,flags=re.S)
    if n==916:
        require(payload.count(b'<!--Section Ends-->')==1,'Task body boundary drift')
        payload=payload.replace(b'<!--Section Ends-->',b'<p><a href="Hell4Handout.pdf">[handout (PDF)]</a></p>\n<!--Section Ends-->')
    return payload,deferred


def audio_structure(path):
    data=path.read_bytes();require(data[:6]==b'ID3\x03\x00\x00' and all(b<128 for b in data[6:10]),'ID3 header drift')
    tag_end=10+sum(data[6+i]<<(7*(3-i)) for i in range(4));require(tag_end==4096 and data[-128:-125]==b'TAG','Audio wrapper drift')
    result=inspect_audio(SimpleNamespace(read_bytes=lambda:data[tag_end:-128]),'audio/mpeg')
    result.update(id3v2_bytes=tag_end,id3v1_bytes=128,original_wrappers_preserved=True);return result


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==5,'Selection drift')
    bases={r['problem_id']:'https://puzzles.mit.edu/'+r['puzzle_url'].rstrip('/')+'/' for r in chosen}
    urls=set(bases.values())|{INDEX,CSS_URL+'puzzle.css',CSS_URL+'print.css'}|set(CSS_IMAGES)|set(CSS_IMAGES.values());deps={}
    for pid,url in bases.items():
        n=int(pid[-5:]);deps[pid]={name:(HANDOUT if n==916 and name=='Hell4Handout.pdf' else urljoin(url,name)) for name in FILES[n]}
        for u in CSS_IMAGES.values():deps[pid][Path(u).name]=u
        urls.update(deps[pid].values())
        if n in DEFERRED:urls.add(urljoin(url,DEFERRED[n]))
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(publisher_download,sorted(urls))}
    index=BeautifulSoup((ROOT/snapshots[INDEX]['path']).read_bytes(),'html.parser');link=index.find('a',href='man_i_hate_these_sudokus',title=False)
    require(link and link.parent.name=='li' and [a['href'] for a in link.parent.find_all('a')]==['../handouts/Hell4Handout.pdf','man_i_hate_these_sudokus'],'Index handout association drift')
    copies=[];updates=[];pdfs=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];n=int(pid[-5:]);url=bases[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher source differs')
        payload,deferred=initial_html(source.read_bytes(),n);soup=BeautifulSoup(payload,'html.parser')
        require({t['src'] for t in soup.find_all('img')}|{a['href'] for a in soup.find_all('a')}==FILES[n],'Unreviewed body reference')
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);new_assets=[];audio={}
        def add(data,name,mime,role='agent_visible'):
            sub='input' if role=='agent_visible' else 'judge';p=ROOT/CACHE/pid/sub/name;p.parent.mkdir(exist_ok=True)
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/'+sub+'/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)))
            new_assets.append(dict(path=dest,role=role,mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(local_css((ROOT/snapshots[CSS_URL+'puzzle.css']['path']).read_bytes()),'puzzle.css','text/css');add((ROOT/snapshots[CSS_URL+'print.css']['path']).read_bytes(),'print.css','text/css')
        attachments=[(name,u,'agent_visible') for name,u in sorted(deps[pid].items())]
        if n in DEFERRED:attachments.append((DEFERRED[n],urljoin(url,DEFERRED[n]),'judge_only'))
        for name,u,role in attachments:
            p=ROOT/snapshots[u]['path'];data=p.read_bytes()
            if urljoin(url,name)==u and (source.parent/name).is_file():require(sha(source.parent/name)==sha(p),'Legacy attachment differs')
            if name.endswith('.pdf'):
                require(data.startswith(b'%PDF-'),'Invalid PDF')
                with fitz.open(stream=data,filetype='pdf') as d:
                    require(not d.is_encrypted and len(d)>0,'Unreadable PDF');objects='\n'.join(d.xref_object(i) for i in range(1,d.xref_length()))
                    require(not any(k in objects for k in ('/JavaScript','/Launch','/EmbeddedFile','/RichMedia','/OpenAction')),'Active PDF dependency')
                    pdfs.append(dict(problem_id=pid,name=name,pages=len(d),role=role,sha256=sha(p)))
                mime='application/pdf'
            elif name.endswith('.mp3'):audio[name]=audio_structure(p);mime='audio/mpeg'
            else:
                with Image.open(p) as im:im.verify()
                mime='image/jpeg' if name.endswith('.jpg') else 'image/png'
            add(data,name,mime,role)
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
        public_note='Original initial assignment and images only; historical host interaction and observations are not reproduced.' if n in DEFERRED else LIMITS[n]
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` and its explicit attachments for original layout, visual marks and media.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=new_assets+assets,
            source_visibility='explicit_archival_packet_conditional_handouts_judge_only',asset_policy='Only explicit public task materials are supplied. Conditional second-part handouts stay judge-only. A standalone archive does not reproduce full-hunt progression, host judging or release timing.')
        row['evaluation']['limitations']=LIMITS[n]+' Gold and total points remain unchanged and uncertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_2007_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),deferred_section=deferred,dependency_urls=deps[pid],audio_structure=audio,pdfs=[p for p in pdfs if p['problem_id']==pid],answers_and_scores_unchanged=True)
        if n==916:row['source_review'].update(handout_index_snapshot=snapshots[INDEX],handout_index_entry=str(link.parent))
        if n==868:row['source_review']['photo_challenge_rubric']=dict(photos=10,categories=['Location','Object','Accessory','Physical position and facial expression','Composition (angle and approximate framing)'],points_per_category=[0,2],base_maximum=100,pass_threshold=75,discretionary_bonus_unspecified=True,not_the_canonical_answer_score=True)
        provenance(row);updates.append(dict(before=old,after=row))
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,pdf_inventory=pdfs)
    Store(ROOT).save(CACHE+'plan.json',plan);print(json.dumps(dict(records=5,roles=writer().copy_role_counts(plan),pdfs=pdfs)))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html';height=12500 if pid.endswith('00868') else 3000 if pid.endswith('00874') else 2200
        proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
