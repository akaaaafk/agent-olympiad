"""Prepare one reproducibly selected mini-data task per competition.

Run with run_mini_dataset.py run (not all/register, which rebuild full sessions).
Selection uses public statement length/IDs, never gold answers or model scores.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ['AGENT_OLYMPIAD_DATA_ROOT'] = str(ROOT / 'data/mini_data')
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
import run_pipeline as pipeline
from contest_manifest import load_contest_manifest, _numbered_prompts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if (out / 'registry.json').exists():
        raise ValueError('Use a fresh output directory; smoke selection is immutable.')
    out.mkdir(parents=True, exist_ok=True)
    registry = pipeline.register(out)
    selected, audit = [], []
    for track in registry['tracks']:
        name = track['competition']
        rows = pipeline.read(pipeline.DATA / 'benchmarks' / name / 'benchmark.json')
        candidates = [j for j in registry['jobs'] if j['competition'] == name]
        by_id = {r['problem_id']: r for r in rows}
        forced = {'iiot': 'iiot_2021_04', 'arml_local': 'arml_local_2013'}.get(name)
        chosen = (by_id[forced] if forced else min(rows, key=lambda r: (
            len(r.get('problem_description') or ''), r['problem_id'])))
        job = next(j for j in candidates if chosen['problem_id'] in j['problem_ids'])
        job['problem_ids'] = [chosen['problem_id']]
        note = 'One complete indivisible benchmark record'
        question = None
        if job['route'] == 'native':
            manifest = pipeline.read(job['manifest'])
            manifest['problem_ids'] = job['problem_ids']
            parts = (chosen.get('gold_label') or {}).get('parts') or []
            ids = [str(p['id']) for p in parts]
            prompts = _numbered_prompts(chosen.get('problem_description', ''), ids) if ids else {}
            # Current LLM packet judge rejects split tasks even when its rubric
            # contains per-problem criteria. Do not silently apply a packet
            # rubric to a single proof. Exact-answer graders support splitting.
            split_supported = chosen.get('evaluation', {}).get('evaluator_id') != 'rubric_llm_v1'
            if ids and len(prompts) == len(ids) and split_supported:
                question = '9' if name == 'arml_local' else ids[0]
                manifest.update(split_parts=True, question_ids=[question])
                note = 'One numbered subquestion from the original statement'
            else:
                manifest['split_parts'] = False
                if ids and not split_supported:
                    note = 'Single-question smoke unavailable: packet rubric has no split-task mapping'
                    job['blockers'].append(note)
            if name == 'wsc_writing':
                note = 'Single-question smoke unavailable: writing flow requires three distinct tasks'
                job['blockers'].append(note)
            pipeline.write(job['manifest'], manifest)
            loaded = load_contest_manifest(job['manifest'], benchmark_root=pipeline.DATA / 'benchmarks')
            assert len(loaded.tasks) == 1, name
        else:
            note = 'One complete artifact task; no independent small-question rubric exists'
        selected.append(job)
        audit.append({'competition': name, 'job_id': job['id'], 'problem_id': chosen['problem_id'],
            'question_id': question, 'route': job['route'], 'scope': note,
            'blockers': job['blockers'],
            'selection': 'Targeted known regression' if forced else 'Shortest public statement, then ID'})
    assert len(selected) == len({j['competition'] for j in selected}) == len(registry['tracks'])
    registry.update(jobs=selected, session_count=len(selected), smoke_scope='one_task_per_competition')
    pipeline.write(out / 'registry.json', registry)
    pipeline.write(out / 'smoke_selection.json', audit)
    print(json.dumps({'output': str(out), 'competitions': len(selected),
        'subquestions': sum(r['question_id'] is not None for r in audit),
        'artifact_tasks': sum(r['route'] != 'native' for r in audit)}))


if __name__ == '__main__':
    main()
