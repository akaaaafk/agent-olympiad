"""Put active puzzle PDFs in data; reconcile mini reviewed permissions without widening scope."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from scripts.repair_data_catalog import Store
from problem_pdf import approved_assets, read_problem_pdf


def rewrite(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [rewrite(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: rewrite(v, mapping) for k, v in value.items()}
    return value


def catalog(store, base):
    index = store.read(f'{base}/benchmarks/index.json')
    return {t['benchmark_path']: deepcopy(store.read(t['benchmark_path'])) for t in index['olympiads']}


def main():
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_pdf_locations_' + uuid.uuid4().hex[:8])
    report = dict(moved=[], archived_duplicates=[], changed_tracks=[], registry_checks={}, paid_model_calls=0)
    main_catalog = catalog(store, 'data')
    mapping = {}
    for rows in main_catalog.values():
        for row in rows:
            for a in row.get('assets', []):
                if a.get('mime_type') != 'application/pdf' or not a['path'].startswith('output/pdf/'):
                    continue
                old = a['path']
                new = 'data/raw/' + old.removeprefix('output/pdf/')
                source, target = store.path(old), store.path(new)
                assert store.sha(old) == a['sha256']
                assert not target.exists(), new
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                assert store.sha(new) == a['sha256']
                mapping[old] = new
    # Update active canonical metadata only; historical run evidence remains immutable.
    for path, rows in main_catalog.items():
        replacement = rewrite(rows, mapping)
        if replacement != rows:
            store.save(path, replacement)
            report['changed_tracks'].append(Path(path).parent.name)
            main_catalog[path] = replacement
    registry_path = 'data/problem_pdf_allowlist.json'
    registry = rewrite(deepcopy(store.read(registry_path)), mapping)
    main_ids = {r['problem_id'] for rows in main_catalog.values() for r in rows}
    registry['assets'] = [a for a in registry['assets'] if a['problem_id'] in main_ids]
    store.save(registry_path, registry)
    mini_catalog = catalog(store, 'data/mini_data')
    mini_rows = {r['problem_id']: r for rows in mini_catalog.values() for r in rows}
    mini_path = 'data/mini_data/problem_pdf_allowlist.json'
    mini_registry = deepcopy(store.read(mini_path))
    stale = [a['problem_id'] for a in mini_registry['assets'] if a['problem_id'] not in mini_rows]
    mini_registry['assets'] = [a for a in mini_registry['assets'] if a['problem_id'] in mini_rows]
    added = []
    for entry in registry['assets']:
        row = mini_rows.get(entry['problem_id'])
        if row is None:
            continue
        relocated = 'data/mini_data/' + entry['path'].removeprefix('data/')
        match = next((a for a in row.get('assets', []) if a.get('path') == relocated
                      and a.get('sha256') == entry['sha256'] and a.get('role') == 'agent_visible'), None)
        if match and not any(a['problem_id'] == entry['problem_id'] and a['path'] == relocated for a in mini_registry['assets']):
            assert store.sha(relocated) == entry['sha256']
            mini_registry['assets'].append({**entry, 'path': relocated})
            added.append(entry['problem_id'])
    store.save(mini_path, mini_registry)
    report['mini_registry'] = dict(removed_stale=stale, added_hash_identical_reviewed=added, membership='preserved')
    duplicates = {
        'output/pdf/mystery_fun_numbers_2010_base10.pdf': 'data/raw/mystery_hunt/reviewed_numbers_20260917/fun_numbers_base10.pdf',
        'output/pdf/mystery_hunt_2013_space_monkey_reviewed.pdf': 'data/raw/mystery_hunt/reviewed_2013_20260917/puzzles.pdf',
        'output/pdf/mystery_hunt_2015_reviewed.pdf': 'data/raw/mystery_hunt/reviewed_2015_20260917/puzzles.pdf',
        'output/pdf/mystery_hunt_2016_reviewed.pdf': 'data/raw/mystery_hunt/reviewed_2016_20260917/puzzles.pdf',
    }
    for old, new in {**mapping, **duplicates}.items():
        assert store.sha(old) == store.sha(new), (old, new)
        store.archive(old)
        report['moved' if old in mapping else 'archived_duplicates'].append(dict(before=old, after=new, sha256=store.sha(new)))
    for base, rows_by_path in [('data', main_catalog), ('data/mini_data', mini_catalog)]:
        by_id = {r['problem_id']: r for rows in rows_by_path.values() for r in rows}
        reg = ROOT / base / 'problem_pdf_allowlist.json'
        entries = json.loads(reg.read_text())['assets']
        checks = 0
        for e in entries:
            row = by_id[e['problem_id']]
            assets = approved_assets(row, root=ROOT, registry=reg)
            asset = next(a for a in assets if a['path'] == e['path'])
            document = assets.index(asset) + 1
            for page in e['pages']:
                payload, attachments = read_problem_pdf(row, [page], document, root=ROOT, registry=reg)
                assert payload['status'] == 'ok' and len(attachments) == 1
                for attachment in attachments:
                    image = Path(attachment.path)
                    image.unlink()
                    image.parent.rmdir()
                checks += 1
        report['registry_checks'][base] = dict(entries=len(entries), rendered_pages=checks)
    store.save('output/pdf_data_locations_repair_20260918.json', report)
    store.finish(report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
