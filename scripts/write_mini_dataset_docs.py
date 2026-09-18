"""Generate the current mini selection; keep commands in one portable runbook."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/mini_data'
DOCS = ROOT / 'docs/from_zhongzheng'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    tracks = read(DATA / 'selection_manifest.json')['tracks']
    count = sum(t['selected_records'] for t in tracks)
    sessions = sum(t['sessions'] for t in tracks)
    intro = (f'The independent mini catalog contains {len(tracks)} tracks, {count} records, '
             f'and {sessions} execution sessions.\n\n'
             'Readiness is per record. A session can be a complete packet rather than one subquestion. '
             'Scoring may use an exact answer, remote verdict, rubric, or static source review; '
             'these are not interchangeable official contest scores.\n\n')
    states = {'offline_execution_preflight_passed': 'offline preflight passed',
              'declared_assets_verified_environment_pending': 'environment pending',
              'declared_assets_verified_evaluator_pending': 'evaluator pending'}
    table = '| Track | Year | Records | Sessions | Saved selection status |\n|---|---|---:|---:|---|\n'
    for track in tracks:
        years = ', '.join('Undated' if y is None else str(y) for y in track['selected_years'])
        table += (f"| {track['competition_id']} | {years} | {track['selected_records']} | "
                  f"{track['sessions']} | {states.get(track['verification'], track['verification'])} |\n")
    verification = DATA / 'verification.json'
    note = 'No saved offline preflight is available.'
    if verification.exists():
        report = read(verification)
        counts = {state: sum(j['state'] == state for j in report['jobs'])
                  for state in ('prepared', 'environment_pending', 'evaluator_pending', 'failed')}
        note = ('Saved offline preflight: ' + ', '.join(f'{k}={v}' for k, v in counts.items()) +
                f"; {report['asset_checks']} asset checks. This describes the saved environment, not live-model quality.")
    commands = ('Current commands for installation, all five baselines, filters, and resume: '
                '[English PowerShell guide](mini_pipeline_powershell.md).\n\n')
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / 'mini_dataset_commands_20260916.md').write_text(
        '# Current mini selection and commands\n\n' + commands + intro + table + '\n' + note + '\n', encoding='utf-8')
    (DOCS / 'mini_dataset_remaining_20260916.md').write_text(
        '# Current mini readiness\n\n' + commands + intro + table + '\n' + note +
        '\n\nCTF uses the current hash-bound runtime evidence described in [CTF delivery](../ctf.md). '
        'Per-record limitations remain authoritative.\n', encoding='utf-8')
    (DATA / 'README.md').write_text('# Independent Agent Olympiad mini dataset\n\n' + intro +
        'Entry point: `scripts/run_mini_dataset.py`. '
        '[Current English commands](../../docs/from_zhongzheng/mini_pipeline_powershell.md).\n\n' +
        note + '\n\n' + table + '\n' +
        'Run `python scripts/verify_mini_dataset.py` from the repository root to refresh preparation checks. '
        'Read both `passed` and `all_jobs_environment_ready`; missing external services are separate from data integrity.\n\n'
        '`selection_manifest.json` records membership, `dependency_manifest.json` binds local files, and '
        '`verification.json` records offline preparation. CTF runtime evidence is local under `validation/ctf/`; '
        'its hashes are bound by each record. See [current CTF delivery](../../docs/ctf.md).\n\n'
        'Rebuilding creates a new data snapshot and requires source-specific repairs and fresh verification. '
        'Do not resume an old run after replacing its data or code. '
        '`scripts/refresh_ctf_metadata.py --audit-dir results/YOUR_FRESH_AUDIT` refreshes the existing CTF selection '
        'from current verified main-catalog metadata; it does not select another year or run model experiments.\n', encoding='utf-8')


if __name__ == '__main__':
    main()
