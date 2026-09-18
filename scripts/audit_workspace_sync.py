"""Read-only reconciliation of the current shared checkout, without Git or models."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    if isinstance(value, dict):
        result = {k: normalized(v) for k, v in value.items() if k != 'source_sha256'}
        if value.get('source_sha256') and 'sha256' in value:
            result['sha256'] = value['source_sha256']
        return result
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value.replace('data/mini_data/', 'data/') if isinstance(value, str) else value


def main():
    issues, intentional, fingerprints = [], [], {}
    sources = [p for tree in ['src', 'scripts', 'tests', 'collectors'] for p in (ROOT / tree).rglob('*.py')]
    for path in sources:
        fingerprints[path.relative_to(ROOT).as_posix()] = digest(path)
        try:
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            issues.append({'kind': 'python_syntax', 'path': str(path), 'reason': str(exc)})
    catalog = read(ROOT / 'data/benchmarks/index.json')
    mini_index = read(ROOT / 'data/mini_data/benchmarks/index.json')
    selection = read(ROOT / 'data/mini_data/selection_manifest.json')
    tracks = {t['competition_id']: t for t in selection['tracks']}
    expected, mini_expected, statuses = set(), set(), Counter()
    missing_assets, diffs = [], []
    if {e['id'] for e in catalog['olympiads']} != {e['id'] for e in mini_index['olympiads']}:
        issues.append({'kind': 'catalog_membership'})
    for entry in catalog['olympiads']:
        name = entry['id']
        rows = read(ROOT / entry['benchmark_path'])
        source = {r['problem_id']: r for r in rows}
        for row in rows:
            expected.add(name + '/' + row['problem_id'])
            statuses[row.get('evaluation', {}).get('status', 'missing')] += 1
            for asset in row.get('assets', []):
                if not (ROOT / asset['path']).is_file():
                    missing_assets.append({'problem_id': row['problem_id'], 'path': asset['path']})
        me = next(e for e in mini_index['olympiads'] if e['id'] == name)
        mr = read(ROOT / me['benchmark_path'])
        if len(mr) != me['problems_collected'] or [r['problem_id'] for r in mr] != tracks[name]['selected_record_ids']:
            issues.append({'kind': 'mini_selected_membership', 'competition': name})
        for row in mr:
            mini_expected.add(name + '/' + row['problem_id'])
            original = source.get(row['problem_id'])
            if original is None:
                issues.append({'kind': 'mini_retired_record', 'problem_id': row['problem_id']})
                continue
            fields = [k for k in set(original) | set(row) if normalized(original.get(k)) != normalized(row.get(k))]
            if fields:
                item = {'competition': name, 'problem_id': row['problem_id'], 'fields': sorted(fields)}
                allowed = (name in {'cybench', 'nyu_ctf_bench'} and set(fields) <= {'evaluation'}) or (
                    name == 'mystery_hunt' and row.get('source_review', {}).get('mini_static_repair')) or (
                    name == 'hmmt_team' and set(fields) <= {'assets', 'provenance'})
                (intentional if allowed else diffs).append(item)
        for path in (ROOT / 'data/rules' / name).glob('*.json'):
            mp = ROOT / 'data/mini_data/rules' / name / path.name
            a = normalized(read(path))
            b = normalized(read(mp)) if mp.is_file() else None
            if path.name == 'evaluation.json' and b is not None:
                ac, bc = a.get('scoring', {}), b.get('scoring', {})
                if ac.get('evaluation_status_counts') != bc.get('evaluation_status_counts'):
                    # Independent mini membership has its own counts; verify both
                    # before excluding this derived field from source comparison.
                    counts = lambda rs: dict(Counter(r['evaluation']['status'] for r in rs))
                    if ac.get('evaluation_status_counts') == counts(rows) and bc.get('evaluation_status_counts') == counts(mr):
                        ac.pop('evaluation_status_counts'); bc.pop('evaluation_status_counts')
            if b is None or a != b:
                issues.append({'kind': 'mini_rule_drift', 'competition': name, 'component': path.name})
    layouts = {}
    for layout in ['base', 'last_exam']:
        cards = read(ROOT / 'data' / layout / 'task_cards.json')['tasks']
        actual = {r['task_id'] for r in cards}
        layouts[layout] = {'tasks': len(cards), 'missing': sorted(expected - actual), 'extra': sorted(actual - expected)}
        if len(cards) != len(actual) or actual != expected:
            issues.append({'kind': 'derived_membership', 'layout': layout})
    issues.extend({'kind': 'missing_asset', **x} for x in missing_assets)
    issues.extend({'kind': 'unreconciled_mini_record', **x} for x in diffs)
    links = []
    for rel in ['README.md', 'docs/README.md', 'docs/from_zhongzheng/README.md', 'data/mini_data/README.md']:
        path = ROOT / rel
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0].strip('<>')
            if target and not (path.parent / target).exists():
                links.append({'document': rel, 'target': target})
    changed = [p for p, h in fingerprints.items() if digest(ROOT / p) != h]
    report = {'passed': not issues and not changed, 'python_sources_parsed': len(sources),
        'main': {'tracks': len(catalog['olympiads']), 'records': len(expected), 'statuses': dict(statuses)},
        'mini': {'tracks': len(tracks), 'records': len(mini_expected), 'sessions': sum(t['sessions'] for t in tracks.values()),
            'states': dict(Counter(t['verification'] for t in tracks.values()))},
        'derived_layouts': layouts, 'preserved_mini_specific_changes': intentional,
        'broken_entry_document_links': links, 'issues': issues, 'sources_changed_during_audit': changed,
        'paid_model_calls': 0, 'source_fingerprints': fingerprints}
    destination = ROOT / 'tmp/workspace_sync_audit_20260916.json'
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ['source_fingerprints', 'preserved_mini_specific_changes']}, ensure_ascii=True))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
