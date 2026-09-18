"""Refresh local JSON snapshots only after a fresh successful mini preflight."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_mini_dependency_hashes import audit, MINI
from scripts.repair_data_catalog import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, required=True)
    args = parser.parse_args()
    report_path = (ROOT / args.verification).resolve()
    assert report_path.is_relative_to(ROOT / 'output')
    report = json.loads(report_path.read_text())
    assert report['passed'] and not report['asset_errors'] and not report['parent_data_reads_denied']
    assert report['paid_model_calls'] == 0
    issues = audit()
    assert all(i['kind'] == 'mini_snapshot_drift' and i['path'].endswith('.json') for i in issues)
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_mini_snapshots_' + uuid.uuid4().hex[:8])
    relative = 'data/mini_data/dependency_manifest.json'
    manifest = store.read(relative)
    for issue in issues:
        path = (MINI / issue['path']).resolve()
        assert path.is_relative_to(MINI)
        json.loads(path.read_text(encoding='utf-8-sig'))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == issue['actual'], 'Mini file changed during refresh'
        manifest['files'][issue['path']]['mini_sha256'] = digest
    manifest['latest_snapshot_refresh'] = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'verification': report_path.relative_to(ROOT).as_posix(),
        'verification_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'updated_files': [i['path'] for i in issues],
        'scope': 'Current mini JSON hashes only; original source hashes and membership preserved.'}
    store.save(relative, manifest)
    store.finish({'operation': 'refresh_mini_local_snapshots', 'changed_snapshots': issues})
    assert not audit()
    print({'updated': len(issues), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
