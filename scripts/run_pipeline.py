"""Register every catalog track, run resumable OTC jobs, and export their results.

No unregistered fallback to the legacy per-problem runner. Unsupported routes and
missing inputs remain explicit blocked jobs in the denominator.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation_readiness import readiness_blockers
from competition_descriptions import competition_description
from dataset_paths import data_root
from pipeline_process import PipelineLock, run_child
DATA = data_root()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    # Windows readers/antivirus may briefly deny rename of an otherwise valid
    # destination. Preserve atomic replacement and retry only this transient
    # failure; never truncate the last durable status or rerun the child job.
    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.1)


def safe(value):
    return hashlib.sha256(str(value).encode()).hexdigest()[:16]


def validate_job_readiness(job):
    entries = read(DATA / 'benchmarks/index.json')['olympiads']
    entry = next((e for e in entries if e['id'] == job['competition']), None)
    if entry is None:
        raise ValueError('Competition absent from current catalog')
    rows = {r['problem_id']: r for r in read(ROOT / entry['benchmark_path'])}
    ids = job.get('problem_ids') or []
    if not ids or any(i not in rows for i in ids):
        raise ValueError('Missing or stale job problem IDs; re-register')
    blockers = readiness_blockers([rows[i] for i in ids])
    if blockers:
        raise ValueError('; '.join(blockers))


def artifact_task_pdf(row):
    """Resolve one contestant PDF; declared asset roles override legacy hints."""
    from evaluation.slides_pipeline import resolve_declared_task_bundle
    bundle = resolve_declared_task_bundle(row, ROOT)
    if bundle is not None:
        return bundle
    assets = row.get('assets')
    if assets is None:
        assets = row.get('provenance', {}).get('assets', [])
    forbidden = {
        (ROOT / asset['path']).resolve() for asset in assets
        if asset.get('role') == 'judge_only' and asset.get('path')
    }
    pdfs = list(dict.fromkeys(
        (ROOT / asset['path']).resolve() for asset in assets
        if asset.get('role') == 'agent_visible'
        and str(asset.get('path', '')).lower().endswith('.pdf')
    ))
    source = (ROOT / row['source_file']).resolve() if row.get('source_file') else None
    # Preserve legacy records without an asset inventory, but never use an
    # unclassified fallback to override an explicit inventory.
    if not assets and source is not None:
        pdfs = [source]
    if any(pdf in forbidden for pdf in pdfs) or (not pdfs and source in forbidden):
        raise ValueError('Task PDF is marked judge_only; contestant input refused')
    if len(pdfs) != 1 or not pdfs[0].is_file() or pdfs[0].suffix.lower() != '.pdf':
        raise ValueError('Requires one verified task PDF or explicit multi-file task mapping')
    return pdfs[0]


def validate_artifact_input(job):
    """Recheck old registries against current canonical input-role metadata."""
    ids = job.get('problem_ids', [])
    if len(ids) != 1:
        raise ValueError('Artifact job requires one benchmark record or an explicit multi-file mapping')
    entries = read(DATA / 'benchmarks/index.json')['olympiads']
    entry = next((item for item in entries if item['id'] == job['competition']), None)
    if entry is None:
        raise ValueError('Artifact competition is absent from the current catalog')
    rows = read(ROOT / entry['benchmark_path'])
    row = next((item for item in rows if item['problem_id'] == ids[0]), None)
    if row is None:
        raise ValueError('Artifact record is absent from the current benchmark')
    expected = artifact_task_pdf(row)
    if not job.get('task_pdf') or Path(job['task_pdf']).resolve() != expected:
        raise ValueError('Artifact task PDF changed or is not contestant-visible; re-register the job')
    return expected


def register(out):
    # Read card components without importing the runtime, so registration still
    # reports all tracks when the runtime itself has an import failure.
    from collections import OrderedDict
    index = read(DATA / 'benchmarks/index.json')['olympiads']
    tracks, jobs = [], []
    for entry in index:
        name = entry['id']
        card = {}
        blockers = []
        for component in ('competition', 'collaboration', 'evaluation'):
            path = DATA / 'rules' / name / (component + '.json')
            if path.is_file():
                card.update(read(path))
            else:
                blockers.append('Missing rule component: ' + str(path))
        official = card.get('deliverable', {}).get('official_deliverable')
        route = card.get('simulation', {}).get('deliverable_pipeline', {}).get('kind')
        if not route:
            route = ('slides' if official == 'slide_deck' else
                     'document' if official in {'proof_packet', 'lab_report', 'worked_answers',
                         'written_memorial', 'written_memorandum', 'written_essay', 'investment_report'} else
                     'native' if official in {'source_code', 'answer_sheet', 'puzzle_answer', 'flag', 'spoken_answer'} else
                     'external_environment')
        path = ROOT / entry['benchmark_path']
        rows = read(path) if path.is_file() else []
        if not rows:
            blockers.append('No benchmark records')
        groups = OrderedDict()
        for row in rows:
            # Preserve published packet boundaries for question-level datasets.
            key = row['problem_id']
            if name == 'icpc':
                key = 'icpc_wf_' + str(row.get('year', 'unknown'))
            elif name in {'science_bowl', 'wsc_writing'}:
                key = row.get('parent_session_id') or row.get('packet') or key
            elif name == 'qanta':
                key = f"qanta_{row.get('year', 'unknown')}_{row.get('tournament', 'unknown')}"
            elif name == 'mystery_hunt':
                key = 'mystery_hunt_' + str(row.get('year', key))
                # Unresolved puzzles must not disable reviewed runnable puzzles
                # from the same edition. Keep unresolved records visible/blocked.
                if readiness_blockers([row]):
                    key += '_not_ready'
            groups.setdefault(str(key), []).append(row)
        tracks.append(dict(competition=name, route=route, records=len(rows), sessions=len(groups), blockers=blockers))
        for key, members in groups.items():
            job_id = name + '_' + safe(key)
            job = dict(id=job_id, competition=name, session=key, route=route,
                       problem_ids=[r['problem_id'] for r in members], blockers=list(blockers))
            job['years'] = sorted({str(r['year']) for r in members if r.get('year') is not None})
            job['blockers'].extend(readiness_blockers(members))
            if route == 'native':
                if official == 'flag':
                    # Flags are only earned inside a reviewed Docker environment.
                    from ctf_environment_runtime import available
                    if name not in {'cybench', 'nyu_ctf_bench'} or not all(available(r) for r in members):
                        job['blockers'].append('Requires provisioned CTF environment; no generic text fallback')
                manifest = dict(session_id=key, competition_id=name, problem_ids=job['problem_ids'],
                                split_parts=name in {'arml_local', 'arml_national_team'},
                                competition_description=competition_description(name, entry.get('name')))
                if name == 'wsc_writing':
                    manifest['competition_flow'] = 'collaborative_writing_v1'
                manifest_path = out / 'manifests' / (job_id + '.json')
                if manifest_path.exists() and read(manifest_path) != manifest:
                    raise ValueError('Changed manifest; use a fresh output root: ' + job_id)
                write(manifest_path, manifest)
                job['manifest'] = str(manifest_path)
            elif route in {'document', 'slides'}:
                row = members[0]
                try:
                    job['task_pdf'] = str(artifact_task_pdf(row))
                except ValueError as exc:
                    job['blockers'].append(str(exc))
                rubric = row.get('evaluation', {}).get('rubric_path') or card.get('scoring', {}).get('rubric_path')
                if rubric and (ROOT / rubric).is_file():
                    job['rubric'] = str(ROOT / rubric)
                else:
                    job['blockers'].append('Missing configured rubric')
            else:
                job['blockers'].append('Specialized environment adapter not configured')
            jobs.append(job)
    registry = dict(tracks=tracks, jobs=jobs, track_count=len(tracks), session_count=len(jobs))
    write(out / 'registry.json', registry)
    print(json.dumps(dict(tracks=len(tracks), sessions=len(jobs),
                          blocked=sum(bool(j['blockers']) for j in jobs))), flush=True)
    return registry


def command(job, out, args, *, completed_results=None, expected_identities=None):
    from env_config import resolve_run_provider
    judge_provider = resolve_run_provider(args.provider, getattr(args, 'judge_provider', None))
    policy = read(DATA / 'evaluation_access_policy.json')
    if job['competition'] in policy.get('excluded_tracks', []):
        raise ValueError('Competition excluded from active evaluation: ' + job['competition'])
    validate_job_readiness(job)
    dest = out / 'runs' / job['id']
    variant = getattr(args, 'system_variant', 'otc')
    common = ['--system-variant', variant, '--provider', args.provider, '--model', args.model,
              '--output', str(dest)]
    common += ['--judge-provider', judge_provider]
    for name in ('max_turns', 'max_api_calls', 'max_total_tokens', 'max_output_tokens', 'temperature'):
        value = getattr(args, name, None)
        if value is not None:
            common += ['--' + name.replace('_', '-'), str(value)]
    if getattr(args, 'judge_model', None):
        common += ['--judge-model', args.judge_model]
    if job['route'] == 'native':
        from run_competition_batch import inspect_contest_run
        from contest_manifest import load_contest_manifest
        from contest_adapters import grade_contest_result
        cli = ['--live', '--benchmark-root', str(DATA / 'benchmarks'), '--contest-manifest', job['manifest'],
               '--no-judge-collab' if variant == 'single_agent' else '--judge-collab', *common]
        state, identity = inspect_contest_run(cli)
        if expected_identities is not None:
            expected_identities[job["id"]] = identity
        if state == 'complete':
            if completed_results is not None:
                from contest_run_identity import read_completed_contest_result
                completed_results[job['id']] = read_completed_contest_result(dest, identity)
            return None
        if state == 'resume' and (dest / 'contest_session.json').is_file():
            # Finalized contestants need only the missing auxiliary judges.
            # Do not require a working programming gateway or rerun submissions.
            from contest_run_identity import read_finalized_contest_result
            read_finalized_contest_result(dest, identity)
            cli.append('--resume')
            return [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'), *cli]
        manifest = load_contest_manifest(Path(job['manifest']), benchmark_root=DATA / 'benchmarks')
        if any(t.programming for t in manifest.tasks):
            if job['competition'] != 'icpc':
                raise ValueError('Programming adapter requires verified remote judge mapping before batch execution')
            if any(not t.benchmark.get('evaluation', {}).get('vjudge_prob_num') or
                   t.benchmark.get('evaluation', {}).get('status') != 'remote_judge_ready'
                   for t in manifest.tasks):
                raise ValueError('Incomplete remote judge mapping; full session retained, not silently filtered')
            if os.name == 'nt':
                probe = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' "
                    "-and $_.CommandLine -match 'run_competition_batch.py' }).Count"],
                    capture_output=True, text=True, check=True)
                if int(probe.stdout.strip() or '0'):
                    raise ValueError('Another contest runner is active; retry this job after it ends')
            subprocess.run(['docker', 'info'], check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, timeout=15)
            from judge.vjudge_gateway_client import gateway_base
            gateway = gateway_base()
            if not gateway:
                raise ValueError('VJUDGE_GATEWAY_URL is not set')
            with urllib.request.urlopen(gateway + '/v1/health', timeout=5) as response:
                if not json.load(response).get('ok'):
                    raise ValueError('VJudge gateway is not healthy')
        else:
            if job['competition'] in {'cybench', 'nyu_ctf_bench'}:
                subprocess.run(['docker', 'image', 'inspect', 'agent-olympiad-ctf:v1'], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
            quick = grade_contest_result(manifest, {'submissions': {}})
            registered = identity['settings']['evaluation'].get('task_judges', {})
            missing = [key for key, row in quick['tasks'].items()
                       if not row['graded'] and key not in registered]
            if missing:
                raise ValueError('No deterministic or registered LLM evaluator for: ' + ', '.join(missing))
        if state == 'resume':
            cli.append('--resume')
        return [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'), *cli]
    task_pdf = validate_artifact_input(job)
    if expected_identities is not None:
        from otc_artifact_pipeline import prepare_artifact_run
        prepared = prepare_artifact_run(competition=job['competition'], task_pdf=task_pdf,
            rubric=job['rubric'], output=dest, provider=args.provider, model=args.model,
            judge_provider=judge_provider,
            judge_model=getattr(args, 'judge_model', None), system_variant=variant,
            max_turns=getattr(args, 'max_turns', None),
            max_api_calls=getattr(args, 'max_api_calls', None),
            max_tokens=getattr(args, 'max_total_tokens', None),
            max_output_tokens=getattr(args, 'max_output_tokens', None),
            temperature=getattr(args, 'temperature', None) if getattr(args, 'temperature', None) is not None else 0.2)
        expected_identities[job['id']] = prepared['identity']
    cli = ['--competition', job['competition'], '--task-pdf', str(task_pdf),
           '--rubric', job['rubric'], *common]
    if (dest / 'run_identity.json').exists():
        cli.append('--resume')
    return [sys.executable, '-u', str(ROOT / 'src/run_otc_artifact.py'), *cli]


def native_completion_state(result):
    """Contestant completion and evaluation completeness are different states."""
    grade = result['grade']
    if grade.get('graded') is True:
        return dict(status='complete')
    reasons = [row.get('reason') for row in grade.get('tasks', {}).values()
               if not row.get('graded') and row.get('reason')]
    return dict(status='ungraded', reason='; '.join(dict.fromkeys(reasons))
                or 'Contest ended, but evaluation is incomplete')


def report(out, registry, states):
    rows = []
    for job in registry['jobs']:
        state = states.get(job['id'], {})
        row = dict(competition=job['competition'], session=job['session'], route=job['route'],
                   status=state.get('status', 'blocked' if job['blockers'] else 'pending'),
                   reason=state.get('reason', '; '.join(job['blockers'])), score='', max_score='',
                   graded_tasks='', coordination='', seconds='', accuracy='N/A',
                   Communication='N/A', Planning='N/A', CS='N/A', turns='N/A',
                   api_calls='N/A', tokens='N/A', sec='N/A', eval_api_calls='N/A',
                   eval_tokens='N/A', eval_sec='N/A', tokens_basis='', eval_tokens_basis='',
                   model='', variant='', missing_reasons='')
        path = out / 'runs' / job['id'] / ('contest_session.json' if job['route'] == 'native' else 'result.json')
        identity = state.get('run_identity')
        result = None
        if row['status'] in {'complete', 'ungraded'} and (not identity or not path.is_file()):
            row.update(status='blocked', reason='Completed state lacks expected identity or result')
        if path.exists() and identity and row['status'] in {'complete', 'ungraded', 'evaluation_pending', 'unsubmitted'}:
            try:
                if job['route'] == 'native':
                    from contest_run_identity import read_completed_contest_result, read_finalized_contest_result
                    result = (read_finalized_contest_result(path.parent, identity)
                              if row['status'] == 'evaluation_pending' else
                              read_completed_contest_result(path.parent, identity))
                    if row['status'] == 'evaluation_pending' and not result.get('evaluation_pending'):
                        # A separate evaluation-only repair may finish while this
                        # supervisor retains the old pending state in memory.
                        # Validate completion before promoting the cached label.
                        result = read_completed_contest_result(path.parent, identity)
                        completed_state = native_completion_state(result)
                        states[job['id']] = {**completed_state, 'run_identity': identity}
                        row.update(status=completed_state['status'],
                                   reason=completed_state.get('reason', ''))
                else:
                    from otc_artifact_pipeline import _validate_completed_result
                    snapshot = read(path)
                    if row['status'] == 'complete' or snapshot.get('graded') is True:
                        _validate_completed_result({'identity': identity, 'rubric': job['rubric']}, snapshot, path.parent,
                                                   require_metrics=row['status'] == 'complete')
                        result = snapshot
                    else:
                        from contest_run_identity import validate_run_identity
                        validate_run_identity(snapshot.get('run_identity'), identity, artifact=path)
                        result = snapshot
            except (ValueError, KeyError, OSError, TypeError) as exc:
                row.update(status='blocked', reason=f'Unverified result: {exc}')
        if row['status'] == 'blocked' and state.get('status') in {'complete', 'ungraded'}:
            states[job['id']] = {**state, 'status': row['status'], 'reason': row['reason']}
        if result is not None:
            from saved_run_metrics import flat_metrics
            contest = result
            sidecar = None
            if job['route'] != 'native':
                contest = read(path.parent / 'contest_session.json')
                sidecar_path = path.parent / 'coordination_required.json'
                sidecar = read(sidecar_path) if sidecar_path.exists() else None
            flat = flat_metrics(contest, result, sidecar)
            for field in ('accuracy', 'Communication', 'Planning', 'CS', 'turns', 'api_calls',
                          'tokens', 'sec', 'eval_api_calls', 'eval_tokens', 'eval_sec',
                          'tokens_basis', 'eval_tokens_basis', 'missing_reasons'):
                row[field] = flat[field]
            settings = (contest.get('run_identity') or {}).get('settings') or {}
            row['model'] = (settings.get('execution') or {}).get('model', '')
            row['variant'] = contest.get('system_variant') or (settings.get('config') or {}).get('system_variant', '')
            grade = result.get('grade') or result.get('evaluation') or {}
            row.update(score=flat['score'],
                       max_score=flat['max_score'], graded_tasks=grade.get('graded_tasks', ''),
                       coordination=flat['CS'], seconds=flat['sec'])
        rows.append(row)
    with (out / 'summary.tsv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ['status'], delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    write(out / 'batch_status.json', dict(counts=dict(Counter(r['status'] for r in rows)), jobs=states))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['register', 'run', 'report', 'all'])
    parser.add_argument('--output', type=Path, default=ROOT / 'results/otc_pipeline')
    parser.add_argument('--provider', default='perplexity')
    parser.add_argument('--judge-provider', help='Must match --provider; defaults to the same service')
    parser.add_argument('--judge-model')
    parser.add_argument('--max-turns', type=int, help='Override duration-derived turns (clamped to 10-90)')
    parser.add_argument('--max-api-calls', type=int)
    parser.add_argument('--max-total-tokens', type=int)
    parser.add_argument('--max-output-tokens', type=int)
    parser.add_argument('--temperature', type=float, default=0.2)
    parser.add_argument('--model', help='Required for run/all; no default model')
    from env_config import add_run_credentials
    add_run_credentials(parser)
    parser.add_argument('--system-variant', choices=['single_agent', 'decentralized',
        'centralized', 'vallina_otc', 'otc'], default='otc')
    parser.add_argument('--competitions', help='Optional comma-separated track filter; default all')
    parser.add_argument('--years', help='Comma-separated benchmark years, e.g. 2009 or 2009,2010')
    parser.add_argument('--sessions', help='Optional exact session IDs, e.g. arml_local_2009')
    parser.add_argument('--limit', type=int, help='Explicit pilot limit; default all sessions')
    parser.add_argument('--job-timeout-seconds', type=int, default=21600,
                        help='Wall-clock limit per child job (default: 6 hours); checkpoints survive timeout')
    args = parser.parse_args()
    from env_config import load_repo_dotenv, resolve_run_provider
    from run_competition_batch import _resolve_model
    load_repo_dotenv()
    try:
        args.judge_provider = resolve_run_provider(args.provider, args.judge_provider)
        args.provider = args.judge_provider
        from env_config import consume_run_credentials
        consume_run_credentials(args)
        if args.stage in {'run', 'all'}:
            args.model = _resolve_model(args.provider, args.model)
            from contest_budget import validate_positive_budget, validate_temperature
            validate_temperature(args.temperature)
            for name in ('max_api_calls', 'max_total_tokens', 'max_output_tokens'):
                validate_positive_budget(name, getattr(args, name))
    except ValueError as exc:
        parser.error(str(exc))
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    if args.job_timeout_seconds < 1:
        parser.error('--job-timeout-seconds must be positive')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Every stage writes: even report persists batch_status.json. Acquire
    # before reading shared state or registering, and hold through final report.
    lock = out / 'pipeline.lock'
    with PipelineLock(lock) as owner:
        args.pipeline_owner = owner
        return _run_locked(args, out)


def select_jobs(registry, args):
    def values(name):
        raw = getattr(args, name, None)
        parsed = {item.strip() for item in raw.split(',') if item.strip()} if raw else set()
        if raw is not None and not parsed:
            raise ValueError(f'Empty {name} filter')
        return parsed
    competitions, years, sessions = (values(name) for name in ('competitions', 'years', 'sessions'))
    candidates = [job for job in registry['jobs']
                  if (not competitions or job['competition'] in competitions)
                  and (not sessions or job['session'] in sessions)]
    if years and any('years' not in job for job in candidates):
        raise ValueError('Registry lacks year metadata; run register or all to refresh it')
    selected = [job for job in candidates if not years or years.intersection(job['years'])]
    if not selected and (competitions or years or sessions):
        raise ValueError('No sessions match the requested competition/year/session filters')
    return selected


def _run_locked(args, out):
    registry = register(out) if args.stage in {'register', 'all'} else read(out / 'registry.json')
    status_path = out / 'batch_status.json'
    states = read(status_path)['jobs'] if status_path.exists() else {}
    exit_code = 0
    if args.stage in {'run', 'all'}:
        selected = select_jobs(registry, args)
        # Start with native answer sheets; expensive artifact and remote
        # sessions follow in the same durable, serial queue.
        selected.sort(key=lambda j: (j['session'] != 'arml_local_2014', j['competition'] != 'arml_local',
                                    j['route'] != 'native', j['id']))
        if args.limit is not None:
            selected = selected[:args.limit]
        for job in selected:
            if job['blockers']:
                exit_code = 1
                continue
            try:
                completed_results = {}
                expected_identities = {}
                cmd = command(job, out, args, completed_results=completed_results,
                              expected_identities=expected_identities)
                if cmd is None:
                    states[job['id']] = native_completion_state(completed_results[job['id']])
                    states[job['id']]['run_identity'] = expected_identities[job['id']]
                    if states[job['id']]['status'] != 'complete':
                        exit_code = 1
                    report(out, registry, states)
                    print(job['id'], states[job['id']]['status'], flush=True)
                    continue
                states[job['id']] = dict(status='running', command=cmd)
                report(out, registry, states)
                logs = out / 'logs'
                logs.mkdir(exist_ok=True)
                with (logs / (job['id'] + '.log')).open('a', encoding='utf-8') as log:
                    completed = run_child(cmd, cwd=ROOT, log=log,
                                          timeout=args.job_timeout_seconds, owner=args.pipeline_owner)
                dest = out / 'runs' / job['id']
                if completed.returncode:
                    final_path = dest / ('contest_session.json' if job['route'] == 'native' else 'result.json')
                    if final_path.is_file() and read(final_path).get('evaluation_pending'):
                        states[job['id']] = dict(status='evaluation_pending',
                            reason='Required evaluations are pending; resume judges without rerunning contestants',
                            run_identity=expected_identities[job['id']])
                        exit_code = 1
                        report(out, registry, states)
                        continue
                    raise RuntimeError(f'Runner exit {completed.returncode}; see per-job log')
                if job['route'] == 'native':
                    if command(job, out, args, completed_results=completed_results) is not None:
                        raise RuntimeError('Runner exited without verified final result')
                    states[job['id']] = native_completion_state(completed_results[job['id']])
                else:
                    from otc_artifact_pipeline import _validate_completed_result
                    snapshot = read(dest / 'result.json')
                    if snapshot['status'] == 'complete':
                        _validate_completed_result({'identity': expected_identities[job['id']],
                                                    'rubric': job['rubric']}, snapshot, dest)
                    states[job['id']] = dict(status=snapshot['status'])
                states[job['id']]['run_identity'] = expected_identities[job['id']]
                if states[job['id']]['status'] != 'complete':
                    exit_code = 1
            except Exception as exc:
                exit_code = 1
                states[job['id']] = dict(status='blocked', reason=f'{type(exc).__name__}: {exc}')
            report(out, registry, states)
            print(job['id'], states[job['id']]['status'], flush=True)
    report(out, registry, states)
    if args.stage in {'run', 'all'} and any(
            states.get(job['id'], {}).get('status') != 'complete' for job in selected):
        exit_code = 1
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
