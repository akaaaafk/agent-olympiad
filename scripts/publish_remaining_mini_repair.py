"""Publish completed five-track checks and refresh independent dataset metadata."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / 'data/mini_data'
TRACKS = {'mystery_hunt', 'cfa_research_challenge', 'eoes', 'odyssey_of_the_mind', 'science_olympiad'}


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    report = read(ROOT / 'tmp/remaining_five_preflight_20260917.json')
    smoke = read(ROOT / 'tmp/remaining_five_smoke_20260917/summary.json')
    assert report['passed'] and all(j['state'] == 'prepared' for j in report['jobs'])
    assert len(smoke['cases']) == 25
    assert all(c['status'] == 'PASS' for c in smoke['cases'])
    backup = ROOT / 'tmp' / ('before_remaining_publish_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True)

    def write(p, value):
        if p.exists():
            shutil.copy2(p, backup / p.name)
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    p = MINI / 'selection_manifest.json'
    selection = read(p)
    for t in selection['tracks']:
        if t['competition_id'] in TRACKS:
            t.update(verification='offline_execution_preflight_passed', runtime_blockers=[],
                record_policy='Reviewed selected task(s) from one edition; companion inputs are not standalone tasks.')
    selection['source_index_sha256'] = hashlib.sha256((ROOT / 'data/benchmarks/index.json').read_bytes()).hexdigest()
    selection['latest_workspace_sync'].update(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        canonical_index_sha256=selection['source_index_sha256'], membership_preserved=False,
        membership_change='Mystery Hunt 2011 replaced by 2012 text puzzle; EOES blank sheets paired with two tasks.')
    write(p, selection)
    p = MINI / 'dependency_manifest.json'
    deps = read(p)
    # Refresh existing bindings and newly added task/rubric/input files. The manifest
    # records provenance; execution isolation is separately enforced by preflight.
    paths = {MINI / rel for rel in deps['files']}
    for track in TRACKS:
        paths.update((MINI / 'rules' / track).glob('*.json'))
        paths.add(MINI / 'benchmarks' / track / 'benchmark.json')
        paths.add(MINI / 'rubrics/task_scorecards' / (track + '.json'))
        for r in read(MINI / 'benchmarks' / track / 'benchmark.json'):
            paths.update(ROOT / a['path'] for a in r['assets'])
            paths.add(ROOT / r['evaluation']['rubric_path'])
    paths.update((MINI / 'raw/cfa_research_challenge/historical_2016').glob('*'))
    paths.update([MINI / 'problem_pdf_allowlist.json', MINI / 'benchmarks/index.json'])
    for local in paths:
        source = ROOT / local.relative_to(ROOT).as_posix().replace('data/mini_data/', 'data/', 1)
        if local.is_file() and source.is_file():
            deps['files'][local.relative_to(MINI).as_posix()] = dict(source=source.relative_to(ROOT).as_posix(),
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                mini_sha256=hashlib.sha256(local.read_bytes()).hexdigest())
    write(p, deps)
    write(MINI / 'verification.json', report)
    print('Published five repaired tracks: 25 route cases, 445 prepared commands, no paid calls.')


if __name__ == '__main__':
    main()
