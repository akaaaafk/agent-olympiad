"""Correct one filename-timestamp/year mismatch using dated tournament evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard
from scripts.repair_data_catalog import Store,provenance
from scripts.repair_iol_sources_20260913 import read,sha,require

PID='debatebench_d_oxbridge_3_round_3_cvr_cr_box_df_4_vid2txt_Jan-08-2025_-13_full'
PATH='data/benchmarks/debatebench/benchmark.json'
CACHE='data/.cache/debate_event_year_20260913/'
RAW='data/raw/debatebench/event_year_verified_20260913/'
REPORT='data/benchmarks/debate_event_year_repair_20260913.json'
URL='https://www.achteminute.de/en/20201109/zagreb-wins-doxbridge-iii/'


def prepare():
    store=Store(ROOT);before=next(r for r in read(ROOT/PATH) if r['problem_id']==PID)
    require(before['year']==2025,'Unexpected current year')
    response=requests.get(URL,timeout=40);response.raise_for_status()
    article=BeautifulSoup(response.content,'html.parser').get_text(' ',strip=True)
    require('7th and 8th of November 2020' in article,'Dated event evidence missing')
    normalize=lambda s:' '.join(s.replace('“','"').replace('”','"').split())
    require(normalize(before['motion']) in normalize(article),'Round motion not corroborated')
    require('Doxbridge III' in article and 'R3:' in article,'Event/round heading missing')
    article_path=CACHE+'tournament_report.html';store.save_text(article_path,response.content.decode('utf-8'))
    evidence=dict(event='Doxbridge 3: Return of the King',round=3,event_year=2020,event_dates=['2020-11-07','2020-11-08'],
        source_url=URL,source_type='contemporaneous tournament report',report_file=RAW+'tournament_report.html',report_sha256=sha(ROOT/article_path),
        official_round_motion_url=before['source_url'],official_motion_snapshot=before['source_review']['motion_source']['archived_snapshot'],
        identity_basis='Event name and exact round-3 motion agree with the official round archive.',
        correction='The Jan-08-2025 timestamp in the preserved transcript filename is not used as the event year.',
        scores_and_speaker_identity_not_recertified=True)
    ev_cache=CACHE+'event_year.json';store.save(ev_cache,evidence)
    row=deepcopy(before);row['year']=2020
    row['source_review']['event_year_evidence']=RAW+'event_year.json'
    row['source_review']['motion_source'].update(year=2020,year_evidence='dated tournament report corroborated by event and exact official round motion')
    if 'rubric_reuse' in row['evaluation']:
        row['evaluation']['rubric_reuse']['target_year']=2020
    new=[]
    for source,name,mime in [(article_path,'tournament_report.html','text/html'),(ev_cache,'event_year.json','application/json')]:
        dest=RAW+name;new.append(dict(source=source,destination=dest,sha256=sha(ROOT/source)))
        row['assets'].append(dict(path=dest,mime_type=mime,role='judge_only',sha256=new[-1]['sha256']))
    provenance(row)
    plan=dict(before=before,after=row,new_files=new,expected_benchmark_sha256=sha(ROOT/PATH),evidence=evidence)
    store.save(CACHE+'plan.json',plan);print(json.dumps(dict(problem_id=PID,before=2025,after=2020)))


def apply():
    plan=read(ROOT/CACHE/'plan.json');store=Store(ROOT)
    require(not (ROOT/REPORT).exists(),'Already applied')
    require(sha(ROOT/PATH)==plan['expected_benchmark_sha256'],'Benchmark changed')
    rows=deepcopy(store.read(PATH)); originals=deepcopy(rows)
    before=plan['before'];row=plan['after']
    protected={a['path']:a['sha256'] for a in before['assets']}
    cards={l:deepcopy(store.read(f'data/{l}/task_cards.json')) for l in ('base','last_exam')};old_cards=deepcopy(cards)
    scores=deepcopy(store.read('data/rubrics/task_scorecards/debatebench.json'));old_scores=deepcopy(scores)
    text_writes={}
    for layout in cards:
        c=next(c for c in cards[layout]['tasks'] if c['task_id']=='debatebench/'+PID)
        folder=ROOT/'data'/layout/c['source_repo_path']/'base/input'
        for p in folder.rglob('*'):
            if p.is_file() and p.name!='task_sop.md':protected[p.relative_to(ROOT).as_posix()]=sha(p)
        sop=folder/'task_sop.md';old=sop.read_text(encoding='utf-8');require(old.count('Edition: 2025')==1,'Unexpected task SOP')
        text_writes[sop.relative_to(ROOT).as_posix()]=old.replace('Edition: 2025','Edition: 2020')
        c['year']=2020
        if layout=='base': c['evaluation']=deepcopy(row['evaluation'])
        else: ref_path=f"data/last_exam/{c['source_repo_path']}/eval/reference.json"
    ref=deepcopy(store.read(ref_path));ref['evaluation']=deepcopy(row['evaluation'])
    for p in ('data/base/input_asset_manifest.json','data/last_exam/input_asset_manifest.json','data/benchmarks/index.json'):
        protected[p]=sha(ROOT/p)
    for track in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if track['benchmark_path']!=PATH:protected[track['benchmark_path']]=sha(ROOT/track['benchmark_path'])
    for f in plan['new_files']:
        require(not (ROOT/f['destination']).exists() and sha(ROOT/f['source'])==f['sha256'],'New source mismatch')
    report=dict(status='applying',problem_id=PID,previous_year=2025,event_year=2020,backup=store.backup.relative_to(ROOT).as_posix(),
        filename_and_id_preserved=True,answers_scores_readiness_unchanged=True)
    store.finish(report)
    for f in plan['new_files']:store.save_text(f['destination'],(ROOT/f['source']).read_bytes().decode('utf-8'))
    for p,t in text_writes.items():store.save_text(p,t)
    target=next(r for r in rows if r['problem_id']==PID);target.clear();target.update(row)
    target=next(s for s in scores['records'] if s['problem_id']==PID);target.clear();target.update(scorecard(row,ROOT))
    store.save(PATH,rows);store.save('data/rubrics/task_scorecards/debatebench.json',scores);store.save(ref_path,ref)
    for l in cards:store.save(f'data/{l}/task_cards.json',cards[l])
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected file changed')
    require([r for r in rows if r['problem_id']!=PID]==[r for r in originals if r['problem_id']!=PID],'Other debates changed')
    require([r for r in scores['records'] if r['problem_id']!=PID]==[r for r in old_scores['records'] if r['problem_id']!=PID],'Other scorecards changed')
    for l in cards:require([c for c in cards[l]['tasks'] if c['task_id']!='debatebench/'+PID]==[c for c in old_cards[l]['tasks'] if c['task_id']!='debatebench/'+PID],'Other cards changed')
    for key in ('gold_label','total_points','problem_description','title','source_file','solution_file','split','license'):
        require(before[key]==row[key],'Protected field changed')
    require(before['evaluation']['status']==row['evaluation']['status'],'Readiness changed')
    require(read(ROOT/PATH)==rows,'Readback differs')
    for f in plan['new_files']:require(sha(ROOT/f['destination'])==f['sha256'],'Archived evidence bytes differ')
    report.update(status='completed',protected_files_unchanged=len(protected),source_evidence=plan['evidence'])
    store.save(REPORT,report);store.finish(report);print(json.dumps({k:v for k,v in report.items() if k!='source_evidence'},indent=2))


def finalize_newline_recovery():
    """Only finish the known interrupted apply; reject all non-newline source drift."""
    plan=read(ROOT/CACHE/'plan.json');store=Store(ROOT)
    require(not (ROOT/REPORT).exists(),'Already finalized')
    original_backup='data/excluded/integrity_repair_20260913T194546Z'
    manifest=read(ROOT/original_backup/'manifest.json')
    require(manifest['report']['problem_id']==PID and manifest['report']['status']=='applying','Unexpected interrupted operation')
    require(next(r for r in read(ROOT/PATH) if r['problem_id']==PID)==plan['after'],'Canonical row changed after interruption')
    for f in plan['new_files']:
        original=(ROOT/f['source']).read_bytes();current=(ROOT/f['destination']).read_bytes()
        require(sha(ROOT/f['source'])==f['sha256'],'Cached evidence changed')
        require(current in (original,original.replace(b'\r\n',b'\n').replace(b'\r',b'\n')),'Difference is not newline-only')
    for f in plan['new_files']:
        store.save_text(f['destination'],(ROOT/f['source']).read_bytes().decode('utf-8'))
        require(sha(ROOT/f['destination'])==f['sha256'],'Evidence hash still differs')
    row=plan['after']
    scores=read(ROOT/'data/rubrics/task_scorecards/debatebench.json')
    require(next(s for s in scores['records'] if s['problem_id']==PID)==scorecard(row,ROOT),'Scorecard differs')
    for a in row['assets']:require(sha(ROOT/a['path'])==a['sha256'],'Source asset changed')
    for layout in ('base','last_exam'):
        card=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']=='debatebench/'+PID)
        require(card['year']==2020,'Card year differs')
        folder=ROOT/'data'/layout/card['source_repo_path']/'base/input'
        require('Edition: 2020\n' in (folder/'task_sop.md').read_text(encoding='utf-8'),'Task year differs')
        if layout=='base':require(card['evaluation']==row['evaluation'],'Evaluation differs')
        else:require(read(folder.parent.parent/'eval/reference.json')['evaluation']==row['evaluation'],'Reference differs')
    changes=[]
    for p in (ROOT/original_backup).rglob('*'):
        if not p.is_file() or p.name=='manifest.json':continue
        target=p.relative_to(ROOT/original_backup).as_posix()
        changes.append(dict(path=target,before_sha256=sha(p),after_sha256=sha(ROOT/target)))
    for f in plan['new_files']:changes.append(dict(path=f['destination'],before_sha256=None,after_sha256=f['sha256']))
    report=dict(status='completed',problem_id=PID,previous_year=2025,event_year=2020,backup=original_backup,
        newline_recovery_backup=store.backup.relative_to(ROOT).as_posix(),filename_and_id_preserved=True,
        answers_scores_readiness_unchanged=True,source_evidence=plan['evidence'],source_hashes_and_projections_verified=True,
        recovery_note='Original CRLF source bytes restored after the first apply normalized line endings. No canonical scoring/data rollback.')
    manifest.update(changed_files=changes,report=report)
    store.save(original_backup+'/manifest.json',manifest);store.save(REPORT,report);store.finish(report)
    print(json.dumps({k:v for k,v in report.items() if k!='source_evidence'},indent=2))


if __name__=='__main__':{'prepare':prepare,'apply':apply,'finalize-newline-recovery':finalize_newline_recovery}[sys.argv[1]]()
