"""Compare derived task directories/cards against canonical main records."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_data_packages import safe_name


def audit():
    index = json.loads((ROOT / 'data/benchmarks/index.json').read_text())
    cards = {layout: json.loads((ROOT / f'data/{layout}/task_cards.json').read_text())['tasks']
             for layout in ('base', 'last_exam')}
    findings = []
    for track in index['olympiads']:
        cid = track['id']
        rows = json.loads((ROOT / track['benchmark_path']).read_text())
        counts = Counter(safe_name(r['problem_id']).casefold() for r in rows)
        folders = {safe_name(r['problem_id']) + ('__' + hashlib.sha256(r['problem_id'].encode()).hexdigest()[:10]
                   if counts[safe_name(r['problem_id']).casefold()] > 1 else '') for r in rows}
        ids = {cid+'/'+r['problem_id'] for r in rows}
        errors = {}
        for layout in cards:
            parent = ROOT / f'data/{layout}/tasks/{cid}'
            actual = {p.name for p in parent.iterdir() if p.is_dir()} if parent.exists() else set()
            if actual != folders:
                errors[layout+'_directories'] = {'extra': sorted(actual-folders), 'missing': sorted(folders-actual)}
            selected = [r for r in cards[layout] if r.get('competition_id', r.get('category')) == cid]
            actual_ids = {r['task_id'] for r in selected}
            if actual_ids != ids or len(selected) != len(rows):
                errors[layout+'_cards'] = {'extra': sorted(actual_ids-ids), 'missing': sorted(ids-actual_ids)}
        if errors:
            findings.append({'competition': cid, 'errors': errors})
    return findings


if __name__ == '__main__':
    findings = audit()
    print(json.dumps(findings, indent=2))
    sys.exit(bool(findings))
