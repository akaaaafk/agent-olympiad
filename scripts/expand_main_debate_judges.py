"""Extend the validated written-speech judge to source-complete main records."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index
from enable_open_artifact_judges import definition


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    data = ROOT / 'data'
    path = data / 'benchmarks/debatebench/benchmark.json'
    rows = read(path)
    staged, originals = {}, {}
    backup = ROOT / 'tmp' / ('before_main_debate_expansion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))

    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

    rubric, prompt, route, limitations = definition('debatebench', data)
    rubric_path = data / 'rubrics' / (rubric['rubric_id'] + '.json')
    assert read(rubric_path) == rubric, 'Review changed rubric before expanding its scope'
    promoted, pending = [], []
    for row in rows:
        if row['evaluation']['status'] != 'not_ready':
            continue
        source = row.get('source_review', {}).get('motion_source', {})
        description = row['problem_description']
        reason = None
        if source.get('status') != 'primary_round_motion_verified':
            reason = 'Separate complete primary round motion/background input is not verified.'
        elif 'Source-review limitation:' in description:
            reason = 'Published background slide is mismatched; input remains unresolved.'
        elif source.get('motion', '').strip() not in description:
            reason = 'Registered prompt does not reproduce the verified motion.'
        elif source.get('infoslide_status') == 'published_present' and source.get('infoslide', '').strip() not in description:
            reason = 'Registered prompt does not reproduce the verified background slide.'
        if reason:
            pending.append(dict(problem_id=row['problem_id'], reason=reason))
            continue
        visible = [a for a in row['assets'] if a['role'] == 'agent_visible']
        assert visible and all(a['path'].endswith('motion.txt') for a in visible), row['problem_id']
        for a in row['assets']:
            assert hashlib.sha256((ROOT / a['path']).read_bytes()).hexdigest() == a['sha256'], a['path']
        ev = row['evaluation']
        ev['before_main_debate_expansion'] = deepcopy(ev)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations',
            rubric_path=rubric_path.relative_to(ROOT).as_posix(), reference_policy='rubric_only',
            grading_scope='written_artifact_benchmark', official_score_equivalent=False,
            reason='Verified round motion/background and tested written-speech rubric registered.',
            limitations=limitations, score_basis=rubric['provenance']['weight_basis'])
        row['problem_description'] += '\n\n' + prompt
        row['total_points'] = 200
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        promoted.append(row['problem_id'])
    put(path, rows)
    index_path = data / 'benchmarks/index.json'
    index = read(index_path)
    update_track_index(index, 'debatebench', rows)
    put(index_path, index)
    p = data / 'rubrics/task_scorecards/debatebench.json'
    cards = read(p)
    cards['records'] = [scorecard(row, ROOT) for row in rows]
    put(p, cards)
    for base in [data, data / 'mini_data']:
        p = base / 'rules/debatebench/evaluation.json'
        rules = read(p)
        scoring = rules['scoring']
        scoring['record_evaluator_overrides'].update({key: 'rubric_llm_v1' for key in promoted})
        scoring['record_rubric_overrides'].update({key: (base / 'rubrics' / rubric_path.name).relative_to(ROOT).as_posix() for key in promoted})
        current = rows if base == data else read(base / 'benchmarks/debatebench/benchmark.json')
        scoring['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in current) for s in {r['evaluation']['status'] for r in current}}
        put(p, rules)
    report = dict(promoted=promoted, pending=pending, unchanged_mini_membership=True, paid_calls=0,
                  scope='Verified main DebateBench written speech-generation inputs only.')
    put(ROOT / 'tmp/main_debate_expansion_20260917.json', report)
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            dst = backup / path.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(promoted=len(promoted), pending=len(pending), backup=str(backup))))


if __name__ == '__main__':
    main()
