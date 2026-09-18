"""Rebuild only the requested tracks, preserving unrelated packages."""
from pathlib import Path
from copy import deepcopy
import sys
import os
import argparse
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from scripts.build_data_packages import build_packages
from src.dataset_catalog import scorecard, update_track_index


def merge_track_entries(existing, replacement, removed):
    """Keep unrelated entries byte-for-byte equivalent, including stale members."""
    return [r for r in existing if r.get('competition_id', r.get('category', r.get('task_id', '').split('/')[0])) not in removed] + replacement


def install_package(source, target):
    """Install into an absent target; tolerate Windows directory rename locks."""
    if target.exists():
        raise FileExistsError('Refusing to replace a concurrently created package: ' + str(target))
    try:
        os.replace(source, target)
    except PermissionError:
        # A scanner can retain a directory handle after the previous tree moves.
        # Copying preserves the staged package and never merges with a new target.
        shutil.copytree(source, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--competition', action='append', help='Rebuild only these tracks; preserve all other packages.')
    parser.add_argument('--refresh-summary', action='store_true', help='Refresh aggregate metadata after bounded package synchronization.')
    args = parser.parse_args()
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.stamp += '_' + uuid.uuid4().hex[:8]
    store.backup = store.backup.with_name('integrity_repair_' + store.stamp)
    ids = set(args.competition or ['ijso_practical', 'iypt', 'itym', 'ichto', 'iol_team'])
    removed = ids if args.competition else ids | {'history_olympiad'}
    index = deepcopy(store.read('data/benchmarks/index.json'))
    tracks = [t for t in index['olympiads'] if t['id'] in ids]
    rows = {t['id']: deepcopy(store.read(t['benchmark_path'])) for t in tracks}
    rules = {t['id']: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json"))
             for k in ('competition', 'collaboration', 'evaluation')} for t in tracks}
    for t in tracks:
        cid = t['id']
        if not args.competition:
            sync_rules(cid, rules[cid]['evaluation'], rows[cid])
        store.save(f"{t['rule_card_path']}/evaluation.json", rules[cid]['evaluation'])
        store.save(f'data/rubrics/task_scorecards/{cid}.json',
                   dict(competition_id=cid, records=[scorecard(r, ROOT) for r in rows[cid]]))
        update_track_index(index, cid, rows[cid])
    index['total_records'] = sum(t['problems_collected'] for t in index['olympiads'])
    index['description'] = f"Agent Olympiad - {len(index['olympiads'])} tracks; mixed-unit team-task corpus. Readiness is per record."
    store.save('data/benchmarks/index.json', index)
    stage = ROOT / 'data/.cache' / f'written_packages_{store.stamp}'
    result = build_packages(ROOT, stage, dict(olympiads=tracks), rows, rules, store.sha)
    for layout in ('base', 'last_exam'):
        for cid in removed:
            target = ROOT / f'data/{layout}/tasks/{cid}'
            if target.exists():
                store.archive(target)
            source = stage / layout / 'tasks' / cid
            if source.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                install_package(source, target)
        if layout == 'last_exam':
            for cid in removed:
                target = ROOT / f'data/{layout}/competitions/{cid}'
                if target.exists():
                    store.archive(target)
                source = stage / layout / 'competitions' / cid
                if source.exists():
                    install_package(source, target)
        for filename, key in [('task_cards.json', 'tasks'), ('input_asset_manifest.json', 'files')]:
            name = f'data/{layout}/{filename}'
            old = deepcopy(store.read(name))
            new = store.read(stage / layout / filename)
            unrelated = merge_track_entries(old[key], [], removed)
            old[key] = merge_track_entries(old[key], new[key], removed)
            if key == 'tasks':
                old['n_tasks'] = len(old[key])
                if args.competition:
                    assert {r['task_id'] for r in new[key]} == {cid + '/' + r['problem_id'] for cid, records in rows.items() for r in records}
                    assert old[key][:len(unrelated)] == unrelated
                else:
                    assert len(old[key]) == index['total_records']
            store.save(name, old)
        name = f'data/{layout}/index.json'
        old = deepcopy(store.read(name))
        if layout == 'base':
            new = store.read(stage / layout / 'index.json')
            old['competitions'] = [t for t in old['competitions'] if t['id'] not in removed] + new['competitions']
        actual_cards = store.read(f'data/{layout}/task_cards.json')['tasks']
        old.update(n_tasks=len(actual_cards), n_competitions=len(index['olympiads']))
        store.save(name, old)
    name = 'data/last_exam/competitions/index.json'
    old = deepcopy(store.read(name))
    new = store.read(stage / 'last_exam/competitions/index.json')
    old['competitions'] = [t for t in old['competitions'] if t['competition_id'] not in removed] + new['competitions']
    old['n_competitions'] = len(old['competitions'])
    store.save(name, old)
    for name in (() if args.competition else ('data/rubrics/task_scorecards/history_olympiad.json',)):
        if (ROOT / name).exists():
            store.archive(name)
    if args.refresh_summary:
        summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    store.finish(dict(operation='bounded_written_track_packages', packages=result))
    print(result, 'total:', index['total_records'], 'backup:', store.backup)


if __name__ == '__main__':
    main()
