"""Bind four ARML National Power editions to reviewed printed award weights."""
from copy import deepcopy
from pathlib import Path
import sys,re,json
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store
from src.dataset_catalog import scorecard,update_track_index
LABELS={
2016:'1a 1b 1c 2a 2b 2c 3a 3b 3c 4a 4b 5a 5b 5c 5d 6a 6b 7a 7b 8a 8b 8c 9a 9b 9c 10'.split(),
2018:'1 2a 2b 3a 3b 4a 4b 5a 5b 6a 6b 6c 6d 7 8a 8b 9 10'.split(),
2019:'1a 1b 1c 1d 2a 2b 2c 3 4a 4b 5a 5b 6a 6b 7 8a 8b 8c 8d 9 10'.split(),
2023:'1a 1b 2a 2b 3a 3b 3c 4 5a 5b 5c 6a 6b 7a 7b 8a 8b 9a 9b 9c 9d 9e 9f'.split()}
MARKER=re.compile(r'\[\s*(\d+)\s*pts?\.?\s*\]')
def main():
 store=Store(ROOT,ROOT.parent/'dataset_backups');bp='data/benchmarks/arml_national_power/benchmark.json';rows=deepcopy(store.read(bp));changed=[];rubrics={}
 for row in rows:
  y=row['year']
  if y not in LABELS:continue
  if row['evaluation']['rubric_path'].endswith('_printed_awards_v2.json'):continue
  assert row['evaluation']['rubric_path']=='data/rubrics/team_power_proof_40_v1.json'
  with pymupdf.open(ROOT/row['source_file']) as d:pages=[p.get_text() for p in d]
  text='\n'.join(pages);matches=list(MARKER.finditer(text));assert len(matches)==len(LABELS[y]);assert sum(int(m[1]) for m in matches)==row['total_points']==50
  with pymupdf.open(ROOT/row['solution_file']) as d:reference='\n\n'.join(p.get_text() for p in d)
  assert len(reference)>1000
  criteria=[];cursor=0
  for label,m in zip(LABELS[y],matches):
   segment=text[cursor:m.end()];cursor=m.end()
   page=next(i+1 for i in range(len(pages)) if m.start()<sum(len(p)+1 for p in pages[:i+1]))
   criteria.append(dict(id='problem_'+label,name='Problem '+label,max_score=int(m[1]),observable=True,description='Score only subproblem '+label+' using its printed maximum. The source excerpt may include shared setup; do not score that setup or any other subproblem again. Follow the original instructions: list/compute need no justification; determine/find/show need work or reasoning; justify/prove require rigorous proof. Earlier numbered results may be used without proof, but later ones may not. Accept valid alternative solutions. Partial-credit judgment is an LLM benchmark approximation, not an official marking calibration.\nSOURCE EXCERPT:\n'+segment,source_page=page))
  rid=row['problem_id']+'_printed_awards_v2';rp='data/rubrics/'+rid+'.json'
  rubric=dict(rubric_id=rid,title=f'ARML National Power {y}: printed subproblem maxima',total_points=50,criteria=criteria,role='judge_only',provenance=dict(source_file=row['source_file'],source_sha256=store.sha(row['source_file']),solution_file=row['solution_file'],solution_sha256=store.sha(row['solution_file']),labels_reviewed_from='Original rendered problem pages, tmp/arml_power_review_20260917/pages.png',weight_basis='All printed subproblem maxima, in original source order; no proportional generic-rubric scaling.',official_partial_credit_reproduced=False))
  store.save(rp,rubric);rubrics[row['problem_id']]=(rp,rubric)
  row.setdefault('source_review',{})['printed_awards_20260917']=dict(previous_evaluation=deepcopy(row['evaluation']),labels=LABELS[y],weights=[c['max_score'] for c in criteria],source_sha256=store.sha(row['source_file']),solution_sha256=store.sha(row['solution_file']))
  row['evaluation'].update(rubric_path=rp,score_basis='Printed per-subproblem maxima total 50; official-reference LLM partial credit, not historical official grader calibration.',limitations=['Official problem weights are preserved; partial credit is assessed by an LLM, not a reproduced official marking scheme.'])
  row['gold_label']['grading_rubric']=rp
  # Supply the complete source reference even for 2023, whose old gold parts are empty.
  row['gold_label']['expected_answer']=None
  row['gold_label']['parts']=[dict(id='official_reference',points=50,answer_type='proof',expected=None,reference=reference,match_mode='reference_llm')]
  row['evaluation'].pop('fallback_evaluator_id',None)
  changed.append(row['problem_id'])
 if not changed:print('Already repaired');return
 store.save(bp,rows)
 for base in ['data','data/mini_data']:
  path=f'{base}/rules/arml_national_power/evaluation.json';rule=deepcopy(store.read(path));sc=rule['scoring']
  for key,(rp,rubric) in rubrics.items():
   dest=rp if base=='data' else rp.replace('data/','data/mini_data/',1)
   if base!='data':store.save(dest,json.loads(json.dumps(rubric).replace('data/','data/mini_data/')))
   sc.setdefault('record_rubric_overrides',{})[key]=dest
   sc.setdefault('record_evaluator_overrides',{})[key]='rubric_llm_v1'
  store.save(path,rule)
 store.save('data/rubrics/task_scorecards/arml_national_power.json',dict(schema_version='1.1',dataset='arml_national_power',visibility='judge_only',records=[scorecard(r,ROOT) for r in rows]))
 cards=deepcopy(store.read('data/base/task_cards.json'));by_id={r['problem_id']:r for r in rows}
 for card in cards['tasks']:
  pid=card['task_id'].split('/')[-1]
  if pid in changed:
   card['evaluation']=deepcopy(by_id[pid]['evaluation'])
   card['has_gold_answer']=False
 store.save('data/base/task_cards.json',cards)
 index=deepcopy(store.read('data/benchmarks/index.json'));update_track_index(index,'arml_national_power',rows);store.save('data/benchmarks/index.json',index)
 report=dict(promoted=changed,operation='repair_existing_scoring',backup=str(store.backup),last_exam_touched=False,paid_calls=0)
 store.save('tmp/arml_power_scoring_repair_20260917.json',report);store.finish(report);print(report)
if __name__=='__main__':main()
