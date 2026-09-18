"""Bounded live adapter validation against a reconstructed new-smoke failure.

Calls the real model, validates returned actions, but executes no contestant
tools and performs no judging. Outputs have their own fresh identity.
"""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from action_transport import request_single_action
from env_config import load_repo_dotenv
from llm import LLMRequest, make_tinker_request_fn
from tinker_action import VERSION, draft_scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'source_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').rglob('*.py')}, indent=2), encoding='utf8')
    load_repo_dotenv()
    source = ROOT / 'results/new_truncation_diagnosis_20260917'
    data = json.loads((source / 'request.json').read_text(encoding='utf8'))
    data['tools'], data['attachments'] = tuple(data['tools']), ()
    req = LLMRequest(**data)
    req = replace(req, metadata={**req.metadata, 'max_transport_attempts': 4,
                                'max_transport_output_tokens': 16384})
    caller = make_tinker_request_fn('Qwen/Qwen3.6-35B-A3B', max_output_tokens=4096)
    rows = []
    for mode in ('fresh_request', 'recover_recorded_draft'):
        current = req
        if mode == 'recover_recorded_draft':
            draft = (source / 'sample_1.txt').read_text(encoding='utf8')
            current = replace(req, metadata={**req.metadata, 'unexecuted_action_draft': {
                'scope': draft_scope(req), 'text': draft, 'executed': False}})
        response = request_single_action(caller, current)
        payload = {'case': mode, 'request': asdict(current), 'response': asdict(response),
                   'tools_executed': False, 'judged': False, 'version': VERSION}
        (args.output / f'{mode}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
        summary = {'case': mode, 'valid_calls': len(response.tool_calls),
                   'actions': [c.name for c in response.tool_calls],
                   'api_calls': response.usage['api_calls'], 'output_tokens': response.usage['output_tokens'],
                   'samples': [{k: x.get(k) for k in ('stage', 'output_tokens', 'max_output_tokens', 'finish_reason', 'error')}
                               for x in response.usage.get('sampling_trace', [])]}
        rows.append(summary)
        print(json.dumps(summary), flush=True)
    (args.output / 'summary.json').write_text(json.dumps(rows, indent=2), encoding='utf8')
    if not all(row['valid_calls'] == 1 for row in rows):
        raise SystemExit('One or more adapter validations failed; inspect saved raw samples.')


if __name__ == '__main__':
    main()
