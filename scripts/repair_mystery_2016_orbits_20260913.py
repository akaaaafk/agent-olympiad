"""Restore the explicitly linked, byte-identical Orbits archive; never execute it."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import urljoin,urlsplit
import zipfile
from bs4 import BeautifulSoup
from scripts.repair_mystery_2016_static_20260913 import ORIGIN,EXT_MIME,sanitize,localize_css,localize_inline,snapshot,check_css,inspect_asset,replace_ref
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2016_orbits_20260913/'
RAW='data/raw/mystery_hunt/separated_2016_orbits_20260913/'
REPORT='data/benchmarks/mystery_2016_orbits_repair_20260913.json'
SELECTED={'mystery_hunt_02203'}
ZIP_SHA='bd1561c4272d942b3df798dae550b4de7f6547dee7cbb6b3c7e55bd88b9152e8'


def zip_review(path):
    require(path.stat().st_size==51749094 and sha(path)==ZIP_SHA,'ZIP source drift');entries=[]
    with zipfile.ZipFile(path) as z:
        infos=z.infolist();require([(i.filename,i.file_size) for i in infos]==[('index.html',127),('orbits.txt',138532800)],'Archive membership/order drift')
        for i in infos:
            require(not i.flag_bits&1 and not stat.S_ISLNK(i.external_attr>>16) and i.compress_size>0 and i.file_size/i.compress_size<4,'Unsafe ZIP member')
            h=hashlib.sha256();size=0;first=None;last=None
            with z.open(i) as stream:
                while True:
                    chunk=stream.read(1000000)
                    if not chunk:break
                    size+=len(chunk);h.update(chunk)
                    if i.filename=='index.html':require(chunk==b'<html>\r\n<head>\r\n\r\n</head><body>\r\n\r\n<h2>Orbits</h2>\r\n\r\n<a href="orbits.txt">orbits.txt (text file, 135MB)</a>\r\n\r\n</body></html>\r','ZIP entrance changed')
                    else:
                        require(re.fullmatch(rb'(?:[A-Z]{8}\r\n)+',chunk) is not None,'Unexpected text framing or active content')
                        if first is None:first=chunk[:8].decode('ascii')
                        last=chunk[-10:-2].decode('ascii')
            require(size==i.file_size,'ZIP size mismatch');entry=dict(name=i.filename,bytes=size,crc32=i.CRC,sha256=h.hexdigest())
            if first is not None:entry.update(lines=size//10,first_line=first,last_line=last,line_endings='CRLF',line_width=8)
            entries.append(entry)
    return dict(entries=entries,crc_checked_to_eof=True,original_zip_bytes_preserved=True,extracted_to_disk=False,executed=False,text_order_or_duplicates_not_changed=True)


def localize_html(payload,url):
    deps={};seen=set()
    for tag,attr in [('img','src'),('a','href')]:
        for el in BeautifulSoup(payload,'html.parser').find_all(tag,attrs={attr:True}):
            ref=el[attr];target=urljoin(url,ref);name=Path(urlsplit(target).path).name;require(target.startswith(ORIGIN) and re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|zip)',name),'Unreviewed attachment');require(name not in deps or deps[name]==target,'Collision');deps[name]=target
            if (attr,ref) not in seen:payload=replace_ref(payload,attr,ref,name);seen.add((attr,ref))
    require([n for n in deps if n.endswith('.zip')]==['orbits.zip'],'Download scope drift');return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==1,'Selection drift');old=chosen[0];row=deepcopy(old);pid=old['problem_id'];url=ORIGIN+'puzzle/orbits/';source=ROOT/old['source_file'];payload,styleurls=sanitize(source.read_bytes(),url);payload,deps=localize_html(payload,url);styles={};cssdeps={};snapshots={}
    for name,target in styleurls.items():snapshots[target]=snapshot(target);styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
    payload=localize_inline(payload,url,cssdeps);require(not(set(deps)&set(cssdeps)),'CSS collision');deps.update(cssdeps)
    for target in list(cssdeps.values()):
        if target.startswith('https://fonts.gstatic.com/'):
            family=urlsplit(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(({url}|set(deps.values()))-set(snapshots)))})
    remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);copies=[];public=[];reviews={}
    def add(data,name,mime):
        p=folder/name
        if p.exists():require(p.read_bytes()==data,'Prepared drift')
        else:
            with p.open('xb') as out:out.write(data)
        dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
    add(payload,'puzzle.html','text/html')
    for name,data in styles.items():add(data,name,'text/css')
    for name,target in sorted(deps.items()):
        p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
        if ext=='.zip':reviews[target]=zip_review(p);mime='application/zip'
        elif ext=='.txt':require(b'SIL OPEN FONT LICENSE' in p.read_bytes(),'Font license drift');mime='text/plain'
        else:reviews[target]=inspect_asset(p,ext);mime=EXT_MIME[ext]
        add(p.read_bytes(),name,mime)
    allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
    for p in folder.glob('*.css'):check_css(p,allowed)
    note='The explicitly active orbits.zip link is restored with the original ZIP bytes, member names, order and CRC-verified contents. Its index.html links only to the included orbits.txt; all 13,853,280 eight-letter CRLF records are preserved without sorting, deduplication, line-ending conversion or solving. The old commented-out S3 text link is not activated or downloaded. Archive solution navigation and sheep/status scripts are removed; round-return navigation is inert. Same-year CSS dependency path repairs follow the preceding static batch. Source-named Google fonts are current snapshots with OFL texts, not certified 2016 binary versions. Gold, total points, splits, license and grading/runtime readiness remain unchanged and are not recertified.'
    assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# Orbits\n\nOpen `puzzle.html` and its explicitly linked original `orbits.zip`.\n\nArchive limitation: '+note,source_visibility='explicit_zip_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2016_orbits_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row)
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots,asset_reviews=reviews));print(json.dumps(dict(records=1,public_files=len(copies),publisher_files=len(snapshots),zip_review=reviews[url+'orbits.zip'])))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);page=ROOT/CACHE/'mystery_hunt_02203/input/puzzle.html';dest=out/'orbits.png';p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1400','--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
