"""Delete three non-independent EOES catalog entries; keep parent inputs, no archive."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json,hashlib,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store,summary_and_figures
from src.dataset_catalog import update_track_index,scorecard
IDS={'eoes_a1','eoes_a2','eoes_additionalfileschallenge1'}
class DirectStore(Store):
 def save_text(self,name,text):
  p=self.path(name);data=text.encode('utf-8');old=self.raw.get(p,p.read_bytes() if p.exists() else None)
  assert (p.read_bytes() if p.exists() else None)==old,f'Concurrent change: {p}'
  p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.eoes-tmp');tmp.write_bytes(data);os.replace(tmp,p)
  self.raw[p]=data;self.hashes[p]=hashlib.sha256(data).hexdigest()
 def archive(self,name):
  p=self.path(name);assert p.parent==ROOT/'data/viz',p
  # Derived figures are overwritten, as requested; do not create archives.
def main():
 s=DirectStore(ROOT);bp='data/benchmarks/eoes/benchmark.json';rows=deepcopy(s.read(bp));by={r['problem_id']:r for r in rows}
 if not IDS&by.keys():print('Already removed');return
 assert IDS<=by.keys()
 for child,parent in [('eoes_a1','eoes_t1'),('eoes_a2','eoes_t2')]:
  source=by[child]['source_file'];refs=by[parent]['source_review']['remaining_mini_repair']['sources'];assert any(a['path']==source and a['sha256']==s.sha(source) for a in refs)
  import pymupdf
  with pymupdf.open(ROOT/source) as original,pymupdf.open(ROOT/next(a['path'] for a in by[parent]['assets'] if a['role']=='agent_visible')) as packet:
   offset=len(packet)-len(original);assert offset>0
   assert all(p.get_text()==packet[offset+i].get_text() and p.read_contents()==packet[offset+i].read_contents() for i,p in enumerate(original))
 companion=by['eoes_additionalfileschallenge1'];review=companion['source_review']['eoes_2015_review'];assert review['independently_scoreable'] is False
 for parent in review['parent_problem_ids']:assert any(a['path']==companion['source_file'] and a['role']=='agent_visible' and a['sha256']==s.sha(a['path']) for a in by[parent]['assets'])
 retained=[r for r in rows if r['problem_id'] not in IDS];report=dict(removed_ids=sorted(IDS),reason='Companion inputs already bound to parent tasks; not independently scoreable.',archive_created=False,last_exam_touched=False,parent_asset_hashes={a['path']:s.sha(a['path']) for pid in ['eoes_t1','eoes_t2',*review['parent_problem_ids']] for a in by[pid]['assets']},retained_records_sha256=hashlib.sha256(json.dumps(retained,sort_keys=True).encode()).hexdigest())
 # Persist only IDs and hashes as evidence, not old task contents.
 s.save('tmp/eoes_companion_removal_20260917.json',report)
 s.save(bp,retained)
 index=deepcopy(s.read('data/benchmarks/index.json'));update_track_index(index,'eoes',retained);s.save('data/benchmarks/index.json',index)
 for base in ['data','data/mini_data']:
  rp=base+'/rules/eoes/evaluation.json';rule=deepcopy(s.read(rp))
  for key in ['record_evaluator_overrides','record_rubric_overrides']:
   for id in IDS:rule['scoring'].get(key,{}).pop(id,None)
  if base=='data':rule['scoring']['evaluation_status_counts']=dict(Counter(r['evaluation']['status'] for r in retained))
  s.save(rp,rule)
 s.save('data/rubrics/task_scorecards/eoes.json',dict(schema_version='1.1',dataset='eoes',visibility='judge_only',records=[scorecard(r,ROOT) for r in retained]))
 for name,key in [('task_cards.json','tasks'),('input_asset_manifest.json','files')]:
  path='data/base/'+name;obj=deepcopy(s.read(path));obj[key]=[x for x in obj[key] if x['task_id'] not in {'eoes/'+id for id in IDS}]
  if key=='tasks':obj['n_tasks']=len(obj[key])
  s.save(path,obj)
 path='data/base/index.json';obj=deepcopy(s.read(path));obj['n_tasks']=index['total_records']
 for t in obj['competitions']:
  if t['id']=='eoes':t['n_tasks']=len(retained)
 s.save(path,obj)
 benchmarks={t['id']:deepcopy(s.read(t['benchmark_path'])) for t in index['olympiads']};summary_and_figures(s,index,benchmarks)
 p=ROOT/'data/README.md';s.save_text(p,p.read_text(encoding='utf-8').replace('1,048 records',f"{index['total_records']:,} records"))
 assert all(s.sha(p)==h for p,h in report['parent_asset_hashes'].items())
 print('Removed 3 independent records; parent files retained; total',index['total_records'])
if __name__=='__main__':main()
