"""Retry pending judges with more output capacity, preserving contestant identity."""
import argparse
import copy
import sys
from pathlib import Path

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--snapshot',type=Path,required=True)
options,argv=parser.parse_known_args()
sys.path.insert(0,str(options.snapshot/'src'))
import run_competition_batch as runner
from llm import resolve_request_fn
from contest_reporting import write_report

args=runner._build_parser().parse_args(argv)
manifest,config,_transport,identity=runner._prepare_contest_run(args)
out=args.output
result=runner.read_finalized_contest_result(out,identity)
immutable=copy.deepcopy((result.get('submissions'),result.get('memory')))
result['evaluation_retry_config']={
    'max_output_tokens':16384,
    'purpose':'Auxiliary judge retry only; original contestant budget/turns/identity preserved',
    'provider':args.judge_provider,'model':args.judge_model,
}
def persist():
    assert (result.get('submissions'),result.get('memory'))==immutable
    runner._write_json_atomic(out/'contest_session.json',result)
request=resolve_request_fn(provider=args.judge_provider,model=args.judge_model,max_output_tokens=16384)
pending=runner._run_contest_auxiliary_judges(result,manifest,config,identity,
    request_fn=request,cce_request_fn=request,persist=persist)
result['report']=write_report(out,result)
persist()
print('Evaluation remaining:',pending)
raise SystemExit(1 if pending else 0)
