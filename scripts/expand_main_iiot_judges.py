"""Enable source-grounded static review for remaining archived IIOT editions."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index

PROMPT = ('BENCHMARK SUBMISSION: Submit complete C++ code and a correctness/complexity explanation '
          'as the final shared text artifact. The evaluator reviews source against the original statement '
          'and published subtask constraints, using judge-only reference implementations. '
          'This is static code review, not an official execution judge. No compilation, hidden-test '
          'pass rate or measured optimization/fractional score may be claimed without execution evidence.')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def published_subtasks(row):
    text = row['problem_description'].split('Scoring', 1)[1].split('Examples\n', 1)[0]
    sub = re.findall(r'Subtask\s*(\d+)\s*[\[(]\s*(\d+)\s*points[\])]\s*:?(.*?)(?=Subtask|$)', text, re.S)
    expected = [(s['id'], s['points']) for s in row['evaluation']['official_subtasks']]
    if [(int(i), int(w)) for i, w, _ in sub] != expected or sum(w for _, w in expected) != 100:
        raise ValueError('Statement and published weight manifest disagree: ' + row['problem_id'])
    return sub


def main():
    data = ROOT / 'data'
    path = data / 'benchmarks/iiot/benchmark.json'
    rows = read(path)
    staged, originals, promoted = {}, {}, []
    backup = ROOT / 'tmp' / ('before_main_iiot_expansion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))

    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

    for row in rows:
        if row['year'] not in {2017, 2022, 2023} or row['evaluation']['status'] != 'not_ready':
            continue
        criteria = []
        for sid, weight, condition in published_subtasks(row):
            if int(weight) == 0:
                continue
            condition = re.sub(r'\[book indicator:[^]]*\]', '', condition)
            condition = re.sub(r'\b[a-z]+\s+Page\s+\d+\s+of\s+\d+.*', '', condition, flags=re.S).strip(' \n\u2013\u2212\u2022-')
            criteria.append(dict(id='subtask_' + sid, name='Subtask ' + sid + ' source review',
                max_score=int(weight), min_score=0, observable=True,
                description='Review this published subtask under the complete statement: ' + condition +
                    ' Assess algorithm correctness, edge cases, input/output handling and complexity. '
                    'Benchmark partial-credit anchors: 0% no usable implementation/fundamentally incorrect; '
                    '25% plausible idea with major gaps; 50% substantial implementation with material defects; '
                    '75% mostly supported with limited gaps; 100% code and reasoning support the full constraint class. '
                    'Cite concrete submitted code. Alternative correct algorithms are acceptable. '
                    'References are examples, not mandatory implementations or evidence that the submission ran. '
                    'For optimization/fractional tasks assess the proposed algorithm; never invent a measured ratio, '
                    'compilation outcome or hidden-test pass rate.'))
        refs = []
        for a in row['assets']:
            if hashlib.sha256((ROOT / a['path']).read_bytes()).hexdigest() != a['sha256']:
                raise ValueError('Source asset changed: ' + a['path'])
            if a['role'] == 'judge_only' and '/references/' in a['path'] and Path(a['path']).suffix in {'.cpp', '.c'}:
                refs.append({k: a[k] for k in ('path', 'sha256')})
        if not refs:
            raise ValueError('No judge-only reference implementation: ' + row['problem_id'])
        ev = row['evaluation']
        ev['before_main_source_review'] = deepcopy(ev)
        limitations = ['Static LLM source-review score using published weights and benchmark partial-credit anchors.',
            'Official test mapping, runtime limits and checker validation remain unresolved; no official execution score.',
            'No compilation, hidden-test result or measured fractional/optimization ratio is inferred.']
        rp = data / 'rubrics' / (row['problem_id'] + '_source_review_v1.json')
        rubric = dict(rubric_id=rp.stem, title=row['problem_id'] + ' static source review', total_points=100,
            criteria=criteria, not_observable_from_deck=limitations,
            provenance=dict(source_path=row['source_file'], published_subtasks=ev['official_subtasks'],
                reference_files=refs, official_score_equivalent=False))
        put(rp, rubric)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations',
            grading_policy='source_review_llm_v1', rubric_path=rp.relative_to(ROOT).as_posix(),
            judge_reference_files=refs, official_score_equivalent=False, execution_verified=False,
            official_execution_status='not_ready', limitations=limitations,
            reason='Published constraints, weights and reference implementations bound to static source review.',
            score_basis='Published subtask maxima; explicitly benchmark static-review partial credit.')
        row['problem_description'] += '\n\n' + PROMPT
        row['total_points'] = 100
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        promoted.append(row['problem_id'])
    put(path, rows)
    for base in [data, data / 'mini_data']:
        p = base / 'rules/iiot/evaluation.json'
        rules = read(p)
        for row in rows:
            if row['problem_id'] in promoted:
                rules['scoring']['record_evaluator_overrides'][row['problem_id']] = 'rubric_llm_v1'
                # Rule overrides for non-selected editions are provenance only in
                # mini; copy their rubrics so no rule points outside that dataset.
                rp = ROOT / row['evaluation']['rubric_path']
                dest = base / 'rubrics' / rp.name
                rules['scoring']['record_rubric_overrides'][row['problem_id']] = dest.relative_to(ROOT).as_posix()
                if base != data:
                    value = json.loads(staged[rp].decode().replace('data/', 'data/mini_data/'))
                    put(dest, value)
        current = rows if base == data else read(base / 'benchmarks/iiot/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in current) for s in {r['evaluation']['status'] for r in current}}
        put(p, rules)
    ip = data / 'benchmarks/index.json'
    index = read(ip)
    update_track_index(index, 'iiot', rows)
    put(ip, index)
    sp = data / 'rubrics/task_scorecards/iiot.json'
    cards = read(sp)
    cards['records'] = [scorecard(r, ROOT,
        read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
        hash_file=lambda p: hashlib.sha256(staged[ROOT / p] if ROOT / p in staged else (ROOT / p).read_bytes()).hexdigest()) for r in rows]
    put(sp, cards)
    put(ROOT / 'tmp/main_iiot_expansion_20260917.json', dict(promoted=promoted,
        scope='Static source review only', mini_membership_changed=False, paid_calls=0))
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            dest = backup / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(promoted=len(promoted), backup=str(backup))))


if __name__ == '__main__':
    main()
