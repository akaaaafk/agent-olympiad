"""Build a dependency-complete mini dataset using offline execution preflight.

One ready edition per active track; honor explicit reviewed subsets, otherwise
prefer the former mini selection, then
try other years newest first. Never launch models or overwrite paid results.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation_readiness import readiness_blockers

REVIEWED_SELECTIONS = {
    'mystery_hunt': (2012, ('mystery_hunt_01610',)),
    'eoes': (2021, ('eoes_t1', 'eoes_t2')),
}


def edition_members(name, rows, year):
    members = [r for r in rows if r.get('year') == year]
    if name in REVIEWED_SELECTIONS:
        selected_year, ids = REVIEWED_SELECTIONS[name]
        if year != selected_year:
            return []
        by_id = {r['problem_id']: r for r in members}
        if not set(ids).issubset(by_id):
            raise ValueError('Reviewed mini selection missing source records: ' + name)
        return [by_id[key] for key in ids]
    return members


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = ROOT / 'data/mini_data'
    old = read(target / 'selection_manifest.json') if target.exists() else {'tracks': []}
    preferred = {t['competition_id']: t.get('selected_years', []) for t in old['tracks']}
    catalog = read(ROOT / 'data/benchmarks/index.json')
    spec = importlib.util.spec_from_file_location('mini_builder_pipeline', ROOT / 'scripts/run_pipeline.py')
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    original_read = pipeline.read
    args = SimpleNamespace(provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
        judge_provider='tinker', judge_model='Qwen/Qwen3.6-35B-A3B', system_variant='decentralized')
    selected, exclusions = [], []
    with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as scratch:
        scratch = Path(scratch)
        for entry in catalog['olympiads']:
            name = entry['id']
            rows = read(ROOT / entry['benchmark_path'])
            years = sorted({r.get('year') for r in rows}, key=lambda y: str(y), reverse=True)
            years = list(dict.fromkeys(preferred.get(name, []) + years))
            if name in REVIEWED_SELECTIONS:
                years = [REVIEWED_SELECTIONS[name][0]]
            failures = []
            for year in years:
                members = edition_members(name, rows, year)
                if not members:
                    continue
                if year is None:
                    # No edition identifier: retain one whole session (e.g. a
                    # three-prompt WSC packet), not all unrelated tasks.
                    session = members[0].get('parent_session_id')
                    members = [r for r in members if session and r.get('parent_session_id') == session] or members[:1]
                blockers = readiness_blockers(members)
                if blockers:
                    failures.append({'year': year, 'reason': '; '.join(blockers)})
                    continue
                candidate = copy.deepcopy(catalog)
                candidate['olympiads'] = [entry]
                def candidate_read(path):
                    path = Path(path)
                    if path == ROOT / 'data/benchmarks/index.json':
                        return candidate
                    if path == ROOT / entry['benchmark_path']:
                        return members
                    return original_read(path)
                try:
                    out = scratch / name / str(year)
                    with patch.object(pipeline, 'read', side_effect=candidate_read), contextlib.redirect_stdout(io.StringIO()):
                        registry = pipeline.register(out)
                        for job in registry['jobs']:
                            if job['blockers']:
                                raise ValueError('; '.join(job['blockers']))
                            pipeline.command(job, out, args, expected_identities={})
                    selected.append({'entry': entry, 'rows': members, 'year': year,
                        'sessions': len(registry['jobs']), 'route': registry['tracks'][0]['route']})
                    print(f'PASS {name} {year}: {len(members)} records', flush=True)
                    break
                except Exception as exc:
                    failures.append({'year': year, 'reason': f'{type(exc).__name__}: {exc}'})
            else:
                exclusions.append({'competition': name, 'attempts': failures})
                print(f'EXCLUDED {name}', flush=True)

        stage = scratch / 'dataset'
        stage.mkdir()
        copied = {}
        # Stored paths remain repository-relative, but point exclusively inside mini_data.
        def relocate(value):
            if isinstance(value, dict):
                return {k: relocate(v) for k, v in value.items()}
            if isinstance(value, list):
                return [relocate(v) for v in value]
            if not isinstance(value, str) or not value.startswith('data/') or value.startswith('data/mini_data/'):
                return value
            source = ROOT / value
            if source.is_dir():
                for child in source.rglob('*'):
                    if child.is_file():
                        relocate(child.relative_to(ROOT).as_posix())
                return 'data/mini_data/' + value[5:]
            if not source.is_file():
                # Nonexistent path metadata must never silently depend on the main dataset.
                return 'data/mini_data/' + value[5:]
            relative = value[5:]
            destination = stage / relative
            if relative.startswith('benchmarks/') and relative.endswith('/benchmark.json'):
                # Rule provenance may refer to the full parent benchmark. The
                # selected benchmark must never be overwritten by that reference.
                return 'data/mini_data/' + relative
            if relative not in copied:
                copied[relative] = {'source': value, 'source_sha256': sha(source)}
                destination.parent.mkdir(parents=True, exist_ok=True)
                if source.suffix == '.json' and not relative.startswith('raw/'):
                    try:
                        write(destination, relocate(read(source)))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        shutil.copy2(source, destination)
                else:
                    shutil.copy2(source, destination)
            return 'data/mini_data/' + relative

        entries, tracks = [], []
        for item in selected:
            name = item['entry']['id']
            entry = copy.deepcopy(item['entry'])
            # Copy only selected benchmark records, never the complete parent benchmark.
            path = stage / 'benchmarks' / name / 'benchmark.json'
            write(path, relocate(item['rows']))
            entry['benchmark_path'] = 'data/mini_data/benchmarks/' + name + '/benchmark.json'
            entry['rule_card_path'] = relocate('data/rules/' + name)
            entry['problems_collected'] = len(item['rows'])
            entry['evaluation_status_counts'] = dict(__import__('collections').Counter(
                r['evaluation']['status'] for r in item['rows']))
            entries.append(relocate(entry))
            tracks.append({'competition_id': name, 'selected_years': [item['year']],
                'selected_record_ids': [r['problem_id'] for r in item['rows']],
                'selected_records': len(item['rows']), 'sessions': item['sessions'],
                'route': item['route'], 'verification': 'offline_execution_preflight_passed'})
        relocate('data/evaluation_access_policy.json')
        ids = {r['problem_id'] for item in selected for r in item['rows']}
        approvals = read(ROOT / 'data/problem_pdf_allowlist.json')
        approvals['assets'] = [a for a in approvals['assets'] if a['problem_id'] in ids]
        write(stage / 'problem_pdf_allowlist.json', relocate(approvals))
        numeric_path = ROOT / 'data/judge_references/numeric_gold/fyziklani_v1.json'
        if numeric_path.exists():
            numeric = read(numeric_path)
            numeric['packets'] = {k: v for k, v in numeric['packets'].items() if k in ids}
            write(stage / 'judge_references/numeric_gold/fyziklani_v1.json', relocate(numeric))
        winners_path = ROOT / 'data/judge_references/winners/index.json'
        if winners_path.exists():
            winners = read(winners_path)
            winners['records'] = [r for r in winners['records'] if r['problem_id'] in ids]
            write(stage / 'judge_references/winners/index.json', relocate(winners))
        write(stage / 'benchmarks/index.json', {'description': 'Independent verified one-edition mini dataset', 'olympiads': entries})
        write(stage / 'selection_manifest.json', {'schema_version': 2,
            'selection_algorithm_version': 'verified_one_edition_v2',
            'source_index_sha256': sha(ROOT / 'data/benchmarks/index.json'),
            'policy': 'Prefer previous selected year; otherwise newest full year passing execution preflight. No paid calls.',
            'tracks': tracks, 'excluded_tracks': exclusions})
        def bind_copied_hashes(value):
            if isinstance(value, dict):
                path = value.get('path')
                if isinstance(path, str) and path.startswith('data/mini_data/') and value.get('sha256'):
                    file = stage / path[len('data/mini_data/'):]
                    if file.is_file() and file.suffix == '.json':
                        actual = sha(file)
                        if actual != value['sha256']:
                            value['source_sha256'] = value['sha256']
                            value['sha256'] = actual
                for child in value.values():
                    bind_copied_hashes(child)
            elif isinstance(value, list):
                for child in value:
                    bind_copied_hashes(child)
        for file in (stage / 'benchmarks').rglob('*.json'):
            value = read(file)
            bind_copied_hashes(value)
            write(file, value)
        write(stage / 'dependency_manifest.json', {'files': copied,
            'note': 'Non-JSON files are byte-identical copies; JSON dependency paths are relocated.'})
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = ROOT / 'tmp' / ('mini_data_before_independent_' + stamp)
        if target.exists():
            shutil.copytree(target, backup)
        # All paths are explicit descendants of this checkout; replace only the mini dataset.
        if target.resolve() != (ROOT / 'data/mini_data').resolve():
            raise ValueError('Unexpected dataset destination')
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(stage, target)
        subprocess.run([sys.executable, str(ROOT / 'scripts/verify_mini_dataset.py')], cwd=ROOT, check=True)
        print(json.dumps({'tracks': len(tracks), 'records': sum(t['selected_records'] for t in tracks),
            'sessions': sum(t['sessions'] for t in tracks), 'dependency_files': len(copied), 'backup': str(backup)}), flush=True)


if __name__ == '__main__':
    main()
