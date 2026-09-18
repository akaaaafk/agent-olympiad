"""Recover matched 2017 section weights; record the 2018 source conflict."""
from copy import deepcopy
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.apply_scoring_scope_20260916 import pdf_text

REPORT='data/judge_references/pumac_section_review_20260916.json'
PATTERN=r'(?m)^(\d+)\s*\n([^\n]{1,75})\((\d+) points\)'


def sections(text):
    # Contents repeats the same labels. The last occurrence is the body heading.
    found={}
    for m in re.finditer(PATTERN,text):found[m[1]]=m
    return sorted(found.values(),key=lambda m:m.start())


def main():
    if (ROOT/REPORT).exists():raise RuntimeError('Frozen review exists; do not replay')
    store=Store(ROOT,ROOT.parent/'dataset_backups')
    path='data/benchmarks/pumac_power/benchmark.json'
    rows=deepcopy(store.read(path));mapping=deepcopy(store.read('data/rubrics/pumac_power_official_rubrics.json'))
    report=dict(role='judge_only',before_sha256=store.sha(path),source_headers={})
    for row in rows:
        import pymupdf
        with pymupdf.open(ROOT/row['source_file']) as d:problem_header=d[0].get_text()[:180]
        with pymupdf.open(ROOT/row['solution_file']) as d:solution_header=d[0].get_text()[:180]
        report['source_headers'][row['problem_id']]=dict(problem=problem_header,solution=solution_header,
            source_sha256=store.sha(row['source_file']),solution_sha256=store.sha(row['solution_file']))
        if row['year'] not in [2017,2018]:continue
        text=pdf_text(row['source_file']);ref=pdf_text(row['solution_file'])
        p=sections(text);s=sections(ref)
        weights=[(m[1],m[2].strip(),int(m[3])) for m in p]
        refs=[(m[1],m[2].strip(),int(m[3])) for m in s]
        report[row['problem_id']]=dict(problem_sections=weights,solution_sections=refs)
        if row['year']==2018:
            assert [m[2] for m in weights]==[93,63,92,390]
            assert [m[2] for m in refs]==[93,57,92,240]
            conflict='2018 problem and solution section maxima disagree: problem 93/63/92/390 (sum 638), solution 93/57/92/240 (sum 482). Do not transfer solution weights or claim official partial-credit allocation; item-level correspondence remains unresolved.'
            old=row['evaluation'].get('limitations',[])
            row['evaluation']['limitations']=([old] if isinstance(old,str) else list(old))+[conflict]
            row.setdefault('source_review',{})['scoring_conflict']=report[row['problem_id']]
            mapping[row['problem_id']]['allocation_note']=conflict
            continue
        assert weights==refs and len(p)==5 and sum(m[2] for m in weights)==299
        criteria=[]
        for n,(m,a) in enumerate(zip(p,s)):
            statement=text[m.start():p[n+1].start() if n+1<len(p) else len(text)]
            reference=ref[a.start():s[n+1].start() if n+1<len(s) else len(ref)]
            criteria.append(dict(id='section_'+m[1],name=m[2].strip(),max_score=int(m[3]),observable=True,
                description='Assess the numbered problems within this section only. Respect printed subproblem maxima without double-counting parent and child weights. Require justified proofs; accept valid alternatives. Detailed partial credit is benchmark judgment.\nSTATEMENT:\n'+statement+'\nOFFICIAL REFERENCE (JUDGE ONLY):\n'+reference))
        rp='data/rubrics/pumac_power_2017_official_sections_v2.json'
        store.save(rp,dict(rubric_id='pumac_power_2017_official_sections_v2',title='PUMaC 2017 printed section maxima',
            role='judge_only',total_points=299,criteria=criteria,official_solution_file=row['solution_file'],official_solution_sha256=store.sha(row['solution_file'])))
        row['total_points']=299
        row['evaluation'].update(rubric_path=rp,score_basis='Five matching printed section maxima sum to 299 points. Official-reference LLM assesses proofs; historical detailed partial-credit calibration is not reproduced.')
        mapping[row['problem_id']].update(official_total_points=299,official_printed_section_maxima=weights,
            coverage='all_five_section_maxima_matched_between_problem_and_solution',
            allocation_note='Printed chapter maxima, not a reconstructed detailed per-item partial-credit scheme.')
    store.save(path,rows);store.save('data/rubrics/pumac_power_official_rubrics.json',mapping)
    store.save(REPORT,report);store.finish(report)
    print('Backup:',store.backup)


if __name__=='__main__':main()
