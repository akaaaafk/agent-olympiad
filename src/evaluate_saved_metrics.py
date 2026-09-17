"""Backfill required metrics without changing historical solver/score files."""
import argparse
import csv
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from contest_reporting import report_row
from contest_run_identity import content_hash
from env_config import load_repo_dotenv
from llm import resolve_request_fn
from saved_run_metrics import ensure_coordination, write_metrics, write_json, valid_coordination, coordination_complete, task_context_judge

ROOT = Path(__file__).resolve().parents[1]


def verify_saved_task_result(directory, contest, result):
    """Reuse task scores only after the existing binding checks pass."""
    if result.get('graded') is not True:
        if result.get('status') == 'complete':
            raise ValueError('Completed artifact lacks a successful evaluation')
        return
    from artifacts.assets import file_sha256
    from otc_artifact_pipeline import _validate_completed_result
    expected_sha = contest['run_identity']['settings'].get('evaluation', {}).get('rubric_sha256')
    candidates = list((ROOT / 'data/rubrics').rglob('*.json')) + list(directory.glob('*rubric*.json'))
    rubric = next((p for p in candidates if expected_sha and file_sha256(p) == expected_sha), None)
    if rubric is None:
        raise ValueError('Cannot certify archived task score: original rubric bytes are unavailable')
    _validate_completed_result({'identity': contest['run_identity'], 'rubric': rubric},
                               result, directory, require_metrics=False)


def saved_task_text(directory, contest):
    for name in ('task_extracted.txt', 'coordination_task.txt'):
        path = directory / name
        if path.is_file():
            return path.read_text(encoding='utf-8')
    settings = contest['run_identity']['settings']
    execution = settings['execution']
    if execution.get('task_pdf_sha256'):
        from judge_references import benchmark_for_asset
        from artifacts.assets import file_sha256
        from llm import LLMRequest, LLMAttachment, pdf_text_request
        row = benchmark_for_asset(settings['competition_id'], execution['task_pdf_sha256'])
        assets = ((row or {}).get('assets') or (row or {}).get('provenance', {}).get('assets') or [])
        candidates = [ROOT / a['path'] for a in assets if a.get('role') == 'agent_visible'
                      and a.get('path', '').lower().endswith('.pdf')]
        for path in candidates:
            if path.is_file() and file_sha256(path) == execution['task_pdf_sha256']:
                start, end = execution['task_pages']
                text = pdf_text_request(LLMRequest('', '', attachments=(
                    LLMAttachment(path, 'application/pdf', page_start=start, page_end=end),))).user_prompt
                (directory / 'coordination_task.txt').write_text(text, encoding='utf-8')
                return text
    else:
        manifest_path = (contest.get('run') or {}).get('manifest')
        if manifest_path and Path(manifest_path).is_file():
            from contest_manifest import load_contest_manifest
            roots = [ROOT / 'data/benchmarks'] + [p / 'data/benchmarks' for p in ROOT.parent.glob('*runtime*')]
            for benchmark_root in roots:
                if not benchmark_root.is_dir():
                    continue
                try:
                    manifest = load_contest_manifest(Path(manifest_path), benchmark_root=benchmark_root)
                    if content_hash(asdict(manifest)) == settings['manifest_hash']:
                        text = '\n\n'.join(t.prompt for t in manifest.tasks)
                        (directory / 'coordination_task.txt').write_text(text, encoding='utf-8')
                        return text
                except (ValueError, KeyError, OSError):
                    continue
    raise ValueError('Cannot recover identity-compatible task text; preserve the run and supply --task-text-file for one run')


def process_run(directory, *, judge_provider=None, judge_model=None, report_only=False, task_text_file=None):
    directory = Path(directory)
    session_path = directory / 'contest_session.json'
    session_bytes = session_path.read_bytes()
    contest = json.loads(session_bytes)
    if (contest.get('session_checkpoint') or {}).get('final_summary') is None:
        raise ValueError('Contestants are not finalized; finish the solver run first')
    result_path = directory / 'result.json'
    result_bytes = result_path.read_bytes() if result_path.is_file() else None
    if result_bytes is None and (contest.get('run_identity') or {}).get('settings', {}).get('execution', {}).get('pipeline'):
        raise ValueError('Artifact task scoring is not finalized; finish its original rubric evaluation first')
    result = json.loads(result_bytes) if result_bytes is not None else contest
    if result_bytes is not None and result.get('run_identity') != contest.get('run_identity'):
        raise ValueError('Artifact result and contestant session identities differ')
    if result_bytes is not None:
        verify_saved_task_result(directory, contest, result)
    sidecar_path = directory / 'coordination_required.json'
    sidecar = json.loads(sidecar_path.read_text(encoding='utf-8')) if sidecar_path.exists() else None
    original_judge = contest['run_identity']['settings'].get('evaluation') or {}
    execution = contest['run_identity']['settings'].get('execution') or {}
    from env_config import resolve_run_provider
    provider = resolve_run_provider(execution.get('provider') or original_judge.get('provider'), judge_provider)
    model = judge_model or (original_judge.get('model') if original_judge.get('provider') == provider
                            else execution.get('model'))
    # Existing certified native evaluations already satisfy the requirement.
    native_complete = (result_bytes is None and valid_coordination(contest.get('coordination'))
                       and not contest.get('evaluation_pending')
                       and (contest.get('evaluation_stages') or {}).get('coordination', {}).get('status') != 'failed'
                       and provider == original_judge.get('provider') and model == original_judge.get('model'))
    if native_complete:
        sidecar = None
    elif report_only:
        if not coordination_complete(directory, result):
            sidecar = {'status': 'pending', 'error': 'Required collaboration evaluation missing or stale'}
    else:
        if not provider or not model:
            raise ValueError('Saved run has no judge configuration; specify judge provider and model')
        variant = contest.get('system_variant') or contest['run_identity']['settings']['config']['system_variant']
        text = '' if variant == 'single_agent' else (Path(task_text_file).read_text(encoding='utf-8')
                    if task_text_file else saved_task_text(directory, contest))
        resolved = None
        def judge_request(request):
            nonlocal resolved
            if resolved is None:
                resolved = resolve_request_fn(provider=provider, model=model, max_output_tokens=8192)
            return resolved(request)
        sidecar = ensure_coordination(directory, result=result, task_text=text,
            judge_request=(judge_request if variant == 'single_agent' else
                           task_context_judge(directory, contest, judge_request, provider)),
            judge_provider=provider, judge_model=model)
    row = write_metrics(directory, contest, result if result_bytes is not None else None, sidecar)
    assert session_path.read_bytes() == session_bytes, 'Historical contestant session was modified'
    if result_bytes is not None:
        assert result_path.read_bytes() == result_bytes, 'Historical task score result was modified'
    task_complete = row['score'] != 'N/A' and row['max_score'] != 'N/A'
    if result_bytes is not None:
        task_complete = task_complete and result.get('graded') is True
    else:
        task_complete = task_complete and (contest.get('grade') or {}).get('graded') is True
    collab_complete = native_complete or sidecar and sidecar.get('status') in {'complete', 'not_applicable'}
    return dict(directory=str(directory), status='complete' if task_complete and collab_complete
                else 'evaluation_pending', **row)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='One run directory or a batch root')
    parser.add_argument('--judge-provider')
    parser.add_argument('--judge-model')
    parser.add_argument('--report-only', action='store_true')
    parser.add_argument('--task-text-file', type=Path, help='Exact archived task text, for one run only')
    args = parser.parse_args(argv)
    load_repo_dotenv(ROOT / '.env')
    output = args.output.resolve()
    if not output.is_dir():
        parser.error('Output directory does not exist')
    sessions = ([output / 'contest_session.json'] if (output / 'contest_session.json').is_file()
                else sorted(output.rglob('contest_session.json')))
    if not sessions:
        parser.error('No saved contestant sessions found')
    if args.task_text_file and len(sessions) != 1:
        parser.error('--task-text-file is for one run directory only')
    rows = []
    for session_path in sessions:
        try:
            row = process_run(session_path.parent, judge_provider=args.judge_provider,
                judge_model=args.judge_model, report_only=args.report_only, task_text_file=args.task_text_file)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            row = dict(directory=str(session_path.parent), status='evaluation_pending', reason=str(exc), **report_row({}))
        rows.append(row)
        print(row['status'], row['directory'], flush=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    target = output / 'required_metrics_summary.csv'
    with target.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    write_json(output / 'required_metrics_status.json', dict(total=len(rows),
        complete=sum(r['status'] == 'complete' for r in rows), rows=rows))
    return 0 if all(r['status'] == 'complete' for r in rows) else 2


if __name__ == '__main__':
    raise SystemExit(main())
