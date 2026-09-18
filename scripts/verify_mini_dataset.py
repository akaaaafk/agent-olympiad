"""Offline proof of dataset isolation; rejects reads from the parent data tree."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/mini_data'
os.environ['AGENT_OLYMPIAD_DATA_ROOT'] = str(DATA)
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DATA / 'verification.json')
    args = parser.parse_args()
    denied = []
    def isolated(event, arguments):
        if event != 'open' or not isinstance(arguments[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(arguments[0])).resolve()
        if path.is_relative_to(ROOT / 'data') and not path.is_relative_to(DATA):
            denied.append(str(path))
            raise RuntimeError(f'Parent dataset access forbidden: {path}')
    sys.addaudithook(isolated)
    spec = importlib.util.spec_from_file_location('verify_mini_pipeline', ROOT / 'scripts/run_pipeline.py')
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    outcomes = []
    selection = pipeline.read(DATA / 'selection_manifest.json')
    evaluator_tracks = {t['competition_id'] for t in selection['tracks']
        if t['verification'] == 'declared_assets_verified_evaluator_pending'}
    with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as scratch:
        scratch = Path(scratch)
        for variant in ['decentralized', 'centralized', 'single_agent', 'vallina_otc', 'otc']:
            out = scratch / variant
            registry = pipeline.register(out)
            config = SimpleNamespace(provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
                judge_provider='tinker', judge_model='Qwen/Qwen3.6-35B-A3B', system_variant=variant)
            for job in registry['jobs']:
                try:
                    if job['blockers']:
                        if job['competition'] in evaluator_tracks:
                            outcomes.append({'id': job['id'], 'variant': variant,
                                'state': 'evaluator_pending', 'reason': '; '.join(job['blockers'])})
                            continue
                        raise ValueError('; '.join(job['blockers']))
                    identities = {}
                    command = pipeline.command(job, out, config, expected_identities=identities)
                    collab = identities[job['id']]['settings']['evaluation']['judge_collab']
                    if collab != (variant != 'single_agent'):
                        raise ValueError('Collaboration evaluation flag does not match baseline')
                    outcomes.append({'id': job['id'], 'variant': variant, 'state': 'prepared',
                        'judge_collab': identities[job['id']]['settings']['evaluation']['judge_collab']})
                except Exception as exc:
                    reason = str(exc)
                    # Unavailable local services are environment state, not data defects.
                    expected = any(s in reason for s in ['LaTeX renderer unavailable', 'docker',
                        'VJudge gateway', 'urlopen error', 'Another contest runner'])
                    outcomes.append({'id': job['id'], 'variant': variant,
                        'state': 'environment_pending' if expected else 'failed', 'reason': reason})
    checked = 0
    errors = []
    for entry in pipeline.read(DATA / 'benchmarks/index.json')['olympiads']:
        rows = pipeline.read(ROOT / entry['benchmark_path'])
        track = next(t for t in selection['tracks'] if t['competition_id'] == entry['id'])
        if sorted(r['problem_id'] for r in rows) != sorted(track['selected_record_ids']):
            errors.append({'competition': entry['id'], 'reason': 'selected membership mismatch'})
        if {r.get('year') for r in rows} != set(track['selected_years']):
            errors.append({'competition': entry['id'], 'reason': 'selected year mismatch'})
        for row in rows:
            for asset in row.get('assets') or row.get('provenance', {}).get('assets', []):
                path = (ROOT / asset['path']).resolve()
                if not path.is_relative_to(DATA) or not path.is_file():
                    errors.append({'problem_id': row['problem_id'], 'path': str(path), 'reason': 'missing or external'})
                    continue
                if asset.get('sha256') and hashlib.sha256(path.read_bytes()).hexdigest() != asset['sha256']:
                    errors.append({'problem_id': row['problem_id'], 'path': str(path), 'reason': 'hash mismatch'})
                checked += 1
    payload = {'passed': not denied and not errors and all(o['state'] != 'failed' for o in outcomes),
        'all_jobs_environment_ready': all(o['state'] == 'prepared' for o in outcomes),
        'parent_data_reads_denied': denied, 'asset_checks': checked, 'asset_errors': errors,
        'paid_model_calls': 0, 'verification_scope': 'Offline execution preflight, not model-generated submissions',
        'jobs': outcomes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in payload.items() if k != 'jobs'}))
    print('prepared', sum(o['state'] == 'prepared' for o in outcomes), 'failed', sum(o['state'] == 'failed' for o in outcomes))
    return 0 if payload['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
