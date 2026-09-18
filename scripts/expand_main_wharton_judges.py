"""Enable report-only scoring for the two complete archived client cases."""
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


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    data = ROOT / 'data'
    path = data / 'benchmarks/wharton_investment/benchmark.json'
    rows = read(path)
    staged, originals, promoted = {}, {}, []
    backup = ROOT / 'tmp' / ('before_main_wharton_expansion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

    rubric, prompt, _, _ = definition('wharton_investment', data)
    rubric['rubric_id'] = 'wharton_archived_client_report_v1'
    limitations = ['Current same-competition qualitative considerations reused for archived cases; not historical official weights.',
        'Equal 25-point weights are benchmark choices, not official scoring maxima.',
        'Written proposal only; simulator trades, realized returns, stock-list eligibility and oral performance are not scored.']
    rubric['not_observable_from_deck'] = limitations
    prompt += (' The historical approved-stock list and simulator are not supplied in this written route. '
        'Give an asset-allocation strategy and clearly label proposed securities as eligibility-unverified; '
        'do not claim that a stock was on the historical list or that trades occurred. '
        'Honor the actual client constraints in this case, state dates and assumptions, and do not contact the client.')
    rp = data / 'rubrics' / (rubric['rubric_id'] + '.json')
    put(rp, rubric)
    required = {2019: ['Reshma Sohoni', '20%', '$100,000'],
                2020: ['Florian Hagenbuch', '20%', '10%', '$10,000', 'December 2020']}
    for row in rows:
        if row['year'] not in required or row['evaluation']['status'] != 'not_ready':
            continue
        assert all(term in row['problem_description'] for term in required[row['year']]), row['problem_id']
        for a in row['assets']:
            assert a['role'] == 'agent_visible' and a['path'].endswith('.html')
            assert hashlib.sha256((ROOT / a['path']).read_bytes()).hexdigest() == a['sha256']
        ev = row['evaluation']
        ev['before_main_report_review'] = deepcopy(ev)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations', rubric_path=rp.relative_to(ROOT).as_posix(),
            reference_policy='rubric_only', grading_scope='written_artifact_benchmark', official_score_equivalent=False,
            limitations=limitations, score_basis=rubric['provenance']['weight_basis'],
            reason='Complete historical client case with explicitly scoped written-report rubric.')
        row['problem_description'] += '\n\n' + prompt
        row['total_points'] = 100
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        promoted.append(row['problem_id'])
    put(path, rows)
    for base in [data, data / 'mini_data']:
        p = base / 'rules/wharton_investment/evaluation.json'
        rules = read(p)
        dest = base / 'rubrics' / rp.name
        if base != data:
            put(dest, json.loads(json.dumps(rubric).replace('data/', 'data/mini_data/')))
        for key in promoted:
            rules['scoring']['record_evaluator_overrides'][key] = 'rubric_llm_v1'
            rules['scoring']['record_rubric_overrides'][key] = dest.relative_to(ROOT).as_posix()
        current = rows if base == data else read(base / 'benchmarks/wharton_investment/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in current) for s in {r['evaluation']['status'] for r in current}}
        put(p, rules)
    ip = data / 'benchmarks/index.json'
    index = read(ip)
    update_track_index(index, 'wharton_investment', rows)
    put(ip, index)
    sp = data / 'rubrics/task_scorecards/wharton_investment.json'
    cards = read(sp)
    cards['records'] = [scorecard(r, ROOT,
        read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
        hash_file=lambda p: hashlib.sha256(staged[ROOT / p] if ROOT / p in staged else (ROOT / p).read_bytes()).hexdigest()) for r in rows]
    put(sp, cards)
    put(ROOT / 'tmp/main_wharton_expansion_20260917.json', dict(promoted=promoted,
        scope='Written client proposal only', mini_membership_changed=False, paid_calls=0))
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
