"""Select one EOES 2015 Challenge 1 catalog representative; preserve source conflict."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import sys,json,hashlib,re
import pymupdf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from remove_eoes_companion_records_20260917 import DirectStore
from scripts.repair_data_catalog import summary_and_figures
from src.dataset_catalog import scorecard,update_track_index
CID='eoes';OLD='eoes_ExpBlowingintheWind';KEEP='eoes_tasksheet1'
def main():
 s=DirectStore(ROOT);bp='data/benchmarks/eoes/benchmark.json';rows=deepcopy(s.read(bp));by={r['problem_id']:r for r in rows}
 if OLD not in by:print('Already deduplicated');return
 old,keep=by[OLD],by[KEEP]
 evidence={}
 for row,total,pages in [(old,306,30),(keep,304,29)]:
  with pymupdf.open(ROOT/row['source_file']) as d:
   assert len(d)==pages
   title=d[0].get_text();head=d[1].get_text();assert 'BLOWING IN THE WIND' in title and 'Challenge 1' in title
   weights=[int(n) for n in re.findall(r'Task\s+[A-E]:\s*(\d+)\s*Marks',head)];assert sum(weights)==row['total_points']==total
  evidence[row['problem_id']]=dict(source_file=row['source_file'],sha256=s.sha(row['source_file']),pages=pages,printed_maxima=weights,total=total)
 assert old['evaluation']['status']==keep['evaluation']['status']=='not_ready'
 unchanged=[deepcopy(r) for r in rows if r['problem_id'] not in [OLD,KEEP]]
 note='Catalog representative selected: tasksheet1 (29-page task sheet, printed total 304). ExpBlowingintheWind is another Challenge 1 variant (30 pages, printed total 306, appended Function/scoring/outline material), not a second challenge. No final-official-version precedence or worksheet equivalence is established; do not transfer its weights or appendices into this task.'
 keep.setdefault('source_review',{})['catalog_variant_selection_20260917']=dict(selected_id=KEEP,removed_independent_id=OLD,reason=note,sources=evidence,official_version_precedence_verified=False)
 keep['evaluation']['limitations'].append(note)
 def clean(value):
  if isinstance(value,dict):
   for k,v in value.items():
    if k=='parent_problem_ids' and isinstance(v,list):value[k]=[x for x in v if x!=OLD]
    else:clean(v)
  elif isinstance(value,list):
   for v in value:clean(v)
 clean(keep)
 rows=[r for r in rows if r['problem_id']!=OLD]
 report=dict(removed_id=OLD,retained_id=KEEP,evidence=evidence,archive_created=False,last_exam_touched=False,unchanged_records_sha256=hashlib.sha256(json.dumps(unchanged,sort_keys=True).encode()).hexdigest(),retained_input_sha256=hashlib.sha256(keep['problem_description'].encode()).hexdigest(),retained_asset_hashes={a['path']:s.sha(a['path']) for a in keep['assets']})
 s.save('tmp/eoes_2015_variant_selection_20260917.json',report);s.save(bp,rows)
 idx=deepcopy(s.read('data/benchmarks/index.json'));update_track_index(idx,CID,rows);s.save('data/benchmarks/index.json',idx)
 for base in ['data','data/mini_data']:
  rp=f'{base}/rules/{CID}/evaluation.json';rule=deepcopy(s.read(rp))
  for key in ['record_rubric_overrides','record_evaluator_overrides']:rule['scoring'].get(key,{}).pop(OLD,None)
  if base=='data':rule['scoring']['evaluation_status_counts']=dict(Counter(r['evaluation']['status'] for r in rows))
  s.save(rp,rule)
 s.save('data/rubrics/task_scorecards/eoes.json',dict(schema_version='1.1',dataset=CID,visibility='judge_only',records=[scorecard(r,ROOT) for r in rows]))
 for name,key in [('task_cards.json','tasks'),('input_asset_manifest.json','files')]:
  p='data/base/'+name;v=deepcopy(s.read(p));v[key]=[x for x in v[key] if x['task_id']!=CID+'/'+OLD]
  if key=='tasks':
   v['n_tasks']=len(v[key])
   for x in v[key]:
    if x['task_id']==CID+'/'+KEEP:x['evaluation']=deepcopy(keep['evaluation'])
  s.save(p,v)
 p='data/base/index.json';v=deepcopy(s.read(p));v['n_tasks']=idx['total_records']
 for t in v['competitions']:
  if t['id']==CID:t['n_tasks']=len(rows)
 s.save(p,v)
 p='data/problem_pdf_allowlist.json';v=deepcopy(s.read(p));v['assets']=[a for a in v['assets'] if a['problem_id']!=OLD];s.save(p,v)
 summary_and_figures(s,idx,{t['id']:deepcopy(s.read(t['benchmark_path'])) for t in idx['olympiads']})
 p=ROOT/'data/README.md';s.save_text(p,p.read_text(encoding='utf-8').replace('1,044 records',f"{idx['total_records']:,} records"))
 print('Selected tasksheet1, removed alternate independent record. Total',idx['total_records'])
if __name__=='__main__':main()
