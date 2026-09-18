"""Apply source-backed 2021 input recovery without claiming official judge readiness."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard
CACHE = ROOT / 'tmp/iiot_2021_recovery'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    discovery, files, validation = read(CACHE / 'discovery.json'), read(CACHE / 'downloads.json'), read(CACHE / 'reference_validation.json')
    assert len(files) == 236 and not any('error' in f for f in files)
    assert len(validation) == 8 and all(v['status'] == 'samples_validated' for v in validation)
    assert all(sha(ROOT / f['path']) == f['sha256'] for f in files)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / 'tmp' / ('iiot_2021_before_' + stamp)
    writes, observed = {}, {}
    def stage(path, value):
        observed.setdefault(path, sha(path) if path.exists() else None)
        writes[path] = value
    canonical_path = ROOT / 'data/benchmarks/iiot/benchmark.json'
    original = read(canonical_path)
    updated = deepcopy(original)
    for row in updated:
        if row.get('year') != 2021:
            continue
        pid = row['problem_id']
        reference_path = ROOT / row['evaluation']['source_archive_manifest']
        reference = read(reference_path)
        task = next(t for t in discovery['tasks'] if t['task'] == reference['task_code'])
        selected = [f for f in files if f['task'] == task['task']]
        assets = []
        for file in selected:
            target = ROOT / 'data/raw/iiot/2021' / task['task'] / 'tests' / file['relative']
            if target.exists() and sha(target) != file['sha256']:
                raise ValueError(f'Existing test differs: {target}')
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(ROOT / file['path'], target)
            assets.append({'path': target.relative_to(ROOT).as_posix(), 'role': 'judge_only',
                'mime_type': 'text/plain', 'sha256': file['sha256'], 'source_url': 'https://drive.google.com/file/d/' + file['id'] + '/view'})
        manifest_path = ROOT / 'data/raw/iiot/2021' / task['task'] / 'tests/source_manifest.json'
        proof = next(v for v in validation if v['problem_id'] == pid)
        source_manifest = {'problem_id': pid, 'publisher': discovery['publisher'],
            'checked_at': discovery['checked_at'], 'test_folder': task['links'].get('Test cases'),
            'inputs': assets, 'input_count': len(assets), 'published_output_count': 0,
            'paired_official_tests': 0, 'test_to_subtask_mapping': None, 'reference_sample_validation': proof}
        stage(manifest_path, source_manifest)
        evaluation = row['evaluation']
        evaluation.update(test_source_manifest=manifest_path.relative_to(ROOT).as_posix(),
            archived_test_inputs=len(assets), official_test_pair_count=0,
            source_repair_status='publisher_inputs_archived_reference_samples_validated',
            reference_execution_validation=proof,
            reason='Publisher test inputs and reference source are archived; official outputs, checker, limits and original subtask mapping are not available.',
            limitations=['Public test folder contains input files only; no published standard output or test/subtask map was recovered.' if assets else
                'The current publisher page has no test-folder link for Chimneys.',
                'Archived reference compiled and passed two printed samples in isolated Docker; this does not certify all hidden cases or official execution limits.',
                'Original checker configuration, time/memory limits and test-to-subtask assignments remain unresolved.'])
        if task['task'] == 'chimneys':
            evaluation['official_scoring_mode'] = 'minimum_case_quality_ratio_per_subtask'
            evaluation['score_basis'] = 'For valid constructions: min(1, shortest_output_chimney / shortest_reference_chimney); subtask score is its weight times minimum case score. Invalid constructions score zero.'
            evaluation['limitations'].append('Chimneys requires a validity and quality-ratio checker, not expected-output equality. No official hidden input/reference quality targets were recovered.')
        reference['source_links'] = task['links']
        reference['public_test_listing'] = {'status': 'inputs_only_archived' if assets else 'no_testcase_link_in_publisher_archive',
            'input_count': len(assets), 'output_count': 0, 'checked_at': discovery['checked_at']}
        reference['reference']['execution_validation'] = proof
        if task['task'] == 'chimneys':
            reference['official_scoring']['mode'] = evaluation['official_scoring_mode']
        stage(reference_path, reference)
        paths = {a['path'] for a in row['assets']}
        row['assets'].extend(a for a in assets if a['path'] not in paths)
    stage(canonical_path, updated)
    by_id = {r['problem_id']: r for r in updated if r.get('year') == 2021}
    def relocate(v):
        if isinstance(v, dict):
            return {k: relocate(x) for k, x in v.items()}
        if isinstance(v, list):
            return [relocate(x) for x in v]
        return 'data/mini_data/' + v[5:] if isinstance(v, str) and v.startswith('data/') and not v.startswith('data/mini_data/') else v
    mini_path = ROOT / 'data/mini_data/benchmarks/iiot/benchmark.json'
    mini = read(mini_path)
    for i, row in enumerate(mini):
        if row['problem_id'] in by_id:
            mini[i] = relocate(deepcopy(by_id[row['problem_id']]))
    stage(mini_path, mini)
    # Stage relocated JSONs before committing; copy input bytes separately.
    for path, value in list(writes.items()):
        if path.is_relative_to(ROOT / 'data/raw/iiot'):
            stage(ROOT / 'data/mini_data' / path.relative_to(ROOT / 'data'), relocate(value))
    for row in mini:
        for asset in row['assets']:
            if '/tests/' not in asset['path']:
                continue
            dest = ROOT / asset['path']
            source = ROOT / asset['path'].replace('data/mini_data/', 'data/', 1)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(source, dest)
            assert sha(dest) == asset['sha256']
    # The publisher reference manifest itself is a declared JSON asset.
    for path, rows in [(canonical_path, updated), (mini_path, mini)]:
        for row in rows:
            if row['problem_id'] not in by_id:
                continue
            for asset in row['assets']:
                file = ROOT / asset['path']
                if file in writes:
                    if path == mini_path:
                        asset['source_sha256'] = next(a['sha256'] for a in by_id[row['problem_id']]['assets']
                            if a['path'] == asset['path'].replace('data/mini_data/', 'data/', 1))
                    asset['sha256'] = hashlib.sha256((json.dumps(writes[file], ensure_ascii=False, indent=2) + '\n').encode()).hexdigest()
            row.setdefault('provenance', {})['files'] = [{k: a[k] for k in ('path', 'role', 'sha256', 'source_sha256') if k in a} for a in row['assets']]
        stage(path, rows)
    for layout in ['base', 'last_exam']:
        path = ROOT / 'data' / layout / 'task_cards.json'
        cards = read(path)
        for card in cards['tasks']:
            pid = card['task_id'].split('/')[-1]
            if card['task_id'].startswith('iiot/') and pid in by_id and 'evaluation' in card:
                card['evaluation'] = deepcopy(by_id[pid]['evaluation'])
        stage(path, cards)
    for pid, row in by_id.items():
        path = ROOT / 'data/last_exam/tasks/iiot' / pid / 'eval/reference.json'
        value = read(path)
        value['evaluation'] = deepcopy(row['evaluation'])
        stage(path, value)
    # Check all pre-existing files again immediately before writing.
    for path, before in observed.items():
        if (sha(path) if path.exists() else None) != before:
            raise ValueError(f'Concurrent edit detected: {path}')
    for path, value in writes.items():
        if path.exists():
            dest = backup / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for prefix, rows in [('data', updated), ('data/mini_data', mini)]:
        path = ROOT / prefix / 'rubrics/task_scorecards/iiot.json'
        cards = read(path)
        lookup = {r['problem_id']: r for r in rows}
        cards['records'] = [scorecard(lookup[c['problem_id']], ROOT) if c['problem_id'] in by_id else c for c in cards['records']]
        dest = backup / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'status': 'source_and_sample_validation_repaired_official_judge_still_pending',
        'tasks': 8, 'official_input_files': len(files), 'official_output_files': 0,
        'compiled_references': 8, 'printed_samples_checked': 16, 'backup': str(backup),
        'readiness_promotions': 0, 'paid_model_calls': 0}
    (CACHE / 'applied.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
