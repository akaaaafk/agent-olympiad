"""Exclude source-incomplete CFA seasons; preserve the reviewed 2016 task."""
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
    store.backup = store.backup.with_name(store.backup.name + '_cfa_exclusion_' + uuid.uuid4().hex[:8])
    cid = 'cfa_research_challenge'
    path = f'data/benchmarks/{cid}/benchmark.json'
    original = deepcopy(store.read(path))
    ready = [r for r in original if r['evaluation']['status'] == 'ready_with_limitations']
    removed = [r for r in original if r['evaluation']['status'] == 'not_ready']
    assert len(original) == 17 and len(removed) == 16
    assert [r['problem_id'] for r in ready] == ['cfa_research_challenge_2016']
    assert {r['year'] for r in removed} == set(range(2010, 2027)) - {2016}
    for row in removed:
        assert not row.get('source_file')
        assert 'research inputs' in row['evaluation']['reason']
        public = [a['path'] for a in row['assets'] if a['role'] == 'agent_visible']
        assert not public or all('/rules/' in p for p in public)
    mini = store.read(f'data/mini_data/benchmarks/{cid}/benchmark.json')
    assert {r['problem_id'] for r in mini} == {r['problem_id'] for r in ready}
    store.save(path, ready)
    rule_path = f'data/rules/{cid}/evaluation.json'
    rule = store.read(rule_path)
    sync_rules(cid, rule, ready)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, cid, ready)
    store.save('data/benchmarks/index.json', index)
    summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    report = {'competition': cid, 'promoted': [], 'removed': [
        {'record': r, 'reason': r['evaluation']['reason']} for r in removed],
        'retained_ids': [r['problem_id'] for r in ready],
        'mini_membership': 'unchanged', 'raw_sources': 'preserved', 'paid_model_calls': 0}
    store.save('output/cfa_incomplete_exclusion_20260917.json', report)
    store.finish(report)
    assert ready[0] == next(r for r in original if r['year'] == 2016)
    print({'removed': len(removed), 'retained': len(ready), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
