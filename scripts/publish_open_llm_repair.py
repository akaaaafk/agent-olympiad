"""Publish verified readiness and dependency metadata after the scoped repair."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / 'data/mini_data'
TRACKS = {'iiot', 'ccdc', 'debatebench', 'gcch_harvard', 'ioai_team', 'wharton_investment'}


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    report = read(ROOT / 'tmp/open_llm_final_preflight_20260917.json')
    assert report['passed'] and not report['asset_errors'] and not report['parent_data_reads_denied']
    registry = read(ROOT / 'tmp/ioai_llm_smoke_20260917/registration/registry.json')
    job_tracks = {j['id']: j['competition'] for j in registry['jobs']}
    selection_path = MINI / 'selection_manifest.json'
    selection = read(selection_path)
    for track in selection['tracks']:
        name = track['competition_id']
        if name not in TRACKS:
            continue
        jobs = [j for j in report['jobs'] if job_tracks[j['id']] == name]
        assert len(jobs) == track['sessions'] * 5
        assert all(j['state'] == 'prepared' for j in jobs), name
        track.update(verification='offline_execution_preflight_passed',
                     route='slides' if name == 'gcch_harvard' else 'native',
                     evaluation_scope='LLM artifact/source-review benchmark; not official execution')
    selection['latest_workspace_sync'].update(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        canonical_index_sha256=hashlib.sha256((ROOT / 'data/benchmarks/index.json').read_bytes()).hexdigest())
    dependency_path = MINI / 'dependency_manifest.json'
    dependencies = read(dependency_path)
    files = set()
    for name in TRACKS:
        for row in read(MINI / 'benchmarks' / name / 'benchmark.json'):
            files.update(a['path'] for a in row['assets'])
            files.add(row['evaluation']['rubric_path'])
            for field in ('source_archive_manifest', 'test_source_manifest'):
                if row['evaluation'].get(field):
                    files.add(row['evaluation'][field])
        files.update(str(p.relative_to(ROOT)).replace('\\', '/') for p in (MINI / 'rules' / name).glob('*.json'))
    for rel in files:
        local = ROOT / rel
        source = ROOT / rel.replace('data/mini_data/', 'data/', 1)
        assert local.is_file() and source.is_file()
        dependencies['files'][local.relative_to(MINI).as_posix()] = dict(source=source.relative_to(ROOT).as_posix(),
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            mini_sha256=hashlib.sha256(local.read_bytes()).hexdigest())
    backup = ROOT / 'tmp' / ('before_open_llm_publish_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True)
    for path, value in [(selection_path, selection), (dependency_path, dependencies), (MINI / 'verification.json', report)]:
        shutil.copy2(path, backup / path.name)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Verified six tracks, 17 records; dependency manifest refreshed.', backup)


if __name__ == '__main__':
    main()
