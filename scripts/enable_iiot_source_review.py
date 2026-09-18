"""Explicitly separate IIOT 2021 LLM code-review points from official execution."""
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


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    backup = ROOT / 'tmp' / ('before_iiot_llm_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    staged = {}
    old = {}
    def stage(p, value):
        old[p] = p.read_bytes() if p.exists() else None
        staged[p] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    prompt = ('BENCHMARK SUBMISSION: Submit complete C++ source code as the final shared text artifact, '
              'with a short correctness and complexity explanation. This run uses LLM source review against '
              'the statement and each published subtask constraint. Reference implementations are judge-only. '
              'It does not submit to an official judge; do not claim unseen tests have passed.')
    for data in (ROOT / 'data', ROOT / 'data/mini_data'):
        path = data / 'benchmarks/iiot/benchmark.json'
        rows = read(path)
        selected = [r for r in rows if r.get('year') == 2021]
        assert len(selected) == 8
        for row in selected:
            row_prompt = prompt + (' Chimneys receives a code-quality estimate, never an invented measured output/reference ratio.'
                                   if row['problem_id'] == 'iiot_2021_01' else '')
            ev = row['evaluation']
            ev.setdefault('before_source_review_llm', deepcopy(ev))
            text = row['problem_description'].split('Scoring', 1)[1].split('Examples\n', 1)[0]
            sub = re.findall(r'Subtask\s*(\d+)\s*\((\d+)\s*points\)(.*?)(?=[–−-]?Subtask|$)', text, re.S)
            assert [(int(i), int(w)) for i, w, _ in sub] == [(s['id'], s['points']) for s in ev['official_subtasks']]
            criteria = []
            for sid, weight, condition in sub:
                if int(weight) == 0:
                    continue
                condition = re.sub(r'\[book indicator:[^]]*\]', '', condition).strip(' –\n')
                description = ('Review submitted source code for this published subtask: ' + condition +
                    ' Apply the full statement as well. Assess algorithm correctness, edge cases, input/output '
                    'handling and complexity under these constraints. This is a static-review benchmark: '
                    '0% = no usable implementation or fundamentally incorrect; 25% = plausible idea but major '
                    'implementation gaps; 50% = substantial implementation with material defects; '
                    '75% = mostly supported with limited gaps; 100% = implementation and reasoning support '
                    'the entire constraint class. Cite concrete code evidence; different correct algorithms '
                    'are acceptable. Partial review credit is not official test-based subtask credit. '
                    'Do not invent a compilation result, hidden test pass rate or measured optimization ratio.')
                criteria.append(dict(id='subtask_' + sid, name='Subtask ' + sid + ' source review',
                    max_score=int(weight), min_score=0, observable=True, description=description))
            rp = data / 'rubrics' / (row['problem_id'] + '_source_review_v1.json')
            limitations = ['LLM static source-review score with published subtask weights and benchmark partial-credit anchors.',
                'No claim of compilation, official test execution or official all-cases credit.',
                'Two printed samples validated only the archived reference, not the generated submission.']
            rubric = dict(rubric_id=rp.stem, title=row['problem_id'] + ' source review', total_points=100,
                criteria=criteria, not_observable_from_deck=limitations,
                provenance=dict(source_path=row['source_file'], published_subtasks=ev['official_subtasks'],
                                official_score_equivalent=False))
            assert sum(c['max_score'] for c in criteria) == 100
            stage(rp, rubric)
            refs = [{k: a[k] for k in ('path', 'sha256')} for a in row['assets']
                    if a['role'] == 'judge_only' and a['path'].endswith('.cpp')]
            assert len(refs) == 1
            ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations',
                grading_policy='source_review_llm_v1', rubric_path=str(rp.relative_to(ROOT)).replace('\\', '/'),
                judge_reference_files=refs, official_score_equivalent=False, execution_verified=False,
                official_execution_status='not_ready', limitations=limitations,
                reason='LLM code review registered; official execution remains unavailable.',
                score_basis='Published subtask maxima; benchmark static-review partial-credit scale.')
            row['problem_description'] = row['problem_description'].split('BENCHMARK SUBMISSION:', 1)[0].rstrip() + '\n\n' + row_prompt
            row['total_points'] = 100
            row['gold_label']['grading_rubric'] = ev['rubric_path']
            # A previous relocation serialized these manifests after binding hashes.
            # Repair only when the content equals the canonical source modulo paths.
            for key in ('assets',):
                for asset in row[key]:
                        if not asset['path'].endswith('/reference_manifest.json'):
                            continue
                        p = ROOT / asset['path']
                        canonical = ROOT / asset['path'].replace('data/mini_data/', 'data/', 1)
                        normalized = json.loads(p.read_text(encoding='utf-8').replace('data/mini_data/', 'data/'))
                        assert normalized == read(canonical), 'Non-relocation source drift'
                        asset['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
                        if data.name == 'mini_data':
                            asset['source_sha256'] = hashlib.sha256(canonical.read_bytes()).hexdigest()
            if isinstance(row.get('provenance', {}).get('assets'), list):
                lookup = {a['path']: a for a in row['assets']}
                row['provenance']['assets'] = [deepcopy(lookup.get(a['path'], a)) for a in row['provenance']['assets']]
        stage(path, rows)
        cp = data / 'rules/iiot/competition.json'
        card = read(cp)
        card['rules_text'] += '\nSelected records with source_review_llm_v1: ' + prompt if prompt not in card['rules_text'] else ''
        stage(cp, card)
        ep = data / 'rules/iiot/evaluation.json'
        payload = read(ep)
        for row in selected:
            payload['scoring']['record_evaluator_overrides'][row['problem_id']] = 'rubric_llm_v1'
            payload['scoring']['record_rubric_overrides'][row['problem_id']] = row['evaluation']['rubric_path']
        payload['scoring']['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in rows)
            for s in {r['evaluation']['status'] for r in rows}}
        stage(ep, payload)
        sp = data / 'rubrics/task_scorecards/iiot.json'
        score = read(sp)
        byid = {r['problem_id']: r for r in selected}
        score['records'] = [scorecard(byid[r['problem_id']], ROOT,
            read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
            hash_file=lambda p: hashlib.sha256(staged.get(ROOT / p) or (ROOT / p).read_bytes()).hexdigest())
            if r['problem_id'] in byid else r for r in score['records']]
        stage(sp, score)
        ip = data / 'benchmarks/index.json'
        index = read(ip); update_track_index(index, 'iiot', rows); stage(ip, index)
    for p, before in old.items():
        if (p.read_bytes() if p.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(p))
    for p, value in staged.items():
        if old[p] == value:
            continue
        if old[p] is not None:
            target = backup / p.relative_to(ROOT); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(old[p])
        p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(value)
    print('IIOT 2021: 8 code-review rubrics registered; official execution not promoted.', backup)


if __name__ == '__main__':
    main()
