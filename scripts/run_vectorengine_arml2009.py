"""One fresh single-agent ARML 2009 run with an isolated VectorEngine key."""
import json
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    args = parser.parse_args()
    values = {}
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name, value = line.split('=', 1)
            values[name.strip()] = value.strip().strip('"').strip("'")
    for name in ('VECTORENGINE_API_KEY', 'VECTORENGINE_BASE_URL', 'VECTORENGINE_MODEL'):
        if not values.get(name):
            raise ValueError('Missing saved ' + name)
        os.environ[name] = values[name]
    from env_config import provider_config
    from llm import resolve_request_fn, LLMRequest
    from run_competition_batch import inspect_contest_run
    profile = provider_config('vectorengine')
    model = args.model
    slug = re.sub(r'[^A-Za-z0-9._-]', '_', model)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'results' / f'vectorengine_arml2009_single_agent_{stamp}_{slug}'
    cmd = [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'),
           '--live', '--provider', 'vectorengine', '--model', model,
           '--contest-manifest', str(ROOT / 'data/contest_manifests/arml_local_2009.json'),
           '--system-variant', 'single_agent', '--action-calling', 'native',
           '--max-output-tokens', '8192', '--max-total-tokens', '220000',
           '--temperature', '0.2', '--judge-collab', '--judge-provider', 'vectorengine',
           '--judge-model', model, '--no-judge-cce', '--output', str(out)]
    state, _ = inspect_contest_run(cmd[3:])
    if state != 'new':
        raise ValueError('Fresh output required')
    out.mkdir()
    print(f'output={out}', flush=True)
    try:
        result = resolve_request_fn('vectorengine', model, max_output_tokens=64)(
            LLMRequest('API connectivity test.', 'Reply only OK.'))
        (out / f'preflight_{slug}.json').write_text(json.dumps(dict(text=result.text, usage=result.usage), indent=2), encoding='utf-8')
        if not result.text.strip() or result.usage.get('tool_error'):
            raise ValueError('Preflight returned no usable completion')
        print('Authenticated preflight succeeded; starting single_agent.', flush=True)
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONIOENCODING='utf-8')
        with (out / f'terminal_{slug}.log').open('w', encoding='utf-8') as log:
            proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                line = line.replace(values['VECTORENGINE_API_KEY'], '[REDACTED]')
                log.write(line)
                log.flush()
                print(line, end='', flush=True)
            code = proc.wait()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'.replace(values['VECTORENGINE_API_KEY'], '[REDACTED]')
        (out / f'error_{slug}.txt').write_text(error, encoding='utf-8')
        print(error, flush=True)
        code = 1
    (out / f'exit_{slug}.json').write_text(json.dumps({'exit_code': code}), encoding='utf-8')
    return code


if __name__ == '__main__':
    sys.exit(main())
