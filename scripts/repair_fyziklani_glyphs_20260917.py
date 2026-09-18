"""Repair source-verified Fyziklani math transcription; no PDF or last_exam edits."""
import json,hashlib,sys
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from remove_eoes_companion_records_20260917 import DirectStore
REPLACEMENTS={
2023:[('V (t) =\n\x1a\n0 V\n−T < t < 0;\n9.0 V\n0 ≤t < T.','V(t) = { 0 V for −T < t < 0; 9.0 V for 0 ≤ t < T }.') ,('∆p = A\nr\n\x14\n1 −\n\x10r0\nr\n\x116\x15\n,','∆p = (A/r) * [1 − (r0/r)^6],')],
2024:[('M = kφ =\nEd4\n64ND φ ,','M = kφ = (E*d^4/(64*N*D)) * φ,'),('m\nd\nD\nN\n\x01F\nFigure 1: Scheme of the door mechanism.','m\nd\nD\nN\nF (upward force vector)\nFigure 1: Scheme of the door mechanism.')]
}
def main():
 s=DirectStore(ROOT);bp='data/benchmarks/fyziklani/benchmark.json';rows=deepcopy(s.read(bp));before=deepcopy(rows);changes=[]
 for row in rows:
  year=row['year']
  if year not in REPLACEMENTS:continue
  prompt=row['problem_description']
  if all(new in prompt for _,new in REPLACEMENTS[year]):continue
  for old,new in REPLACEMENTS[year]:
   assert prompt.count(old)==1,(year,repr(old));prompt=prompt.replace(old,new)
  assert not [c for c in prompt if ord(c)<32 and c not in '\n\r\t']
  base=ROOT/'data/base/tasks/fyziklani'/row['problem_id']/'base/input/problem.md'
  assert base.read_text(encoding='utf-8')==(row['problem_description']+'\n').replace('\r\n','\n').replace('\r','\n')
  s.save_text(base,prompt+'\n');row['problem_description']=prompt;changes.append(row['problem_id'])
 if not changes:print('Already repaired');return
 s.save(bp,rows)
 for old,new in zip(before,rows):assert {k:v for k,v in old.items() if k!='problem_description'}=={k:v for k,v in new.items() if k!='problem_description'}
 report=dict(changed=changes,replacements={str(y):[dict(before=old,after=new) for old,new in pairs] for y,pairs in REPLACEMENTS.items()},source_evidence={'2023':{'raw_pdf':'data/raw/fyziklani/2023/fyziklani_2023_en.pdf','pages':[53,75]},'2024':{'raw_pdf':'data/raw/fyziklani/2024/fyziklani_2024_en.pdf','pages':[18]}},pdf_hashes={a['path']:s.sha(a['path']) for r in rows if r['year'] in REPLACEMENTS for a in r['assets']},last_exam_touched=False,archive_created=False,scope='Four local text replacements; all remaining record fields and PDF files preserved.')
 s.save('tmp/fyziklani_glyph_repair_20260917.json',report);print(changes)
if __name__=='__main__':main()
