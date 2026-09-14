"""Two explicitly linked archival inputs; no modern element data or audio rewrite."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
import wave
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2003_static_20260913 import SCRIPT,sanitize as sanitize_2003
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_linked_archives_20260913/'
RAW='data/raw/mystery_hunt/separated_linked_archives_20260913/'
REPORT='data/benchmarks/mystery_linked_archives_repair_20260913.json'
SELECTED={'mystery_hunt_00177','mystery_hunt_00383'}
TABLE='https://puzzles.mit.edu/2001/phase4/01/table.html'
VARIATIONS='https://puzzles.mit.edu/2002/round1/07/Puzzle.html'
OLD_VARIATIONS='http://www.mit.edu/~puzzle/02/round1/07/Puzzle.html'
ELEMENT=re.compile(rb'href="(http://pearl1\.lanl\.gov/periodic/elements/([0-9]+)\.html)"')


def sanitize_table(data):
    links=ELEMENT.findall(data)
    require(len(links)==115 and len({n for u,n in links})==115,'Element link set drift')
    require(len(BeautifulSoup(data,'html.parser').find_all('a'))==len(links),'Unexpected table link')
    # Same labels, cells and historical URLs, but no outbound navigation. Preserve
    # the published black underlined link appearance even without an href.
    payload=ELEMENT.sub(lambda m:b'data-archive-href="'+m[1]+b'"',data)
    require(payload.count(b'</head>')==1,'Head drift')
    payload=payload.replace(b'</head>',b'<style>a[data-archive-href] { color: #000000; text-decoration: underline; }</style></head>')
    return payload,[dict(reason='disable unavailable historical element navigation while retaining URLs and labels',count=len(links))]


def sanitize_variations(data):
    require(len(SCRIPT.findall(data))==1,'Secondary script drift');data=SCRIPT.sub(b'',data)
    pattern=rb'<a href="\.\./index\.html">2002 MIT Mystery Hunt</a>'
    require(len(re.findall(pattern,data))==1,'Secondary index drift');data=re.sub(pattern,b'2002 MIT Mystery Hunt',data)
    for n in ('4','3'):
        old=f'src="../../images/{n}.gif"'.encode();require(data.count(old)==1,'Header image drift')
        data=data.replace(old,f'src="{n}.gif"'.encode())
    return data


def inspect_audio(path,mime):
    if mime=='audio/wav':
        with wave.open(str(path),'rb') as w:
            frames=w.getnframes();rate=w.getframerate();channels=w.getnchannels();width=w.getsampwidth()
            require(w.getcomptype()=='NONE' and len(w.readframes(frames))==frames*channels*width,'Truncated/unexpected WAV')
        return dict(format='PCM WAV',frames=frames,rate=rate,channels=channels,sample_width=width,duration_seconds=frames/rate,content_listened=False)
    data=path.read_bytes();i=0;frames=0;rates=set()
    # Parse each observed MPEG-1 Layer III frame, not merely a .mp3 suffix.
    # This is structural validation, not decoding, transcription or equivalence.
    bitrates=[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]
    while i<len(data):
        require(i+4<=len(data),'Truncated MPEG header');h=int.from_bytes(data[i:i+4],'big')
        require((h>>21)==0x7ff and ((h>>19)&3)==3 and ((h>>17)&3)==1,'Unexpected MPEG stream')
        bitrate=bitrates[(h>>12)&15];rate_index=(h>>10)&3
        require(bitrate>0 and rate_index<3,'Invalid MPEG rate');rate=[44100,48000,32000][rate_index]
        length=144000*bitrate//rate+((h>>9)&1);require(i+length<=len(data),'Truncated MPEG frame')
        i+=length;frames+=1;rates.add(rate)
    require(frames>0 and len(rates)==1,'Inconsistent MPEG frame stream')
    return dict(format='MPEG-1 Layer III',frames=frames,rate=rate,duration_seconds=frames*1152/rate,content_listened=False,decoded=False)


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==2,'Selection drift')
    urls={TABLE,VARIATIONS};media={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url'];urls.add(url)
        refs=[t['src'] for t in BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser').find_all('img')]
        require(refs==([] if row['problem_id'].endswith('00177') else ['images/head5.jpg','images/mad-props.jpg']),'Primary media drift')
        media[row['problem_id']]=refs;urls.update(urljoin(url,r) for r in refs)
    linked_media=['../../images/4.gif','../../images/3.gif','grid.gif','Puzzle.wav','Puzzle.mp3']
    urls.update(urljoin(VARIATIONS,r) for r in linked_media)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots={s['source_url']:s for s in pool.map(download,sorted(urls))}
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=row['problem_id'];source=ROOT/row['source_file'];url='https://puzzles.mit.edu/'+row['puzzle_url'];remote=ROOT/snapshots[url]['path']
        require(SCRIPT.sub(b'',source.read_bytes()).replace(b'\r',b'')==SCRIPT.sub(b'',remote.read_bytes()).replace(b'\r',b''),'Publisher differs')
        folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[];audio={}
        def add(data,name,mime):
            target=folder/name
            if target.exists():require(target.read_bytes()==data,'Prepared bytes differ')
            else:
                with target.open('xb') as out:out.write(data)
            dest=RAW+pid+'/input/'+name;copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(target)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(target)))
        if pid.endswith('00177'):
            require(len(SCRIPT.findall(source.read_bytes()))==1,'Primary script drift')
            payload=SCRIPT.sub(b'',source.read_bytes());edits=[dict(reason='remove archive answer checker')]
            table,table_edits=sanitize_table((ROOT/snapshots[TABLE]['path']).read_bytes());edits+=table_edits
            add(payload,'puzzle.html','text/html');add(table,'table.html','text/html')
            note='The linked table is preserved exactly as a puzzle artifact, including its historical symbols and values. Its external element-information pages are not recovered; their URLs remain inert in the HTML source. No release schedule is inferred from the word periodically.'
            public_note='Open table.html through the original link. Historical external element-information pages are not included; their links are inert. The table is an archival puzzle artifact, not a current chemistry reference.'
        else:
            payload,edits=sanitize_2003(source.read_bytes());oldlink=('href="'+OLD_VARIATIONS+'"').encode()
            require(payload.count(oldlink)==1,'Explicit cross-reference drift');payload=payload.replace(oldlink,b'href="variations.html"')
            edits.append(dict(reason='localize explicitly linked older puzzle without solution material',before=OLD_VARIATIONS,after='variations.html'))
            add(payload,'puzzle.html','text/html');add(sanitize_variations((ROOT/snapshots[VARIATIONS]['path']).read_bytes()),'variations.html','text/html')
            for ref in media[pid]:
                p=ROOT/snapshots[urljoin(url,ref)]['path']
                for local in (source.parent/ref,source.parent/Path(ref).name):
                    if local.is_file():require(sha(local)==sha(p),'Original image differs')
                with Image.open(p) as im:im.verify()
                add(p.read_bytes(),Path(ref).name,'image/jpeg')
            for ref in linked_media:
                p=ROOT/snapshots[urljoin(VARIATIONS,ref)]['path'];name=Path(ref).name
                mime='audio/wav' if name.endswith('.wav') else 'audio/mpeg' if name.endswith('.mp3') else 'image/gif'
                if mime.startswith('image/'):
                    with Image.open(p) as im:im.verify()
                else:audio[name]=inspect_audio(p,mime)
                add(p.read_bytes(),name,mime)
            note='The explicitly linked 2002 page, grid and both original audio encodings are archived. Audio was structurally checked, not listened to or declared semantically equivalent; the original double-speed MP3 warning is preserved. No transcript, resampling, solving hints or answers are added.'
            public_note='The explicitly linked older puzzle, images and both original audio files are included. Preserve the published playback warning; no audio transcription or timing correction has been added.'
        allowed={p.resolve() for p in folder.iterdir()}
        for p in folder.glob('*.html'):check_html(p,allowed)
        clean=BeautifulSoup(payload,'html.parser')
        prompt='# '+clean.title.get_text(strip=True)+'\n\nOpen `puzzle.html` for the original layout and explicit links. No flattened preview replaces tables, diagrams, ordering or typography.\n\nArchive limitation: '+public_note
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,assets=public+assets,
            source_visibility='explicit_linked_archive_original_judge_only',asset_policy='Only the listed public puzzle files are initial inputs. Archive solution controls and live external navigation are not available.')
        row['evaluation']['limitations']=note+' Gold, scores and end-to-end evaluation are not recertified. Prior limitations: '+old['evaluation']['limitations']
        row['source_review']=deepcopy(old.get('source_review') or {})
        row['source_review'].update(batch='mystery_linked_archives_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),edits=edits,audio_structure=audio,scope_note=note,answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots))
    print(json.dumps(dict(records=2,public_files=len(copies))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        for page in sorted((ROOT/CACHE/pid/'input').glob('*.html')):
            height=7000 if pid.endswith('00383') and page.name=='puzzle.html' else 2000
            dest=out/(pid+'_'+page.stem+'.png')
            proc=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
                 '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1600,'+str(height),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
            require(proc.returncode==0 and dest.exists(),'Render failed');print(dest.name,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
