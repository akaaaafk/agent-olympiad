"""Archive user-excluded Mystery Hunt and EOES years, preserving raw sources."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    store = Store(ROOT)
    report = {'operation': 'user_requested_year_exclusion', 'tracks': {},
              'preserved': 'Original source files, rules, judge references and historical experiment outputs.'}
    for cid in ('mystery_hunt', 'eoes'):
        path = f'data/benchmarks/{cid}/benchmark.json'
        rows = store.read(path)
        def excluded(row):
            year = int(row['year'])
            return year < 2010 if cid == 'mystery_hunt' else year in {2003, 2004, 2006}
        removed = [r for r in rows if excluded(r)]
        retained = [r for r in rows if not excluded(r)]
        assert retained and len(removed) + len(retained) == len(rows)
        if removed:
            store.save(store.backup / f'{cid}_removed_records.json', removed)
            store.save(path, retained)
        report['tracks'][cid] = {'before': len(rows), 'removed': len(removed),
                                'remaining': len(retained),
                                'removed_ids': [r['problem_id'] for r in removed],
                                'removed_years': sorted({r['year'] for r in removed})}
    store.finish(report)
    print({cid: {k: v for k, v in values.items() if k != 'removed_ids'}
           for cid, values in report['tracks'].items()})
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
