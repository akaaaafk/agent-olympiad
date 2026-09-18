"""Publish a verified local reconciliation snapshot without replacing agent fixes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from tool_registry import ACTION_SET_VERSION, ACTION_MODULE_VERSION, ACTION_REGISTRY
from action_modules import MODULE_SPECS


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    audit = read(ROOT / 'tmp/workspace_sync_audit_20260916.json')
    verification = read(ROOT / 'tmp/workspace_sync_mini_verification_20260916.json')
    smoke = read(ROOT / 'tmp/workspace_sync_smoke_20260916_2129/summary.json')
    raw_tests = (ROOT / 'tmp/workspace_sync_tests_20260916.log').read_bytes()
    tests = raw_tests.decode('utf-16' if raw_tests.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig', errors='replace')
    match = re.search(r'Ran (\d+) tests', tests)
    if not audit['passed'] or not verification['passed'] or smoke['counts'].get('FAIL') or not match or not re.search(r'^OK\s*$', tests, re.M):
        raise ValueError('Cannot publish successful reconciliation before required checks pass')
    stamp = datetime.now(timezone.utc).isoformat()
    selection_path = ROOT / 'data/mini_data/selection_manifest.json'
    selection = read(selection_path)
    selection['latest_workspace_sync'] = {'timestamp_utc': stamp,
        'canonical_index_sha256': hashlib.sha256((ROOT / 'data/benchmarks/index.json').read_bytes()).hexdigest(),
        'action_set_version': ACTION_SET_VERSION, 'membership_preserved': True,
        'preserved_overrides': ['mini CTF readiness', 'Pattern Recognition static packet', 'relocated JSON hash bindings']}
    write(selection_path, selection)
    write(ROOT / 'data/mini_data/verification.json', verification)
    from write_mini_dataset_docs import main as write_docs
    write_docs()
    counts = dict(Counter(j['state'] for j in verification['jobs']))
    modules = {k: len(v) for k, v in MODULE_SPECS.items()}
    summary = {'timestamp_utc': stamp, 'main': audit['main'], 'mini': audit['mini'],
        'action_set_version': ACTION_SET_VERSION, 'action_module_version': ACTION_MODULE_VERSION,
        'actions': len(ACTION_REGISTRY), 'action_modules': modules,
        'focused_tests': {'passed': int(match.group(1)), 'failed': 0},
        'route_smoke': smoke['counts'], 'mini_preflight': counts,
        'mini_asset_checks': verification['asset_checks'], 'paid_model_calls': 0,
        'preserved_mini_specific_changes': audit['preserved_mini_specific_changes']}
    write(ROOT / 'tmp/workspace_sync_summary_20260916.json', summary)
    text = '# Local workspace reconciliation (2026-09-16)\n\n'
    text += f'Checked at {stamp} UTC against current files in E:/agent_olympiad/agent-olympiad. No Git merge or checkout switch, paid model experiment, or historical result modification was performed. Recheck after other agents edit the workspace; this report is a snapshot of this verification.\n\n'
    text += '## Reconciled state\n\n'
    text += f"- Main data: {audit['main']['tracks']} tracks and {audit['main']['records']} records; base and last_exam contain exactly the same 1,050 task IDs.\n"
    text += f"- Mini: {audit['mini']['tracks']} tracks, {audit['mini']['records']} records and {audit['mini']['sessions']} sessions; states: {audit['mini']['states']}. WSC retains the complete three-task synthetic packet.\n"
    text += f'- Action registry: action set {ACTION_SET_VERSION}, module version {ACTION_MODULE_VERSION}, {len(ACTION_REGISTRY)} actions, module counts {modules}. Baseline permissions and memory boundaries are preserved.\n'
    text += '- Selected main and mini records and rules agree. Preserved mini overrides include Docker-verified CTF readiness, the independent Pattern Recognition static repair, and relocated JSON hash bindings. These repairs were not resampled or overwritten with older main data.\n\n'
    text += '## Integration fixes\n\n'
    text += '- Auxiliary-evaluation resume tests follow the unified provider policy and still require retries to call only the failed judge, never the contestant.\n'
    text += '- Catalog tests check tracks in the active index instead of treating retained historical directories as the current evaluation set.\n'
    text += '- Current documentation points to action set 13 and 89 actions. Older catalog, paid-run and action tables remain dated snapshots to preserve historical statistics.\n'
    text += '- Mini documentation reads verification.json instead of stale hardcoded counts, and explains that rebuilding requires reapplying repairs and validating CTF again.\n\n'
    text += '## Validation and limitations\n\n'
    text += f"- {audit['python_sources_parsed']} Python files passed AST parsing; current entry documents have no broken local links.\n"
    text += f"- {match.group(1)} tests across 19 relevant modules passed; this does not claim every historical repository test passed. Log: tmp/workspace_sync_tests_20260916.log.\n"
    text += f"- Five-baseline route smoke: {smoke['counts']}. Inputs, rendering, score parsing and resume are real; agents, judges and external programming judges are mocked. This is not a model-quality result. Evidence: tmp/workspace_sync_smoke_20260916_2129/summary.json.\n"
    text += f"- Independent dataset preflight: {counts}; {verification['asset_checks']} asset path/hash checks, no errors or parent-data reads. Evidence: data/mini_data/verification.json.\n"
    pending = [j for j in verification['jobs'] if j['state'] == 'environment_pending']
    for reason in sorted({j['reason'] for j in pending}):
        text += '- Environment limitation: ' + reason + '. Other agents runners were not interrupted.\n'
    text += '\nOffline structural, workflow and mock checks do not replace real model evaluation or missing evaluator integration. Historical paid outputs are preserved.\n\n'
    text += '## Entry points\n\n- [Mini run commands](mini_dataset_commands_20260916.md)\n- [Full competition entry point](run_baseline_competition_year.md)\n- [Pending mini evaluators](mini_dataset_remaining_20260916.md)\n'
    (ROOT / 'docs/from_zhongzheng/workspace_sync_20260916.md').write_text(text, encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'preserved_mini_specific_changes'}))


if __name__ == '__main__':
    main()
