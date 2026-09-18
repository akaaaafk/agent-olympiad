"""Refresh existing CTF selections from hash-verified current runtime evidence.

Keeps task membership, statements, flags, assets, rules and scoring semantics.
Only superseded readiness text and derived mini scorecards are replaced.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / 'data/mini_data'
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard

TRACKS = ('cybench', 'nyu_ctf_bench')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relocate(value):
    if isinstance(value, dict):
        return {k: relocate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [relocate(v) for v in value]
    if isinstance(value, str) and value.startswith('data/') and not value.startswith('data/mini_data/'):
        return 'data/mini_data/' + value[5:]
    return value


def prepare():
    writes = {}
    dependency_path = MINI / 'dependency_manifest.json'
    dependency = read(dependency_path)
    evidence = {}
    membership = {}
    for track in TRACKS:
        source = ROOT / 'data/benchmarks' / track / 'benchmark.json'
        rows = read(source)
        for row in rows:
            binding = row['evaluation']['runtime_validation']
            report_path = (ROOT / binding['report']).resolve()
            if not report_path.is_relative_to(ROOT):
                raise ValueError('Runtime evidence outside checkout')
            raw = report_path.read_bytes()
            if digest(raw) != binding['report_sha256']:
                raise ValueError('Runtime evidence hash mismatch: ' + row['problem_id'])
            report = json.loads(raw)
            matches = [r for r in report['records'] if r['problem_id'] == row['problem_id']]
            if len(matches) != 1 or matches[0]['status'] != 'passed' or binding['status'] != 'passed':
                raise ValueError('No verified runtime evidence: ' + row['problem_id'])
            row['source_review'].pop('remaining_limitations', None)
            evidence[row['problem_id']] = binding['report_sha256']
        writes[source] = encoded(rows)
        main = {r['problem_id']: r for r in rows}
        destination = MINI / 'benchmarks' / track / 'benchmark.json'
        selected = read(destination)
        original = deepcopy(selected)
        for row in selected:
            current = main[row['problem_id']]
            row['evaluation'] = relocate(deepcopy(current['evaluation']))
            row['source_review'].pop('remaining_limitations', None)
            binding = row['evaluation']['runtime_validation']
            original_report = ROOT / current['evaluation']['runtime_validation']['report']
            local_report = MINI / 'validation/ctf' / original_report.name
            raw = original_report.read_bytes()
            writes[local_report] = raw
            binding['report'] = local_report.relative_to(ROOT).as_posix()
            dependency['files'][local_report.relative_to(MINI).as_posix()] = {
                'source': original_report.relative_to(ROOT).as_posix(),
                'source_sha256': digest(raw), 'mini_sha256': digest(raw)}
        # Prove no task content or permission field was replaced during refresh.
        for before, after in zip(original, selected):
            before.pop('evaluation')
            before['source_review'].pop('remaining_limitations', None)
            comparable = deepcopy(after)
            comparable.pop('evaluation')
            if before != comparable:
                raise AssertionError('Unexpected non-evaluation change')
        writes[destination] = encoded(selected)
        cards_path = MINI / 'rubrics/task_scorecards' / (track + '.json')
        cards = read(cards_path)
        cards['records'] = [scorecard(row, ROOT) for row in selected]
        writes[cards_path] = encoded(cards)
        for path, origin in [(destination, source),
                             (cards_path, ROOT / 'data/rubrics/task_scorecards' / (track + '.json'))]:
            dependency['files'][path.relative_to(MINI).as_posix()] = {
                'source': origin.relative_to(ROOT).as_posix(),
                'source_sha256': digest(writes.get(origin, origin.read_bytes())),
                'mini_sha256': digest(writes[path])}
        membership[track] = {'main': list(main), 'mini': [r['problem_id'] for r in selected]}
    writes[dependency_path] = encoded(dependency)
    return writes, {'membership': membership, 'runtime_evidence': evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, required=True)
    args = parser.parse_args()
    audit = args.audit_dir.resolve()
    if not audit.is_relative_to(ROOT / 'results'):
        raise ValueError('Use an audit directory under results')
    audit.mkdir(parents=True, exist_ok=True)
    archive = audit / 'ctf_metadata_before.zip'
    if archive.exists():
        raise FileExistsError('Use a fresh audit directory')
    writes, report = prepare()
    report['files'] = []
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as backup:
        for path, raw in writes.items():
            resolved = path.resolve()
            if not resolved.is_relative_to(ROOT / 'data'):
                raise ValueError('Write outside data')
            relative = path.relative_to(ROOT).as_posix()
            old = path.read_bytes() if path.exists() else None
            if old is not None:
                backup.writestr(relative, old)
            report['files'].append({'path': relative, 'before': digest(old) if old is not None else None,
                                    'after': digest(raw)})
    (audit / 'ctf_metadata_changes.json').write_bytes(encoded(report))
    for path, raw in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + '.refresh.tmp')
        temp.write_bytes(raw)
        temp.replace(path)
    print(json.dumps({'main_records': sum(len(v['main']) for v in report['membership'].values()),
                      'mini_records': sum(len(v['mini']) for v in report['membership'].values()),
                      'files': len(writes), 'task_membership_changed': False}))


if __name__ == '__main__':
    main()
