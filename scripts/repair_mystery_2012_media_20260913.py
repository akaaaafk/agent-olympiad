"""Restore four explicit PDF/audio packets; preserve originals, never autoplay."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
from PIL import Image,ImageFont
import pymupdf as fitz
from scripts.repair_mystery_2012_static_20260913 import snapshot,css_graph,check_css,sanitize as static_html,SCRIPTS
from scripts.repair_mystery_2009_media_20260913 import audio_structure
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2012_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2012_media_20260913/'
REPORT='data/benchmarks/mystery_2012_media_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1582,1585,1616,1618)}
MIMES={'.gif':'image/gif','.jpg':'image/jpeg','.png':'image/png','.pdf':'application/pdf','.mp3':'audio/mpeg','.ogg':'audio/ogg','.ttf':'font/ttf','.txt':'text/plain'}


def crc_table():
    table=[]
    for n in range(256):
        c=n<<24
        for _ in range(8):c=((c<<1)^0x04c11db7 if c&0x80000000 else c<<1)&0xffffffff
        table.append(c)
    return table


CRC=crc_table()


def ogg_structure(data):
    # Container framing/CRC only, per https://www.xiph.org/ogg/doc/framing.html.
    pos=0;pages=0;serial=None;packet=bytearray();headers=[];packets=0;last_granule=0;eos=False
    while pos<len(data):
        require(not eos and pos+27<=len(data) and data[pos:pos+5]==b'OggS\x00','Truncated or unexpected Ogg header');count=data[pos+26];require(pos+27+count<=len(data),'Truncated lacing table');laces=data[pos+27:pos+27+count];end=pos+27+count+sum(laces);require(end<=len(data),'Truncated Ogg body')
        flags=data[pos+5];sn=int.from_bytes(data[pos+14:pos+18],'little');sequence=int.from_bytes(data[pos+18:pos+22],'little');require(flags&~7==0 and sequence==pages and (serial is None or sn==serial),'Unreviewed multiplexed or discontinuous Ogg');require(bool(flags&2)==(pages==0) and bool(flags&1)==bool(packet),'Ogg BOS/continuation mismatch');serial=sn;eos=bool(flags&4)
        page=bytearray(data[pos:end]);expected=int.from_bytes(page[22:26],'little');page[22:26]=bytes(4);crc=0
        for b in page:crc=((crc<<8)&0xffffffff)^CRC[(crc>>24)^b]
        require(crc==expected,'Ogg page CRC mismatch');j=pos+27+count
        for length in laces:
            packet.extend(data[j:j+length]);j+=length
            if length<255:
                if packets<3:headers.append(bytes(packet))
                else:require(packet and not packet[0]&1,'Unexpected non-audio Vorbis packet')
                packets+=1;packet.clear()
        granule=int.from_bytes(data[pos+6:pos+14],'little',signed=True)
        if granule!=-1:require(granule>=last_granule,'Ogg granule regression');last_granule=granule
        pages+=1;pos=end
    require(eos and not packet and packets>3 and len(headers[0])==30,'Incomplete Ogg stream');require([p[:7] for p in headers]==[b'\x01vorbis',b'\x03vorbis',b'\x05vorbis'],'Missing Vorbis headers');ident=headers[0];require(ident[7:11]==bytes(4) and ident[11] in (1,2) and ident[29]==1,'Unreviewed Vorbis identity');rate=int.from_bytes(ident[12:16],'little');require(rate in (22050,44100,48000),'Unreviewed sample rate')
    return dict(format='Ogg Vorbis',pages=pages,packets=packets,serial=serial,channels=ident[11],rate=rate,final_granule=last_granule,duration_seconds=last_granule/rate,all_page_crc_verified=True,decoded=False,listened=False,mp3_ogg_semantic_equivalence_certified=False)


def sanitize(data,url,n):
    if n==1616:
        scripts=SCRIPTS.findall(data);extra=[s for s in scripts if b'jquery/1.7.1/jquery.min.js' in s or b'// add mouseover playback for convenience' in s];require(len(extra)==2,'Mouseover scripts drift')
        require(b'http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js' in extra[0] and b's2.src = e.href.replace(/[.]mp.$/, ".ogg");' in extra[1] and b'$(e).mouseenter(function() { tryToReset(); a.play(); });' in extra[1],'Unreviewed playback script')
        for script in extra:data=data.replace(script,b'')
    payload,styleurls=static_html(data,url)
    if n==1618:
        require(payload.count(b'preload=""')==31 and not BeautifulSoup(payload,'html.parser').find_all('audio',autoplay=True),'Audio controls drift');payload=payload.replace(b'preload=""',b'preload="none"')
    return payload,styleurls


def localize(payload,url):
    deps={};s=BeautifulSoup(payload,'html.parser')
    for tag,attr in [('img','src'),('a','href'),('source','src')]:
        for el in s.find_all(tag,attrs={attr:True}):
            ref=el[attr];name=Path(ref).name;require(re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|gif|pdf|mp3|ogg)',name),'Unreviewed attachment');target=urljoin(url,ref);require(target.startswith('https://puzzles.mit.edu/2012/puzzles/'),'External attachment');require(name not in deps or deps[name]==target,'Attachment collision');deps[name]=target
            for q in (b'"',b"'"):payload=payload.replace(attr.encode()+b'='+q+ref.encode()+q,attr.encode()+b'='+q+name.encode()+q)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==4,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];n=int(pid[-5:]);url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url,n);payload,deps=localize(payload,url);styles,cssdeps,allstyles=css_graph(styleurls,snapshots);require(not(set(deps)&set(cssdeps)),'Asset collision');deps.update(cssdeps)
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlparse(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        urls.add(url);urls.update(deps.values());prepared[pid]=(url,payload,styles,styleurls,allstyles,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];n=int(pid[-5:]);url,payload,styles,styleurls,allstyles,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];media={}
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
                require(data.startswith(b'%PDF-'),'Not PDF')
                with fitz.open(p) as doc:require(len(doc)==(1 if n==1582 else 4) and not doc.is_encrypted,'Unexpected PDF');media[name]=dict(pages=len(doc),page_sizes=[[pg.rect.width,pg.rect.height] for pg in doc],original_bytes_preserved=True)
            elif ext=='.mp3':media[name]=audio_structure(p)
            elif ext=='.ogg':media[name]=ogg_structure(data)
            add(data,name,MIMES[ext])
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for name in styles:check_css(folder/name,allowed)
        note='Original PDF pages, images and explicitly linked MP3/OGG files retain their bytes and ordering. Sudoku number/star rules, unequal-length blank boxes, arithmetic signs and the leading-zero extraction string are preserved. The Voices page retains its 30 direct MP3 links; its optional script-generated hover/OGG player is not reconstructed. Argh retains all 31 native players and both explicit formats, with preload disabled. MP3 frame boundaries and Ogg framing/page CRC are checked, not decoded, listened to, transcribed or certified semantically equivalent. Original CSS is localized; source-named Google Fonts use current publisher binaries, not certified historical revisions. No other answers, scores, cross-task state or grading/runtime readiness are changed or recertified.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original styled packet and local PDF/audio links. Text previews do not replace images or audio.\n\nArchive limitation: '+note,assets=public+assets,source_visibility='explicit_media_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2012_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,all_stylesheet_urls=allstyles,media_structure=media,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=4,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);heights={1582:1400,1585:5800,1616:1300,1618:4600}
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(heights[int(pid[-5:])]),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)
    for pid,name in [('mystery_hunt_01582','grid-lg.pdf'),('mystery_hunt_01585','1.pdf')]:
        p=subprocess.run([str(ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'),'-png','-r','130',str(ROOT/CACHE/pid/'input'/name),str(out/pid)],capture_output=True,timeout=45);require(p.returncode==0,'PDF render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
