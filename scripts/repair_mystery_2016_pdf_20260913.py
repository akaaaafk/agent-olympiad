"""Restore four original 2016 PDF attachments (seven pages), without re-export."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
import pymupdf as fitz
from scripts.repair_mystery_2016_static_20260913 import ORIGIN,EXT_MIME,sanitize,localize_css,localize_inline,snapshot,check_css,inspect_asset,failed_font_paths,failed_logo_path,replace_ref
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2016_pdf_20260913/'
RAW='data/raw/mystery_hunt/separated_2016_pdf_20260913/'
REPORT='data/benchmarks/mystery_2016_pdf_repair_20260913.json'
PAGE_COUNTS={2133:1,2146:1,2185:2,2186:3}
SELECTED={f'mystery_hunt_{n:05}' for n in PAGE_COUNTS}


def localize_html(data,url):
    deps={};seen=set()
    for tag,attr in [('img','src'),('a','href')]:
        for el in BeautifulSoup(data,'html.parser').find_all(tag,attrs={attr:True}):
            ref=el[attr];target=urljoin(url,ref);name=Path(urlsplit(target).path).name;require(target.startswith(ORIGIN) and re.fullmatch(r'[A-Za-z0-9_-]+\.(png|jpg|pdf)',name),'Unreviewed attachment');require(name not in deps or deps[name]==target,'Attachment collision');deps[name]=target
            if (attr,ref) not in seen:data=replace_ref(data,attr,ref,name);seen.add((attr,ref))
    require(sum(n.endswith('.pdf') for n in deps)==1,'PDF link count drift');return data,deps


def pdf_review(path,pages):
    require(path.read_bytes().startswith(b'%PDF-'),'PDF signature drift')
    with fitz.open(path) as doc:
        require(len(doc)==pages and not doc.is_encrypted and doc.embfile_count()==0,'PDF scope/encryption/embedded file drift')
        for p in doc:require(not p.get_links() and not list(p.widgets() or []),'Interactive PDF input not reviewed')
        for n in range(1,doc.xref_length()):require(not re.search(r'/(?:JavaScript|JS|Launch|AA|OpenAction)\b',doc.xref_object(n)),'Active PDF object not reviewed')
        return dict(pages=pages,page_sizes=[[p.rect.width,p.rect.height] for p in doc],text=[p.get_text() for p in doc],original_bytes_preserved=True,links=0,widgets=0,embedded_files=0)


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==4,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url);payload,deps=localize_html(payload,url);styles={};cssdeps={}
        for name,target in styleurls.items():
            if target not in snapshots:snapshots[target]=snapshot(target)
            styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
        payload=localize_inline(payload,url,cssdeps);require(not(set(cssdeps)&set(deps)),'CSS collision');deps.update(cssdeps)
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlsplit(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        urls.add(url);urls.update(deps.values());prepared[old['problem_id']]=(url,payload,styles,styleurls,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[];reviews={}
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];n=int(pid[-5:]);url,payload,styles,styleurls,deps=prepared[pid];source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);public=[]
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
            if ext=='.pdf':reviews[target]=pdf_review(p,PAGE_COUNTS[n]);mime='application/pdf'
            elif ext=='.txt':require(b'SIL OPEN FONT LICENSE' in p.read_bytes(),'Font license drift');mime='text/plain'
            else:
                if target not in reviews:reviews[target]=inspect_asset(p,ext)
                mime=EXT_MIME[ext]
            add(p.read_bytes(),name,mime)
        allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
        for p in folder.glob('*.css'):check_css(p,allowed)
        note='The explicitly linked original PDF and its original page order are preserved byte-for-byte, without re-export, OCR replacement or solved annotations. Original grids, colored marks, pictures, blank regions and repeated clue wording are task content, not inferred errors. Archive navigation, solution links and sheep/status scripts are removed; artwork attribution text remains, with its hyperlink inert. Original same-year Bootstrap fonts and unused archive-logo file repair the source CSS paths documented in the static batch. Source-named Google fonts are current snapshots with OFL texts, not certified 2016 binary versions. Gold, total points, splits, license and grading/runtime readiness are unchanged and not recertified.'
        if n==2146:note+=' Both separately printed 8W clues are retained; direction labels, one/two right-angle-turn rules and wording about paint marks are not deduplicated or solved. No colored marks are invented for the printed grid.'
        if n==2185:note+=' Both the text-clue page and the separate blank/shaded answer-cell page remain. The historical December 9 political reference is not updated to a modern event.'
        if n==2186:note+=' All three pages of arrowhead pieces, labels and deliberately repeated or conflicting properties remain; purported fakes are not removed.'
        assets=deepcopy(old['assets'])
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        title=clean.select_one('.header h2').get_text(' ',strip=True);row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# '+title+'\n\nOpen `puzzle.html` and its linked original PDF. All PDF pages are required; text extraction does not replace visual clues.\n\nArchive limitation: '+note,source_visibility='explicit_pdf_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2016_pdf_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots,asset_reviews=reviews,failed_font_paths=failed_font_paths(),failed_logo_path=failed_logo_path()));print(json.dumps(dict(records=4,public_files=len(copies),publisher_files=len(snapshots),pdf_pages=7)))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def correct_prepared_descriptions():
    require(not (ROOT/REPORT).exists(),'Applied plan is frozen');plan=read(ROOT/CACHE/'plan.json');changed=[]
    replacements={2146:('direction labels, one/two right-angle-turn rules and colored paint marks are not deduplicated or solved.','direction labels, one/two right-angle-turn rules and wording about paint marks are not deduplicated or solved. No colored marks are invented for the printed grid.'),2185:('the separate picture page remain.','the separate blank/shaded answer-cell page remain.')}
    for u in plan['updates']:
        r=u['after'];n=int(r['problem_id'][-5:])
        if n not in replacements:continue
        old,new=replacements[n]
        for obj,key in [(r,'asset_policy'),(r,'problem_description'),(r['evaluation'],'limitations')]:require(obj[key].count(old)==1,'Prepared description drift');obj[key]=obj[key].replace(old,new)
        changed.append(n)
    require(changed==[2146,2185],'Prepared correction scope drift');Store(ROOT).save(CACHE+'plan.json',plan)


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        folder=ROOT/CACHE/pid/'input';page=folder/'puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1400','--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'HTML render failed')
        pdfs=list(folder.glob('*.pdf'));require(len(pdfs)==1,'PDF scope drift');p=subprocess.run([str(ROOT/'data/.cache/science_olympiad_repair_20260913/poppler/poppler-26.07.0/Library/bin/pdftoppm.exe'),'-png','-r','140',str(pdfs[0]),str(out/(pid+'-pdf'))],capture_output=True,timeout=45);require(p.returncode==0,'PDF render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='correct-prepared-descriptions':correct_prepared_descriptions()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
