"""Replace the mini hunt selection with a reviewed standalone text puzzle."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index

ID = 'mystery_hunt_01610'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    backup = ROOT / 'tmp' / ('before_text_hunt_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    staged, originals = {}, {}

    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

    main_path = ROOT / 'data/benchmarks/mystery_hunt/benchmark.json'
    rows = read(main_path)
    row = next(r for r in rows if r['problem_id'] == ID)
    source = ROOT / row['provenance']['source_file']
    soup = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser')
    content = soup.select_one('#content')
    assert content and not content.find_all(['img', 'video', 'audio', 'iframe', 'object', 'script'])
    assert len(content.find_all('h3')) == 7 and len(content.find_all('li')) == 46
    lines = [content.h1.get_text()]
    for child in content.find_all(['h3', 'ol'], recursive=False):
        if child.name == 'h3':
            lines.extend(['', child.get_text()])
        else:
            lines.extend(f'{i}. {li.get_text()}' for i, li in enumerate(child.find_all('li', recursive=False), 1))
    text = '\n'.join(lines) + '\n'
    target = ROOT / 'data/raw/mystery_hunt/text_2012/initial_public_offering.txt'
    put(target, text.encode())
    digest = hashlib.sha256(text.encode()).hexdigest()
    asset = dict(path=target.relative_to(ROOT).as_posix(), role='agent_visible', mime_type='text/plain', sha256=digest)
    row['assets'] = [asset] + [a for a in row['assets'] if a['role'] == 'judge_only']
    row['problem_description'] = text + '\nSubmit the final puzzle answer. The seven groups and their local numbering are independent; preserve the supplied order.'
    row['provenance']['source_file'] = asset['path']
    row['provenance']['files'] = deepcopy(row['assets'])
    row.setdefault('source_review', {})['text_selection'] = dict(
        original_contestant_source=source.relative_to(ROOT).as_posix(),
        original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        official_solution_url='https://puzzles.mit.edu/2012/puzzles/mayan_fair_lady/initial_public_offering/solution/',
        review='Seven groups, 46 ordered clues, punctuation and indices preserved. Official solution confirms an independent textual extraction puzzle; no image, media, organizer or feeder-answer dependency.')
    row['evaluation'].update(evaluator_id='gold_answer_v1', status='ready',
        reason='Complete standalone text and official short answer verified.',
        limitations='Single puzzle answer accuracy; not full-hunt progression, timing or coin finding.')
    put(main_path, rows)
    mini = ROOT / 'data/mini_data'
    mini_row = json.loads(json.dumps(row).replace('data/', 'data/mini_data/'))
    put(mini / 'benchmarks/mystery_hunt/benchmark.json', [mini_row])
    for a in mini_row['assets']:
        dest = ROOT / a['path']
        src = ROOT / a['path'].replace('data/mini_data/', 'data/', 1)
        put(dest, staged[src] if src in staged else src.read_bytes())
    for data, records in ((ROOT / 'data', rows), (mini, [mini_row])):
        path = data / 'rubrics/task_scorecards/mystery_hunt.json'
        payload = read(path)
        payload['records'] = [scorecard(r, ROOT) for r in records]
        put(path, payload)
        path = data / 'benchmarks/index.json'
        index = read(path)
        update_track_index(index, 'mystery_hunt', records)
        put(path, index)
        path = data / 'rules/mystery_hunt/evaluation.json'
        rules = read(path)
        scoring = rules['scoring']
        scoring.setdefault('record_evaluator_overrides', {})[ID] = 'gold_answer_v1'
        scoring['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in records) for s in {r['evaluation']['status'] for r in records}}
        put(path, rules)
    path = mini / 'selection_manifest.json'
    selection = read(path)
    entry = next(t for t in selection['tracks'] if t['competition_id'] == 'mystery_hunt')
    if entry['selected_years'] != [2012]:
        selection.setdefault('superseded_selections', []).append(dict(**deepcopy(entry), reason='User requested replacement of 2011 with a standalone text-only puzzle.'))
    entry.update(selected_years=[2012], selected_record_ids=[ID], selected_records=1, sessions=1,
        route='native', verification='declared_assets_verified_evaluator_pending',
        selection_scope='One reviewed standalone text puzzle; not the complete 2012 hunt.')
    put(path, selection)
    path = mini / 'dependency_manifest.json'
    dependencies = read(path)
    for dest, value in list(staged.items()):
        if dest.is_relative_to(mini) and dest != path:
            src = ROOT / dest.relative_to(ROOT).as_posix().replace('data/mini_data/', 'data/', 1)
            if src.exists() or src in staged:
                original = staged[src] if src in staged else src.read_bytes()
                dependencies['files'][dest.relative_to(mini).as_posix()] = dict(source=src.relative_to(ROOT).as_posix(),
                    source_sha256=hashlib.sha256(original).hexdigest(), mini_sha256=hashlib.sha256(value).hexdigest())
    put(path, dependencies)
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            saved = backup / path.relative_to(ROOT)
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(problem_id=ID, year=2012, clues=46, backup=str(backup))))


if __name__ == '__main__':
    main()
