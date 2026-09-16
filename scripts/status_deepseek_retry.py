"""Read-only concise status for the retry validation run."""
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'results/openagents_deepseek_v4_pro_arml2009_otc_8192_retry2_20260915'
rows = [json.loads(s) for s in (p/'response_metadata.jsonl').read_text().splitlines()]
finished = [x for x in rows if x['event']=='request_finished']
attempts = [json.loads(s) for s in (p/'gateway_attempts.jsonl').read_text().splitlines()]
print('finished',len(finished),'http_attempts',len(attempts),'504',sum(a.get('status')==504 for a in attempts),
      'request_errors',sum('error_type' in r for r in finished))
print('length',sum(r.get('usage',{}).get('finish_reason')=='length' for r in finished),
      'max_requested',max([r.get('usage',{}).get('max_output_tokens',0) for r in finished] or [0]))
if (p/'contest_checkpoint.json').exists():
    s=json.loads((p/'contest_checkpoint.json').read_text())['session']
    print('budget', {k:v for k,v in s['budget'].items() if k.endswith('_used')})
    print('round',s['engine_state'].get('round'))
    print('submitted',sum(t.get('terminal_verdict')=='SUBMITTED' for t in s['tasks']))
if (p/'launcher_exit.json').exists():
    print('exit',(p/'launcher_exit.json').read_text())
