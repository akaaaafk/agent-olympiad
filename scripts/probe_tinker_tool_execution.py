"""Bounded live transport probe with real local work dispatch, NOT a benchmark.

The contestant action uses Tinker; auxiliary text is an explicit offline stub.
No judging, submission, shell execution, or old-run writes are performed.
"""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contest_config import ContestRunConfig
from contest_engine import _ContestEngine
from contest_manifest import ContestManifest, ManifestTask
from env_config import load_repo_dotenv
from llm import make_tinker_request_fn
from tinker_action import VERSION
from tinker_model_policy import model_policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-output-tokens', type=int, default=6144)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    load_repo_dotenv()
    identity = {'model': args.model, 'version': VERSION, 'policy': asdict(model_policy(args.model)),
                'max_output_tokens': args.max_output_tokens, 'max_api_calls': 5,
                'benchmark': False, 'auxiliary_text': 'offline_stub', 'judged': False,
                'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (ROOT / 'src').glob('*.py')}}
    (args.output / 'identity.json').write_text(json.dumps(identity, indent=2), encoding='utf8')
    native = make_tinker_request_fn(args.model, max_output_tokens=args.max_output_tokens)
    def action(req):
        req = replace(req, tools=tuple(t for t in req.tools if t['name'] == 'work'),
            system_prompt=req.system_prompt + '\nTransport integration probe: record the answer to 6*7 '
                'using work, in one short sentence. No other task or tool is available.',
            metadata={**req.metadata, 'max_transport_attempts': 4,
                      'max_transport_output_tokens': args.max_output_tokens * 4})
        (args.output / 'request.json').write_text(json.dumps(asdict(req), indent=2), encoding='utf8')
        result = native(req)
        (args.output / 'response.json').write_text(json.dumps(asdict(result), indent=2), encoding='utf8')
        return result
    manifest = ContestManifest(args.output.name, 'arml_local', (
        ManifestTask('probe', 'probe', None, 'What is 6*7? Record one short sentence.', 'math', 1, False, {}),))
    config = ContestRunConfig('single_agent', 1, 1, max_api_calls=5,
                              max_tokens=args.max_output_tokens * 4, deadline_submit=False)
    def checkpoint(session, memory):
        (args.output / 'checkpoint.json').write_text(json.dumps({'session': session, 'memory': memory}, indent=2), encoding='utf8')
    engine = _ContestEngine(manifest, lambda *_: 'Transport probe only.', config,
                            action_request_fn=action, action_transport='emulated', checkpoint_callback=checkpoint)
    result = engine.run()
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    executed = [row['name'] for row in engine.action_transport_log if row.get('executed')]
    summary = {'model': args.model, 'version': VERSION, 'executed_actions': executed,
               'work_versions': len(engine.session.tasks[0].versions),
               'api_calls': engine.transport_api_calls,
               'output_tokens': sum(row['output_tokens'] for row in engine.action_sampling_log),
               'samples': [{k: row.get(k) for k in ('stage', 'finish_reason', 'max_output_tokens', 'output_tokens', 'error')}
                           for row in engine.action_sampling_log], 'judged': False}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print(json.dumps(summary), flush=True)
    if executed != ['work'] or not engine.session.tasks[0].versions:
        raise SystemExit('Probe failed: no verified local work execution')


if __name__ == '__main__':
    main()
