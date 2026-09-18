"""Refresh rules and packages for the five source-repaired main tracks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules
from scripts.build_data_packages import safe_name
from collections import Counter

TRACKS = ('eoes', 'cfa_research_challenge', 'science_olympiad',
          'odyssey_of_the_mind', 'mystery_hunt')


def main():
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_main_rules_' + uuid.uuid4().hex[:8])
    before = {}
    for cid in TRACKS:
        path = f'data/benchmarks/{cid}/benchmark.json'
        rows = store.read(path)
        before[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        rule = f'data/rules/{cid}/evaluation.json'
        value = store.read(rule)
        sync_rules(cid, value, rows)
        store.save(rule, value)
    store.finish({'operation': 'sync_main_rules_from_current_records', 'tracks': TRACKS})
    subprocess.run([sys.executable, str(ROOT / 'scripts/sync_written_track_packages_20260916.py'),
                    *[arg for cid in TRACKS for arg in ('--competition', cid)]], check=True, cwd=ROOT)
    for cid in TRACKS:
        path = f'data/benchmarks/{cid}/benchmark.json'
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == before[path]
        rows = store.read(path)
        counts = Counter(safe_name(r['problem_id']).casefold() for r in rows)
        folders = {safe_name(r['problem_id']) + ('__' + hashlib.sha256(r['problem_id'].encode()).hexdigest()[:10]
                   if counts[safe_name(r['problem_id']).casefold()] > 1 else '') for r in rows}
        for layout in ('base', 'last_exam'):
            actual = {p.name for p in (ROOT / f'data/{layout}/tasks/{cid}').iterdir() if p.is_dir()}
            assert actual == folders, (cid, layout, actual ^ folders)
        cards = json.loads((ROOT / 'data/base/task_cards.json').read_text())['tasks']
        assert {r['task_id'] for r in cards if r['category'] == cid} == {cid+'/'+r['problem_id'] for r in rows}
        scoring = json.loads((ROOT / f'data/rules/{cid}/evaluation.json').read_text())['scoring']
        assert scoring['evaluation_status_counts'] == dict(Counter(r['evaluation']['status'] for r in rows))
        print(cid, len(rows), 'rules and package membership PASS', flush=True)


if __name__ == '__main__':
    main()
