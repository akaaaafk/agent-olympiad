"""Keep current QANTA data strictly post-2010; archive originals outside checkout.

Default is read-only planning. --apply verifies byte-for-byte backups before
replacing data. Raw questions are filtered by year, never relabelled or sampled.
"""
import argparse
import csv
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from scripts.repair_data_catalog import Store, sync_rules
from dataset_catalog import update_track_index


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def after2010(row):
    return type(row.get('year')) is int and row['year'] > 2010


def refresh_qanta_membership_csv(backup):
    """Change QANTA membership flags only, preserving historical run statuses."""
    path = ROOT / 'docs/from_zhongzheng/current_catalog_run_membership_20260916.csv'
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        fields, original = reader.fieldnames, list(reader)
    current_ids = {r['problem_id'] for r in read(ROOT / 'data/benchmarks/qanta/benchmark.json')}
    registry_jobs = {}
    for batch in {r['batch'] for r in original if r['competition'] == 'qanta'}:
        for job in read(ROOT / 'results' / batch / 'registry.json')['jobs']:
            if job['competition'] == 'qanta':
                registry_jobs[(batch, job['id'])] = job
    updated = deepcopy(original)
    for row in updated:
        if row['competition'] == 'qanta':
            job = registry_jobs[(row['batch'], row['id'])]
            row['current_catalog_member'] = str(bool(job.get('problem_ids')) and set(job['problem_ids']) <= current_ids)
    destination = Path(backup) / path.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    assert sha(path) == sha(destination)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(updated)
    assert all({k: r[k] for k in fields if k != 'current_catalog_member'} ==
               {k: old[k] for k in fields if k != 'current_catalog_member'}
               for r, old in zip(updated, original))
    qanta = [r for r in updated if r['competition'] == 'qanta']
    print(json.dumps({'membership_rows': len(qanta),
        'eligible': sum(r['current_catalog_member'] == 'True' for r in qanta)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    rows = read(ROOT / 'data/benchmarks/qanta/benchmark.json')
    kept, removed = [r for r in rows if after2010(r)], [r for r in rows if not after2010(r)]
    assert kept and len({r['problem_id'] for r in rows}) == len(rows)
    kept_ids = {r['problem_id'] for r in kept}
    raw_paths = sorted({r['source_file'] for r in rows} | {'data/raw/qanta/qanta.dev.2021.12.20.json'})
    raw_data, raw_plan = {}, []
    for name in raw_paths:
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT / 'data/raw') and path.is_file()
        data = read(path)
        questions = data['questions']
        assert all(type(q.get('qanta_id')) is int for q in questions)
        selected = [q for q in questions if after2010(q)]
        raw_data[name] = dict(original=data, selected=selected)
        raw_plan.append(dict(path=name, original_sha256=sha(path),
            before_questions=len(questions), after_questions=len(selected)))
    # Check the retained catalog against original upstream records before rewriting.
    for row in kept:
        qid = int(row['problem_id'].rsplit('_', 1)[1])
        lookup = next(q for q in raw_data[row['source_file']]['selected'] if q['qanta_id'] == qid)
        assert lookup['year'] == row['year']
        assert lookup['text'].strip() == row['problem_description'].strip(), row['problem_id']
        assert lookup['answer'] == row['gold_label']['expected_answer'], row['problem_id']
    legacy_dirs = set()
    for pattern in ('*/qanta', '*/data/raw/qanta', '*/data/raw/external/qanta',
                    '*/data/benchmarks/qanta'):
        legacy_dirs.update(p.resolve() for p in (ROOT / 'data/excluded').glob(pattern) if p.is_dir())
    legacy_files = sorted({p for directory in legacy_dirs for p in directory.rglob('*') if p.is_file()})
    plan = dict(operation='qanta_strict_post2010', minimum_year=2011,
        before_records=len(rows), after_records=len(kept),
        removed_ids=[r['problem_id'] for r in removed], retained_ids=sorted(kept_ids),
        years=dict(sorted(Counter(r['year'] for r in kept).items())), raw=raw_plan,
        legacy_qanta_directories=[p.relative_to(ROOT).as_posix() for p in sorted(legacy_dirs)],
        legacy_files=len(legacy_files),
        scope='QANTA only; historical paid results and active frozen snapshots are preserved.')
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if not args.apply:
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = (ROOT.parent / 'dataset_backups' / ('qanta_post2010_' + stamp)).resolve()
    assert backup.is_relative_to(ROOT.parent) and not backup.is_relative_to(ROOT) and not backup.exists()
    backup.mkdir(parents=True)
    store = Store(ROOT)
    store.backup = backup
    # Inventory and copy every original that will be replaced/moved, before mutation.
    originals = [ROOT / name for name in raw_paths] + [ROOT / name for name in (
        'data/benchmarks/qanta/benchmark.json', 'data/benchmarks/index.json',
        'data/rubrics/qanta_upstream_answer_key_v1.json', 'data/rubrics/qanta_short_answers.json',
        'data/rules/qanta/evaluation.json')]
    originals += legacy_files
    for directory in legacy_dirs:
        assert directory.is_relative_to(ROOT / 'data/excluded')
    inventory = [dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p), bytes=p.stat().st_size)
                 for p in originals]
    store.finish({**plan, 'status': 'backup_planned', 'original_files': inventory})
    for item in inventory:
        source = ROOT / item['path']
        destination = backup / item['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        assert sha(destination) == item['sha256'] == sha(source)
    store.finish({**plan, 'status': 'backups_verified', 'original_files': inventory})
    for name, value in raw_data.items():
        if len(value['selected']) == len(value['original']['questions']):
            continue
        data = deepcopy(value['original'])
        data['questions'] = value['selected']
        data['local_scope'] = dict(minimum_year=2011, unknown_years='excluded',
            original_sha256=next(p['original_sha256'] for p in raw_plan if p['path'] == name),
            upstream_question_fields='preserved unchanged', upstream_version=data.get('version'))
        store.save(name, data)
        assert all(after2010(q) for q in read(ROOT / name)['questions'])
    current = deepcopy(kept)
    for row in current:
        old_row = next(r for r in kept if r['problem_id'] == row['problem_id'])
        assert row['gold_label'] == old_row['gold_label'] and row['problem_description'] == old_row['problem_description']
        for asset in row.get('assets', []):
            if asset['path'] in raw_data:
                asset['sha256'] = sha(ROOT / asset['path'])
        provenance = row['provenance']
        provenance['files'] = [{k: a[k] for k in ('path', 'role', 'sha256')} for a in row['assets']]
        provenance['source_scope'] = 'Local upstream question subset: year >= 2011; question text and labels unchanged.'
    store.save('data/benchmarks/qanta/benchmark.json', current)
    answers = read(ROOT / 'data/rubrics/qanta_upstream_answer_key_v1.json')
    answers['answers'] = {k: v for k, v in answers['answers'].items() if k in kept_ids}
    assert set(answers['answers']) == kept_ids
    coverage = answers['coverage']
    coverage.update(promoted_benchmark_records=len(current), promoted_records_mapped=len(current),
        unmapped_promoted_records=[], promoted_dev_records_verified_against_upstream=
        sum(r['problem_id'].startswith('qanta_dev_') for r in current),
        limitations=['Current catalog contains only 2011+ questions; labels preserve upstream text.',
                     'These upstream labels are not a claim of official organizer-published keys.'])
    store.save('data/rubrics/qanta_upstream_answer_key_v1.json', answers)
    short = read(ROOT / 'data/rubrics/qanta_short_answers.json')
    short = {k: v for k, v in short.items() if k.startswith('_') or k in kept_ids}
    assert {k for k in short if not k.startswith('_')} == kept_ids
    store.save('data/rubrics/qanta_short_answers.json', short)
    rule = read(ROOT / 'data/rules/qanta/evaluation.json')
    sync_rules('qanta', rule, current)
    store.save('data/rules/qanta/evaluation.json', rule)
    index = read(ROOT / 'data/benchmarks/index.json')
    update_track_index(index, 'qanta', current)
    store.save('data/benchmarks/index.json', index)
    # The old QANTA-only backups are already verified externally. Remove only
    # these explicitly inventoried leaf trees, never data/excluded as a whole.
    for directory in sorted(legacy_dirs, key=lambda p: len(p.parts), reverse=True):
        if directory.exists():
            assert directory.is_relative_to(ROOT / 'data/excluded')
            for p in directory.rglob('*'):
                if p.is_file():
                    assert sha(p) == sha(backup / p.relative_to(ROOT))
            shutil.rmtree(directory)
    # Rebuild the portable/current catalogs with all backups outside the checkout.
    from scripts import repair_data_catalog
    original_argv = sys.argv
    try:
        sys.argv = ['repair_data_catalog.py', '--derived-only', '--backup-root', str(backup / 'derived_before')]
        repair_data_catalog.main()
    finally:
        sys.argv = original_argv
    from scripts.build_mini_data import main as build_mini
    shutil.copytree(ROOT / 'data/mini_data', backup / 'data/mini_data')
    build_mini()
    refresh_qanta_membership_csv(backup)
    assert {r['problem_id'] for r in read(ROOT / 'data/benchmarks/qanta/benchmark.json')} == kept_ids
    assert all(after2010(r) for r in read(ROOT / 'data/mini_data/benchmarks/qanta/benchmark.json'))
    assert all(r['gold_label'] == next(k for k in kept if k['problem_id'] == r['problem_id'])['gold_label'] for r in current)
    store.finish({**plan, 'status': 'completed', 'original_files': inventory,
                  'external_backup': str(backup), 'validation': 'Exact retained IDs, upstream text/answers, raw years and backup hashes matched.'})
    print('QANTA filtered and validated. External backup: ' + str(backup), flush=True)


if __name__ == '__main__':
    main()
