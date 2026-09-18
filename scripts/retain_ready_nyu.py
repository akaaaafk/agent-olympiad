"""Retain validated CTF tasks only, with recoverable record backups."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from src.dataset_catalog import update_track_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--competition', choices=['nyu_ctf_bench', 'cybench'], default='nyu_ctf_bench')
    cid = parser.parse_args().competition
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_retain_' + cid + '_' + uuid.uuid4().hex[:8])
    path = f'data/benchmarks/{cid}/benchmark.json'
    rows = store.read(path)
    ready = [r for r in rows if r['evaluation']['status'] == 'ready_with_limitations']
    removed = [r for r in rows if r not in ready]
    if cid == 'nyu_ctf_bench':
        assert any(r['year'] == 2021 for r in ready), 'A validated 2021 task is required first'
    assert all(r['evaluation']['status'] == 'not_ready' for r in removed)
    ids = {r['problem_id'] for r in ready}
    mini = store.read(f'data/mini_data/benchmarks/{cid}/benchmark.json')
    assert {r['problem_id'] for r in mini} <= ids, 'Mini contains excluded tasks'
    for row in ready:
        import hashlib
        evidence = row['evaluation']['runtime_validation']
        assert hashlib.sha256((ROOT / evidence['report']).read_bytes()).hexdigest() == evidence['report_sha256']
    store.save(path, ready)
    rule_path = f'data/rules/{cid}/evaluation.json'
    rule = store.read(rule_path)
    sync_rules(cid, rule, ready)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, cid, ready)
    store.save('data/benchmarks/index.json', index)
    benchmarks = {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']}
    summary_and_figures(store, index, benchmarks)
    store.finish({'operation': 'retain_validated_ctf_only', 'competition': cid, 'retained': len(ready),
                  'removed_records': removed, 'raw_sources': 'preserved', 'mini': 'unchanged'})
    print({'retained': len(ready), 'removed': len(removed),
           'years': dict(Counter(r['year'] for r in ready)), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
