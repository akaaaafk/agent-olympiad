import json,re,sys,hashlib
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from evaluation.models import load_rubric,scale_rubric
from evaluation.finalize import _reference_text
YEARS={2016:26,2018:18,2019:21,2023:23}
def test_printed_weights_and_complete_reference():
 rows=json.loads((ROOT/'data/benchmarks/arml_national_power/benchmark.json').read_text())
 for row in rows:
  if row['year'] not in YEARS:continue
  rubric=load_rubric(ROOT/row['evaluation']['rubric_path']);raw=json.loads((ROOT/row['evaluation']['rubric_path']).read_text())
  with pymupdf.open(ROOT/row['source_file']) as doc:
   weights=[int(n) for page in doc for n in re.findall(r'\[\s*(\d+)\s*pts?\.?\s*\]',page.get_text())]
  assert len(weights)==YEARS[row['year']]
  assert [c.max_score for c in rubric.criteria]==weights
  assert sum(weights)==rubric.total_points==row['total_points']==50
  assert [c.max_score for c in scale_rubric(rubric,50).criteria]==weights
  assert len(set(c.id for c in rubric.criteria))==len(weights)
  with pymupdf.open(ROOT/row['solution_file']) as doc:
   reference='\n\n'.join(page.get_text() for page in doc)
  assert reference in _reference_text(row)
  assert hashlib.sha256((ROOT/row['solution_file']).read_bytes()).hexdigest()==raw['provenance']['solution_sha256']
  assert row['gold_label']['expected_answer'] is None
  assert all(p['expected'] is None for p in row['gold_label']['parts'])
  assert row['solution_file'] not in [a['path'] for a in row['assets'] if a['role']=='agent_visible']
def test_reviewed_labels_not_formula_digits():
 rows=json.loads((ROOT/'data/benchmarks/arml_national_power/benchmark.json').read_text())
 maps={r['year']:[c.id for c in load_rubric(ROOT/r['evaluation']['rubric_path']).criteria] for r in rows if r['year'] in YEARS}
 assert maps[2016][:3]==['problem_1a','problem_1b','problem_1c']
 assert maps[2018][9:13]==['problem_6a','problem_6b','problem_6c','problem_6d']
 assert maps[2023][11:15]==['problem_6a','problem_6b','problem_7a','problem_7b']
 assert maps[2023][-6:]==['problem_9'+x for x in 'abcdef']

def test_actual_finalize_uses_printed_criteria_and_full_reference(tmp_path):
 from evaluation.finalize import apply_registered_judge
 from llm import LLMResponse
 rows=json.loads((ROOT/'data/benchmarks/arml_national_power/benchmark.json').read_text())
 for row in rows:
  if row['year'] not in YEARS:continue
  for fraction in [0,.5,1]:
   def judge(request):
    assert 'OFFICIAL REFERENCE / MARKING NOTES' in request.user_prompt
    assert _reference_text(row) in request.user_prompt
    r,_=json.JSONDecoder().raw_decode(request.user_prompt.split('STRUCTURED RUBRIC:',1)[1].lstrip())
    assert len(r['criteria'])==YEARS[row['year']]
    cs=[dict(id=c['id'],score=c['max_score']*fraction,max_score=c['max_score'],evidence=['mock protocol fixture'],justification='Protocol only',confidence=1,observable=True) for c in r['criteria']]
    return LLMResponse(json.dumps(dict(criteria=cs,total_score=50*fraction,max_score=50,warnings=[],limitations=['Mock judge'])), 'mock','offline')
   result=apply_registered_judge(row,'Protocol fixture, not a mathematical solution.',dict(graded=False,method='llm_judge_required'),request_fn=judge,work_dir=tmp_path/str(row['year']),repo_root=ROOT)
   assert result['score']==50*fraction
   assert result['max_score']==50
