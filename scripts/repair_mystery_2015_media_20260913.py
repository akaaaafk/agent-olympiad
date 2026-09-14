"""Restore explicit Coins, Image and music-video inputs; do not run puzzle code."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2015_static_20260913 import ORIGIN,MIRROR,EXT_MIME,URL,QUOTES,sanitize,replace_ref,localize_css,localize_inline,check_css,check_css_data,inspect_asset,snapshot as static_snapshot
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2015_media_20260913/'
RAW='data/raw/mystery_hunt/separated_2015_media_20260913/'
REPORT='data/benchmarks/mystery_2015_media_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1994,1997,2037)}
VIDEO_BASE='https://hunt-2015-assets.s3.amazonaws.com/cl2uh1ojxx4g3brx88b35noh21xhoaod/check-out-this-sticked-asiatic-music.'
VIDEO_URLS={VIDEO_BASE+ext for ext in ('mp4','webm')}
DECODER='data/.cache/mystery_2013_highlight_20260913/tools'


def snapshot(url):
    if url not in VIDEO_URLS:return static_snapshot(url)
    stem=hashlib.sha256(url.encode()).hexdigest();p=ROOT/CACHE/'publisher'/(stem+'.bin');meta=p.with_suffix('.json')
    if p.exists():
        d=read(meta);require(d['source_url']==url and d['final_url']==url and sha(p)==d['sha256'],'Video cache drift');return d
    r=requests.get(url,timeout=60);r.raise_for_status();require(r.url==url and len(r.content)==int(r.headers['Content-Length']) and 1_000_000<len(r.content)<90_000_000,'Unexpected video download');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as out:out.write(r.content)
    d=dict(source_url=url,final_url=r.url,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(r.content),content_type=r.headers.get('Content-Type'),etag=r.headers.get('ETag'),last_modified=r.headers.get('Last-Modified'),retrieved_at_utc=Store(ROOT).stamp);Store(ROOT).save(meta.relative_to(ROOT).as_posix(),d);return d


def video_review(path):
    sys.path.insert(0,str(ROOT/DECODER));import av
    require(av.__version__=='16.0.1','Decoder drift');stats={}
    with av.open(str(path),'r') as container:
        require(sorted(s.type for s in container.streams)==['audio','video'],'Unexpected stream types');duration=container.duration/av.time_base
        for s in container.streams:stats[s.index]=dict(index=s.index,type=s.type,codec=s.codec_context.name,frames=0,first_time=None,last_time=None,last_end_time=None,samples=0)
        for packet in container.demux():
            require(not packet.is_corrupt,'Corrupt packet')
            for f in packet.decode():
                require(not f.is_corrupt and f.pts is not None,'Corrupt/untimed frame');d=stats[packet.stream.index];t=float(f.pts*f.time_base);require(d['last_time'] is None or t>=d['last_time'],'Timestamp regression');d['first_time']=t if d['first_time'] is None else d['first_time'];d['last_time']=t;d['frames']+=1
                if d['type']=='audio':d['samples']+=f.samples;d['sample_rate']=f.sample_rate;d['last_end_time']=t+f.samples/f.sample_rate
                else:d['width']=f.width;d['height']=f.height;d['last_end_time']=t+float(packet.stream.time_base*(f.duration or 1))
    require(all(s['frames']>100 for s in stats.values()) and 10<duration<3600,'Unexpected media extent');return dict(pyav_version=av.__version__,container_duration_seconds=duration,streams=list(stats.values()),all_streams_decoded_to_eof=True,listened=False,fully_watched=False,transcoded=False,cross_format_semantic_equivalence_certified=False)


def probe():
    for url in sorted(VIDEO_URLS):
        s=snapshot(url);v=video_review(ROOT/s['path']);Store(ROOT).save(CACHE+'video-'+url.rsplit('.',1)[1]+'-review.json',dict(snapshot=s,review=v));print(json.dumps(dict(source=s,review=v)),flush=True)


def localize_packet(data,url,n):
    data,styles=sanitize(data,url);soup=BeautifulSoup(data,'html.parser');deps={};refs=[a['href'] for a in soup.find_all('a',href=True)]
    require(refs==({1994:[VIDEO_BASE+'mp4'],1997:['clickbait.html','clickbait.html'],2037:['image']}[n]),'Unreviewed linked input')
    for el in soup.find_all('img',src=True):
        ref=el['src'];target=urljoin(url,ref);name=Path(urlsplit(target).path).name;require(target.startswith((ORIGIN,MIRROR)) and re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg)',name),'Unreviewed image');require(name not in deps,'Image collision');deps[name]=target;data=replace_ref(data,'src',ref,name)
    if n==1994:
        require([s['src'] for s in soup.find_all('source')]==[VIDEO_BASE+'webm',VIDEO_BASE+'mp4'],'Video source drift')
        for ext in ('webm','mp4'):
            ref=VIDEO_BASE+ext;name=Path(urlsplit(ref).path).name;deps[name]=ref;data=replace_ref(data,'src',ref,name)
            if ext=='mp4':data=replace_ref(data,'href',ref,name)
        require(data.count(b'<video controls style="width: 850px;">')==1,'Video opening drift');data=data.replace(b'<video controls style="width: 850px;">',b'<video controls preload="none" style="width: 850px;">')
    elif n==1997:deps['clickbait.html']=urljoin(url,'clickbait.html')
    else:deps['image']=urljoin(url,'image')
    return data,styles,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==3,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        n=int(old['problem_id'][-5:]);url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls,deps=localize_packet((ROOT/old['source_file']).read_bytes(),url,n);styles={};cssdeps={};extras={}
        if n==1997:
            target=deps.pop('clickbait.html');snapshots[target]=snapshot(target);article=(ROOT/snapshots[target]['path']).read_bytes();soup=BeautifulSoup(article,'html.parser');require([x.name for x in soup.find_all()]==['link','div','div','h1','ol','li','li','li','li'],'Linked article structure drift');require([x.get_text(' ',strip=True) for x in soup.find_all('li')]==['The Supremes','Pie r squared',"Bobby's World","Pappy's Pepperoni Palace"],'Linked article list drift');ref=soup.link['href'];require(ref==MIRROR+'static/stylesheets/clickbait.css','Linked style drift');styleurls['clickbait.css']=ref;extras['clickbait.html']=replace_ref(article,'href',ref,'clickbait.css')
        for name,target in styleurls.items():
            if target not in snapshots:snapshots[target]=snapshot(target)
            styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
        payload=localize_inline(payload,url,cssdeps);require(not(set(cssdeps)&set(deps)),'CSS collision');deps.update(cssdeps);urls.add(url);urls.update(deps.values());prepared[old['problem_id']]=(url,payload,styles,styleurls,deps,extras)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[];reviews={}
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];n=int(pid[-5:]);url,payload,styles,styleurls,deps,extras=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML differs');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
        def add(data,name,mime):
            p=folder/name
            if p.exists():require(p.read_bytes()==data,'Prepared drift')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
        add(payload,'puzzle.html','text/html')
        for name,data in extras.items():add(data,name,'text/html')
        for name,data in styles.items():add(data,name,'text/css')
        for name,target in sorted(deps.items()):
            p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
            if ext in ('.mp4','.webm'):
                v=read(ROOT/CACHE/('video-'+ext[1:]+'-review.json'));require(v['snapshot']['sha256']==sha(p),'Video review stale');reviews[target]=v['review'];mime='video/'+ext[1:]
            elif name=='image':
                require(hashlib.md5(p.read_bytes()).hexdigest()=='f5ac27a1a43331d1e47662928028dc4a' and p.stat().st_size==3542016,'Published attachment MD5/size mismatch');reviews[target]=inspect_asset(p,'.png');mime='application/octet-stream'
            else:
                if target not in reviews:reviews[target]=inspect_asset(p,ext)
                mime=EXT_MIME[ext]
            add(p.read_bytes(),name,mime)
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for p in folder.glob('*.html'):check_html(p,allowed)
        for p in folder.glob('*.css'):check_css(p,allowed)
        note='Only explicitly linked original inputs and their static publisher dependencies are restored. Archive solution navigation, answer-reveal header and gold-bearing scripts are removed; no puzzle code is run. Fonts and CSS dependencies are original publisher files or mechanical local URL rewrites. Gold, total points, splits, licensing and grading/runtime readiness are unchanged, not recertified.'
        if n==1994:note+=' The original MP4 and WebM retain their published bytes, order and embedded audio. Both audio/video streams decode to EOF (about 91 seconds); this does not certify complete viewing/listening, semantic equivalence or equal visual quality between formats. Native playback controls are retained with preload disabled; no transcript or inferred subtitles are added.'
        elif n==1997:note+=' All 32 coin-side images and the 16 counts (total 72) are preserved. Both explicit recommended-article links remain, with the original four-name article and its styling; the banner is puzzle content, not removed as a generic advertisement. The class name solution-table is original clue markup and is not treated as an answer leak.'
        else:note+=' The original extensionless attachment image is retained without renaming, transformation or new file-type hints. Its bytes match the MD5 printed on the original page. A private decoding check is not a reconstructed solution.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        title=clean.select_one('.puzzle-page-header h1').get_text(' ',strip=True);row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# '+title+'\n\nOpen `puzzle.html` with its explicitly linked original input files.\n\nArchive limitation: '+note,source_visibility='explicit_media_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2015_media_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,linked_article_url=urljoin(url,'clickbait.html') if n==1997 else None,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,asset_reviews=reviews));print(json.dumps(dict(records=3,public_files=len(copies),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);pages=[(1994,'puzzle.html',1900),(1997,'puzzle.html',5500),(1997,'clickbait.html',1200),(2037,'puzzle.html',1600)]
    for n,name,height in pages:
        pid=f'mystery_hunt_{n:05}';page=ROOT/CACHE/pid/'input'/name;dest=out/(pid+'-'+name+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(dest.name,flush=True)
    with Image.open(ROOT/CACHE/'mystery_hunt_02037/input/image') as im:im.save(out/'image-qa.png',format='PNG')


def native_video_qa():
    folder=ROOT/CACHE/'mystery_hunt_01994/input';out=ROOT/CACHE/'renders';data=(folder/'puzzle.html').read_bytes();data=data.replace(b'<head>',b'<head><base href="'+(folder.as_uri()+'/').encode()+b'">').replace(b'<video controls preload="none"',b'<video controls muted autoplay preload="auto"')
    for ext in ('mp4','webm'):data=data.replace(('check-out-this-sticked-asiatic-music.'+ext+'" type=').encode(),('check-out-this-sticked-asiatic-music.'+ext+'#t=45" type=').encode())
    page=out/'native-video-qa.html';Store(ROOT).save_text(page.relative_to(ROOT).as_posix(),data.decode('utf-8'));dest=out/'native-video-qa.png';p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--allow-file-access-from-files','--autoplay-policy=no-user-gesture-required','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1700','--virtual-time-budget=3000',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Native player QA failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='probe':probe()
    elif mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='native-video-qa':native_video_qa()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
