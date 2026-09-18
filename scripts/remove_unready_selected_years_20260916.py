"""Remove the ten explicitly requested unready editions; no historical copies.

Default is a read-only plan. --apply saves an audit inventory (not task contents),
removes exclusive sources, and regenerates current portable and mini catalogs.
Historical paid results and frozen experiment runtimes are outside this scope.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import update_track_index
from scripts import repair_data_catalog as repair
from scripts.build_mini_data import main as build_mini, question_units

POLICY = {
    'iol_team': {f'iol_team_{y}' for y in (2011, 2012, 2016, 2017, 2019, 2022, 2024)},
    'ijso_practical': {f'ijso_practical_{y}_team_practical_{y}' for y in (2011, 2015)},
    'arml_power': {'arml_power_spring_2022'},
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def inventory(paths):
    return [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size,
                 sha256=sha(p)) for p in sorted(paths)]


def source_plan(catalog, removed):
    protected = set()
    for cid, rows in catalog.items():
        for row in rows:
            if row['problem_id'] in POLICY.get(cid, set()):
                continue
            protected.update((ROOT / s).resolve() for s in strings(row) if s.startswith('data/'))
    candidates = set()
    for row in removed:
        for s in strings(row):
            if s.startswith('data/raw/'):
                p = (ROOT / s).resolve()
                if p.is_file():
                    candidates.add(p)
                elif p.is_dir():
                    candidates.update(f.resolve() for f in p.rglob('*') if f.is_file())
    # Include original sidecars in the explicitly removed source editions.
    for year in (2011, 2012, 2016, 2017, 2019, 2022, 2024):
        candidates.update(p.resolve() for p in (ROOT / 'data/raw/iol').glob(f'iol-{year}-team*') if p.is_file())
        for parent in ('recovered_20260913', 'followup_20260913'):
            directory = ROOT / 'data/raw/iol' / parent / str(year)
            if directory.exists():
                candidates.update(p.resolve() for p in directory.rglob('*') if p.is_file())
    for name in ('lao_20260913', 'emoji_20260913'):
        directory = ROOT / 'data/raw/iol' / name
        if directory.exists():
            candidates.update(p.resolve() for p in directory.rglob('*') if p.is_file())
    for directory in (ROOT / 'data/raw/ijso/2011', ROOT / 'data/raw/ijso/2015',
                      ROOT / 'data/raw/arml/Spring_2022'):
        if directory.exists():
            candidates.update(p.resolve() for p in directory.rglob('*') if p.is_file())
    for prefix in ('iol_team_2012_', 'iol_team_2016_', 'iol_team_2017_',
                   'iol_team_2022_', 'iol_team_2024_', 'arml_power_spring_2022_'):
        candidates.update(p.resolve() for p in (ROOT / 'data/rubrics').glob(prefix + '*.json'))
    selected, shared = [], []
    for p in sorted(candidates):
        assert p.is_relative_to(ROOT / 'data/raw') or p.is_relative_to(ROOT / 'data/rubrics')
        assert not p.is_symlink() and not any(parent.is_symlink() for parent in p.parents)
        # A retained directory source may depend on any of its descendants.
        if any(p == keep or (keep.is_dir() and p.is_relative_to(keep)) for keep in protected):
            shared.append(p)
        else:
            selected.append(p)
    return inventory(selected), [p.relative_to(ROOT).as_posix() for p in shared]


class NoBackupStore(repair.Store):
    """Use the normal validation/rebuild, with inventoried deletion of old copies."""
    def __init__(self, root, backup_root=None):
        super().__init__(root, backup_root=AUDIT / 'derived_audit')

    def save_text(self, name, text):
        p = self.path(name)
        payload = text.encode('utf-8')
        current = p.read_bytes() if p.exists() else None
        if current == payload:
            return
        if p in self.raw and self.raw[p] != current:
            raise RuntimeError(f'Concurrent edit: {p}')
        if p.is_relative_to(ROOT / 'data/benchmarks') and p.name == 'benchmark.json' and p.parent.name not in POLICY:
            if read(p) != json.loads(text):
                raise RuntimeError(f'Unrelated canonical record mutation refused: {p}')
            return
        if p.is_relative_to(ROOT / 'data/rules') and p.parent.name not in POLICY:
            if read(p) != json.loads(text):
                raise RuntimeError(f'Unrelated rule mutation refused: {p}')
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        temporary = p.with_name(p.name + '.selected-cleanup-tmp')
        temporary.write_bytes(payload)
        os.replace(temporary, p)
        self.raw[p] = payload
        self.hashes[p] = hashlib.sha256(payload).hexdigest()
        self.changes.append(dict(path=p.relative_to(ROOT).as_posix(),
                                 before_sha256=hashlib.sha256(current).hexdigest() if current else None,
                                 after_sha256=self.hashes[p]))

    def archive(self, name):
        p = self.path(name)
        figure = p.parent == ROOT / 'data/viz' and p.suffix == '.png' and p.is_file()
        if p not in {ROOT / 'data/base', ROOT / 'data/last_exam'} and not figure:
            raise ValueError(f'Unapproved tree replacement: {p}')
        if p.is_symlink():
            raise ValueError('Symlink deletion refused')
        records = inventory([p] if figure else (f for f in p.rglob('*') if f.is_file()))
        self.archived.append(dict(path=p.relative_to(ROOT).as_posix(),
                                  operation='delete_obsolete_derived_copy', files=records))
        self.finish({'status': 'replacing_derived', 'backup_payloads': False})
        if figure:
            p.unlink()
        else:
            shutil.rmtree(p)


def trim_rule(value, excluded_ids):
    if isinstance(value, dict):
        return {k: trim_rule(v, excluded_ids) for k, v in value.items() if k not in excluded_ids}
    if isinstance(value, list):
        return [trim_rule(v, excluded_ids) for v in value
                if not (isinstance(v, dict) and v.get('problem_id') in excluded_ids)]
    return value


def main():
    global AUDIT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--resume', type=Path, help='Resume derived rebuild from an existing cleanup audit')
    args = parser.parse_args()
    index = read(ROOT / 'data/benchmarks/index.json')
    catalog = {t['id']: read(ROOT / t['benchmark_path']) for t in index['olympiads']}
    removed = []
    if args.resume:
        AUDIT = args.resume.resolve()
        assert AUDIT.is_relative_to(ROOT / 'docs/cleanup_audits') and AUDIT.is_dir()
        plan = read(AUDIT / 'manifest.json')
        assert set(plan['removed_ids']) == set().union(*POLICY.values())
        assert all(not (ids & {r['problem_id'] for r in catalog[cid]}) for cid, ids in POLICY.items())
        assert all(len(catalog[cid]) == plan['tracks'][cid]['after'] for cid in POLICY)
        files = plan['source_files_deleted']
        args.apply = True
    else:
        for cid, ids in POLICY.items():
            actual = [r for r in catalog[cid] if r['problem_id'] in ids]
            assert {r['problem_id'] for r in actual} == ids, f'Unexpected population: {cid}'
            assert all(r['evaluation']['status'] == 'not_ready' for r in actual)
            removed.extend(actual)
        files, shared = source_plan(catalog, removed)
        plan = dict(operation='remove_selected_unready_editions',
                    removed_ids=sorted(r['problem_id'] for r in removed),
                    tracks={cid: dict(before=len(catalog[cid]), after=len(catalog[cid]) - len(ids)) for cid, ids in POLICY.items()},
                    source_files_deleted=files, shared_sources_preserved=shared,
                    backup_payloads=False, historical_results_modified=False)
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if not args.apply:
        return
    if not args.resume:
        AUDIT = ROOT / 'docs/cleanup_audits' / ('selected_unready_years_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        AUDIT.mkdir(parents=True, exist_ok=False)
        (AUDIT / 'manifest.json').write_text(json.dumps({**plan, 'status': 'planned'}, indent=2) + '\n', encoding='utf-8')
    store = NoBackupStore(ROOT)
    retained = deepcopy(catalog)
    for cid, ids in POLICY.items():
        retained[cid] = [r for r in catalog[cid] if r['problem_id'] not in ids]
        store.save(f'data/benchmarks/{cid}/benchmark.json', retained[cid])
        rule = trim_rule(read(ROOT / f'data/rules/{cid}/evaluation.json'), ids)
        repair.sync_rules(cid, rule, retained[cid])
        membership_path = ROOT / f'data/rubrics/{cid}_active_score_membership.json'
        if membership_path.exists():
            membership = read(membership_path)
            kept_ids = {r['problem_id'] for r in retained[cid]}
            membership['records'] = [r for r in membership['records'] if r['problem_id'] in kept_ids]
            assert {r['problem_id'] for r in membership['records']} == kept_ids
            membership['active_records'] = len(kept_ids)
            membership['active_years'] = sorted({r['year'] for r in retained[cid]})
            membership['excluded_years'] = sorted(set(membership.get('excluded_years', [])) | {r['year'] for r in catalog[cid] if r['problem_id'] in ids})
            store.save(membership_path, membership)
            rule['scoring']['active_score_membership']['records'] = len(kept_ids)
        store.save(f'data/rules/{cid}/evaluation.json', rule)
        update_track_index(index, cid, retained[cid])
    store.save('data/benchmarks/index.json', index)
    for item in files:
        p = (ROOT / item['path']).resolve()
        assert p.is_relative_to(ROOT / 'data/raw') or p.is_relative_to(ROOT / 'data/rubrics')
        if args.resume and not p.exists():
            continue
        assert p.is_file()
        assert sha(p) == item['sha256'], f'Source changed: {p}'
        p.unlink()
    # Remove only now-empty parents of the inventoried files, never broad roots.
    for item in files:
        parent = (ROOT / item['path']).parent
        while parent not in {ROOT / 'data/raw', ROOT / 'data/rubrics'} and parent.is_relative_to(ROOT / 'data'):
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
    original_store, original_argv = repair.Store, sys.argv
    try:
        repair.Store = NoBackupStore
        sys.argv = ['repair_data_catalog.py', '--derived-only']
        repair.main()
    finally:
        repair.Store, sys.argv = original_store, original_argv
    build_mini()
    excluded_ids = set().union(*POLICY.values())
    current_index = read(ROOT / 'data/benchmarks/index.json')
    all_current = []
    for track in current_index['olympiads']:
        cid = track['id']
        current = read(ROOT / track['benchmark_path'])
        assert {r['problem_id'] for r in current} == {r['problem_id'] for r in retained[cid]}
        if cid not in POLICY:
            assert current == catalog[cid], f'Unrelated records changed: {cid}'
        for r in current:
            old = next(k for k in retained[cid] if k['problem_id'] == r['problem_id'])
            for key in ('problem_description', 'gold_label', 'split', 'assets'):
                assert r.get(key) == old.get(key), (cid, key)
        all_current.extend(current)
        assert not excluded_ids & {r['problem_id'] for r in read(ROOT / 'data/mini_data/benchmarks' / cid / 'benchmark.json')}
        cards = read(ROOT / f'data/rubrics/task_scorecards/{cid}.json')['records']
        assert {r['problem_id'] for r in cards} == {r['problem_id'] for r in current}
    assert len(all_current) == current_index['total_records'] == 1081
    assert all(not (ROOT / item['path']).exists() for item in files)
    readme = (ROOT / 'data/README.md').read_text(encoding='utf-8')
    store.save_text('data/README.md', readme.replace('`excluded/` contains historical backups.',
        '`excluded/` contains only four referenced audit manifests; historical backup payloads were deleted on 2026-09-16.'))
    (AUDIT / 'manifest.json').write_text(json.dumps({**plan, 'status': 'completed',
        'after_records': len(all_current), 'after_question_task_units': sum(question_units(r)[0] for r in all_current),
        'evaluation_status_counts': dict(Counter(r['evaluation']['status'] for r in all_current)),
        'validation': 'Exact membership, preserved retained inputs/gold/splits/assets, unchanged other tracks, scorecards, mini and portable packages validated.'}, indent=2) + '\n', encoding='utf-8')
    print('Cleanup completed; audit: ' + str(AUDIT), flush=True)


if __name__ == '__main__':
    main()
