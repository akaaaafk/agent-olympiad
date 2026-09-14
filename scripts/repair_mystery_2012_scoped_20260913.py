"""Recover two scoped standalone pages and correct one wrong round source privately."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image,ImageFont
from scripts.repair_mystery_2012_static_20260913 import snapshot,css_graph,check_css,sanitize as static_html,localize,SCRIPTS
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2012_scoped_20260913/'
RAW='data/raw/mystery_hunt/separated_2012_scoped_20260913/'
REPORT='data/benchmarks/mystery_2012_scoped_repair_20260913.json'
SELECTED={f'mystery_hunt_{n:05}' for n in (1543,1558,1597)}
SOURCE_ONLY='mystery_hunt_01543'
CID='mystery_hunt'
NOTES={
 1543:'The legacy source was the Borbonicus & Bodley main homepage, not A Circus Line. The correct official round HTML is now retained on the judge side with its original bytes. Its puzzle list and image are script populated and archive solved/release state is not an initial-state contract. No empty replacement puzzle, all-unlocked state, other task answers or public packet is manufactured. Public packet and staged round behavior remain pending; this repair corrects provenance only.',
 1558:'This restores only the explicit archived Investigator report, photograph and diagram. The original task requires physical electronic components from HQ. Those components, firmware, observations and host interactions have not been recovered, synthesized or executed; the page alone does not make the task runnable.',
 1597:'This is the complete standalone archived Betsy Johnson letter/review attached to this existing letter record. Its source title and h2 are empty and remain empty. The post-show narrative is not injected into a preceding round, interpreted as an initial release rule, or completed with other tasks or answers. Original emphasis, signature and six-rings review rating remain puzzle text, not canonical scoring.',
}


def sanitize(data,url,n):
    if n==1558:return static_html(data,url)
    require(n==1597,'Source-only page must not be sanitized into public input');s=BeautifulSoup(data,'html.parser');scripts=s.find_all('script');require(len(scripts)==4 and [t.get('src') for t in scripts]==[None,'../../points.js','../../shortcuts.js','/checkanswer.js'] and scripts[0].get_text()=='this.depth="../../";','Letter script drift');require(s.title.get_text()=='' and s.find('h2').get_text()=='','Untitled letter drift');payload=SCRIPTS.sub(b'',data)
    token=b'<link rel="shortcut icon" href="../../favicon.ico" />';require(payload.count(token)==1,'Favicon drift');payload=payload.replace(token,b'');require(payload.count(b'href="../.."')==1,'Navigation drift');payload=payload.replace(b'href="../.."',b'data-archive-href="../.."');styles={}
    from urllib.parse import urljoin
    for i,link in enumerate(s.find_all('link',rel='stylesheet')):
        ref=link['href'];require(ref in ('../../subpage.css','style.css'),'Letter style drift');name=f'style-{i}.css';styles[name]=urljoin(url,ref);payload=payload.replace(('href="'+ref+'"').encode(),('href="'+name+'"').encode())
    require(len(styles)==2 and not re.search(rb'url\(',payload),'Unexpected letter dependencies');return payload,styles


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==3,'Selection drift');snapshots={};prepared={};urls=set()
    for old in chosen:
        pid=old['problem_id'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';urls.add(url)
        if pid==SOURCE_ONLY:continue
        payload,styleurls=sanitize((ROOT/old['source_file']).read_bytes(),url,int(pid[-5:]));payload,deps=localize(payload,url);styles,cssdeps,allstyles=css_graph(styleurls,snapshots);require(not(set(deps)&set(cssdeps)),'Asset collision');deps.update(cssdeps)
        for target in cssdeps.values():
            if target.startswith('https://fonts.gstatic.com/'):
                family=urlparse(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
        urls.update(deps.values());prepared[pid]=(payload,styles,styleurls,allstyles,deps)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(urls-set(snapshots)))})
    updates=[];copies=[]
    for old in chosen:
        row=deepcopy(old);pid=old['problem_id'];n=int(pid[-5:]);url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';source=ROOT/old['source_file'];remote=ROOT/snapshots[url]['path'];assets=deepcopy(old['assets']);added=[]
        if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
        def add(data,name,mime,role='agent_visible'):
            area='input' if role=='agent_visible' else 'judge';p=ROOT/CACHE/pid/area/name;p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():require(p.read_bytes()==data,'Prepared byte drift')
            else:
                with p.open('xb') as out:out.write(data)
            dest=RAW+pid+'/'+area+'/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));added.append(dict(path=dest,role=role,mime_type=mime,sha256=sha(p)));return dest
        rev=dict(batch='mystery_2012_scoped_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),answers_and_scores_unchanged=True)
        note=NOTES[n]
        if pid==SOURCE_ONLY:
            a=BeautifulSoup(source.read_bytes(),'html.parser');b=BeautifulSoup(remote.read_bytes(),'html.parser');require(a.title.get_text()=='Borbonicus & Bodley' and b.title.get_text()=='A Circus Line' and b.body['onload']=='load_a_circus_line()','Source mismatch classification drift');require(not b.find(id='index-image').get_text(strip=True) and not b.find(id='puzzle-list').get_text(strip=True),'Dynamic round drift');source_file=add(remote.read_bytes(),'round-original.html','text/html','judge_only');title='A Circus Line';rev.update(source_correction_only=True,public_packet_review_pending=True,legacy_wrong_page_title=a.title.get_text(),correct_publisher_title=b.title.get_text())
        else:
            require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher source drift');payload,styles,styleurls,allstyles,deps=prepared[pid];source_file=add(payload,'puzzle.html','text/html')
            for name,data in styles.items():add(data,name,'text/css')
            for name,target in sorted(deps.items()):
                p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
                if ext in ('.jpg','.png','.gif'):
                    with Image.open(p) as im:im.verify()
                elif ext=='.ttf':ImageFont.truetype(str(p),16).getmask('Archive')
                add(p.read_bytes(),name,{'.jpg':'image/jpeg','.png':'image/png','.gif':'image/gif','.ttf':'font/ttf','.txt':'text/plain'}[ext])
            folder=ROOT/CACHE/pid/'input';allowed={p.resolve() for p in folder.iterdir()};clean=check_html(folder/'puzzle.html',allowed)
            for name in styles:check_css(folder/name,allowed)
            title=clean.title.get_text(strip=True) or clean.find('h3').get_text(strip=True);rev.update(dependency_urls=deps,stylesheet_urls=styleurls,all_stylesheet_urls=allstyles,font_binary_historical_version_certified=False)
            note+=' The original CSS and named font families are localized; current publisher font binaries are not certified historical revisions. Archive navigation and points/answer-checking scripts are inactive.'
        row.update(source_url=url,source_file=source_file,assets=added+assets,problem_description='# '+title+'\n\n'+('No reviewed public packet is available for the dynamic round.\n\n' if pid==SOURCE_ONLY else 'Open `puzzle.html` for the original standalone page and its images.\n\n')+'Archive limitation: '+note,source_visibility='corrected_archive_source_judge_only_public_packet_pending' if pid==SOURCE_ONLY else 'explicit_scoped_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),**rev);provenance(row);updates.append(dict(before=old,after=row))
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=updates,copies=copies,publisher_snapshots=snapshots));print(json.dumps(dict(records=3,public_files=sum('/input/' in c['destination'] for c in copies),judge_files=sum('/judge/' in c['destination'] for c in copies),publisher_files=len(snapshots))))


def verify():
    plan=read(ROOT/CACHE/'plan.json');rows={r['problem_id']:r for r in read(ROOT/PATH)}
    for u in plan['updates']:
        row=u['after'];pid=row['problem_id'];require(rows[pid]==row,'Canonical readback differs');require(sha(ROOT/u['before']['source_file'])==row['source_review']['original_sha256'],'Original source changed')
        for k in ('gold_label','total_points','year','split','license','team_size','title'):require(row[k]==u['before'][k],'Protected metadata changed')
        require(row['evaluation']['status']==u['before']['evaluation']['status'],'Readiness changed')
        for layout in ('base','last_exam'):
            card=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']==CID+'/'+pid);folder=ROOT/'data'/layout/card['source_repo_path']/'base/input';allowed={folder/Path(a['path']).name for a in row['assets'] if a['role']=='agent_visible'}
            if pid==SOURCE_ONLY:require(not allowed and not(folder/'puzzle.html').exists(),'Dynamic packet published')
            else:
                check_html(folder/'puzzle.html',{p.resolve() for p in allowed})
                for p in allowed:
                    if p.suffix=='.css':check_css(p,{x.resolve() for x in allowed})
            require((folder/'problem.md').read_text(encoding='utf-8')==row['problem_description']+'\n','Prompt drift');names={p.name for p in allowed}|{'problem.md','task_sop.md','input_environment_spec.md','ground_rules.md','collaboration.md'};require({p.name for p in folder.iterdir()}==names,'Unlisted input')
            for a in row['assets']:
                require(sha(ROOT/a['path'])==a['sha256'],'Source asset drift')
                if a['role']=='agent_visible':require(sha(folder/Path(a['path']).name)==a['sha256'],'Staged bytes differ')
    return dict(source_packets=2,source_only_corrections=1,task_input_copies=4,explicit_allowlists_valid=True,original_sources_unchanged=True,legacy_answers_not_recertified=True,dynamic_round_public_packet_still_pending=True)


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;m.verify=verify;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for n,height in [(1558,3600),(1597,1900)]:
        pid=f'mystery_hunt_{n:05}';page=ROOT/CACHE/pid/'input/puzzle.html';dest=out/(pid+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+str(height),'--virtual-time-budget=1500',page.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(pid,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(verify()))
    else:raise ValueError(mode)
