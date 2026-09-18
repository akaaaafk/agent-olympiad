"""Exclude uncertified DebateBench input packets, preserving reviewed tasks."""
from copy import deepcopy
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from src.dataset_catalog import update_track_index


def main():
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_debate_exclusion_' + uuid.uuid4().hex[:8])
    cid = 'debatebench'
    path = f'data/benchmarks/{cid}/benchmark.json'
    original = deepcopy(store.read(path))
    removed = [r for r in original if r['evaluation']['status'] == 'not_ready']
    retained = [r for r in original if r['evaluation']['status'] != 'not_ready']
    expected = {'debatebench_Astana Open Round 5',
                'debatebench_Cambridge IV 2020 Round 1',
                'debatebench_Cambridge IV 2020 Round 2'} | {
        f'debatebench_The Natolin European Round Robin Debating Championships Round {i}'
        for i in range(1, 6)}
    assert len(original) == 32 and len(retained) == 24
    assert {r['problem_id'] for r in removed} == expected
    exclusions = []
    for row in removed:
        limitations = row['evaluation']['limitations']
        evidence = [s for s in limitations if any(marker in s for marker in (
            'relevance to the motion is unverified',
            'complete original background slide and tournament input packet are not certified',
            'verified original motion/infoslide packet is still missing'))]
        assert len(evidence) == 1, row['problem_id']
        for asset in row['assets']:
            assert store.path(asset['path']).is_file(), asset['path']
        exclusions.append({'record': row, 'reason': evidence[0]})
    mini = store.read(f'data/mini_data/benchmarks/{cid}/benchmark.json')
    assert {r['problem_id'] for r in mini} <= {r['problem_id'] for r in retained}
    store.save(path, retained)
    rule_path = f'data/rules/{cid}/evaluation.json'
    rule = store.read(rule_path)
    sync_rules(cid, rule, retained)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, cid, retained)
    store.save('data/benchmarks/index.json', index)
    summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    report = {'competition': cid, 'promoted': [], 'removed': exclusions,
              'retained_ids': [r['problem_id'] for r in retained],
              'mini_membership': 'unchanged', 'raw_sources': 'preserved',
              'paid_model_calls': 0}
    store.save('output/debate_incomplete_exclusion_20260917.json', report)
    store.finish(report)
    assert retained == [r for r in original if r['problem_id'] not in expected]
    print({'removed': len(removed), 'retained': len(retained), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
