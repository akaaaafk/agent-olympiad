"""Apply the user's written-only scope and reviewed gold/proof scoring policy.

New batch only; never replays an older repair or exposes scoring references.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store

REPORT = 'data/judge_references/scoring_scope_20260916.json'
GOLD = {
    2013: {'1':'sqrt(3)/2','2':'16','3':'7/2','4':'72','5':'2013^4025'},
    2014: {'2':'127','7':'7'}, 2015: {'1':'-28','9':'13'},
    2016: {'2':'329','3':'14040'}, 2017: {'2':'No','8':'Yes'},
    2019: {'2':'No','4':'1, 2, 3, 4','8':'Yes'}, 2021: {'5':'36'},
    2022: {'1':'5','2':'4'}, 2023: {'1':'12','4':'9','5':'4950'},
    2024: {'1':'550','2':'18','5':'Yes','9':'6014950'},
    2025: {'2':'2','4':'8096','7':'No'}, 2026: {'3':'10','5':'3037'},
}


def pdf_text(path):
    import pymupdf
    with pymupdf.open(ROOT/path) as doc:
        return '\n'.join(p.get_text() for p in doc)


def main():
    if (ROOT/REPORT).exists():
        raise RuntimeError('Frozen batch already exists; do not replay')
    store = Store(ROOT, ROOT.parent/'dataset_backups')
    report = dict(operation='written_scope_and_mixed_gold', role='judge_only',
                  scopes={}, hmmt={}, arml={}, pumac={})
    # Pin all target data before writes; Store also rejects concurrent edits.
    target = ['ijso_practical','iypt','itym','hmmt_team','arml_power','pumac_power']
    payloads = {c:deepcopy(store.read(f'data/benchmarks/{c}/benchmark.json')) for c in target}
    report['before_snapshot'] = {f'data/benchmarks/{c}/benchmark.json':store.sha(f'data/benchmarks/{c}/benchmark.json') for c in target}
    scopes = {
        'ijso_practical': ('written_report', 'One shared written scientific report.',
            'Score only the written experimental report from supplied observations and data. No physical execution, instrument operation, or live delivery is assessed.'),
        'iypt': ('research_report', 'One shared written physics research report.',
            'Score only the written research report: theory, investigation design, documented evidence and clarity. No physical execution, oral defense, opponent or reviewer exchange is assessed.'),
        'itym': ('research_solution_paper', 'One shared written mathematical research paper.',
            'Score only the written mathematical research paper. No live mathematical fight, oral defense, opponent or reviewer exchange is assessed.'),
    }
    for cid,(deliverable,answer,basis) in scopes.items():
        for row in payloads[cid]:
            e=row['evaluation']
            e.update(deliverable=deliverable, score_basis=basis, assessment_scope='written_only',
                     excluded_assessment=['physical_execution','oral_delivery','live_opponents'],
                     official_score_equivalent=False,
                     limitations=['Uses the declared benchmark rubric, not a full official competition score.'],
                     status='ready')
            row['gold_label']['grading_rubric']=basis
        for component in ['competition','collaboration','evaluation']:
            path=f'data/rules/{cid}/{component}.json'
            card=deepcopy(store.read(path))
            if component=='competition':
                card['rules_text']=answer+' '+basis+' Distinguish observations, simulations and proposals; do not invent evidence.'
                card['human_constraints']=[answer,basis,'Do not fabricate measurements, results or citations.']
                card['deliverable']['answer_format']=answer
                card['provenance'].setdefault('adaptations',[]).append('User-selected written-only assessment scope on 2026-09-16: '+basis)
                if cid=='iypt':
                    card['deliverable']['original_official_deliverable']=card['deliverable'].get('official_deliverable')
                    card['deliverable'].update(official_deliverable='lab_report',mime_types=['application/pdf'])
            elif component=='collaboration':
                card['rule_sections']['competition_format']=[answer,basis]
                card['rule_sections']['deliverable_format']=[answer]
                if cid=='iypt':
                    pipeline=card['simulation']['deliverable_pipeline']
                    pipeline.update(kind='document',source_format='text',max_source_chars=60000)
            else:
                card['evaluation_guidance']=basis+' Assess team collaboration separately. Missing physical or oral performance is outside scope and must not be penalized.'
                card['scoring'].update(score_basis=basis,assessment_scope='written_only',official_score_equivalent=False)
                availability=card['scoring'].get('current_repository_availability',{})
                availability.update(submission_adaptation=deliverable,proxy_limitations=['Benchmark rubric; not an official whole-contest score.'])
            store.save(path,card)
        report['scopes'][cid]=dict(records=len(payloads[cid]),scope=basis)
    rp='data/rubrics/iypt_research_report_100_v1.json'
    rubric=deepcopy(store.read(rp));rubric['title']='IYPT written research report benchmark rubric'
    rubric['scoring_basis']=scopes['iypt'][2]
    rubric['criteria'][-1].update(name='Report clarity',description='Written report communicates assumptions, methods, evidence, conclusions and citations clearly. No slide layout or oral delivery is assessed.')
    rubric['not_observable_from_deck']=[]
    rubric['excluded_assessment']=['physical execution','oral delivery','live opponent/reviewer exchanges']
    store.save(rp,rubric)

    plan=store.read('data/rubrics/hmmt_team/official_reference_plan_20260912.json')
    refs={r['year']:r for r in plan['records']}
    for row in payloads['hmmt_team']:
        exact=GOLD.get(row['year'],{})
        source=refs[row['year']]
        if store.sha(source['solution_file'])!=source['solution_sha256']:
            raise ValueError('HMMT reviewed solution hash changed')
        for part in row['gold_label']['parts']:
            p=next(x for x in source['parts'] if x['id']==part['id'])
            if part['id'] in exact:
                part.update(expected=exact[part['id']],match_mode='normalized',answer_type='short_answer',
                    reference=p['reference_text'],source_verified=True,
                    verification='Rendered official answer box reviewed; benchmark final-answer scoring override.')
            else:
                part.update(expected=None,match_mode='reference_llm')
        row['evaluation'].update(grading_policy='gold_else_llm_v1',
            score_basis='Per-part gold final-answer scoring when verified; remaining proof/complex-answer parts use the official-reference LLM rubric. Printed per-part maxima are preserved.',
            official_score_equivalent=False,
            limitations=['Gold parts assess the final answer only, as a user-selected benchmark adaptation; official HMMT requires justification even for numerical answers.',
                         'Remaining proof/complex-answer parts use LLM partial credit; PDF notation remains authoritative.'])
        report['hmmt'][row['problem_id']]=dict(gold_part_ids=list(exact),llm_parts=10-len(exact),source_sha256=source['solution_sha256'])
    cp='data/rules/hmmt_team/competition.json'
    card=deepcopy(store.read(cp))
    guidance='Benchmark scoring override: submit numbered final answers for verified short-answer parts; include complete proofs/reasoning for remaining parts. Exact gold is used where a final answer is verified, otherwise an official-reference LLM judge is used. This is not the official HMMT proof-grading policy.'
    card['rules_text']+=' '+guidance
    card['human_constraints'].append(guidance)
    card['deliverable']['answer_format']=guidance
    store.save(cp,card)
    ep='data/rules/hmmt_team/evaluation.json'
    card=deepcopy(store.read(ep));card['evaluation_guidance']=guidance
    card['scoring']['grading_policy']='gold_else_llm_v1';store.save(ep,card)

    # All active ARML Power rubric maxima already sum to the printed 40.
    # Deliver the full source reference inside a criterion (no reference truncation).
    for row in payloads['arml_power']:
        path=row['evaluation']['rubric_path'];rubric=deepcopy(store.read(path))
        assert sum(c['max_score'] for c in rubric['criteria'])==row['total_points']==40
        source=row['solution_file'];text=pdf_text(source)
        if 'OFFICIAL REFERENCE' not in rubric['criteria'][0]['description']:
            rubric['criteria'][0]['description']+='\n\nOFFICIAL REFERENCE FOR THE COMPLETE PACKET (JUDGE ONLY; apply to the corresponding problems throughout this rubric):\n'+text
            rubric.update(official_solution_file=source,official_solution_sha256=store.sha(source))
            store.save(path,rubric)
        row['evaluation']['judge_assets']=list(dict.fromkeys(row['evaluation'].get('judge_assets',[])+[source]))
        report['arml'][row['problem_id']]=dict(printed_maximum=40,rubric_maximum=40,solution_sha256=store.sha(source),partial_credit='LLM benchmark judgment, not official marking calibration')

    mapping=deepcopy(store.read('data/rubrics/pumac_power_official_rubrics.json'))
    for row in payloads['pumac_power']:
        text=pdf_text(row['source_file'])
        report['pumac'][row['problem_id']]=dict(source_sha256=store.sha(row['source_file']),
            point_marker_candidates=re.findall(r'\((?:[^\n)]{0,10})\d+(?:[^\n)]{0,10})(?:pts?|points)\)',text,re.I),
            caution='Candidate list may include contents, section totals and subparts; never sum blindly.')
        if row['year']!=2009:
            continue
        pattern=r'Problem\s+(\d+\.\d+)\s*\((\d+)pts\)'
        problems=list(re.finditer(pattern,text));solution=pdf_text(row['solution_file'])
        answers=list(re.finditer(pattern,solution))
        assert len(problems)==len(answers)==21
        assert [(m[1],m[2]) for m in problems]==[(m[1],m[2]) for m in answers]
        assert sum(int(m[2]) for m in problems)==86
        assert '21 Problems; 86 Points' in text and '21 Problems; 86 Points' in solution
        criteria=[]
        for n,m in enumerate(problems):
            statement=text[m.start():problems[n+1].start() if n+1<len(problems) else len(text)]
            a=answers[n];reference=solution[a.start():answers[n+1].start() if n+1<len(answers) else len(solution)]
            criteria.append(dict(id='problem_'+m[1],name='Problem '+m[1],max_score=int(m[2]),observable=True,
                description='Grade this problem only. Require justified reasoning, including yes/no and calculation questions; bare answers earn no credit under the printed rules. Accept valid alternative proofs. Partial credit is benchmark judgment. PDF typesetting is authoritative.\nSTATEMENT:\n'+statement+'\nOFFICIAL REFERENCE (JUDGE ONLY):\n'+reference))
        path='data/rubrics/pumac_power_2009_official_reference_v2.json'
        store.save(path,dict(rubric_id='pumac_power_2009_official_reference_v2',title='PUMaC 2009-10 A Version: 21 problems, 86 printed points',
            role='judge_only',total_points=86,criteria=criteria,official_solution_file=row['solution_file'],official_solution_sha256=store.sha(row['solution_file'])))
        row['total_points']=86
        row['evaluation'].update(rubric_path=path,score_basis='Sum of 21 printed per-problem maxima: 86 points. Official references anchor correctness; LLM partial credit is a benchmark adaptation.')
        entry=mapping[row['problem_id']]
        entry.update(official_total_points=86,official_printed_point_values_in_order=[int(m[2]) for m in problems],
            coverage='all_21_problem_weights_and_official_references_matched',allocation_note='21 per-problem maxima sum to the printed 86; detailed partial-credit calibration is not recovered.')
        report['pumac'][row['problem_id']].update(recovered_maximum=86,recovered_problems=21)
    store.save('data/rubrics/pumac_power_official_rubrics.json',mapping)
    for cid,rows in payloads.items():store.save(f'data/benchmarks/{cid}/benchmark.json',rows)
    report['changes']=store.changes
    store.save(REPORT,report);store.finish(report)
    print('Backup:',store.backup)
    print('Gold parts:',sum(len(v) for v in GOLD.values()))
    print('Report:',REPORT)


if __name__=='__main__':main()
