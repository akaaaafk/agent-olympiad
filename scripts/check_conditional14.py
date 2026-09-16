"""Offline configuration/evidence audit. Does not certify a successful live run."""
import json
import sys
from pathlib import Path
from hashlib import sha256

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from otc_artifact_pipeline import prepare_artifact_run
from artifact_contract import delivery_route
from rules.loader import load_rule_card
from evaluation.models import load_rubric
from judge_references import winner_references


def main():
    previous=json.loads((ROOT/'output/conditional14_audit/probes.json').read_text(encoding='utf-8'))
    results=[]
    for old in previous['tracks']:
        cid=old['competition']
        if not (ROOT/'data/benchmarks'/cid/'benchmark.json').exists():
            continue  # Explicitly removed tracks are no longer active catalog entries.
        rows=json.loads((ROOT/'data/benchmarks'/cid/'benchmark.json').read_text(encoding='utf-8'))
        route=delivery_route(load_rule_card(cid,required=True))
        report=dict(competition=cid,records=len(rows),route=route,asset_errors=[],rubric_maxima=[],
                    winner_reference_tasks=[],preflight={})
        for row in rows:
            for asset in row.get('assets',[]):
                path=ROOT/asset['path']
                if not path.is_file() or (asset.get('sha256') and sha256(path.read_bytes()).hexdigest()!=asset['sha256']):
                    report['asset_errors'].append(asset['path'])
            rubric_path=(row.get('evaluation') or {}).get('rubric_path')
            if rubric_path and (row.get('evaluation') or {}).get('evaluator_id')!='programming_judge':
                rubric=load_rubric(ROOT/rubric_path)
                pair=[rubric.total_points,sum(c.max_score for c in rubric.criteria if c.observable)]
                if pair not in report['rubric_maxima']: report['rubric_maxima'].append(pair)
            refs=winner_references(row['problem_id'])
            if refs: report['winner_reference_tasks'].append(dict(problem_id=row['problem_id'],references=len(refs)))
        if route in {'document','slides'}:
            selected=next(r for r in rows if r['problem_id']==old['selected_problem'])
            asset=next((a for a in selected.get('assets',[]) if a.get('role')=='agent_visible' and a['path'].lower().endswith('.pdf')),None)
            if asset:
                for provider in ('openai','perplexity'):
                    try:
                        p=prepare_artifact_run(competition=cid,task_pdf=ROOT/asset['path'],
                            output=ROOT/'output/conditional14_repair/preflight_unused'/cid,
                            provider='perplexity',judge_provider=provider)
                        report['preflight'][provider]=dict(status='PASS',task=selected['problem_id'],
                            rubric=str(p['rubric'].relative_to(ROOT)),winner_references=len(p['winner_references']),
                            max_source_chars=p['contract'].max_source_chars,max_pages=p['contract'].max_pages)
                    except Exception as exc:
                        report['preflight'][provider]=dict(status='BLOCKED',reason=str(exc))
        results.append(report)
    output=ROOT/'output/conditional14_repair/recheck.json'
    output.write_text(json.dumps(dict(scope=f"{sum(r['records'] for r in results)} active records checked for asset/rubric integrity; one existing PDF per artifact track preflighted. No paid or contestant calls.",tracks=results),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for r in results: print(r['competition'],r['records'],'asset_errors='+str(len(r['asset_errors'])),r['preflight'])


if __name__=='__main__': main()
