"""Read-only preflight of existing full-data written/static review tracks."""
import json
from collections import Counter
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
import run_pipeline as pipeline


def main():
    destination = ROOT / 'output/ctf_docker/static_track_expansion_preflight_20260917.json'
    assert not destination.exists()
    targets = ['iiot', 'ioai_team', 'ccdc']
    data = {cid: pipeline.read(ROOT / f'data/benchmarks/{cid}/benchmark.json') for cid in targets}
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='static_preflight_', dir=ROOT/'tmp') as folder:
        for variant in ['single_agent','decentralized','centralized','vallina_otc','otc']:
            out = Path(folder)/variant
            registry = pipeline.register(out)
            config = SimpleNamespace(provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
                judge_provider='tinker', judge_model='Qwen/Qwen3.6-35B-A3B', system_variant=variant)
            for job in registry['jobs']:
                cid = job['competition']
                if cid not in targets:
                    continue
                rows = [r for r in data[cid] if r['problem_id'] in job['problem_ids']]
                state = 'expected_blocked'
                if job['blockers']:
                    assert all(r['evaluation']['status']=='not_ready' for r in rows), job
                else:
                    assert all(r['evaluation']['evaluator_id']=='rubric_llm_v1' for r in rows)
                    identities = {}
                    assert pipeline.command(job,out,config,expected_identities=identities)
                    assert identities[job['id']]['settings']['evaluation']['judge_collab'] == (variant!='single_agent')
                    state = 'prepared'
                outcomes.append({'competition':cid,'session':job['session'],'variant':variant,'state':state,'blockers':job['blockers']})
    report = {'passed':True,'paid_model_calls':0,'scope':'Existing static source/written artifact review; no official runtime/simulation/live-service score.',
              'tracks':{cid:{'records':len(rows),'statuses':dict(Counter(r['evaluation']['status'] for r in rows)),
                             'preflight':dict(Counter(o['state'] for o in outcomes if o['competition']==cid))} for cid,rows in data.items()},'jobs':outcomes}
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='jobs'}))


if __name__ == '__main__':
    main()
