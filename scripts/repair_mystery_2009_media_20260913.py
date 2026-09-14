"""Recover explicit original media for seven 2009 standalone archive records."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from collections import Counter
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
import pymupdf as fitz
from scripts.repair_mystery_2009_static_20260913 import sanitize as static_html,styles,CSS_URL,STYLE_NAMES
from scripts.repair_mystery_linked_archives_20260913 import inspect_audio
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2009_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2009_media_20260913/'
REPORT='data/benchmarks/mystery_2009_media_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1099,1110,1111,1124,1173,1209,1226)}
MIMES={'.png':'image/png','.jpg':'image/jpeg','.pdf':'application/pdf','.mp3':'audio/mpeg','.wav':'audio/wav','.flv':'video/x-flv'}


def audio_structure(path):
    data=path.read_bytes();start=0;end=len(data)
    if data.startswith(b'RIFF'):return inspect_audio(path,'audio/wav')
    if data.startswith(b'ID3'):
        require(len(data)>=10 and data[3:6]==bytes([3,0,0]) and all(n<128 for n in data[6:10]),'Unreviewed ID3 header')
        start=10+sum(data[6+i]<<(7*(3-i)) for i in range(4));require(start<len(data),'Truncated ID3')
    if data[-128:-125]==b'TAG':end-=128
    require(end>start,'Empty stream');result=inspect_audio(SimpleNamespace(read_bytes=lambda:data[start:end]),'audio/mpeg')
    return dict(result,id3v2_prefix_bytes=start,id3v1_suffix_bytes=len(data)-end,original_bytes_preserved=True)


def flv_structure(path):
    data=path.read_bytes();require(data[:9]==b'FLV\x01\x01\x00\x00\x00\x09','Unreviewed FLV header')
    require(data[9:13]==bytes(4),'Invalid first previous-size');i=13;counts=Counter();codecs=Counter();last=0;metadata={}
    while i<len(data):
        require(i+15<=len(data),'Truncated FLV header');kind=data[i];size=int.from_bytes(data[i+1:i+4],'big');stamp=int.from_bytes(data[i+4:i+7],'big')+(data[i+7]<<24)
        require(kind in (9,18) and size>0 and i+15+size<=len(data),'Unexpected/truncated FLV tag')
        require(data[i+8:i+11]==bytes(3) and int.from_bytes(data[i+11+size:i+15+size],'big')==11+size,'FLV boundary mismatch')
        body=data[i+11:i+11+size];counts[str(kind)]+=1;last=max(stamp,last)
        if kind==9:codecs[str(body[0]&15)]+=1
        else:
            require(body[:18]==b'\x02\x00\x0aonMetaData\x08\x00\x00\x00\x07','Unreviewed metadata grammar');j=18
            for _ in range(7):
                length=int.from_bytes(body[j:j+2],'big');j+=2;key=body[j:j+length].decode('ascii');j+=length
                require(body[j]==0 and key not in metadata,'Non-numeric/duplicate FLV metadata');metadata[key]=struct.unpack('>d',body[j+1:j+9])[0];j+=9
            require(body[j:]==b'\x00\x00\x09','Unreviewed metadata tail')
        i+=15+size
    require(counts=={'9':10284,'18':1} and codecs=={'2':10284} and metadata.get('filesize')==len(data),'FLV stream drift')
    return dict(format='FLV',tags=dict(counts),video_codecs=dict(codecs),last_timestamp_ms=last,metadata=metadata,decoded=False,content_watched=False,original_bytes_preserved=True)


def sanitize(data,pid):
    payload=static_html(data)
    if pid.endswith('01226'):
        script=rb'<script src="../../../support/flowplayer/example/flowplayer-3.0.1.min.js"></script>'
        require(payload.count(script)==1,'Player script drift');payload=payload.replace(script,b'')
        pattern=rb'<script language="JavaScript">\s*flowplayer\("video", "../../../support/flowplayer/flowplayer-3.0.1.swf"\);\s*</script>'
        require(len(re.findall(pattern,payload))==1,'Player initializer drift');payload=re.sub(pattern,b'',payload)
    soup=BeautifulSoup(payload,'html.parser');require(not soup.find_all('script'),'Unreviewed script remains')
    return payload


def localize(payload,url):
    deps={};soup=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in soup.find_all(tag):
            path=el[attr];name=Path(path).name;require(Path(name).suffix in MIMES and '/' not in name,'Unreviewed attachment path')
            u=urljoin(url,path);require(name not in deps or deps[name]==u,'Basename collision');deps[name]=u
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+path.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==7,'Selection drift')
    snapshots={s['source_url']:s for s in map(download,[CSS_URL+n for n in STYLE_NAMES])};main=(ROOT/snapshots[CSS_URL+'puzzle.css']['path']).read_bytes();images=(ROOT/snapshots[CSS_URL+'puzzle-page-images.css']['path']).read_bytes()
    prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'];url=url if url.endswith('.html') else url.rstrip('/')+'/'
        payload=sanitize((ROOT/old['source_file']).read_bytes(),pid);css,cssdeps,review=styles(main,images,payload);payload,deps=localize(payload,url)
        require(not(set(deps)&set(cssdeps)),'CSS collision');deps.update(cssdeps);urls.update(deps.values());urls.add(url);prepared[pid]=(url,payload,css,deps,review)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,css,deps,style_review=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path']
        require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML differs: '+pid)
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];media_review={}
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(css,'puzzle.css','text/css');add((ROOT/snapshots[CSS_URL+'print.css']['path']).read_bytes(),'print.css','text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path'];mime=MIMES[Path(name).suffix]
            if urljoin(url,name)==u and (source.parent/name).exists():require(sha(p)==sha(source.parent/name),'Unreviewed legacy media mismatch')
            if mime.startswith('image/'):
                with Image.open(p) as im:im.verify()
            elif mime.startswith('audio/'):media_review[name]=audio_structure(p)
            elif mime=='video/x-flv':media_review[name]=flv_structure(p)
            else:
                with fitz.open(p) as doc:require(not doc.is_encrypted and len(doc)>0,'Bad PDF');media_review[name]=dict(pages=len(doc),text_by_page=[pg.get_text() for pg in doc],byte_preserved=True)
            add(p.read_bytes(),name,mime)
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        note='The original explicitly linked standalone archive materials are preserved byte-for-byte. Audio/video structure checks are not listening, watching, transcription or semantic grading. Historical full-hunt progression and host interaction are not reproduced.'
        if pid.endswith('01173'):note+=' Only the original HBS-index.html view and its three WAV links are included; no historical view changes or timing is inferred or implemented.'
        if pid.endswith('01226'):note+=' The original FLV remains an attachment requiring a compatible media reader; the obsolete Flash player is not run or replaced.'
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` and its explicit local attachments for the original task. No text-only preview replaces images, audio/video or PDF sheets.\n\nArchive limitation: '+note
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,source_visibility='explicit_media_packet_original_archive_judge_only',asset_policy='Explicit original HTML, applicable styles and linked media only. No archive navigation, answer checker, executable player, inferred timing or other task answers.')
        row['evaluation']['limitations']=note+' Gold and scores unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2009_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,style_review=style_review,media_review=media_review,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=7,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1099:3400,1110:1200,1111:1200,1124:1500,1173:1600,1209:14500,1226:2500}
    for pid in sorted(SELECTED):
        if len(sys.argv)>2 and pid not in sys.argv[2:]:continue
        dest=out/(pid+'.png');page=ROOT/CACHE/pid/'input/puzzle.html'
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)
    poppler=ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'
    for pid in sorted(SELECTED):
        for p in (ROOT/CACHE/pid/'input').glob('*.pdf'):
            dest=ROOT/'tmp/pdfs/mystery_2009_media_20260913'/p.stem;dest.mkdir(parents=True,exist_ok=True)
            subprocess.run([str(poppler),'-r','100','-png',str(p),str(dest/'page')],check=True,capture_output=True,timeout=60)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
