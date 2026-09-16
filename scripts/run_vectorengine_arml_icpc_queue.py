"""Ordered ARML remaining-four then ICPC WF 2012 five-baseline queue."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'claude-sonnet-4-5-20250929'
VARIANTS = ('single_agent', 'decentralized', 'centralized', 'vallina_otc', 'otc')
PRIOR = ROOT / 'results/vectorengine_arml2009_single_agent_20260916T040217639324Z_claude-sonnet-4-5-20250929/contest_session.json'
sys.path.insert(0, str(ROOT / 'src'))


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def command(contest, variant, output):
    return [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'),
            '--live', '--provider', 'vectorengine', '--model', MODEL,
            '--contest-manifest', str(ROOT / f'data/contest_manifests/{contest}.json'),
            '--system-variant', variant, '--action-calling', 'native',
            '--max-output-tokens', '8192', '--max-total-tokens', '220000',
            '--temperature', '0.2', '--judge-collab', '--judge-provider', 'vectorengine',
            '--judge-model', MODEL, '--no-judge-cce', '--output', str(output)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    from dotenv import dotenv_values
    values = dotenv_values(ROOT / '.env')
    for name, value in values.items():
        if value is not None:
            os.environ[name] = value
    if not os.environ.get('VECTORENGINE_API_KEY'):
        raise ValueError('Missing VECTORENGINE_API_KEY')
    from run_competition_batch import inspect_contest_run
    registry_path = out / f'registry_{MODEL}.json'
    if args.prepare:
        if out.exists():
            raise ValueError('Refusing to overwrite existing queue')
        prior = json.loads(PRIOR.read_text(encoding='utf-8'))
        execution = prior['run_identity']['settings']['execution']
        if execution['provider'] != 'vectorengine' or execution['model'] != MODEL or not prior['grade']['graded']:
            raise ValueError('Prior single-agent result did not match')
        jobs = []
        for contest, variants in (('arml_local_2009', VARIANTS[1:]), ('icpc_wf_2012', VARIANTS)):
            for variant in variants:
                target = out / f'{contest}_{variant}_{MODEL}'
                state, identity = inspect_contest_run(command(contest, variant, target)[3:])
                if state != 'new':
                    raise ValueError('Fresh job required')
                jobs.append(dict(contest=contest, variant=variant, output=str(target), identity=identity, status='pending'))
        out.mkdir(parents=True)
        write(registry_path, dict(model=MODEL, prior_single_agent=str(PRIOR), jobs=jobs))
        print(f'Prepared {len(jobs)} ordered jobs in {out}', flush=True)
        return 0
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    lock = out / 'supervisor.lock'
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    current = None
    try:
        for job in registry['jobs']:
            current = job
            if job['status'] != 'pending':
                raise ValueError('Queue has prior execution state; inspect before resuming')
            target = Path(job['output'])
            state, identity = inspect_contest_run(command(job['contest'], job['variant'], target)[3:])
            if state != 'new' or identity != job['identity']:
                raise ValueError('Source/config drift or existing output; refusing mixed experiment')
            if job['contest'] == 'icpc_wf_2012':
                subprocess.run(['docker', 'info'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with urllib.request.urlopen('http://127.0.0.1:8787/v1/health', timeout=5) as response:
                    if not json.load(response).get('ok'):
                        raise ValueError('ICPC judge gateway is not healthy')
            job['status'] = 'running'
            write(registry_path, registry)
            print(f"START {job['contest']} {job['variant']}", flush=True)
            env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONIOENCODING='utf-8')
            with (out / (target.name + '.log')).open('w', encoding='utf-8') as log:
                process = subprocess.Popen(command(job['contest'], job['variant'], target), cwd=ROOT,
                    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    encoding='utf-8', errors='replace')
                job['pid'] = process.pid
                write(registry_path, registry)
                for line in process.stdout:
                    for name in ('VECTORENGINE_API_KEY', 'OPENAI_API_KEY', 'OPENAGENTS_API_KEY', 'VJUDGE_COOKIE'):
                        if env.get(name):
                            line = line.replace(env[name], '[REDACTED]')
                    log.write(line)
                    log.flush()
                    print(line, end='', flush=True)
                code = process.wait()
            job['exit_code'] = code
            state, _ = inspect_contest_run(command(job['contest'], job['variant'], target)[3:])
            if code or state != 'complete':
                raise RuntimeError(f'Job stopped: exit={code}, state={state}')
            result = json.loads((target / 'contest_session.json').read_text(encoding='utf-8'))
            job.update(status='complete', score=result['grade'].get('score'), max_score=result['grade'].get('max_score'))
            write(registry_path, registry)
            print(f"DONE {job['contest']} {job['variant']} score={job['score']}", flush=True)
    except Exception as exc:
        if current:
            current['status'] = 'blocked'
            current['error'] = str(exc).replace(os.environ['VECTORENGINE_API_KEY'], '[REDACTED]')
            write(registry_path, registry)
        print(f'Queue stopped: {type(exc).__name__}', flush=True)
        return 1
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
