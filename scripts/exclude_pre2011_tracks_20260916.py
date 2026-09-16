"""Keep strictly post-2010 editions in five user-selected tracks."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    store = Store(ROOT)
    report = {'operation': 'user_requested_post2010_filter',
              'policy': 'Keep year >= 2011; preserve unknown years without inventing dates.',
              'tracks': {}, 'preserved': 'Raw sources and historical experiment outputs.'}
    for cid in ('iypt', 'ijso_practical', 'iol_team', 'itym', 'eoes'):
        path = f'data/benchmarks/{cid}/benchmark.json'
        rows = store.read(path)
        removed = [r for r in rows if isinstance(r.get('year'), int) and r['year'] <= 2010]
        retained = [r for r in rows if r not in removed]
        assert retained
        if removed:
            store.save(store.backup / f'{cid}_removed_records.json', removed)
            store.save(path, retained)
        report['tracks'][cid] = {'before': len(rows), 'removed': len(removed),
                                'after': len(retained),
                                'removed_years': sorted({r['year'] for r in removed}),
                                'removed_ids': [r['problem_id'] for r in removed]}
    store.finish(report)
    print({cid: {k: v for k, v in t.items() if k != 'removed_ids'}
           for cid, t in report['tracks'].items()})
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
