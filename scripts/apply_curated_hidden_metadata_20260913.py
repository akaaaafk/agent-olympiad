"""Apply a frozen, hidden-material-only dataset repair; never rebuild public inputs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard
from scripts.repair_data_catalog import Store
from scripts.repair_iol_sources_20260913 import read,sha,require


def apply(plan_path):
    plan=read(ROOT/plan_path); store=Store(ROOT); cid=plan['competition_id']
    require(not (ROOT/plan['report_path']).exists(),'Report already exists; no blind replay')
    require(sha(ROOT/plan['benchmark_path'])==plan['expected_benchmark_sha256'],'Benchmark changed')
    rows=deepcopy(store.read(plan['benchmark_path'])); originals=deepcopy(rows)
    updates={r['after']['problem_id']:r for r in plan['updates']}
    require(len(updates)==len(plan['updates']),'Duplicate updates')
    old_assets={}
    for item in updates.values():
        before,after=item['before'],item['after']
        require(next(r for r in rows if r['problem_id']==before['problem_id'])==before,'Record changed')
        for k in ('problem_description','source_file','gold_label','split','license','year','team_size'):
            require(before.get(k)==after.get(k),'Hidden repair must not change '+k)
        require(before['evaluation']['status']==after['evaluation']['status'],'Readiness change forbidden')
        require(before['evaluation']['evaluator_id']==after['evaluation']['evaluator_id'],'Evaluator change forbidden')
        require([a for a in before['assets'] if a['role']=='agent_visible']==[a for a in after['assets'] if a['role']=='agent_visible'],'Public assets changed')
        old_assets.update({a['path']:a['sha256'] for a in before['assets']})
    destinations=set()
    for f in plan['new_files']:
        path=store.path(f['destination'])
        require(path.is_relative_to(ROOT/'data/raw') or path.is_relative_to(ROOT/'data/rubrics'),'Unexpected new-file scope')
        require(f['destination'] not in destinations and not path.exists(),'Destination occupied or duplicate')
        destinations.add(f['destination'])
        require(sha(store.path(f['source']))==f['sha256'],'New source bytes changed')
    for p,h in old_assets.items(): require(sha(ROOT/p)==h,'Existing source changed')
    cards=deepcopy(store.read('data/base/task_cards.json')); old_cards=deepcopy(cards)
    score_path=f'data/rubrics/task_scorecards/{cid}.json'
    scores=deepcopy(store.read(score_path)); old_scores=deepcopy(scores)
    references={}; protected={}
    for pid in updates:
        task=cid+'/'+pid; card=next(c for c in cards['tasks'] if c['task_id']==task)
        relative=card['source_repo_path']
        for layout in ('base','last_exam'):
            folder=ROOT/'data'/layout/relative/'base/input'
            protected.update({p.relative_to(ROOT).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()})
        ref_path=f'data/last_exam/{relative}/eval/reference.json'
        references[pid]=(ref_path,deepcopy(store.read(ref_path)))
    for name in ('data/last_exam/task_cards.json','data/base/input_asset_manifest.json','data/last_exam/input_asset_manifest.json','data/benchmarks/index.json'):
        protected[name]=sha(ROOT/name)
    for track in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if track['benchmark_path']!=plan['benchmark_path']: protected[track['benchmark_path']]=sha(ROOT/track['benchmark_path'])
    report=dict(status='applying',plan_path=plan_path,backup=store.backup.relative_to(ROOT).as_posix(),
                selected_records=len(updates),new_files=len(destinations),record_count_change=0,
                programs_executed=False,readiness_changed=False,score_changes=plan.get('score_changes',[]))
    store.finish(report)
    for f in plan['new_files']:
        dest=store.path(f['destination']); dest.parent.mkdir(parents=True,exist_ok=True)
        with store.path(f['source']).open('rb') as src,dest.open('xb') as dst: shutil.copyfileobj(src,dst)
        require(sha(dest)==f['sha256'],'Copied file differs')
        store.changes.append(dict(path=f['destination'],before_sha256=None,after_sha256=f['sha256']))
    for pid,item in updates.items():
        row=next(r for r in rows if r['problem_id']==pid); row.clear(); row.update(item['after'])
        card=next(c for c in cards['tasks'] if c['task_id']==cid+'/'+pid)
        card.update(evaluation=deepcopy(row['evaluation']),solution_file=row.get('solution_file'))
        old_score=next(c for c in scores['records'] if c['problem_id']==pid)
        old_score.clear(); old_score.update(scorecard(row,ROOT))
        ref_path,ref=references[pid]
        ref.update(evaluation=deepcopy(row['evaluation']),solution_file=row.get('solution_file'),
                   rubric_path=row['evaluation'].get('rubric_path'))
        store.save(ref_path,ref)
    store.save(plan['benchmark_path'],rows); store.save(score_path,scores); store.save('data/base/task_cards.json',cards)
    for p,h in {**protected,**old_assets}.items(): require(sha(ROOT/p)==h,'Protected file changed: '+p)
    require([r for r in rows if r['problem_id'] not in updates]==[r for r in originals if r['problem_id'] not in updates],'Other records changed')
    require([c for c in scores['records'] if c['problem_id'] not in updates]==[c for c in old_scores['records'] if c['problem_id'] not in updates],'Other scores changed')
    selected_tasks={cid+'/'+pid for pid in updates}
    require([c for c in cards['tasks'] if c['task_id'] not in selected_tasks]==[c for c in old_cards['tasks'] if c['task_id'] not in selected_tasks],'Other cards changed')
    require(read(ROOT/plan['benchmark_path'])==rows and read(ROOT/score_path)==scores and read(ROOT/'data/base/task_cards.json')==cards,'Metadata readback failed')
    for pid,item in updates.items():
        for a in item['after']['assets']: require(sha(ROOT/a['path'])==a['sha256'],'Asset hash mismatch')
        ref_path,ref=references[pid]; require(read(ROOT/ref_path)==ref,'Reference readback failed')
    report.update(status='completed',protected_files_unchanged=len(protected),old_assets_unchanged=len(old_assets),
                  other_records_and_scorecards_unchanged=True,new_assets_verified=True,public_inputs_unchanged=True,
                  summary=plan.get('summary'))
    store.save(plan['report_path'],report); store.finish(report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': apply(sys.argv[1])
