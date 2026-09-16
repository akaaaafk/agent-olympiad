"""Conservative official-PDF answer boundaries; unresolved packets stay blocked."""
import json
import re
import sys
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def normalize(text):
    return re.sub(r'\s+', '', text).casefold().replace('\u200b', '')


def recover(row):
    with pymupdf.open(ROOT / row['source_file']) as doc:
        text = '\n'.join(p.get_text() for p in doc).replace('\u00a0', ' ')
    markers = list(re.finditer(r'(?im)^[ \t]*ANSWER\s*:[ \t]*', text))
    parts = row['gold_label']['parts']
    if len(markers) != len(parts):
        raise ValueError(f'Official answer marker count {len(markers)} differs from stored part count {len(parts)}')
    cursor = 0
    prompts = []
    evidence = []
    for i, (marker, part) in enumerate(zip(markers, parts)):
        prompt = text[cursor:marker.start()].strip()
        tail = text[marker.end():markers[i+1].start() if i+1<len(markers) else len(text)]
        boundary = re.search(r'\n[ \t]*\n|\n(?=[ \t]*(?:\(\d+\)|\d+[.)]\s|BONUS\s*:|(?:First|Second|Third|Fourth)\s+Quarter))',tail,re.I)
        end = boundary.start() if boundary else len(tail)
        answer = tail[:end].strip()
        if not answer or len(answer)>650 or normalize(part['expected']) not in normalize(answer):
            raise ValueError(f"{part['id']}: stored answer not confirmed within bounded official answer block")
        if any(answer.count(a)!=answer.count(b) for a,b in [('(',')'),('[',']')]):
            raise ValueError(f"{part['id']}: unbalanced answer annotation at boundary")
        if len(prompt)<20 or re.search(r'(?i)\bANSWER\s*:|\b(?:accept|prompt on|do not accept)\b',prompt):
            raise ValueError(f"{part['id']}: incomplete question or possible judge annotation")
        prompts.append(f"[{part['id']}] {prompt}")
        evidence.append({'id':part['id'],'official_answer_block':answer})
        cursor = marker.end()+end
    return '\n\n'.join(prompts), evidence


def main():
    store=Store(ROOT)
    rows=store.read('data/benchmarks/history_olympiad/benchmark.json')
    audit=[]
    for row in rows:
        try:
            prompt,evidence=recover(row)
        except ValueError as exc:
            row['evaluation'].update(status='not_ready',evaluator_id=None,reason=str(exc))
            audit.append({'id':row['problem_id'],'status':'not_ready','reason':str(exc)})
            continue
        row['problem_description']=prompt
        row['gold_label']['expected_answer']=None
        row['total_points']=sum(p['points'] for p in row['gold_label']['parts'])
        row['evaluation'].update(status='ready_with_limitations',evaluator_id='gold_answer_v1',
            score_basis='One point per stored answer; conservative normalized exact matching; not official match points.',
            limitations=['Static full-packet answer sheet; no buzzer, progressive clues, opponent or timed quarter scoring.',
                         'Stored canonical answer strings only; moderator acceptance rules are not fully modeled.'])
        row['evaluation'].pop('reason',None)
        audit.append({'id':row['problem_id'],'status':'recovered','source':row['source_file'],
                      'source_sha256':store.sha(row['source_file']),'parts':evidence})
    store.save('data/benchmarks/history_olympiad/benchmark.json',rows)
    comp=store.read('data/rules/history_olympiad/competition.json')
    comp['protocol']='static_answer_sheet_proxy'
    comp['profile']='proxy'
    comp['deliverable']['answer_format']='Submit numbered answers Q1: ..., Q2: ... for the complete exposed packet.'
    comp['rules_text']='History Bowl static answer-sheet benchmark adaptation. Read the full provided packet, discuss within the team, and submit numbered answers Q1, Q2, etc. Use only provided materials; no internet, calculators or code execution. Scoring is one point per correct canonical answer. No live buzz, progressive clue timing, opponent outcome, quarter-dependent points or moderator ruling is reproduced.'
    comp['provenance'].setdefault('adaptations',[]).append('Static full-packet answer sheet with one-point canonical answers; official match rules retained only as source context.')
    comp['provenance'].setdefault('original_human_constraints',comp['human_constraints'])
    comp['provenance'].setdefault('original_execution',comp['execution'])
    comp['human_constraints']=[comp['rules_text']]
    comp['execution']={'official_minutes':None,'adaptation':'Runner safety budget only; no official stage or quarter clocks.'}
    comp['team']['collaboration']='Team discussion and review of the full exposed answer-sheet packet.'
    store.save('data/rules/history_olympiad/competition.json',comp)
    collab=store.read('data/rules/history_olympiad/collaboration.json')
    collab['simulation']['deliverable_pipeline']={'kind':'native','fidelity':'static_answer_sheet_proxy'}
    collab['agent_constraints']=[comp['rules_text'],'Do not access hidden answers, original answer-bearing PDFs or evaluator files.']
    for role in collab['agent_roles']:
        role['duties']=['Discuss the exposed packet and verify numbered answers. Only designated submitters submit.']
    collab['rule_sections']={'competition_format':[comp['rules_text']], 'deliverable_format':[comp['deliverable']['answer_format']]}
    for role in collab['agent_roles']:
        for section in role.get('rule_expertise', []):
            collab['rule_sections'].setdefault(section,[comp['rules_text']])
    store.save('data/rules/history_olympiad/collaboration.json',collab)
    evaluation=store.read('data/rules/history_olympiad/evaluation.json')
    evaluation['scoring']['mode']='canonical_answer_accuracy'
    evaluation['evaluation_guidance']=comp['rules_text']+' Per-record readiness controls whether evaluation is allowed.'
    store.save('data/rules/history_olympiad/evaluation.json',evaluation)
    out=ROOT/'output/readiness_routes_20260915';out.mkdir(parents=True,exist_ok=True)
    (out/'history_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'recovered':sum(a['status']=='recovered' for a in audit),'blocked':sum(a['status']=='not_ready' for a in audit)}
    store.finish(summary)
    print(summary)


if __name__=='__main__':main()
