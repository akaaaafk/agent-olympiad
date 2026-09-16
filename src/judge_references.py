"""Verified, task-matched evidence exclusively for post-submission judges."""
import json
from pathlib import Path
from hashlib import sha256
from dataclasses import replace
from llm import LLMAttachment

ROOT = Path(__file__).resolve().parents[1]


def benchmark_for_asset(competition, digest):
    index = ROOT / 'data/judge_references/winners/index.json'
    if index.exists() and any(r['sha256'] == digest for r in json.loads(index.read_text(encoding='utf-8'))['records']):
        raise ValueError('Awarded work cannot be used as a contestant task PDF')
    path = ROOT / 'data/benchmarks' / competition / 'benchmark.json'
    if not path.exists():
        return None
    rows = json.loads(path.read_text(encoding='utf-8'))
    if any(asset.get('role') == 'judge_only' and asset.get('sha256') == digest
           for row in rows for asset in row.get('assets', [])):
        raise ValueError('Judge-only asset cannot be used as a contestant task PDF')
    matches = [row for row in rows if any(
        asset.get('role') == 'agent_visible' and asset.get('sha256') == digest
        for asset in row.get('assets', []))]
    if len(matches) > 1:
        raise ValueError('Ambiguous benchmark PDF: explicit task mapping is required')
    return matches[0] if matches else None


def winner_references(problem_id):
    index = ROOT / 'data/judge_references/winners/index.json'
    if not index.exists() or not problem_id:
        return []
    records = json.loads(index.read_text(encoding='utf-8'))['records']
    selected = [r for r in records if r['problem_id'] == problem_id]
    for record in selected:
        path = (ROOT / record['path']).resolve()
        if (record.get('role') != 'judge_only' or not path.is_relative_to(ROOT)
                or sha256(path.read_bytes()).hexdigest() != record['sha256']):
            raise ValueError('Invalid winner reference provenance or hash')
    return selected


def with_winner_references(request_fn, records):
    def call(request):
        if request.purpose not in {'evaluation', 'grading', 'judge'}:
            raise ValueError('Award references are available only to judges')
        # Recheck at request time, including after evaluation-only resume.
        attachments = []
        for record in records:
            path = ROOT / record['path']
            if sha256(path.read_bytes()).hexdigest() != record['sha256']:
                raise ValueError('Winner reference changed after preflight')
            attachments.append(LLMAttachment(path=path, mime_type='application/pdf', role='judge_only'))
        notes = '\n'.join(f"{r['id']}: {r['side']}; {r['award']}" for r in records)
        return request_fn(replace(request, attachments=request.attachments + tuple(attachments),
            user_prompt=request.user_prompt + '\nJUDGE-ONLY AWARDED EXAMPLES:\n' + notes +
            '\nThese works have no known numeric calibration. Do not assume a perfect score. '
            'Use the rubric and submission evidence; allow different valid arguments and respect the submitted side.'))
    return call


def with_rule_context(request_fn, rules_text):
    def call(request):
        if request.purpose not in {'evaluation', 'grading', 'judge'}:
            raise ValueError('Scoring context is available only to judges')
        return request_fn(replace(request, user_prompt=request.user_prompt +
            '\nCOMPETITION RULES (context; score only the supplied rubric):\n' + rules_text))
    return call
