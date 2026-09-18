"""User-requested removal of two sessions from the active catalog; preserve sources."""
from copy import deepcopy
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    report_path = 'data/judge_references/user_excluded_sessions_20260916.json'
    if (ROOT / report_path).exists():
        raise RuntimeError('Frozen exclusion batch exists; do not replay')
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    targets = {'ijso_practical': 'ijso_practical_2013_team_practical_2013',
               'pumac_power': 'pumac_power_2018'}
    report = dict(operation='user_requested_active_catalog_exclusion', excluded_records=[],
                  source_policy='Preserve original raw files and historical evidence.', before_hashes={})
    pending = {}
    for track, pid in targets.items():
        path = f'data/benchmarks/{track}/benchmark.json'
        rows = deepcopy(store.read(path))
        excluded = [row for row in rows if row['problem_id'] == pid]
        assert len(excluded) == 1 and excluded[0]['year'] == (2013 if track == 'ijso_practical' else 2018)
        kept = [row for row in rows if row['problem_id'] != pid]
        assert len(kept) == len(rows) - 1
        report['excluded_records'].append(dict(track=track, record=excluded[0]))
        report['before_hashes'][path] = store.sha(path)
        pending[path] = kept
    mapping_path = 'data/rubrics/pumac_power_official_rubrics.json'
    mapping = deepcopy(store.read(mapping_path))
    assert 'pumac_power_2018' in mapping
    report['excluded_official_rubric_mapping'] = mapping.pop('pumac_power_2018')
    pending[mapping_path] = mapping
    for path, rows in pending.items():
        store.save(path, rows)
    store.save(report_path, report)
    store.finish(report)
    print('Excluded:', list(targets.values()))
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
