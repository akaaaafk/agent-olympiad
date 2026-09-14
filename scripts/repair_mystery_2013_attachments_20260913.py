"""Restore an original three-page score and original ZIP of sixteen sound pieces."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urljoin,urlparse
import zipfile
from bs4 import BeautifulSoup
from PIL import Image,ImageFont
import pymupdf as fitz
from scripts.repair_mystery_2013_static_20260913 import sanitize,localize_css,localize_inline,compile_less,snapshot,check_css,packet_title,ORIGIN,missing_tile_evidence,UNUSED_EVIL
from scripts.repair_mystery_2009_media_20260913 import audio_structure
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2013_attachments_20260913/'
RAW='data/raw/mystery_hunt/separated_2013_attachments_20260913/'
REPORT='data/benchmarks/mystery_2013_attachments_repair_20260913.json'
SELECTED={'mystery_hunt_01692','mystery_hunt_01719'}
MIMES={'.png':'image/png','.jpg':'image/jpeg','.gif':'image/gif','.ttf':'font/ttf','.txt':'text/plain','.pdf':'application/pdf','.zip':'application/zip'}
PIECES=sorted(f'PuzzlePiece{i}.mp3' for i in range(1,17))


def zip_review(data):
    require(data.startswith(b'PK\x03\x04'),'Not ZIP');records=[]
    with zipfile.ZipFile(BytesIO(data)) as z:
        infos=z.infolist();require([i.filename for i in infos]==PIECES,'Unexpected ZIP membership/order');require(sum(i.file_size for i in infos)<10000000,'Oversized ZIP')
        for i in infos:
            require(not i.flag_bits&1 and not stat.S_ISLNK(i.external_attr>>16) and 0<i.file_size<1000000 and i.compress_size>0 and i.file_size/i.compress_size<10,'Unsafe ZIP member')
            raw=z.read(i);require(len(raw)==i.file_size,'ZIP length mismatch');media=audio_structure(SimpleNamespace(read_bytes=lambda:raw));records.append(dict(name=i.filename,bytes=len(raw),crc32=i.CRC,sha256=hashlib.sha256(raw).hexdigest(),audio_structure=media))
    return dict(entries=records,zip_crc_verified=True,extracted_to_disk=False,executed=False,decoded=False,listened=False,original_zip_bytes_preserved=True)


def localize(payload,url):
    deps={};s=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in s.find_all(tag,attrs={attr:True}):
            ref=el[attr];name=Path(ref).name;require(re.fullmatch(r'[A-Za-z0-9_-]+\.(jpg|png|pdf|zip)',name),'Unreviewed attachment');target=urljoin(url,ref);require(target.startswith(ORIGIN),'External attachment');require(name not in deps or deps[name]==target,'Attachment collision');deps[name]=target
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+ref.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==2,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        require(not any(a['role']=='agent_visible' for a in old['assets']),'Already public');pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'];payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url,int(pid[-5:]));payload,deps=localize(payload,url);styles={};cssdeps={};require(not BeautifulSoup(payload,'html.parser').select('#evilbg, #evilbar1'),'Unused selectors became active')
        for name,target in styleurls.items():
            if target not in snapshots:snapshots[target]=snapshot(target)
            data=(ROOT/snapshots[target]['path']).read_bytes();styles[name]=localize_css(compile_less(data) if target.endswith('.less') else data,target,cssdeps)
        payload=localize_inline(payload,url,cssdeps);require(not(set(deps)&set(cssdeps)),'CSS collision');deps.update(cssdeps)
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlparse(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        prepared[pid]=(url,payload,styles,styleurls,deps);urls.add(url);urls.update(deps.values())
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];url,payload,styles,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];review={}
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared byte drift')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in styles.items():add(data,name,'text/css')
        for name,target in sorted(deps.items()):
            p=ROOT/snapshots[target]['path'];data=p.read_bytes();ext=Path(name).suffix
            if ext in ('.jpg','.png','.gif'):
                with Image.open(p) as im:im.verify()
            elif ext=='.ttf':ImageFont.truetype(str(p),16).getmask('Archive')
            elif ext=='.pdf':
                with fitz.open(p) as doc:require(len(doc)==3 and not doc.is_encrypted,'PDF scope drift');review[name]=dict(pages=3,page_sizes=[[pg.rect.width,pg.rect.height] for pg in doc],original_bytes_preserved=True)
            elif ext=='.zip':review[name]=zip_review(data)
            add(data,name,MIMES[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styles:check_css(folder/name,allowed)
        note='The original three-page music score is preserved, including all notes, syllables and empty staves; PDF text extraction is not a substitute for its musical notation.' if pid.endswith('01692') else 'The explicitly linked original ZIP is preserved intact, with its sixteen original MP3 names and archive order. ZIP CRC and MPEG frame structure are checked in memory; no files are extracted to disk, executed, decoded, listened to, transcribed or reordered into a proposed solution.'
        note+=' Archive solved status and solution navigation are removed; other navigation is inert. Original LESS is compiled offline with version 1.3.0. Fonts and surviving image dependencies are localized; current Google font binaries are not certified as historical revisions. Missing Feynman page-decoration gptile.jpg retains the source grey fallback; missing evilfg.png only appears in rules whose IDs are absent. Gold, benchmark points, membership and readiness are unchanged, not recertified.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# '+packet_title(clean)+'\n\nOpen `puzzle.html` and its explicitly linked original attachment.\n\nArchive limitation: '+note,source_visibility='explicit_attachment_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2013_attachments_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,attachment_review=review,less_version='1.3.0',font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,unavailable_dependencies=[missing_tile_evidence(),missing_tile_evidence(UNUSED_EVIL)]));print(json.dumps(dict(records=2,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,2000','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'HTML render failed')
    p=subprocess.run([str(ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'),'-png','-r','140',str(ROOT/CACHE/'mystery_hunt_01692/input/puzzle.pdf'),str(out/'score')],capture_output=True,timeout=45);require(p.returncode==0,'PDF render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
