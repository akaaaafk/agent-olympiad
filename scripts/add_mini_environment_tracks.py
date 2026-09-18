"""Preserve material-ready tracks separately from local environment readiness."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import argparse
import tempfile
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/mini_data'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-remaining', action='store_true', help='Include all active tracks, retaining evaluator blockers')
    args = parser.parse_args()
    catalog = read(ROOT / 'data/benchmarks/index.json')
    index = read(DATA / 'benchmarks/index.json')
    selection = read(DATA / 'selection_manifest.json')
    dependency = read(DATA / 'dependency_manifest.json')
    protected = {e['benchmark_path'] for e in catalog['olympiads']}
    seen = set()
    def relocate(value):
        if isinstance(value, dict):
            return {k: relocate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relocate(v) for v in value]
        if not isinstance(value, str) or not value.startswith('data/') or value.startswith('data/mini_data/'):
            return value
        source = ROOT / value
        destination = DATA / value[5:]
        if value not in seen and value not in protected:
            seen.add(value)
            if source.is_dir():
                for file in source.rglob('*'):
                    if file.is_file():
                        relocate(file.relative_to(ROOT).as_posix())
            elif source.is_file():
                dependency['files'][value[5:]] = {'source': value,
                    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
                destination.parent.mkdir(parents=True, exist_ok=True)
                if source.suffix == '.json' and not value.startswith('data/raw/'):
                    write(destination, relocate(read(source)))
                else:
                    shutil.copy2(source, destination)
        return 'data/mini_data/' + value[5:]
    choices = [('mcm', 2024, 'mcm_2024_A', 'Docker/LaTeX renderer'),
        ('icm', 2015, 'icm_2015_D', 'Docker/LaTeX renderer'),
        ('icpc', 2018, None, 'Docker and VJudge gateway')]
    if args.include_remaining:
        before = ROOT / 'tmp' / ('mini_inclusion_before_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
        before.mkdir(parents=True)
        for relative in ['benchmarks/index.json', 'selection_manifest.json', 'dependency_manifest.json', 'verification.json']:
            if (DATA / relative).exists():
                shutil.copy2(DATA / relative, before / Path(relative).name)
        former = read(ROOT / 'tmp/mini_data_before_independent_20260916_180257/selection_manifest.json')
        preferred = {t['competition_id']: t['selected_years'] for t in former['tracks']}
        for item in selection['excluded_tracks']:
            name = item['competition']
            entry = next(e for e in catalog['olympiads'] if e['id'] == name)
            rows = read(ROOT / entry['benchmark_path'])
            years = {r.get('year') for r in rows}
            year = next((y for y in preferred.get(name, []) if y in years),
                sorted(years, key=lambda y: str(y), reverse=True)[0])
            choices.append((name, year, None, None))
    for name, year, problem, environment in choices:
        if any(e['id'] == name for e in index['olympiads']):
            continue
        entry = copy.deepcopy(next(e for e in catalog['olympiads'] if e['id'] == name))
        rows = [r for r in read(ROOT / entry['benchmark_path']) if r.get('year') == year
            and (problem is None or r['problem_id'] == problem)]
        assert rows
        if environment is not None:
            assert all(r['evaluation']['status'] in {'ready', 'remote_judge_ready'} for r in rows)
        # Validate every declared file and hash before copying.
        for row in rows:
            for asset in row.get('assets', []):
                file = ROOT / asset['path']
                if not file.is_file() or (asset.get('sha256') and hashlib.sha256(file.read_bytes()).hexdigest() != asset['sha256']):
                    raise ValueError(f'Invalid declared asset: {file}')
        relocate('data/rules/' + name)
        write(DATA / 'benchmarks' / name / 'benchmark.json', relocate(rows))
        entry = relocate(entry)
        entry['problems_collected'] = len(rows)
        entry['evaluation_status_counts'] = dict(__import__('collections').Counter(r['evaluation']['status'] for r in rows))
        entry['dataset_environment_status'] = 'environment_pending' if environment else 'evaluator_pending'
        index['olympiads'].append(entry)
        selection['tracks'].append({'competition_id': name, 'selected_years': [year],
            'selected_record_ids': [r['problem_id'] for r in rows], 'selected_records': len(rows),
            'sessions': 1, 'route': 'native' if name == 'icpc' else 'document',
            'verification': 'declared_assets_verified_environment_pending' if environment else 'declared_assets_verified_evaluator_pending',
            'required_environment': environment,
            'record_policy': 'one complete published problem' if problem else 'one full contest year'})
        selection['excluded_tracks'] = [t for t in selection['excluded_tracks'] if t['competition'] != name]
        print(name, year, len(rows), environment)
    write(DATA / 'benchmarks/index.json', index)
    write(DATA / 'selection_manifest.json', selection)
    write(DATA / 'dependency_manifest.json', dependency)
    # Bind relocated JSON assets to their actual dataset bytes, retaining source hashes.
    for path in (DATA / 'benchmarks').glob('*/benchmark.json'):
        rows = read(path)
        for row in rows:
            for asset in row.get('assets', []):
                file = ROOT / asset['path']
                if file.suffix == '.json' and asset.get('sha256') and file.is_file():
                    digest = hashlib.sha256(file.read_bytes()).hexdigest()
                    if digest != asset['sha256']:
                        asset.setdefault('source_sha256', asset['sha256'])
                        asset['sha256'] = digest
        write(path, rows)
    with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as scratch:
        subprocess.run([sys.executable, str(ROOT / 'scripts/run_mini_dataset.py'), 'register',
            '--output', scratch], cwd=ROOT, check=True)
        registry = read(Path(scratch) / 'registry.json')
    for track in selection['tracks']:
        jobs = [j for j in registry['jobs'] if j['competition'] == track['competition_id']]
        track['sessions'] = len(jobs)
        track['route'] = next(t['route'] for t in registry['tracks'] if t['competition'] == track['competition_id'])
        if track['verification'] == 'declared_assets_verified_evaluator_pending':
            track['runtime_blockers'] = list(dict.fromkeys(b for j in jobs for b in j['blockers']))
    write(DATA / 'selection_manifest.json', selection)


if __name__ == '__main__':
    main()
