"""One real request, no retry; retain terminal traceback without credentials."""
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from env_config import openagents_config


def main():
    env = {}
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name, value = line.split('=', 1)
            env[name.strip()] = value.strip().strip('"').strip("'")
    profile = openagents_config()
    key = env.get('OPENAGENTS_API_KEY')
    if not key:
        raise SystemExit('Missing repository gateway credential')
    payload = json.loads((ROOT / 'results/deepseek_request_diagnosis_20260915/captured_payload.json').read_text(encoding='utf-8'))
    out = ROOT / 'results' / ('gateway_terminal_once_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir()
    start = time.monotonic()
    code = 0
    lines = [f"model={payload['model']} max_tokens={payload.get('max_tokens')} retries=0"]
    print(lines[0], flush=True)
    try:
        with OpenAI(api_key=key, base_url=profile['base_url'], timeout=150, max_retries=0) as client:
            response = client.chat.completions.create(**payload)
        lines.append('HTTP 200: request succeeded; gateway timeout NOT reproduced.')
        lines.append(f'finish_reason={response.choices[0].finish_reason}')
    except Exception:
        code = 1
        lines.append(traceback.format_exc().replace(key, '[REDACTED]'))
    lines.append(f'elapsed_seconds={time.monotonic() - start:.3f}')
    (out / 'terminal.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[1:]), flush=True)
    print(f'log={out / "terminal.txt"}', flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
