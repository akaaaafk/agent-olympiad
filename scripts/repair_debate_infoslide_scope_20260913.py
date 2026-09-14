"""Quarantine one published but semantically mismatched background slide."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys
import requests
from scripts.repair_iol_sources_20260913 import ROOT,read,sha,require
from scripts.repair_data_catalog import Store,provenance
from scripts.repair_debatebench_sources_20260913 import verify_motion_source
sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard

PID='debatebench_Astana Open Round 5'
PATH='data/benchmarks/debatebench/benchmark.json'
CACHE='data/.cache/debate_infoslide_scope_20260913/'
PUBLIC='data/raw/debatebench/infoslide_review_20260913/astana_round5_reviewed_motion.txt'
REPORT='data/benchmarks/debate_infoslide_scope_repair_20260913.json'
WARNING=('Source-review limitation: the published Round 5 page pairs this motion with a toy-history background slide whose relevance to the motion is unverified. '
         'That slide is withheld from the active task input and retained in the judge-only original archive. '
         'This does not establish that the original round had no background slide; no replacement slide is invented. '
         'This task remains not_ready for evaluation.')


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Frozen plan already exists')
    store=Store(ROOT);rows=read(ROOT/PATH);before=next(r for r in rows if r['problem_id']==PID)
    source=before['source_review']['motion_source']
    require(source['round']==5 and source['infoslide_status']=='published_present','Unexpected previous source')
    require('ethnic makeup' in before['motion'] and source['infoslide'].startswith('Barbie was first introduced'),'Mismatch evidence changed')
    verify_motion_source((ROOT/source['archived_snapshot']).read_bytes(),source)
    response=requests.get(source['source_url'],timeout=(8,20));response.raise_for_status()
    verify_motion_source(response.content,source)
    snapshot=CACHE+'current_source.html';store.save_text(snapshot,response.content.decode('utf-8'))
    require(sha(ROOT/snapshot)==hashlib.sha256(response.content).hexdigest(),'Source bytes differ')
    row=deepcopy(before);row['infoslide']='';row['source_file']=PUBLIC
    row['problem_description']='Motion\n\n'+before['motion']+'\n\n'+WARNING
    review=dict(status='published_semantic_mismatch_quarantined',original_source_file=before['source_file'],original_sha256=sha(ROOT/before['source_file']),
        original_published_slide=before['infoslide'],replacement_inferred=False,original_round_had_no_slide_inferred=False,
        evidence=dict(source_url=source['source_url'],round_heading='Round 5',modal_id='info_32018',
            archived_snapshot=source['archived_snapshot'],archived_sha256=sha(ROOT/source['archived_snapshot']),
            current_snapshot=snapshot,current_sha256=sha(ROOT/snapshot),checked_at_utc=store.stamp),
        reasoning='The motion concerns national ethnic representation in neighbourhoods, whereas the published slide describes the history of a toy. Same-round extraction is verified; contextual suitability is not.')
    row['source_review']['infoslide_scope_review']=review
    # The nested motion_source is an immutable observation of what the publisher
    # actually displayed; only its suitability for current input is qualified.
    row['evaluation']['infoslide_scope_review']=deepcopy(review)
    row['evaluation']['limitations'].append(WARNING)
    row['asset_policy']='Only the reviewed round motion and explicit source limitation are active contestant inputs. The unverified published background slide, historical speeches and scores are judge-only. No new speech score is inferred.'
    row['assets']=[dict(a,role='judge_only') if a['path']==before['source_file'] else a for a in row['assets']]
    payload=row['problem_description']+'\n'
    row['assets'].append(dict(path=PUBLIC,role='agent_visible',mime_type='text/plain',sha256=hashlib.sha256(payload.encode()).hexdigest()))
    provenance(row)
    protected={a['path']:sha(ROOT/a['path']) for a in before['assets']}
    protected[source['archived_snapshot']]=sha(ROOT/source['archived_snapshot']);protected[snapshot]=sha(ROOT/snapshot)
    store.save(CACHE+'plan.json',dict(before_rows=rows,updates=[dict(before=before,after=row)],protected=protected,
        expected_benchmark_sha256=sha(ROOT/PATH),public_text=payload,
        summary='Astana Round 5: retain the verified motion; quarantine the semantically mismatched published infoslide, preserve original bytes, historical scores and not_ready.'))
    print(json.dumps(dict(records=1,original_slide_preserved=True,replacement_invented=False)))


def apply():
    require(not (ROOT/REPORT).exists(),'No blind replay')
    plan=read(ROOT/CACHE/'plan.json');require(sha(ROOT/PATH)==plan['expected_benchmark_sha256'],'Canonical drift')
    before,row=plan['updates'][0]['before'],plan['updates'][0]['after'];store=Store(ROOT);rows=deepcopy(plan['before_rows'])
    writes={PUBLIC:plan['public_text']};archives=[];protected=deepcopy(plan['protected'])
    cards={l:read(ROOT/f'data/{l}/task_cards.json') for l in ('base','last_exam')}
    manifests={l:read(ROOT/f'data/{l}/input_asset_manifest.json') for l in cards}
    new=next(a for a in row['assets'] if a['role']=='agent_visible');name=Path(PUBLIC).name;task='debatebench/'+PID
    for layout in cards:
        c=next(c for c in cards[layout]['tasks'] if c['task_id']==task);relative=c['source_repo_path'];folder=f'data/{layout}/{relative}/base/input/'
        old_name=Path(before['source_file']).name
        require(sha(ROOT/folder/old_name)==sha(ROOT/before['source_file']),'Old public bytes differ')
        require((ROOT/folder/'problem.md').read_text(encoding='utf-8')==before['problem_description']+'\n','Old prompt drift')
        archives.append(folder+old_name)
        for p in (ROOT/folder).iterdir():
            if p.is_file() and p.name not in (old_name,'problem.md'):protected[p.relative_to(ROOT).as_posix()]=sha(p)
        writes[folder+name]=plan['public_text'];writes[folder+'problem.md']=row['problem_description']+'\n'
        files=c['input_files'] if layout=='base' else c['input']['files'];files[:]=[f for f in files if f['name']!=old_name]
        entry=dict(name=name,path=('input/' if layout=='base' else 'base/input/')+name)
        if layout=='base':entry['description']='Agent-visible input'
        files.append(entry);files.sort(key=lambda f:f['path'])
        manifests[layout]['files'][:]=[m for m in manifests[layout]['files'] if m['task_id']!=task]
        manifests[layout]['files'].append(dict(task_id=task,source=PUBLIC,sha256=new['sha256'],staged=relative+'/base/input/'+name))
        if layout=='base':c.update(evaluation=deepcopy(row['evaluation']),source_file=PUBLIC) if 'source_file' in c else c.update(evaluation=deepcopy(row['evaluation']))
        else:
            rp=f'data/last_exam/{relative}/eval/reference.json';ref=read(ROOT/rp);ref['evaluation']=deepcopy(row['evaluation']);writes[rp]=ref
    target=next(r for r in rows if r['problem_id']==PID);target.clear();target.update(row);writes[PATH]=rows
    for l in cards:writes.update({f'data/{l}/task_cards.json':cards[l],f'data/{l}/input_asset_manifest.json':manifests[l]})
    scores=read(ROOT/'data/rubrics/task_scorecards/debatebench.json');s=next(s for s in scores['records'] if s['problem_id']==PID);s.clear();s.update(scorecard(row,ROOT));writes['data/rubrics/task_scorecards/debatebench.json']=scores
    for track in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if track['benchmark_path']!=PATH:protected[track['benchmark_path']]=sha(ROOT/track['benchmark_path'])
    for p,h in protected.items():require(sha(ROOT/p)==h,'Preflight source drift')
    for p in [PUBLIC]+[p for p in writes if p.endswith('/'+name)]:require(not (ROOT/p).exists(),'New file occupied')
    report=dict(status='applying',backup=store.backup.relative_to(ROOT).as_posix(),records=1,removed_from_initial_inputs=archives,record_count_change=0,readiness_promotions=0,summary=plan['summary'])
    store.finish(report)
    for p in archives:store.archive(p)
    for p,v in writes.items():store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected file drift')
    report.update(status='completed',verification=verify(),protected_files_unchanged=len(protected));store.save(REPORT,report);store.finish(report);print(json.dumps(report,indent=2))


def verify():
    plan=read(ROOT/CACHE/'plan.json');u=plan['updates'][0];a,b=u['before'],u['after'];rows=read(ROOT/PATH)
    require(next(r for r in rows if r['problem_id']==PID)==b,'Canonical drift')
    expected=[b if r['problem_id']==PID else r for r in plan['before_rows']]
    later_report=ROOT/'data/benchmarks/debate_header_year_repair_20260913.json'
    if later_report.exists():
        from scripts.repair_debate_header_year_20260913 import expected_rows
        later=read(ROOT/'data/.cache/debate_header_year_20260913/plan.json')
        require(later['before_rows']==expected,'Broken batch 51 -> 52 transition')
        expected=expected_rows(later)
    require(rows==expected,'Unlisted later debate changes')
    for k in ('motion','gold_label','solution_file','total_points','year','title','split','license','team_size'):require(a.get(k)==b.get(k),'Protected metadata changed')
    for k in ('status','rubric_path','historical_reference_path','historical_score_identity'):require(a['evaluation'].get(k)==b['evaluation'].get(k),'Historical score/readiness changed')
    for p,h in plan['protected'].items():require(sha(ROOT/p)==h,'Original source drift')
    for asset in b['assets']:require(sha(ROOT/asset['path'])==asset['sha256'],'Asset drift')
    require((ROOT/PUBLIC).read_text(encoding='utf-8')==plan['public_text'],'Public content drift')
    for layout in ('base','last_exam'):
        c=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']=='debatebench/'+PID);folder=ROOT/'data'/layout/c['source_repo_path']/'base/input'
        require(not (folder/Path(a['source_file']).name).exists(),'Old slide still exposed')
        require(sha(folder/Path(PUBLIC).name)==sha(ROOT/PUBLIC),'Public copy drift')
        require((folder/'problem.md').read_text(encoding='utf-8')==plan['public_text'],'Prompt differs')
        ev=c['evaluation'] if layout=='base' else read(folder.parent.parent/'eval/reference.json')['evaluation'];require(ev==b['evaluation'],'Evaluation projection drift')
    return dict(records=1,original_slide_retained_judge_only=True,old_staged_copies_recoverably_archived=2,scores_and_readiness_unchanged=True)


if __name__=='__main__':{'prepare':prepare,'apply':apply,'verify':lambda:print(verify())}[sys.argv[1]]()
