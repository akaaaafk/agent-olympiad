"""Check expanded metadata, generated packages and all five baseline preflights."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_pipeline as pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--competition', required=True, choices=['cybench','nyu_ctf_bench'])
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    cid = args.competition
    rows = pipeline.read(ROOT / f'data/benchmarks/{cid}/benchmark.json')
    ids = {r['problem_id'] for r in rows}
    scorecards = {r['problem_id']:r for r in pipeline.read(ROOT/f'data/rubrics/task_scorecards/{cid}.json')['records']}
    assert set(scorecards) == ids
    base = {r['task_id']:r for r in pipeline.read(ROOT/'data/base/task_cards.json')['tasks'] if r['category']==cid}
    last = {r['task_id']:r for r in pipeline.read(ROOT/'data/last_exam/task_cards.json')['tasks'] if r['competition_id']==cid}
    assert set(base) == set(last) == {cid+'/'+pid for pid in ids}
    for row in rows:
        pid = row['problem_id']
        e = row['evaluation']
        assert base[cid+'/'+pid]['evaluation'] == e
        reference = pipeline.read(ROOT/f'data/last_exam/tasks/{cid}/{pid}/eval/reference.json')
        assert reference['evaluation'] == e
        assert scorecards[pid]['evaluation_status'] == e['status']
        if e['status'] == 'ready_with_limitations':
            evidence = e['runtime_validation']
            path = ROOT/evidence['report']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence['report_sha256']
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='ctf_preflight_', dir=ROOT/'tmp') as folder:
        for variant in ['single_agent','decentralized','centralized','vallina_otc','otc']:
            out = Path(folder)/variant
            registry = pipeline.register(out)
            config = SimpleNamespace(provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
                judge_provider='tinker', judge_model='Qwen/Qwen3.6-35B-A3B',system_variant=variant)
            for job in registry['jobs']:
                if job['competition'] != cid:
                    continue
                if job['blockers']:
                    assert all(next(r for r in rows if r['problem_id']==pid)['evaluation']['status']=='not_ready' for pid in job['problem_ids'])
                    outcomes.append({'problem':job['session'],'variant':variant,'state':'expected_blocked'})
                    continue
                identity = {}
                command = pipeline.command(job,out,config,expected_identities=identity)
                assert command and identity[job['id']]['settings']['evaluation']['judge_collab'] == (variant!='single_agent')
                outcomes.append({'problem':job['session'],'variant':variant,'state':'prepared'})
    report = {'competition':cid,'passed':True,'records':len(rows),'counts':dict(Counter(r['state'] for r in outcomes)),
              'metadata_and_generated_packages':'matched','paid_model_calls':0,'jobs':outcomes}
    dest = (ROOT/args.output).resolve()
    assert dest.is_relative_to(ROOT/'output/ctf_docker') and not dest.exists()
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='jobs'}))


if __name__ == '__main__':
    main()
