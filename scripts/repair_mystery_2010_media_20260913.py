"""Byte-preserve the explicit 22 FLVs and two-page Banner Headline PDF."""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
import pymupdf as fitz
from scripts.repair_mystery_2010_static_20260913 import sanitize as static_html,local_css,CSS_URL,STYLE_NAMES
from scripts.repair_mystery_hunt_sources_20260913 import check_css
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2010_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2010_media_20260913/'
REPORT='data/benchmarks/mystery_2010_media_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1286,1357,1372)}
MIMES={'.gif':'image/gif','.jpg':'image/jpeg','.png':'image/png','.pdf':'application/pdf','.flv':'video/x-flv'}


def flv_structure(data):
    # The source header really contains 0x0d. Preserve it; do not repair codec flags.
    require(data[:13]==b'FLV\x01\x0d\x00\x00\x00\x09'+bytes(4),'Unreviewed original FLV header')
    i=13;counts=Counter();codecs=Counter();last={};metadata={}
    while i<len(data):
        require(i+15<=len(data),'Truncated tag header');kind=data[i];size=int.from_bytes(data[i+1:i+4],'big');stamp=int.from_bytes(data[i+4:i+7],'big')+(data[i+7]<<24)
        require(kind in (8,9,18) and size>0 and i+15+size<=len(data),'Truncated/unreviewed tag');require(data[i+8:i+11]==bytes(3) and int.from_bytes(data[i+11+size:i+15+size],'big')==11+size,'Tag size/stream-id mismatch')
        body=data[i+11:i+11+size];counts[str(kind)]+=1;require(stamp>=last.get(str(kind),0),'Per-stream timestamp regression');last[str(kind)]=stamp
        if kind in (8,9):codecs[('audio_' if kind==8 else 'video_')+str(body[0]>>4 if kind==8 else body[0]&15)]+=1
        else:
            require(not metadata and body[:18]==b'\x02\x00\x0aonMetaData\x08\x00\x00\x00\x16','Unreviewed metadata prefix');j=18
            for _ in range(22):
                length=int.from_bytes(body[j:j+2],'big');j+=2;key=body[j:j+length].decode('ascii');j+=length;kind_value=body[j];j+=1;require(key not in metadata,'Duplicate metadata')
                if kind_value==0:value=struct.unpack('>d',body[j:j+8])[0];j+=8
                elif kind_value==1:require(body[j] in (0,1),'Invalid boolean');value=bool(body[j]);j+=1
                elif kind_value==2:length=int.from_bytes(body[j:j+2],'big');j+=2;value=body[j:j+length].decode('ascii');j+=length
                elif kind_value==11:value=dict(milliseconds=struct.unpack('>d',body[j:j+8])[0],offset_bytes=body[j+8:j+10].hex());j+=10
                else:raise AssertionError('Unreviewed metadata value')
                metadata[key]=value
            require(body[j:]==b'\x00\x00\x09','Metadata tail drift')
        i+=15+size
    require(counts['18']==1 and counts['8']>0 and counts['9']>0 and set(codecs)=={'audio_2','video_2'},'Source stream drift');require(metadata['filesize']==len(data)+38 and metadata['width']==320 and metadata['height']==240,'Source metadata drift')
    return dict(bytes=len(data),source_flags_hex='0d',source_metadata_filesize_excess_bytes=38,tag_counts=dict(counts),codec_counts=dict(codecs),last_timestamps_ms=last,metadata=metadata,decoded=False,listened=False,watched=False,full_codec_conformance_certified=False)


def sanitize(data,n):
    payload,name=static_html(data)
    if n!=1357:
        scripts=re.findall(rb'<script\b[^>]*>.*?</script>',payload,re.S);require(len(scripts)==3,'Player script count drift')
        require(b'src="../../../support/jquery-1.3.2.min.js"' in scripts[0] and b'src="../../../support/flowplayer-3.1.4.min.js"' in scripts[1] and b'$f("a.player", "../../../support/flowplayer-3.1.5.swf"' in scripts[2],'Player source drift')
        for script in scripts:payload=payload.replace(script,b'')
    require(not BeautifulSoup(payload,'html.parser').find_all('script'),'Unreviewed script')
    return payload,name


def localize(payload,url):
    deps={};s=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href')]:
        for el in s.find_all(tag):
            path=el[attr];name=Path(path).name;require(Path(name).suffix in MIMES,'Unreviewed attachment');u=urljoin(url,path);require(name not in deps or deps[name]==u,'Dependency collision');deps[name]=u
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+path.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==3,'Selection drift')
    snapshots={s['source_url']:s for s in map(download,[CSS_URL+n for n in STYLE_NAMES])};prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];n=int(pid[-5:]);url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/'
        payload,name=sanitize((ROOT/old['source_file']).read_bytes(),n);css,cssdeps=local_css((ROOT/snapshots[CSS_URL+name]['path']).read_bytes());payload,deps=localize(payload,url)
        require(not(set(deps)&set(cssdeps)),'CSS/image collision');deps.update(cssdeps);urls.update(deps.values());urls.add(url);prepared[pid]=(url,payload,name,css,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];url,payload,cssname,css,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift')
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];media={}
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html');add(css,cssname,'text/css')
        for name,u in sorted(deps.items()):
            p=ROOT/snapshots[u]['path'];data=p.read_bytes();ext=Path(name).suffix
            if urljoin(url,name)==u and (source.parent/name).exists():require(sha(p)==sha(source.parent/name),'Unreviewed attachment mismatch')
            if ext=='.pdf':
                require(data.startswith(b'%PDF-'),'Not PDF')
                with fitz.open(p) as doc:require(len(doc)==2 and not doc.is_encrypted,'Unexpected PDF');media[name]=dict(pages=len(doc),text_chars=[len(pg.get_text()) for pg in doc],original_bytes_preserved=True)
            elif ext=='.flv':media[name]=flv_structure(data)
            else:
                with Image.open(p) as im:im.verify()
            add(data,name,MIMES[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed);check_css(folder/cssname,allowed)
        note='The original PDF and/or video attachments, ordering and player images are preserved byte-for-byte. Obsolete player scripts are removed and original links point to local files. FLV tag boundaries are complete, but every original video has metadata filesize 38 bytes greater than its actual length. This discrepancy and original 0x0d header flags are preserved, not repaired or interpreted as proof of codec validity; decoding, listening and viewing are not certified.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original local attachment links. The original PDF/FLV files are the inputs; text previews do not replace them.\n\nArchive limitation: '+note,assets=public+assets,source_visibility='explicit_media_packet_original_archive_judge_only',asset_policy=note)
        row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2010_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,css_name=cssname,media_structure=media,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=3,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png')
        p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,2400','--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)
    pdf=ROOT/CACHE/'mystery_hunt_01357/input/banner_headline.pdf';p=subprocess.run([str(ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'),'-png','-r','130',str(pdf),str(out/'banner')],capture_output=True,timeout=45);require(p.returncode==0,'PDF render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
