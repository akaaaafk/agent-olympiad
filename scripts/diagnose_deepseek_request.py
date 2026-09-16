"""Capture a checkpoint request offline, then run bounded gateway comparisons."""
import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/deepseek_request_diagnosis_20260915'
SOURCE = ROOT / 'results/openagents_deepseek_v4_pro_arml2009_otc_8192_bounded_20260915'

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def capture():
    import openai
    OUT.mkdir(exist_ok=True)
    replay = OUT / 'offline_replay'
    if replay.exists():
        raise SystemExit('Replay already exists; inspect existing capture')
    shutil.copytree(SOURCE, replay)
    class Captured(BaseException):
        pass
    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = self.completions = self
        def create(self, **kwargs):
            dump(OUT / 'captured_payload.json', kwargs)
            raise Captured()
    openai.OpenAI = FakeClient
    probe = ROOT / 'scripts/probe_openagents_deepseek_v4_pro.py'
    code = probe.read_text(encoding='utf-8')
    code = code.replace('OUT = ROOT / "results/openagents_deepseek_v4_pro_arml2009_otc_8192_bounded_20260915"', 'OUT = Path(' + repr(str(replay)) + ')')
    sys.argv = [str(probe), '--resume']
    try:
        exec(compile(code, str(probe), 'exec'), {'__file__': str(probe), '__name__': '__main__'})
    except Captured:
        payload = json.loads((OUT / 'captured_payload.json').read_text(encoding='utf-8'))
        print(json.dumps({'captured': True, 'messages_chars': sum(len(str(m)) for m in payload['messages']), 'tools': len(payload.get('tools', [])), 'thinking': payload.get('extra_body'), 'max_tokens': payload['max_tokens']}))

def probe(case):
    import httpx
    sys.path.insert(0, str(ROOT / 'src'))
    from env_config import openagents_config
    # Parse repository credentials explicitly; never log headers or credentials.
    env = {}
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('\"').strip("'")
    profile = openagents_config()
    key = env.get('OPENAGENTS_API_KEY')
    if not key:
        raise SystemExit('Missing repository gateway credential')
    path = OUT / (case + '.json')
    if path.exists():
        raise SystemExit('Case already recorded; refuse replay')
    payload = json.loads((OUT / 'captured_payload.json').read_text(encoding='utf-8'))
    payload.update(payload.pop('extra_body', {}))
    payload['max_tokens'] = 8192 if case == 'tools_off_8192' else 512
    payload['thinking'] = {'type': 'enabled' if case == 'tools_on' else 'disabled'}
    if case == 'text_off':
        for k in ('tools', 'tool_choice', 'parallel_tool_calls'):
            payload.pop(k, None)
    dump(OUT / (case + '_request.json'), payload)
    start = time.monotonic()
    result = {'case': case, 'request_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()}
    try:
        with httpx.Client(timeout=140) as client:
            response = client.post(profile['base_url'].rstrip('/') + '/chat/completions', headers={'Authorization': 'Bearer ' + key}, json=payload)
        result['status'] = response.status_code
        data = response.json()
        result['response'] = data
        choice = (data.get('choices') or [{}])[0]
        msg = choice.get('message') or {}
        result['summary'] = {'finish_reason': choice.get('finish_reason'), 'usage': data.get('usage'), 'content_chars': len(msg.get('content') or ''), 'reasoning_chars': len(msg.get('reasoning_content') or ''), 'inline_think': '<think>' in (msg.get('content') or ''), 'tools': [t.get('function', {}).get('name') for t in msg.get('tool_calls') or []]}
    except Exception as e:
        result['error_type'] = type(e).__name__
    result['seconds'] = round(time.monotonic() - start, 2)
    dump(path, result)
    print(json.dumps({k:v for k,v in result.items() if k != 'response'}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=['capture', 'tools_off', 'tools_on', 'text_off', 'tools_off_8192'])
    args = parser.parse_args()
    capture() if args.case == 'capture' else probe(args.case)
