"""Recover visually checked section maxima; do not call these executable criteria."""
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store,provenance
from scripts.repair_iol_sources_20260913 import read,sha,require

CACHE='data/.cache/eoes_2025_score_metadata_20260913/'
SELECTED={
 'eoes_EOES2025_Task1_TaskSheet-final':dict(task=1,pages=[2,10,22],maxima=[47,37,36],total=120),
 'eoes_EOES2025_Task2_TaskSheet_final':dict(task=2,pages=[2,11,19],maxima=[41.5,43.5,40],total=125)}


def prepare():
    store=Store(ROOT); path='data/benchmarks/eoes/benchmark.json'; rows=read(ROOT/path)
    updates=[]; files=[]; changes=[]
    for pid,expected in SELECTED.items():
        before=next(r for r in rows if r['problem_id']==pid); row=deepcopy(before)
        source=row['solution_file']; sections=[]
        with pymupdf.open(ROOT/source) as doc:
            for n,(page,points) in enumerate(zip(expected['pages'],expected['maxima']),1):
                match=re.match(r'Problem (\d)\.\s*(.*?)\s*\(TOTAL MARKS: ([\d.]+)\)',doc[page-1].get_text(sort=True),re.S)
                require(match and int(match[1])==n and float(match[3])==points,'Published section maximum changed')
                sections.append(dict(id=str(n),title=' '.join(match[2].split()),max_score=points,
                                     source_page=page,source_file=source,source_sha256=sha(ROOT/source)))
        require(sum(s['max_score'] for s in sections)==expected['total'],'Section sum mismatch')
        rubric_path=f"data/rubrics/eoes_2025_task{expected['task']}_published_section_maxima_v1.json"
        rubric=dict(rubric_id=f"eoes_2025_task{expected['task']}_published_section_maxima_v1",total_points=expected['total'],
            official_problem_maxima=sections,criteria=[],source_file=source,source_sha256=sha(ROOT/source),
            source_url=row['source_url'],visibility='judge_only',executable=False,
            score_basis='Sum of the three section maxima printed in the 2025 marking scheme, not a normalized tournament score.',
            limitations=['Section maxima only; detailed answer-dependent grading rules are still in the original marking PDF.',
                'No simulated measurements, missing spreadsheet calculator, observer signatures or physical evidence are invented.',
                'No cross-day or cross-discipline normalization is inferred.'],
            visual_review=dict(renderer='Poppler',pages=expected['pages'],date='2026-09-13'))
        cache_path=CACHE+Path(rubric_path).name; store.save(cache_path,rubric)
        files.append(dict(source=cache_path,destination=rubric_path,sha256=sha(ROOT/cache_path)))
        row['total_points']=expected['total']
        old_reuse=row['evaluation'].pop('rubric_reuse',None)
        if old_reuse: row['evaluation']['superseded_rubric_reuse']=old_reuse
        row['evaluation'].update(rubric_path=rubric_path,official_max_score=expected['total'],
            official_problem_maxima=sections,score_basis=rubric['score_basis'],
            source_repair_status='edition_specific_section_maxima_verified',
            limitations=rubric['limitations'])
        row['assets'].append(dict(path=rubric_path,mime_type='application/json',role='judge_only',sha256=files[-1]['sha256']))
        provenance(row)
        updates.append(dict(before=before,after=row)); changes.append(dict(problem_id=pid,before=before['total_points'],after=expected['total'],basis='printed section maxima'))
    plan=dict(competition_id='eoes',benchmark_path=path,expected_benchmark_sha256=sha(ROOT/path),updates=updates,new_files=files,
              report_path='data/excluded/benchmark_audit_reports/eoes_2025_score_metadata_repair_20260913.json',score_changes=changes,
              summary='Two 2025 task totals recovered as 120 and 125; not an executable lab grading rubric.')
    store.save(CACHE+'plan.json',plan)
    print(json.dumps(changes,indent=2))


if __name__=='__main__': prepare()
