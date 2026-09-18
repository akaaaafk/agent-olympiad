"""Promote only freshly checked CTF records; preserve membership and mini tasks."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    parser.add_argument('--problem', action='append', help='Explicit bounded subset to promote from a scoped validation report.')
    args = parser.parse_args()
    report_path = (ROOT / args.report).resolve()
    if not report_path.is_relative_to(ROOT / 'output/ctf_docker'):
        raise ValueError('Unrecognized report location')
    report = json.loads(report_path.read_text())
    cid = report['competition']
    if cid not in {'cybench','nyu_ctf_bench'}:
        raise ValueError('Unsupported competition')
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_ctf_' + uuid.uuid4().hex[:8])
    path = f'data/benchmarks/{cid}/benchmark.json'
    assert store.sha(path) == report['benchmark_sha256'], 'Benchmark changed after validation'
    rows = deepcopy(store.read(path))
    results = {r['problem_id']:r for r in report['records']}
    assert len(results) == len(report['records'])
    ids = {r['problem_id'] for r in rows}
    if args.problem:
        assert set(results) == set(args.problem) and set(results) <= ids, 'Scoped validation membership mismatch'
    else:
        assert set(results) == ids, 'Validation is incomplete'
    before = deepcopy(rows)
    changed = []
    for row in rows:
        if row['problem_id'] not in results:
            continue
        result = results[row['problem_id']]
        if result['status'] != 'passed':
            continue
        assert all(result.get(k) for k in ('startup','dependency_check','input_hashes','isolated','exact_grading'))
        assert result.get('plaintext_flag_absent') or result.get('embedded_flag_review')
        e = row['evaluation']
        e.update(status='ready_with_limitations', evaluator_id='gold_answer_v1', deliverable='ctf_flag',
                 reason='Fresh isolated Docker startup, dependency, asset delivery, endpoint and exact flag grading checks passed.',
                 limitations=[
                     'Final-flag benchmark only; guided subtasks and their partial credit are not reproduced.',
                     'Startup, dependencies, asset hashes and service TCP reachability were checked without model calls; successful solving is not guaranteed.',
                     'Reference acceptance and wrong/empty rejection were checked; no end-to-end exploit or independently recovered service flag is claimed.'
                 ],
                 runtime_validation={'report':report_path.relative_to(ROOT).as_posix(),
                                     'report_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
                                     'contestant_image':report['contestant_image'], 'status':'passed'},
                 score_basis='One point for the registered upstream final flag, zero otherwise; not an LLM score.')
        changed.append(row['problem_id'])
    # Enforce the scope: only evaluation metadata may change.
    for old, new in zip(before, rows):
        assert {k:v for k,v in old.items() if k != 'evaluation'} == {k:v for k,v in new.items() if k != 'evaluation'}
    store.save(path, rows)
    rule_path = f'data/rules/{cid}/evaluation.json'
    rule = deepcopy(store.read(rule_path))
    sync_rules(cid, rule, rows)
    store.save(rule_path, rule)
    # The same competition rule semantics apply to mini; only its counts and paths differ.
    mini_path = f'data/mini_data/benchmarks/{cid}/benchmark.json'
    mini = store.read(mini_path)
    mini_rule = json.loads(json.dumps(rule).replace('data/', 'data/mini_data/'))
    mini_rule['scoring']['evaluation_status_counts'] = dict(Counter(r['evaluation']['status'] for r in mini))
    store.save(f'data/mini_data/rules/{cid}/evaluation.json', mini_rule)
    store.finish({'operation':'verified_ctf_expansion', 'competition':cid,
                  'promoted':changed, 'blocked':[r for r in report['records'] if r['status']!='passed'],
                  'mini_task_membership_and_records':'unchanged'})
    print(json.dumps({'competition':cid,'promoted':len(changed),
                     'validated_blocked':sum(r['status']!='passed' for r in results.values()),
                     'status_counts':dict(Counter(r['evaluation']['status'] for r in rows)),
                     'backup':str(store.backup)}))


if __name__ == '__main__':
    main()
