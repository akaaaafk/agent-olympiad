"""Resume auxiliary evaluation first, then current-catalog native jobs in ten lanes."""
import collections
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/tinker_requested_current_20260916'
SNAP=ROOT.parent/'qwen-current-native-runtime-20260916'
MODEL='Qwen/Qwen3.6-35B-A3B'
VARIANTS=('single_agent','otc')
REQUESTED=('arml_local','arml_national_team','purple_comet','wmtc','history_olympiad',
 'qanta','science_bowl','arml_national_power','arml_power','pumac_power','iol_team',
 'ioaa_group','ijso_practical','wsc_writing','hmmt_team')
OLD=(('tinker_task_based_arml_icpc_20260914',ROOT.parent/'tinker-frozen-runtime-20260915'),
     ('tinker_requested_remaining_20260915',ROOT.parent/'qwen-extension-runtime-20260915'))

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+'.tmp')
 temp.write_text(json.dumps(data,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
 temp.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def command(j):
 if j['kind']=='artifact':
  cmd=[sys.executable,'-u',str(ROOT/'src/run_otc_artifact.py')]
  for name,value in j['artifact_options'].items():cmd+=['--'+name.replace('_','-'),str(value)]
  if (Path(j['output'])/'run_identity.json').exists():cmd.append('--resume')
  return cmd
 cmd=[sys.executable,'-u',str(Path(j['snapshot'])/'src/run_competition_batch.py'),
  '--live','--provider','tinker','--model',MODEL,
  '--benchmark-root',str(Path(j['snapshot'])/'data/benchmarks'),
  '--contest-manifest',j['manifest'],'--system-variant',j['variant'],
  '--max-output-tokens',str(j.get('max_output_tokens',8192)),
  '--max-total-tokens',str(j.get('max_total_tokens',220000)),
  '--temperature','0.2','--action-calling','emulated','--judge-collab',
  '--judge-provider','tinker','--judge-model',MODEL,'--no-judge-cce','--output',j['output']]
 if j.get('max_turns_override') is not None:cmd+=['--max-turns',str(j['max_turns_override'])]
 if j['kind']=='evaluation' or (Path(j['output'])/'contest_checkpoint.json').exists() or (Path(j['output'])/'contest_session.json').exists():cmd.append('--resume')
 if j['kind']=='evaluation':
  cmd=[sys.executable,'-u',str(ROOT/'scripts/resume_qwen_evaluation_only_20260916.py'),
       '--snapshot',j['snapshot']]+cmd[3:]
 return cmd

def prepare():
 if (OUT/'registry.json').exists():
  if (OUT/'supervisor.lock').exists() or (OUT/'evaluation_phase_finished.json').exists():
   raise ValueError('Cannot replace a started registry')
  shutil.copy2(OUT/'registry.json',OUT/'registry.before_preflight_fix.json')
 current={c:{r['problem_id']:r for r in read(ROOT/'data/benchmarks'/c/'benchmark.json')} for c in REQUESTED}
 jobs=[];blocked=[];covered=set();historical={};checks={}
 for batch,snap in OLD:
  directory=ROOT/'results'/batch
  registry=read(directory/'registry.json')
  frozen={}
  for job in registry['jobs']:
   c=job['competition'];result=directory/'runs'/job['id']/'contest_session.json'
   base=dict(id=batch+'__'+job['id'],legacy_id=job['id'],competition=c,variant=job['variant'],
    snapshot=str(snap),manifest=str(directory/'manifests'/(job['id']+'.json')),
    output=str(result.parent),max_output_tokens=job.get('max_output_tokens',8192),
    max_total_tokens=job.get('max_total_tokens_override',220000),
    max_turns_override=job.get('max_turns_override'),problem_ids=job['problem_ids'])
   if result.exists():
    r=read(result)
    if r.get('evaluation_pending'):jobs.append(dict(base,kind='evaluation'))
   if c not in current or job['variant'] not in VARIANTS:continue
   ids=set(job['problem_ids']);available=set(current[c])
   if not ids<=available:
    blocked.append(dict(id=job['id'],competition=c,reason='Excluded by current catalog membership',missing_ids=sorted(ids-available)))
    continue
   if c not in frozen:frozen[c]={r['problem_id']:r for r in read(snap/'data/benchmarks'/c/'benchmark.json')}
   # Compare actual task text/gold, not only an ID or label.
   if any(current[c][p].get('problem_description')!=frozen[c][p].get('problem_description') or
          current[c][p].get('gold_label')!=frozen[c][p].get('gold_label') for p in ids):
    blocked.append(dict(id=job['id'],competition=c,reason='Current task text or gold differs; fresh experiment required'))
    if result.exists():
     # Preserve completed paid runs, even when catalog repairs changed their content.
     covered.update((c,p,job['variant']) for p in ids)
    continue
   covered.update((c,p,job['variant']) for p in ids)
   historical[base['id']]=dict(finished=result.exists(),competition=c,variant=job['variant'])
   if not result.exists():jobs.append(dict(base,kind='contest'))
  # Source identity checking is enforced by each runner on --resume.

 if not SNAP.exists():shutil.copytree(ROOT/'src',SNAP/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for directory in ['rules','rubrics','evaluators']:
  if (ROOT/'data'/directory).exists():shutil.copytree(ROOT/'data'/directory,SNAP/'data'/directory,dirs_exist_ok=True)
 shutil.copytree(ROOT/'data/judge_references/numeric_gold',SNAP/'data/judge_references/numeric_gold',dirs_exist_ok=True)
 for c in REQUESTED:
  write(SNAP/'data/benchmarks'/c/'benchmark.json',list(current[c].values()))
 sys.path.insert(0,str(SNAP/'src'))
 from artifact_contract import delivery_route
 from rules.loader import load_rule_card
 from contest_manifest import load_contest_manifest
 from contest_adapters import grade_contest_result
 from run_competition_batch import inspect_contest_run
 fresh=[]
 for c,rows in current.items():
  route=delivery_route(load_rule_card(c))
  if route in {'document','slides','artifact_bundle'}:
   blocked.append(dict(competition=c,records=len(rows),reason='Tinker does not support required PDF/image artifact input',route=route))
   continue
  # Legacy QANTA and Science Bowl remain grouped by their registered tournament/packet.
  # Other not-yet-run native tracks use one canonical record per session.
  for p,row in rows.items():
   if (row.get('evaluation') or {}).get('status') not in {'ready','ready_with_limitations'}:
    blocked.append(dict(competition=c,problem_id=p,reason='Current record not evaluation-ready'))
    continue
   for variant in VARIANTS:
    if (c,p,variant) in covered:continue
    # Do not regroup old tournament sessions if an incompatible old session exists.
    if c in {'qanta','science_bowl'}:
     blocked.append(dict(competition=c,problem_id=p,variant=variant,reason='No identity-compatible registered legacy session; fresh grouped manifest required'))
     continue
    jid=c+'_'+hashlib.sha256(p.encode()).hexdigest()[:12]+'_'+variant
    manifest=OUT/'manifests'/(jid+'.json')
    write(manifest,dict(session_id=p,competition_id=c,problem_ids=[p],split_parts=False))
    j=dict(id=jid,competition=c,variant=variant,snapshot=str(SNAP),manifest=str(manifest),
     output=str(OUT/'runs'/jid),kind='contest',problem_ids=[p],limitations=['Canonical extracted text only; Tinker does not visually inspect PDFs/images.'])
    try:
     loaded=load_contest_manifest(manifest,benchmark_root=SNAP/'data/benchmarks')
     grade=grade_contest_result(loaded,{})
     unsupported=[t.task_id for t in loaded.tasks if not grade['tasks'][t.task_id]['graded'] and
       (t.benchmark.get('evaluation') or {}).get('evaluator_id')!='rubric_llm_v1']
     if unsupported:raise ValueError('Unsupported evaluators: '+','.join(unsupported))
     state,identity=inspect_contest_run(command(j)[3:])
     assert state=='new'
     j.update(run_identity=identity,task_count=len(loaded.tasks))
     jobs.append(j);fresh.append(j)
    except Exception as exc:blocked.append(dict(competition=c,problem_id=p,variant=variant,reason=str(exc)))
 checks={p.relative_to(SNAP).as_posix():sha(p) for directory in ['src','data/benchmarks','data/rules','data/rubrics','data/judge_references/numeric_gold'] for p in (SNAP/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 registry=dict(model=MODEL,variants=VARIANTS,lanes=10,watchdog_idle_seconds=480,jobs=jobs,
  blocked=blocked,historical_current_membership=historical,snapshot=str(SNAP),file_hashes=checks,
  policy='Pending evaluation first. New solves only single_agent/otc, within current catalog. Historical scope exclusions retained, not rerun.')
 write(OUT/'registry.json',registry)
 print(json.dumps(dict(evaluation_jobs=sum(j['kind']=='evaluation' for j in jobs),contest_jobs=sum(j['kind']=='contest' for j in jobs),fresh_jobs=len(fresh),contest_by_track=dict(collections.Counter(j['competition'] for j in jobs if j['kind']=='contest')),blocked=len(blocked)),indent=2),flush=True)

def kill(proc):
 if proc.poll() is None:subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def worker(j,key):
 dest=Path(j['output']);result=dest/('result.json' if j['kind']=='artifact' else 'contest_session.json')
 if j['kind']=='artifact' and result.exists() and (read(result).get('graded') or read(result).get('status')=='unsubmitted'):
  # Source changes must not force a completed paid solver/rubric run to repeat.
  code=subprocess.run([sys.executable,'-u',str(ROOT/'src/evaluate_saved_metrics.py'),
    '--output',str(dest),'--judge-provider','tinker','--judge-model',MODEL],cwd=ROOT,
    env=dict(os.environ,TINKER_API_KEY=key)).returncode
  state=dict(id=j['id'],competition=j['competition'],variant=j['variant'],kind=j['kind'],
    status=('complete' if read(result).get('graded') else 'unsubmitted') if code==0 else 'evaluation_pending',exit_code=code)
  write(OUT/'states'/(j['id']+'.json'),state)
  return state
 if j['kind']=='artifact':
  from otc_artifact_pipeline import prepare_artifact_run
  prepared=prepare_artifact_run(**j['artifact_options'])
  if prepared['identity']!=j['run_identity']:raise ValueError('Artifact identity changed: '+j['id'])
 terminal=result.exists() and ((read(result).get('status') in {'complete','unsubmitted'}) if j['kind']=='artifact' else not read(result).get('evaluation_pending'))
 if terminal:
  state=dict(id=j['id'],competition=j['competition'],variant=j['variant'],kind=j['kind'],status='already_complete')
  write(OUT/'states'/(j['id']+'.json'),state)
  return state
 # Capture finished contestant state before requesting evaluation-only resume.
 immutable=None
 if j['kind']=='evaluation':
  r=read(result);immutable=(r.get('submissions'),r.get('memory'))
  backup=OUT/'evaluation_before'/j['id']/'contest_session.json'
  if not backup.exists():write(backup,r)
 state=dict(id=j['id'],competition=j['competition'],variant=j['variant'],kind=j['kind'],status='running',started_at=time.time())
 state_path=OUT/'states'/(j['id']+'.json');write(state_path,state)
 log=OUT/'logs'/(j['id']+'.log');log.parent.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,TINKER_API_KEY=key)
 for attempt in range(2):
  with log.open('a',encoding='utf-8') as f:
   proc=subprocess.Popen(command(j),cwd=j['snapshot'],env=env,stdout=f,stderr=subprocess.STDOUT)
   state.update(pid=proc.pid,attempt=attempt+1);write(state_path,state)
   paths=[log,dest/'contest_checkpoint.json',dest/'calls.jsonl',dest/'contest_session.json',result]
   last=time.time()
   while proc.poll() is None:
    last=max([last]+[p.stat().st_mtime for p in paths if p.exists()])
    if time.time()-last>480:
     f.write('\n[watchdog] 480s without progress; restarting from checkpoint.\n');f.flush();kill(proc);break
    time.sleep(5)
   code=proc.wait()
  if immutable is not None:
   r=read(result)
   if (r.get('submissions'),r.get('memory'))!=immutable:raise RuntimeError('Evaluation modified contestant state: '+j['id'])
  if result.exists():
   if j['kind']=='artifact' and read(result).get('status') in {'complete','unsubmitted'}:break
   if j['kind']!='artifact' and not read(result).get('evaluation_pending'):break
 state.update(status=((read(result).get('status') or 'failed') if j['kind']=='artifact' else ('evaluation_pending' if read(result).get('evaluation_pending') else 'complete')) if result.exists() else 'failed',exit_code=code,finished_at=time.time())
 write(state_path,state)
 print(j['kind'],j['id'],state['status'],flush=True)
 return state

def run():
 sys.path.insert(0,str(ROOT/'src'))
 from dotenv import dotenv_values
 for name,value in dotenv_values(ROOT/'.env').items():
  if value is not None:os.environ[name]=value
 keys=[os.environ.get('TINKER_API_KEY'),os.environ.get('TINKER_API_KEY2')]
 if not all(keys) or keys[0]==keys[1]:raise ValueError('Two distinct Tinker keys required')
 registry=read(OUT/'registry.json')
 changed=[p for p,h in registry['file_hashes'].items() if sha(SNAP/p)!=h]
 if changed:raise RuntimeError('New frozen snapshot changed: '+','.join(changed[:5]))
 lock=OUT/'supervisor.lock'
 with lock.open('x') as f:f.write(str(os.getpid()))
 try:
  skip_competitions=set(registry.get('skip_competitions',[]))
  for kind in registry.get('phase_order',['evaluation','contest']):
   jobs=[j for j in registry['jobs'] if (j['kind'] in {'artifact','contest'} if kind=='work' else j['kind']==kind) and j['competition'] not in skip_competitions]
   jobs.sort(key=lambda j:j.get('priority',100))
   print(f'PHASE={kind} jobs={len(jobs)} lanes=10',flush=True)
   with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futures=[pool.submit(worker,j,keys[i%2]) for i,j in enumerate(jobs)]
    for future in concurrent.futures.as_completed(futures):future.result()
   write(OUT/(kind+'_phase_finished.json'),dict(status='phase_exhausted',time=time.time()))
  write(OUT/'finished.json',dict(status='queue_exhausted'))
 finally:lock.unlink(missing_ok=True)

if __name__=='__main__':prepare() if sys.argv[1:]==['prepare'] else run()
