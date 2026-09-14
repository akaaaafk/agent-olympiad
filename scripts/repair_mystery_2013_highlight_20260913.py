"""Fix duplicated video paths and retain all original timed caption data."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageFont
from scripts.repair_mystery_2013_static_20260913 import sanitize as static_html,localize_css,localize_inline,compile_less,snapshot,check_css,ORIGIN,missing_tile_evidence,UNUSED_EVIL,SCRIPTS
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2013_highlight_20260913/'
RAW='data/raw/mystery_hunt/separated_2013_highlight_20260913/'
REPORT='data/benchmarks/mystery_2013_highlight_repair_20260913.json'
PID='mystery_hunt_01712'
SELECTED={PID}
PAGE=ORIGIN+'get_smart/highlight_reel/index.html'
CUE=re.compile(rb'pop\.subtitle\(\{\s*start:\s*(\d+),\s*end:\s*(\d+),\s*text:\s*"([A-Za-z0-9 ]+)",\s*target:\s*"caption"\s*\}\);')
CAPTION_CSS=b'#video::cue { color: white; background-color: transparent; text-shadow: 2px 2px black; font-size: 32px; font-family: Arial, sans-serif; }\n'


def cues_and_sanitize(data):
    scripts=SCRIPTS.findall(data);inline=[s for s in scripts if b'var pop = Popcorn' in s];require(len(inline)==1,'Caption script count drift');script=inline[0];matches=list(CUE.finditer(script));require(len(matches)==26,'Caption count drift')
    remain=b''.join(CUE.sub(b'',script).split());expected=b'''<script>document.addEventListener("DOMContentLoaded",function(){varpop=Popcorn("#video")},false);functionmaximize(){varelt=document.getElementById("video_container");if(elt.mozRequestFullScreen!=undefined){elt.mozRequestFullScreen();}elseif(elt.webkitRequestFullScreen!=undefined){elt.webkitRequestFullScreen();}returntrue;}</script>''';require(remain==expected,'Unreviewed caption logic')
    cues=[dict(start=int(m[1]),end=int(m[2]),text=m[3].decode('ascii')) for m in matches];require(cues[0]==dict(start=0,end=10,text='GET SMART') and cues[-1]==dict(start=291,end=319,text='Murghab via Turkmenhowayollary'),'Cue boundary drift');require(all(c['start']<c['end'] for c in cues) and all(a['end']<b['start'] for a,b in zip(cues,cues[1:])),'Cue order drift')
    lib=b'<script src="popcorn-complete.min.js"></script>';require(data.count(lib)==1,'Caption library drift');payload=data.replace(lib,b'').replace(script,b'');payload,styles=static_html(payload,PAGE,1712)
    link=b'<a data-archive-href="index.html#" onclick="return maximize();">View full screen</a>';require(payload.count(link)==1,'Fullscreen control drift');payload=payload.replace(link,b'<span data-archive-control="fullscreen">Use the native player for full screen.</span>')
    for ext in ('mp4','webm'):
        token=('src="highlight_reel/video.'+ext+'"').encode();require(payload.count(token)==1,'Duplicated video path drift');payload=payload.replace(token,('src="video.'+ext+'"').encode())
    token=b'<video id="video" controls>';require(payload.count(token)==1,'Player opening drift');payload=payload.replace(token,b'<video id="video" controls preload="none">')
    payload=payload.replace(b'</video>',b'<track kind="subtitles" src="captions.vtt" srclang="en" label="Original puzzle captions" default>\n</video>');payload=payload.replace(b'</head>',b'<link rel="stylesheet" href="native-captions.css">\n</head>')
    note=b'<p>Archive repair: both original videos and the <a href="captions.vtt">original timed captions (WebVTT)</a> are local. Caption timing and wording are unchanged; native subtitle layout may differ from the old player. If local-file browser restrictions prevent subtitles, open the video with the supplied subtitle file in a compatible player. The original final caption ends at 319 seconds, beyond the archived video; no padding or retiming is added.</p>'
    require(payload.count(b'<div id="video_top">')==1,'Video wrapper drift');payload=payload.replace(b'<div id="video_top">',note+b'\n<div id="video_top">');return payload,styles,cues


def make_vtt(cues):
    def stamp(t):return f'{t//3600:02}:{t//60%60:02}:{t%60:02}.000'
    return ('WEBVTT\n\n'+'\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues,1))+'\n').encode('ascii')


def video_review(path):
    sys.path.insert(0,str(ROOT/CACHE/'tools'));import av
    require(av.__version__=='16.0.1','Decoder version drift');stats=[]
    with av.open(str(path),'r') as container:
        require([s.type for s in container.streams]==['video','audio'],'Unexpected streams');container_duration=container.duration/av.time_base
        for s in container.streams:stats.append(dict(index=s.index,type=s.type,codec=s.codec_context.name,frames=0,first_time=None,last_time=None,last_end_time=None,samples=0))
        for packet in container.demux():
            require(not packet.is_corrupt,'Corrupt media packet')
            for f in packet.decode():
                require(not f.is_corrupt and f.pts is not None,'Corrupt or untimed frame');d=stats[packet.stream.index];t=float(f.pts*f.time_base);require(d['last_time'] is None or t>=d['last_time'],'Decoded timestamp regression');d['first_time']=t if d['first_time'] is None else d['first_time'];d['last_time']=t;d['frames']+=1
                if d['type']=='audio':d['samples']+=f.samples;d['sample_rate']=f.sample_rate;d['last_end_time']=t+f.samples/f.sample_rate
                else:d['width']=f.width;d['height']=f.height;d['last_end_time']=t+float(packet.stream.time_base*(f.duration or 1))
    require(all(s['frames']>100 for s in stats) and 310<container_duration<320,'Unexpected video extent');return dict(pyav_version=av.__version__,container_duration_seconds=container_duration,streams=stats,all_streams_decoded_to_eof=True,listened=False,fully_watched=False,transcoded=False,semantic_equivalence_between_formats_certified=False)


def failed_paths():
    path=ROOT/CACHE/'failed_paths.json'
    if path.exists():return read(path)
    rows=[]
    for ext in ('mp4','webm'):
        u=urljoin(PAGE,'highlight_reel/video.'+ext);r=requests.get(u,timeout=20);require(r.status_code==404 and r.url==u,'Failed path changed');rows.append(dict(source_url=u,http_status=404,response_sha256=hashlib.sha256(r.content).hexdigest(),retrieved_at_utc=Store(ROOT).stamp,recovered_url=urljoin(PAGE,'video.'+ext)))
    Store(ROOT).save(path.relative_to(ROOT).as_posix(),rows);return rows


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);old=next(r for r in before if r['problem_id']==PID);require(not any(a['role']=='agent_visible' for a in old['assets']),'Already public');source=ROOT/old['source_file'];data=source.read_bytes();payload,styleurls,cues=cues_and_sanitize(data);snapshots={};styles={};deps={}
    require(not BeautifulSoup(payload,'html.parser').select('#evilbg, #evilbar1'),'Unused selectors changed')
    for name,target in styleurls.items():
        if target not in snapshots:snapshots[target]=snapshot(target)
        raw=(ROOT/snapshots[target]['path']).read_bytes();styles[name]=localize_css(compile_less(raw) if target.endswith('.less') else raw,target,deps)
    payload=localize_inline(payload,PAGE,deps)
    for target in list(deps.values()):
        if target.startswith('https://fonts.gstatic.com/'):
            family=urlparse(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
    deps.update({'video.mp4':urljoin(PAGE,'video.mp4'),'video.webm':urljoin(PAGE,'video.webm')});urls=set(deps.values())|{PAGE}
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    require(data.replace(b'\r',b'')==(ROOT/snapshots[PAGE]['path']).read_bytes().replace(b'\r',b''),'Publisher HTML drift');failures=failed_paths();folder=ROOT/CACHE/PID/'input';folder.mkdir(parents=True,exist_ok=True);public=[];copies=[];media={}
    def add(raw,name,mime):
        p=folder/name
        if p.exists():require(p.read_bytes()==raw,'Prepared drift')
        else:
            with p.open('xb') as out:out.write(raw)
        dest=RAW+PID+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
    add(payload,'puzzle.html','text/html');add(make_vtt(cues),'captions.vtt','text/vtt');add(CAPTION_CSS,'native-captions.css','text/css')
    for name,raw in styles.items():add(raw,name,'text/css')
    mimes={'.png':'image/png','.ttf':'font/ttf','.txt':'text/plain','.mp4':'video/mp4','.webm':'video/webm'}
    for name,target in sorted(deps.items()):
        p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
        if ext=='.png':
            with Image.open(p) as im:im.verify()
        elif ext=='.ttf':ImageFont.truetype(str(p),16).getmask('Archive')
        elif ext in ('.mp4','.webm'):media[name]=video_review(p)
        add(p.read_bytes(),name,mimes[ext])
    allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
    for p in folder.glob('*.css'):check_css(p,allowed)
    note='The original MP4 and WebM were incorrectly linked through a repeated highlight_reel directory (both 404); their surviving same-directory publisher files are now localized without changing video bytes. All 26 original script-defined captions and their start/end times are converted mechanically to a local WebVTT track. Native subtitle layout is an adaptation, not a certification of historical pixel layout; local-file subtitle restrictions may require a compatible player and the linked VTT file. The original final cue ends at 319 seconds, beyond the approximately 314-second video, and remains unchanged: no padding or timing inference. Both original audio/video streams decode to EOF using an isolated PyAV 16.0.1 tool; this is not full viewing/listening or cross-format semantic equivalence. No puzzle scripts execute. Archive status, solution navigation and scripted fullscreen controls are removed. Current font revisions and missing unused evilfg.png follow the explicitly documented static-page limitations. Gold, total points, membership, licensing and grading/runtime readiness are unchanged, not recertified.'
    assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    row=deepcopy(old);row.update(source_url=PAGE,source_file=RAW+PID+'/input/puzzle.html',assets=public+assets,problem_description='# Highlight Reel\n\nOpen `puzzle.html` with the supplied videos and `captions.vtt`. The timed title captions are part of the puzzle and must not be omitted.\n\nArchive limitation: '+note,source_visibility='explicit_video_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2013_highlight_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[PAGE]['path'],publisher_html_sha256=snapshots[PAGE]['sha256'],dependency_urls=deps,stylesheet_urls=styleurls,captions=cues,video_review=media,failed_video_paths=failures,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row)
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots,unavailable_dependencies=[missing_tile_evidence(UNUSED_EVIL)],failed_video_paths=failures));print(json.dumps(dict(records=1,public_files=len(copies),publisher_files=len(snapshots),video_review=media)))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);source=ROOT/CACHE/PID/'input/puzzle.html'
    for name,qa,start in [('page',False,None),('native-caption-qa',True,None),('native-caption-middle-qa',True,54),('native-caption-last-qa',True,300)]:
        page=source
        if qa:
            # QA-only local access and muted autoplay; public packet never autoplays.
            data=source.read_bytes().replace(b'<head>',b'<head><base href="'+(source.parent.as_uri()+'/').encode()+b'">').replace(b'controls preload="none"',b'controls autoplay muted preload="auto"');page=out/(name+'.html')
            if start is not None:
                for ext in ('mp4','webm'):data=data.replace(('src="video.'+ext+'"').encode(),('src="video.'+ext+'#t='+str(start)+'"').encode())
            if page.exists():require(page.read_bytes()==data,'QA copy drift')
            else:
                with page.open('xb') as f:f.write(data)
        dest=out/(name+'.png');args=[r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,2100','--virtual-time-budget=5000']
        if qa:args+=['--allow-file-access-from-files','--autoplay-policy=no-user-gesture-required']
        p=subprocess.run(args+[page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(name,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
