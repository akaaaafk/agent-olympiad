"""Recover publisher-linked 2023 test files, without running any reference program."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.repair_iol_sources_20260913 import read,sha,rel,require

CACHE="data/.cache/iiot_2023_test_recovery_20260913"
TASKS=("binge","cipher","fence","ktree","matgame","publictransport","tetris","tourdetree")


def listing(text,parent):
    match=re.search(r"window\['_DRIVE_ivd'\] = '(.*?)';",text,re.S)
    require(match is not None,"No public folder listing")
    encoded=re.sub(r"\\x([0-9a-fA-F]{2})",lambda m:chr(int(m[1],16)),match[1])
    encoded=encoded.replace("\\/","/").replace("\\'","'")
    data=json.loads(encoded)
    require(data[1] is None,"Pagination token present; do not treat partial listing as complete")
    files=[]
    for row in data[0]:
        require(parent in row[1],"Folder ownership mismatch")
        files.append(dict(id=row[0],name=row[2],mime=row[3],bytes=row[13]))
    require(len({v['name'] for v in files})==len(files),"Duplicate filenames")
    return files


def fetch(url):
    response=requests.get(url,timeout=(15,45))
    response.raise_for_status()
    return response


def discover():
    store=Store(ROOT)
    archive=fetch("https://iio.team/competition/tasks/2023").text
    store.save_text(CACHE+"/publisher_archive_2023.html",archive)
    official=next(v for v in read(ROOT/"data/.cache/iiot_repair_20260913/official_task_links.json") if v['year']==2023)
    folders=read(ROOT/"data/.cache/iiot_repair_20260913/folder_manifest.json")
    jobs=[]; summaries=[]
    for task in TASKS:
        official_task=next(v for v in official['tasks'] if v['task']==task)
        top_url=official_task['links']['Test cases']
        top_id=re.search(r"/folders/([^?]+)",top_url)[1]
        require(top_id in archive and official_task['title'] in archive,"Official archive link changed")
        top_text=fetch(top_url).text
        store.save_text(CACHE+f"/{task}/folder.html",top_text)
        children=listing(top_text,top_id)
        require({v['name'] for v in children}=={'input','output'},"Unexpected test folder contents")
        ids={}; unpaired={}; counts={}
        for child in children:
            require(child['mime']=='application/vnd.google-apps.folder',"Not a folder")
            kind=child['name']; url="https://drive.google.com/drive/folders/"+child['id']
            html=fetch(url).text
            store.save_text(CACHE+f"/{task}/{kind}_folder.html",html)
            first_page=listing(html,child['id'])
            metadata={v['id']:v for v in first_page}
            embedded_url="https://drive.google.com/embeddedfolderview?id="+child['id']
            embedded=fetch(embedded_url).text
            store.save_text(CACHE+f"/{task}/{kind}_embedded.html",embedded)
            files=[]
            for anchor in BeautifulSoup(embedded,'html.parser').find_all('a'):
                file_match=re.search(r"https://drive.google.com/file/d/([^/]+)/view",anchor.get('href',''))
                if not file_match: continue
                fid=file_match[1]; name=anchor.get_text(' ',strip=True)
                f=metadata.get(fid,dict(id=fid,name=name,mime=None,bytes=None))
                require(f['name']==name,"Two publisher views disagree on filename")
                files.append(f)
            require(len({v['id'] for v in files})==len(files) and len({v['name'] for v in files})==len(files),"Duplicate embedded entries")
            require(set(metadata).issubset({v['id'] for v in files}),"Embedded view omits visible files")
            ids[kind]=set()
            unpaired[kind]=[]; counts[kind]=len(files)
            for f in files:
                match=re.fullmatch(kind+r"(\d+)\.txt",f['name'])
                require(re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:txt|in|out)",f['name']) is not None,"Unexpected test filename")
                require(f['mime'] in (None,'text/plain','application/octet-stream'),"Unexpected file MIME")
                require(f['bytes'] is None or isinstance(f['bytes'],int) and f['bytes']>0,"Invalid published size")
                if match: ids[kind].add(int(match[1]))
                else: unpaired[kind].append(f['name'])
                jobs.append(dict(task=task,kind=kind,**f,source_url="https://drive.google.com/uc?export=download&id="+f['id'],
                    cache=f"{CACHE}/{task}/{kind}/{f['name']}",parent_folder=url,listing_url=embedded_url,official_archive_url=official_task['archive_url']))
        matched=ids['input'] & ids['output']
        summaries.append(dict(task=task,pairs=len(matched),pair_ids=sorted(matched),unmapped_files=unpaired,
            unmatched_input_ids=sorted(ids['input']-matched),unmatched_output_ids=sorted(ids['output']-matched),
            files=counts,source_url=top_url))
        print(json.dumps(summaries[-1]),flush=True)
    plan=dict(discovered_at_utc=datetime.now(timezone.utc).isoformat(),tasks=summaries,jobs=jobs,
              declared_total_bytes=sum(j['bytes'] or 0 for j in jobs),files_without_published_size=sum(j['bytes'] is None for j in jobs),programs_executed=False)
    store.save(CACHE+"/download_plan.json",plan)
    print(json.dumps(dict(tasks=len(TASKS),pairs=sum(t['pairs'] for t in summaries),files=len(jobs),bytes=plan['declared_total_bytes'])))


def download():
    plan=read(ROOT/CACHE/"download_plan.json")
    def one(j):
        path=ROOT/j['cache']; error=None
        if path.exists():
            payload=path.read_bytes()
            require((j['bytes'] is None or len(payload)==j['bytes']) and not payload.lstrip().lower().startswith((b'<!doctype',b'<html')),"Cached test invalid")
            return dict(j,sha256=sha(path),verified_bytes=len(payload),reused=True)
        for attempt in range(3):
            try:
                r=fetch(j['source_url']); payload=r.content
                require(j['bytes'] is None or len(payload)==j['bytes'],"Published size differs")
                require(b'\0' not in payload and not payload.lstrip().lower().startswith((b'<!doctype',b'<html')),"Not a text test")
                payload.decode('utf-8')
                require(urlparse(r.url).hostname in ('drive.google.com','drive.usercontent.google.com','drive.googleusercontent.com'),"Unexpected download origin")
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('xb') as stream: stream.write(payload)
                return dict(j,sha256=hashlib.sha256(payload).hexdigest(),verified_bytes=len(payload),final_url=r.url)
            except Exception as exc: error=str(exc)
        return dict(j,error=error)
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one,j) for j in plan['jobs']]
        for future in as_completed(futures):
            result=future.result(); results.append(result)
            if len(results)%20==0 or result.get('error'):
                print(json.dumps(dict(done=len(results),total=len(futures),failed=sum('error' in r for r in results),task=result['task'],file=result['name'],error=result.get('error'))),flush=True)
    results.sort(key=lambda v:(v['task'],v['kind'],v['name']))
    Store(ROOT).save(CACHE+"/download_results.json",dict(files=results,failures=[r for r in results if 'error' in r]))
    print(json.dumps(dict(files=len(results),failures=sum('error' in r for r in results)),indent=2))


if __name__=='__main__':
    {'discover':discover,'download':download}[sys.argv[1]]()
