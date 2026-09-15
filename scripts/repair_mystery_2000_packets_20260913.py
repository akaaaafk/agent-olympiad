"""Curated 2000 HTML/media repair; keep historical interaction and answer gaps explicit."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard
from scripts.repair_data_catalog import Store,provenance
from scripts.repair_mystery_hunt_sources_20260913 import download,check_html
from scripts.repair_iol_sources_20260913 import read,sha,require

CID='mystery_hunt'; PATH=f'data/benchmarks/{CID}/benchmark.json'
CACHE='data/.cache/mystery_2000_packets_20260913/'
RAW='data/raw/mystery_hunt/separated_2000_20260913/'
REPORT='data/benchmarks/mystery_2000_packets_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (78,80,82,89,94,95,96,102,103,105,106,112,113,116,118,124)}
LIMITS={
 82:'Flight itineraries refer to January 2000; current schedules are not a substitute for historical information.',
 95:'The journal depends on historical campus landmarks and physical navigation; these are not reproduced.',
 96:'Objects must be accepted by a live host before a clue is released. No objects, host decisions or later clues are invented.',
 102:'Historical phone-call interaction with participants is absent; no telephone call is placed.',
 106:'The publisher post-hunt addendum reproduces a poem originally collected at a physical handout location. It is retained as an explicitly labeled archival reconstruction, not evidence of original at-start access.',
 112:'The word isolation is part of the scrambled clue, not a result disclosure; it is preserved.',
 113:'The word RISING is part of the source word list, not a result disclosure; it is preserved.',
 118:'The coordinate puzzle may require historical local references; no map or coordinate semantics are inferred.'}


def sanitize(data):
    edits=[]
    for pattern,label in [
      (rb'<script type="module" src="/checkanswer\.js"></script>','archive answer-checking script'),
      (rb'<a href="\.\./\.\./index\.html">Back to hunt</a>','hunt navigation'),
      (rb'<a href="\.\./index\.html">Back to puzzle set</a>','puzzle-set navigation')]:
        matches=list(re.finditer(pattern,data,re.I))
        require(len(matches)==1,'Unexpected archive markup: '+label)
        edits.append(dict(reason=label,removed=matches[0][0].decode('ascii')))
        data=re.sub(pattern,b'',data,flags=re.I)
    return data,edits


def prepare(refresh=False):
    if (ROOT/CACHE/'plan.json').exists():
        require(refresh and sha(ROOT/PATH)==read(ROOT/CACHE/'plan.json')['expected_benchmark_sha256'],'Prepared plan exists or canonical data changed')
    store=Store(ROOT); before=read(ROOT/PATH); chosen=[r for r in before if r['problem_id'] in SELECTED]
    require(len(chosen)==16 and all(r['year']==2000 for r in chosen),'Membership differs')
    urls=set(); media={}
    for row in chosen:
        url='https://puzzles.mit.edu/'+row['puzzle_url']; urls.add(url)
        soup=BeautifulSoup((ROOT/row['source_file']).read_bytes(),'html.parser')
        names=[t['src'] for t in soup.find_all('img')]
        require(all(re.fullmatch(r'[A-Za-z0-9]+\.(?:gif|jpg)',n) for n in names),'Unexpected media path')
        require(len(names)==len(set(names)),'Duplicate media names')
        media[row['problem_id']]=names
        urls.update(urljoin(url,n) for n in names)
    with ThreadPoolExecutor(max_workers=4) as pool: snapshots={r['source_url']:r for r in pool.map(download,sorted(urls))}
    updates=[]; copies=[]; review={}
    for before_row in chosen:
        row=deepcopy(before_row); pid=row['problem_id']; url='https://puzzles.mit.edu/'+row['puzzle_url']
        original=ROOT/row['source_file']; remote=ROOT/snapshots[url]['path']
        require(original.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher content changed')
        payload,edits=sanitize(remote.read_bytes())
        prepared=ROOT/CACHE/pid/'input/puzzle.html'; prepared.parent.mkdir(parents=True,exist_ok=True)
        if prepared.exists(): require(prepared.read_bytes()==payload,'Prepared HTML differs')
        else:
            with prepared.open('xb') as out: out.write(payload)
        public=[]
        def add(source,name,mime):
            dest=RAW+pid+'/input/'+name
            copies.append(dict(source=source.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(source)))
            public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(source)))
        add(prepared,'puzzle.html','text/html')
        for name in media[pid]:
            source=original.parent/name; downloaded=ROOT/snapshots[urljoin(url,name)]['path']
            if source.exists(): require(sha(source)==sha(downloaded),'Publisher image differs')
            else: source=downloaded
            with Image.open(source) as im: im.verify()
            local=prepared.parent/name
            if local.exists(): require(sha(local)==sha(source),'Prepared image differs')
            else:
                with local.open('xb') as out,source.open('rb') as inp: shutil.copyfileobj(inp,out)
            add(local,name,'image/gif' if name.endswith('.gif') else 'image/jpeg')
        clean=check_html(prepared,{p.resolve() for p in prepared.parent.iterdir()})
        note=LIMITS.get(int(pid.rsplit('_',1)[1]),'Historical rule/answer-mechanism equivalence and image/layout-aware evaluation remain uncertified.')
        prompt='# '+clean.title.get_text(strip=True)+'\n\n'
        prompt+='Open `puzzle.html` for the original table, image and monospace layout. The auxiliary text below is not a layout replacement.\n\n'
        public_note='Historical rule/answer-mechanism equivalence and image/layout-aware evaluation remain uncertified.' if pid.endswith(('00112','00113')) else note
        prompt+='Archive limitation: '+public_note+'\n\n'
        body=clean.body.get_text('\n',strip=True).replace('\r\n','\n').replace('\r','\n')
        prompt+='## Source text (layout is in puzzle.html)\n\n'+body
        row.update(source_url=url,source_file=RAW+pid+'/input/puzzle.html',problem_description=prompt,
            assets=public+deepcopy(row['assets']),source_visibility='explicit_static_packet_original_archive_judge_only',
            asset_policy='Only explicit agent_visible HTML/media are contestant inputs. Original archive controls/navigation and all judge references remain excluded. Historical interaction is not reproduced.')
        row['evaluation']['limitations']='Static HTML/media packet recovered; legacy answer targets, historical rules and end-to-end evaluator behavior are not recertified. '+note
        row['source_review']=dict(batch='mystery_2000_packets_20260913',original_source_file=before_row['source_file'],
            original_sha256=sha(original),publisher_html_sha256=sha(remote),publisher_snapshot=snapshots[url]['path'],
            comparison='same content after removing CR bytes; publisher line endings used in derived HTML',
            edits=edits,media_count=len(media[pid]),
            media_missing_from_legacy_archive=[n for n in media[pid] if not (original.parent/n).exists()],
            answers_and_scores_unchanged=True)
        provenance(row);updates.append(dict(before=before_row,after=row));review[pid]=row['source_review']
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,
        publisher_snapshots=snapshots,review=review,excluded_endgame='mystery_hunt_00068 remains gated by full-hunt meta progression')
    store.save(CACHE+'plan.json',plan)
    print(json.dumps(dict(records=16,publisher_files=len(snapshots),public_files=len(copies),media=sum(len(v) for v in media.values())),indent=2))


def render():
    chrome=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    out=ROOT/CACHE/'renders'; out.mkdir(exist_ok=True)
    for pid in sorted(SELECTED):
        page=ROOT/CACHE/pid/'input/puzzle.html'
        height=4000 if pid.endswith('00089') else 3600 if pid.endswith('00103') else 3000 if pid.endswith(('00078','00095','00112')) else 1800
        dest=out/(pid+'.png')
        proc=subprocess.run([chrome,'--headless=new','--disable-gpu','--disable-extensions','--no-first-run',
            '--no-default-browser-check','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1',
            '--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),
            '--window-size=1400,'+str(height),'--virtual-time-budget=1000',page.as_uri()],capture_output=True,timeout=45)
        require(proc.returncode==0 and dest.exists(),'Render failed')
        print(pid,flush=True)


def apply():
    plan=read(ROOT/CACHE/'plan.json'); store=Store(ROOT)
    require(not (ROOT/REPORT).exists(),'Already applied')
    require(sha(ROOT/PATH)==plan['expected_benchmark_sha256'],'Benchmark changed')
    before=deepcopy(store.read(PATH));rows=deepcopy(before)
    cards={layout:deepcopy(store.read(f'data/{layout}/task_cards.json')) for layout in ('base','last_exam')}
    original_cards=deepcopy(cards)
    manifests={layout:deepcopy(store.read(f'data/{layout}/input_asset_manifest.json')) for layout in cards}
    original_manifests=deepcopy(manifests)
    score_path='data/rubrics/task_scorecards/mystery_hunt.json'; scores=deepcopy(store.read(score_path)); old_scores=deepcopy(scores)
    protected={}
    for tree in ['data/raw/external/MIT_Mystery_Hunt','data/rules']:
        protected.update({p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/tree).rglob('*') if p.is_file()})
    for track in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if track['benchmark_path']!=PATH: protected[track['benchmark_path']]=sha(ROOT/track['benchmark_path'])
    payloads=list(plan['copies']);writes={};references={}
    for u in plan['updates']:
        row=u['after']; pid=row['problem_id'];task=CID+'/'+pid
        require(not any(a['role']=='agent_visible' for a in u['before']['assets']),'Unexpected pre-existing public asset')
        for layout in cards:
            card=next(c for c in cards[layout]['tasks'] if c['task_id']==task); rel=card['source_repo_path']
            folder=f'data/{layout}/{rel}/base/input/'
            for p in (ROOT/folder).rglob('*'):
                if p.is_file() and p.name!='problem.md': protected[p.relative_to(ROOT).as_posix()]=sha(p)
            writes[folder+'problem.md']=row['problem_description']+'\n'
            public=[c for c in plan['copies'] if c['destination'].startswith(RAW+pid+'/input/')]
            require(not any(m['task_id']==task for m in manifests[layout]['files']),'Unexpected old input manifest')
            for f in public:
                name=Path(f['destination']).name
                payloads.append(dict(source=f['source'],destination=folder+name,sha256=f['sha256']))
                manifests[layout]['files'].append(dict(task_id=task,source=f['destination'],sha256=f['sha256'],staged=rel+'/base/input/'+name))
                if layout=='base': card['input_files'].append(dict(name=name,path='input/'+name,description='Agent-visible input'))
                else: card['input']['files'].append(dict(name=name,path='base/input/'+name))
            card['source_url']=row['source_url']
            if layout=='base': card.update(evaluation=deepcopy(row['evaluation']));card['input_files'].sort(key=lambda f:f['path'])
            else:
                card['input']['files'].sort(key=lambda f:f['path'])
                rp=f'data/last_exam/{rel}/eval/reference.json';ref=deepcopy(store.read(rp));ref['evaluation']=deepcopy(row['evaluation']);references[rp]=ref
    for f in payloads:
        require(sha(ROOT/f['source'])==f['sha256'],'Prepared file changed')
        require(not (ROOT/f['destination']).exists(),'New destination occupied')
    report=dict(status='applying',records=16,public_source_files=len(plan['copies']),publisher_files=len(plan['publisher_snapshots']),
        backup=store.backup.relative_to(ROOT).as_posix(),answers_scores_readiness_unchanged=True,records_removed=0)
    store.finish(report)
    for f in payloads:
        dest=store.path(f['destination']);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as out,(ROOT/f['source']).open('rb') as inp: shutil.copyfileobj(inp,out)
        store.changes.append(dict(path=f['destination'],before_sha256=None,after_sha256=f['sha256']))
    for p,t in writes.items():store.save_text(p,t)
    for p,v in references.items():store.save(p,v)
    for u in plan['updates']:
        r=next(r for r in rows if r['problem_id']==u['after']['problem_id']);r.clear();r.update(u['after'])
        s=next(s for s in scores['records'] if s['problem_id']==r['problem_id']);s.clear();s.update(scorecard(r,ROOT))
    store.save(PATH,rows);store.save(score_path,scores)
    for layout in cards:
        store.save(f'data/{layout}/task_cards.json',cards[layout]);store.save(f'data/{layout}/input_asset_manifest.json',manifests[layout])
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected file changed: '+p)
    require([r for r in rows if r['problem_id'] not in SELECTED]==[r for r in before if r['problem_id'] not in SELECTED],'Other rows changed')
    require([r for r in scores['records'] if r['problem_id'] not in SELECTED]==[r for r in old_scores['records'] if r['problem_id'] not in SELECTED],'Other scores changed')
    tasks={CID+'/'+p for p in SELECTED}
    for layout in cards:
        require([c for c in cards[layout]['tasks'] if c['task_id'] not in tasks]==[c for c in original_cards[layout]['tasks'] if c['task_id'] not in tasks],'Other cards changed')
        require([m for m in manifests[layout]['files'] if m['task_id'] not in tasks]==original_manifests[layout]['files'],'Other manifests changed')
    for f in payloads:require(sha(ROOT/f['destination'])==f['sha256'],'Copied bytes differ')
    require(read(ROOT/PATH)==rows,'Canonical readback failed')
    report.update(status='completed',protected_files_unchanged=len(protected),verification=verify())
    store.save(REPORT,report);store.finish(report);print(json.dumps(report,indent=2))


def verify():
    plan=read(ROOT/CACHE/'plan.json')
    for u in plan['updates']:
        row=u['after'];pid=row['problem_id']
        for k in ('gold_label','total_points','split','license','team_size','title'):
            require(row[k]==u['before'][k],'Protected metadata changed')
        require(row['evaluation']['status']==u['before']['evaluation']['status'],'Readiness changed')
        require(sha(ROOT/u['before']['source_file'])==row['source_review']['original_sha256'],'Original source changed')
        for layout in ('base','last_exam'):
            card=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']==CID+'/'+pid)
            folder=ROOT/'data'/layout/card['source_repo_path']/'base/input'
            allowed={folder/Path(a['path']).name for a in row['assets'] if a['role']=='agent_visible'}
            check_html(folder/'puzzle.html',{p.resolve() for p in allowed})
            require((folder/'problem.md').read_text(encoding='utf-8')==row['problem_description']+'\n','Prompt differs')
            names={p.name for p in allowed}|{'problem.md','task_sop.md','input_environment_spec.md','ground_rules.md','collaboration.md'}
            require({p.name for p in folder.iterdir()}==names,'Unlisted input file')
            for a in row['assets']:
                require(sha(ROOT/a['path'])==a['sha256'],'Source asset differs')
                if a['role']=='agent_visible': require(sha(folder/Path(a['path']).name)==a['sha256'],'Staged asset differs')
    return dict(source_packets=16,task_input_copies=32,initial_scope_not_extended_to_endgame=True,
                explicit_allowlists_valid=True,original_sources_unchanged=True,legacy_answers_not_recertified=True)


if __name__=='__main__':
    {'prepare':prepare,'refresh':lambda:prepare(True),'render':render,'apply':apply,'verify':lambda:print(json.dumps(verify(),indent=2))}[sys.argv[1]]()
