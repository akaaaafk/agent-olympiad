"""Judge-only, source-bound numeric checks, separate from rubric scores."""
import hashlib
import json
import re
from pathlib import Path

from evaluation.numeric import compare_numeric, validate_spec

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = 'data/judge_references/numeric_gold/fyziklani_v1.json'


def load_packet(row):
    path = ROOT / REGISTRY
    if not path.exists():
        raise ValueError('Missing numeric gold registry')
    raw = path.read_bytes()
    registry = json.loads(raw)
    if registry.get('role') != 'judge_only':
        raise ValueError('Numeric registry must be judge-only')
    packet = registry['packets'].get(row['problem_id'])
    if packet is None:
        return None
    ids = {str(p['id']) for p in row['gold_label']['parts']}
    seen = set()
    for part in packet['parts']:
        if part['id'] not in ids or part['id'] in seen or part['status'] != 'verified_source_value':
            raise ValueError('Invalid or unverified numeric part')
        seen.add(part['id'])
        validate_spec(part['numeric_spec'])
        source = part['source']
        resolved = (ROOT / source['path']).resolve()
        if not resolved.is_relative_to(ROOT) or not any(
            a.get('role') == 'judge_only' and (ROOT / a['path']).resolve() == resolved
            for a in row.get('assets', [])
        ):
            raise ValueError('Numeric source is not a declared judge-only asset')
        if hashlib.sha256(resolved.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Numeric source hash mismatch')
    return packet, hashlib.sha256(raw).hexdigest(), ids


def numeric_identity(row):
    loaded = load_packet(row)
    return {'registry_sha256': loaded[1], 'part_ids': [p['id'] for p in loaded[0]['parts']]} if loaded else None


def check_submission(row, submission):
    loaded = load_packet(row)
    if loaded is None:
        return None
    packet, digest, ids = loaded
    # Explicit packet IDs only. Duplicate sections are ambiguous, never gold-selected.
    headings = list(re.finditer(r'(?im)^\s*(?:#{1,6}\s*)?(?:problem\s+)?(FoL\.\d+)\s*[:=.)-]\s*', submission))
    answers = {}
    for i, match in enumerate(headings):
        key = next((k for k in ids if k.lower() == match[1].lower()), match[1])
        answers.setdefault(key, []).append(submission[match.end():headings[i+1].start() if i+1 < len(headings) else len(submission)].strip())
    results = []
    for part in packet['parts']:
        candidates = answers.get(part['id'], [])
        result = compare_numeric(part['numeric_spec'], candidates[0]) if len(candidates) == 1 else {
            'correct': False, 'reason': 'missing_answer' if not candidates else 'ambiguous_duplicate_answers'}
        results.append({'id': part['id'], **result})
    return dict(method='numeric_gold_v1', registry_sha256=digest, results=results,
                correct_count=sum(r['correct'] for r in results), checked_parts=len(results),
                total_parts=len(ids), coverage=len(results)/len(ids),
                official_score_equivalent=False, included_in_rubric_score=False)
