"""Remove IOAI 2024 requiring unavailable production and judging services, without an archive."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import sys,json,hashlib
import pymupdf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from remove_eoes_companion_records_20260917 import DirectStore
from scripts.repair_data_catalog import summary_and_figures
from src.dataset_catalog import scorecard,update_track_index
CID='ioai_team'
PID='ioai_team_2024_practical'
def main():
 s=DirectStore(ROOT);bp=f'data/benchmarks/{CID}/benchmark.json';rows=deepcopy(s.read(bp));old=next((r for r in rows if r['problem_id']==PID),None)
 if old is None:print('Already removed');return
 contract=s.read(old['evaluation']['task_contract_path'])
 assert old['evaluation']['status']=='not_ready' and old['evaluation']['evaluator_id'] is None
 assert any('47-second' in x for x in contract['required_artifacts'])
 assert 'NeuralFrames' in contract['tools']['video']
 assert contract['final_ranking_formula'] is None
 retained=[r for r in rows if r['problem_id']!=PID]
 report=dict(removed_id=PID,reason='Original media are archived, but required NeuralFrames production conditions and multimodal judging are unavailable; not repairable by catalog/source cleanup alone.',source_sha256=s.sha(old['source_file']),archive_created=False,last_exam_touched=False,retained_records_sha256=hashlib.sha256(json.dumps(retained,sort_keys=True).encode()).hexdigest(),retained_asset_hashes={a['path']:s.sha(a['path']) for r in retained for a in r.get('assets',[])})
 s.save('tmp/ioai_2024_removal_20260917.json',report);s.save(bp,retained)
 idx=deepcopy(s.read('data/benchmarks/index.json'));update_track_index(idx,CID,retained);s.save('data/benchmarks/index.json',idx)
 for base in ['data','data/mini_data']:
  rp=f'{base}/rules/{CID}/evaluation.json';rule=deepcopy(s.read(rp))
  for key in ['record_rubric_overrides','record_evaluator_overrides']:rule['scoring'].get(key,{}).pop(PID,None)
  if base=='data':rule['scoring']['evaluation_status_counts']=dict(Counter(r['evaluation']['status'] for r in retained))
  s.save(rp,rule)
 s.save(f'data/rubrics/task_scorecards/{CID}.json',dict(schema_version='1.1',dataset=CID,visibility='judge_only',records=[scorecard(r,ROOT) for r in retained]))
 for name,key in [('task_cards.json','tasks'),('input_asset_manifest.json','files')]:
  p='data/base/'+name;v=deepcopy(s.read(p));v[key]=[x for x in v[key] if x['task_id']!=CID+'/'+PID]
  if key=='tasks':v['n_tasks']=len(v[key])
  s.save(p,v)
 p='data/base/index.json';v=deepcopy(s.read(p));v['n_tasks']=idx['total_records']
 for t in v['competitions']:
  if t['id']==CID:t['n_tasks']=len(retained)
 s.save(p,v)
 p='data/problem_pdf_allowlist.json';v=deepcopy(s.read(p));v['assets']=[a for a in v['assets'] if a['problem_id']!=PID];s.save(p,v)
 summary_and_figures(s,idx,{t['id']:deepcopy(s.read(t['benchmark_path'])) for t in idx['olympiads']})
 p=ROOT/'data/README.md';s.save_text(p,p.read_text(encoding='utf-8').replace('1,042 records',f"{idx['total_records']:,} records"))
 print('Removed unresolved IOAI 2024; retained',len(retained),'IOAI records; total',idx['total_records'])
if __name__=='__main__':main()
