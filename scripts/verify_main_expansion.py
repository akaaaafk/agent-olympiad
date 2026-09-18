"""Check every promoted task across five baselines without model calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from smoke_five_baseline_routes import BASELINE_NAMES, native, artifact, pipeline

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--competition', required=True)
    parser.add_argument('--expansion-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh output directory')
    args.output.mkdir(parents=True)
    promoted = set(json.loads(args.expansion_report.read_text(encoding='utf-8'))['promoted'])
    original_read = pipeline.read
    catalog = original_read(pipeline.DATA / 'benchmarks/index.json')
    catalog['olympiads'] = [e for e in catalog['olympiads'] if e['id'] == args.competition]
    def read(path):
        return catalog if Path(path) == pipeline.DATA / 'benchmarks/index.json' else original_read(path)
    with patch.object(pipeline, 'read', side_effect=read):
        registry = pipeline.register(args.output / 'registration')
    jobs = [j for j in registry['jobs'] if set(j['problem_ids']) & promoted]
    assert set().union(*(set(j['problem_ids']) for j in jobs)) == promoted
    cases = []
    for job in jobs:
        assert not job['blockers'], job
        assert job['route'] in {'native', 'slides', 'document'}
        for variant in BASELINE_NAMES:
            config = SimpleNamespace(provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
                judge_provider='tinker', judge_model='Qwen/Qwen3.6-35B-A3B', system_variant=variant)
            identities = {}
            pipeline.command(job, args.output, config, expected_identities=identities)
            assert identities[job['id']]['settings']['evaluation']['judge_collab'] == (variant != 'single_agent')
            dest = args.output / 'runs' / job['id'] / variant
            dest.mkdir(parents=True)
            result = (native if job['route'] == 'native' else artifact)(job, variant, dest)
            case = dict(id=job['id'], variant=variant, status='PASS' if all(result['checks'].values()) else 'FAIL', **result)
            cases.append(case)
            (args.output / 'verification.json').write_text(json.dumps(dict(cases=cases,
                counts=dict(Counter(c['status'] for c in cases)), expected_cases=len(jobs)*len(BASELINE_NAMES),
                paid_calls=0, judge='mock', solver='mock'), indent=2) + '\n', encoding='utf-8')
        print(job['session'], '5 baselines checked', flush=True)
    assert all(c['status'] == 'PASS' for c in cases)
    print('PASS', len(cases), 'cases', flush=True)


if __name__ == '__main__':
    main()
