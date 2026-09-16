"""Run the three Qwen-comparable ARML baselines using repo-local OPENAI_* values."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ('single_agent', 'vallina_otc', 'otc')


def openai_environment(path):
    values = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name, value = line.split('=', 1)
            values[name.strip()] = value.strip().strip('"').strip("'")
    names = ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL')
    missing = [name for name in names if not values.get(name)]
    if missing:
        raise ValueError('Missing from saved .env: ' + ', '.join(missing))
    if values['OPENAI_BASE_URL'].rstrip('/') != 'https://api.openai.com/v1':
        raise ValueError('OPENAI_BASE_URL must use the official OpenAI endpoint')
    env = dict(os.environ)
    env.update({name: values[name] for name in names})
    env['PYTHONPATH'] = str(ROOT / 'src')
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def command(model, variant, out):
    return [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'),
            '--live', '--provider', 'openai', '--model', model,
            '--contest-manifest', str(ROOT / 'data/contest_manifests/arml_local_2009.json'),
            '--system-variant', variant, '--action-calling', 'native',
            '--max-output-tokens', '8192', '--max-total-tokens', '220000',
            '--temperature', '0.2', '--judge-collab', '--judge-provider', 'openai',
            '--judge-model', model, '--no-judge-cce', '--output', str(out)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Validate saved configuration; no API calls')
    args = parser.parse_args()
    env = openai_environment(ROOT / '.env')
    model = env['OPENAI_MODEL']
    print(json.dumps(dict(provider='openai', model=model, base_url=env['OPENAI_BASE_URL'],
                          credential_variable='OPENAI_API_KEY', variants=VARIANTS)), flush=True)
    if args.check:
        return 0
    os.environ.update({k: env[k] for k in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL')})
    sys.path.insert(0, str(ROOT / 'src'))
    from llm import LLMRequest, resolve_request_fn
    from run_competition_batch import inspect_contest_run
    slug = re.sub(r'[^A-Za-z0-9._-]', '_', model)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'results' / f'openai_arml2009_{stamp}_{slug}'
    jobs = [(variant, out / f'{variant}_{slug}') for variant in VARIANTS]
    for variant, target in jobs:
        state, _ = inspect_contest_run(command(model, variant, target)[3:])
        if state != 'new':
            raise ValueError('Fresh output required')
    out.mkdir()
    print(f'output={out}', flush=True)
    preflight = resolve_request_fn('openai', model, max_output_tokens=64, temperature=0.2)(
        LLMRequest('You are checking API connectivity.', 'Reply only OK.'))
    (out / f'preflight_{slug}.json').write_text(json.dumps(dict(
        model=model, provider=preflight.provider, usage=preflight.usage,
        text=preflight.text), indent=2), encoding='utf-8')
    if not preflight.text.strip() or preflight.usage.get('tool_error'):
        raise ValueError('Preflight did not produce a usable response')
    print('Authenticated preflight succeeded.', flush=True)
    statuses = []
    for variant, target in jobs:
        print(f'START {variant}', flush=True)
        with (out / f'{variant}_{slug}.log').open('w', encoding='utf-8') as log:
            proc = subprocess.Popen(command(model, variant, target), cwd=ROOT, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                safe = line.replace(env['OPENAI_API_KEY'], '[REDACTED]')
                log.write(safe)
                log.flush()
                print(safe, end='', flush=True)
            code = proc.wait()
        statuses.append(dict(variant=variant, exit_code=code, output=str(target)))
        (out / f'status_{slug}.json').write_text(json.dumps(statuses, indent=2), encoding='utf-8')
        print(f'END {variant} exit_code={code}', flush=True)
        if code:
            return code
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        message = str(exc)
        for name in ('OPENAI_API_KEY', 'OPENAI_API_KEY_1'):
            if os.environ.get(name):
                message = message.replace(os.environ[name], '[REDACTED]')
        print(f'{type(exc).__name__}: {message}', file=sys.stderr)
        sys.exit(1)
