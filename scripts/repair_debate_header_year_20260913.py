"""Recover explicit archived motion headings and corroborate Natolin's year.

No motion is inferred from debate arguments; background slides remain unresolved.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re
import sys
import requests
from bs4 import BeautifulSoup
from scripts.repair_iol_sources_20260913 import ROOT,read,sha,require
from scripts.repair_data_catalog import Store,provenance
sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard

PATH='data/benchmarks/debatebench/benchmark.json'
CACHE='data/.cache/debate_header_year_20260913/'
RAW='data/raw/debatebench/header_year_review_20260913/'
REPORT='data/benchmarks/debate_header_year_repair_20260913.json'
PREFIX='debatebench_The Natolin European Round Robin Debating Championships Round '
CAMBRIDGE='debatebench_Cambridge IV 2020 Round 1'
SELECTED={PREFIX+str(n) for n in range(1,6)}|{CAMBRIDGE}
EVENT='https://www2.coleurope.eu/events/european-round-robin-debating-championships'
ARTICLE='https://www.achteminute.de/en/20190709/tel-aviv-wins-european-round-robin/'
CAMBRIDGE_SOURCE='https://tokyodebate.github.io/motions/international/CambridgeIV.html'
LIMIT='Only the explicitly stated archived motion has been recovered; the complete original background slide and tournament input packet are not certified. No speaker arguments or completed speeches are contestant inputs.'


def header_motion(pid,text):
    if pid==CAMBRIDGE:
        m=re.match(r'<pm>\s*Okay\. So the motion for the house is (this house regrets the decline of tightly integrated families\.)',text,re.I)
        require(m is not None,'Cambridge motion introduction drift')
        return m[1]
    m=re.match(r'Motion:\s*(.*?)\s*<pm>',text,re.S|re.I)
    require(m is not None and pid in {PREFIX+str(n) for n in (1,2,3)},'No explicit pre-speech motion heading')
    return ' '.join(m[1].split())


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Frozen plan exists')
    store=Store(ROOT);rows=read(ROOT/PATH);sources=[];texts={}
    # The public organizer page was read using the web reader. Direct requests
    # returned 403; do not mislabel our source-review note as its original HTML.
    primary=dict(source_url=EVENT,source_type='review_note_from_web_reader_not_original_html',
        page_title='European Round Robin Debating Championships',organizer='College of Europe in Natolin',
        event_start='2019-07-05',event_end='2019-07-07',displayed_competition_dates=['2019-07-06','2019-07-07'],
        source_excerpt='On 5-7 July 2019',reviewed_at_utc=store.stamp,direct_http_status=403,
        organizer_linked_recordings=['https://www.youtube.com/watch?v=m-fMM_4Lw2U','https://www.youtube.com/watch?v=aV5dQ4hb-vA'],
        recordings_played=False)
    cp=CACHE+'event_source_review.json';store.save(cp,primary)
    sources.append(dict(key='event',url=EVENT,cache_path=cp,path=RAW+'event_source_review.json',sha256=sha(ROOT/cp),mime_type='application/json',checked_at_utc=store.stamp))
    for key,url in [('report',ARTICLE),('cambridge',CAMBRIDGE_SOURCE)]:
        response=requests.get(url,timeout=(8,20));response.raise_for_status();path=CACHE+key+'.html'
        store.save_text(path,response.content.decode('utf-8'));require(sha(ROOT/path)==hashlib.sha256(response.content).hexdigest(),'HTML bytes drift')
        texts[key]=BeautifulSoup(response.content,'html.parser').get_text(' ',strip=True)
        sources.append(dict(key=key,url=url,cache_path=path,path=RAW+key+'.html',sha256=sha(ROOT/path),mime_type='text/html',checked_at_utc=store.stamp))
    require('Jul 9th, 2019' in texts['report'] and 'first edition' in texts['report'],'Contemporaneous report identity absent')
    require('Cambridge IV 2020' in texts['cambridge'],'Cambridge event heading absent')
    compact=lambda s:re.sub(r'[^a-z0-9]','',s.casefold())
    # A report typo ('Beli eves') is ignored only for this corroboration; the
    # original transcript heading, not the report, supplies public wording.
    for n in (1,2,3):
        r=next(r for r in rows if r['problem_id']==PREFIX+str(n));t=(ROOT/r['solution_file']).read_text(encoding='utf-8-sig');motion=header_motion(r['problem_id'],t)
        needle=compact(motion).replace('thishouse','th',1)
        require(needle in compact(texts['report']).replace('thishouse','th'),'Natolin header not corroborated')
    require('THR the decline of tightly integrated families.' in texts['cambridge'],'Cambridge round-1 corroboration absent')
    updates=[];public_texts={};protected={}
    for before in rows:
        pid=before['problem_id']
        if pid not in SELECTED:continue
        row=deepcopy(before);t=(ROOT/row['solution_file']).read_text(encoding='utf-8-sig')
        for a in before['assets']:protected[a['path']]=sha(ROOT/a['path'])
        natolin=pid!=CAMBRIDGE
        evidence=[s for s in sources if (s['key']!='cambridge')==natolin]
        review=dict(event_date_basis='organizer event page, corroborated by the contemporaneous first-edition report' if natolin else 'unchanged filename event year; explicit spoken motion corroborated by a round-organized debate-society archive',
            source_evidence=[{k:v for k,v in s.items() if k!='cache_path'} for s in evidence],
            identity_basis='Same named Natolin tournament series; exact pre-speech headings in rounds 1-3 agree with the report, which also lists rounds 4-5. Round 4 wealth and round 5 Iran-policy subject matter were read for consistency, not used to invent motion wording.' if natolin else 'Canonical event/round title and explicit introductory motion sentence.',
            original_transcript=before['solution_file'],original_transcript_sha256=sha(ROOT/before['solution_file']),
            scores_speakers_and_full_video_not_recertified=True)
        if natolin:
            require(before['year']==2017,'Unexpected old Natolin year');row['year']=2019
            review.update(previous_year=2017,event_year=2019,event_dates=['2019-07-05','2019-07-07'])
            if row['evaluation'].get('rubric_reuse'):row['evaluation']['rubric_reuse']['target_year']=2019
        recovered=pid==CAMBRIDGE or pid in {PREFIX+str(n) for n in (1,2,3)}
        if recovered:
            motion=header_motion(pid,t);number='cambridge_round1' if pid==CAMBRIDGE else 'natolin_round'+pid[-1]
            public=RAW+number+'_motion.txt';payload='Motion\n\n'+motion+'\n\n'+LIMIT+'\n'
            row.update(motion=motion,source_file=public,problem_description=payload.rstrip('\n'),source_visibility='agent_visible_motion_only')
            public_texts[public]=payload
            row['assets'].append(dict(path=public,role='agent_visible',mime_type='text/plain',sha256=hashlib.sha256(payload.encode()).hexdigest()))
            row['source_review']['motion_recovered']=True
            review.update(motion_source_kind='explicit_spoken_introductory_motion' if pid==CAMBRIDGE else 'explicit_pre_speech_motion_header',
                motion=motion,full_background_slide_recovered=False,motion_inferred_from_arguments=False)
            row['evaluation']['limitations']=[s for s in row['evaluation']['limitations'] if s!='An event-and-round verified original motion/infoslide packet is still missing.']+[LIMIT]
            row['asset_policy']='Only the explicit archived motion and its completeness limitation are contestant inputs. Human speeches, historical scores and corroborating source pages remain judge-only.'
        for s in evidence:row['assets'].append(dict(path=s['path'],role='judge_only',mime_type=s['mime_type'],sha256=s['sha256']))
        row['source_review']['header_year_review']=review;row['evaluation']['header_year_review']=deepcopy(review)
        provenance(row);updates.append(dict(before=before,after=row))
    require(len(updates)==6 and len(public_texts)==4,'Unexpected scope')
    plan=dict(before_rows=rows,updates=updates,protected=protected,public_texts=public_texts,sources=sources,expected_benchmark_sha256=sha(ROOT/PATH),
        summary='Natolin: 5 event years corrected from 2017 to 2019. Four explicit motions recovered from original transcripts (Natolin 1-3, Cambridge 1), corroborated independently. No inferred infoslides, gold, score or readiness changes.')
    store.save(CACHE+'plan.json',plan);print(json.dumps(dict(records=6,year_corrections=5,explicit_motions=4)))


def apply():
    require(not (ROOT/REPORT).exists(),'No blind replay');plan=read(ROOT/CACHE/'plan.json');require(sha(ROOT/PATH)==plan['expected_benchmark_sha256'],'Canonical drift')
    store=Store(ROOT);rows=deepcopy(plan['before_rows']);writes=dict(plan['public_texts']);protected=deepcopy(plan['protected'])
    for s in plan['sources']:
        require(sha(ROOT/s['cache_path'])==s['sha256'] and not (ROOT/s['path']).exists(),'Evidence occupied or changed')
        writes[s['path']]=(ROOT/s['cache_path']).read_bytes().decode('utf-8')
    cards={l:read(ROOT/f'data/{l}/task_cards.json') for l in ('base','last_exam')};manifests={l:read(ROOT/f'data/{l}/input_asset_manifest.json') for l in cards}
    scores=read(ROOT/'data/rubrics/task_scorecards/debatebench.json')
    for u in plan['updates']:
        a,b=u['before'],u['after'];pid=b['problem_id'];task='debatebench/'+pid
        for layout in cards:
            c=next(c for c in cards[layout]['tasks'] if c['task_id']==task);relative=c['source_repo_path'];folder=f'data/{layout}/{relative}/base/input/'
            for p in (ROOT/folder).iterdir():
                if p.is_file() and p.name not in ('problem.md','task_sop.md'):protected[p.relative_to(ROOT).as_posix()]=sha(p)
            require((ROOT/folder/'problem.md').read_text(encoding='utf-8')==a['problem_description']+'\n','Old prompt drift')
            if a['year']!=b['year']:
                sop=(ROOT/folder/'task_sop.md').read_text(encoding='utf-8');require(sop.count('Edition: 2017')==1,'Unexpected old edition')
                writes[folder+'task_sop.md']=sop.replace('Edition: 2017','Edition: 2019');c['year']=2019
            else:protected[folder+'task_sop.md']=sha(ROOT/folder/'task_sop.md')
            writes[folder+'problem.md']=b['problem_description']+'\n'
            for asset in b['assets']:
                if asset['role']!='agent_visible':continue
                name=Path(asset['path']).name;require(not (ROOT/folder/name).exists(),'Public file occupied')
                writes[folder+name]=plan['public_texts'][asset['path']]
                entry=dict(name=name,path=('input/' if layout=='base' else 'base/input/')+name)
                if layout=='base':entry['description']='Agent-visible input'
                files=c['input_files'] if layout=='base' else c['input']['files'];files.append(entry);files.sort(key=lambda f:f['path'])
                manifests[layout]['files'].append(dict(task_id=task,source=asset['path'],sha256=asset['sha256'],staged=relative+'/base/input/'+name))
            if layout=='base':c['evaluation']=deepcopy(b['evaluation'])
            else:
                rp=f'data/last_exam/{relative}/eval/reference.json';ref=read(ROOT/rp);ref['evaluation']=deepcopy(b['evaluation']);writes[rp]=ref
        r=next(r for r in rows if r['problem_id']==pid);r.clear();r.update(b)
        s=next(s for s in scores['records'] if s['problem_id']==pid);s.clear();s.update(scorecard(b,ROOT))
    writes.update({PATH:rows,'data/rubrics/task_scorecards/debatebench.json':scores})
    for l in cards:writes.update({f'data/{l}/task_cards.json':cards[l],f'data/{l}/input_asset_manifest.json':manifests[l]})
    for t in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if t['benchmark_path']!=PATH:protected[t['benchmark_path']]=sha(ROOT/t['benchmark_path'])
    for p,h in protected.items():require(sha(ROOT/p)==h,'Preflight protected drift')
    for p in plan['public_texts']:require(not (ROOT/p).exists(),'Source output occupied')
    report=dict(status='applying',backup=store.backup.relative_to(ROOT).as_posix(),records=6,year_corrections=5,explicit_motions=4,record_count_change=0,readiness_promotions=0,summary=plan['summary']);store.finish(report)
    for p,v in writes.items():store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected drift')
    report.update(status='completed',verification=verify(),protected_files_unchanged=len(protected));store.save(REPORT,report);store.finish(report);print(json.dumps(report,indent=2))


def expected_rows(plan):
    expected=deepcopy(plan['before_rows']);changed={u['after']['problem_id']:u['after'] for u in plan['updates']}
    return [changed.get(r['problem_id'],r) for r in expected]


def verify():
    plan=read(ROOT/CACHE/'plan.json');require(read(ROOT/PATH)==expected_rows(plan),'Canonical or unrelated row drift')
    cam=next(s for s in plan['sources'] if s['key']=='cambridge')
    section=BeautifulSoup((ROOT/cam['path']).read_bytes(),'html.parser').find('section',id='cambridge-iv-2020')
    require(section is not None,'Cambridge edition missing')
    first=section.find('section',id='r1')
    require(first is not None and 'THR the decline of tightly integrated families.' in first.get_text(' ',strip=True),'Wrong Cambridge round')
    for p,h in plan['protected'].items():require(sha(ROOT/p)==h,'Original source changed')
    for u in plan['updates']:
        a,b=u['before'],u['after'];pid=b['problem_id']
        for k in ('title','gold_label','solution_file','total_points','split','license','team_size'):require(a.get(k)==b.get(k),'Protected record field changed')
        for k in ('status','historical_reference_path','historical_score_identity'):require(a['evaluation'].get(k)==b['evaluation'].get(k),'Historical scoring/readiness changed')
        for asset in b['assets']:require(sha(ROOT/asset['path'])==asset['sha256'],'Asset drift')
        for layout in ('base','last_exam'):
            c=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']=='debatebench/'+pid);folder=ROOT/'data'/layout/c['source_repo_path']/'base/input'
            require(c['year']==b['year'],'Derived year drift')
            require(f"Edition: {b['year']}\n" in (folder/'task_sop.md').read_text(encoding='utf-8'),'SOP year drift')
            require((folder/'problem.md').read_text(encoding='utf-8')==b['problem_description']+'\n','Derived prompt drift')
            for asset in b['assets']:
                if asset['role']=='agent_visible':require(sha(folder/Path(asset['path']).name)==asset['sha256'],'Staged source drift')
            ev=c['evaluation'] if layout=='base' else read(folder.parent.parent/'eval/reference.json')['evaluation'];require(ev==b['evaluation'],'Evaluation projection drift')
    return dict(records=6,year_corrections=5,explicit_motions=4,transcripts_and_historical_scores_unchanged=True,no_background_slides_invented=True)


if __name__=='__main__':{'prepare':prepare,'apply':apply,'verify':lambda:print(verify())}[sys.argv[1]]()
