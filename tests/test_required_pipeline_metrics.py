import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('required_pipeline',ROOT/'scripts/run_pipeline.py')
pipeline=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class RequiredPipelineTests(unittest.TestCase):
    def test_both_baselines_reach_native_and_artifact_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            registry=pipeline.register(out)
            for variant in ('decentralized','centralized'):
                args=SimpleNamespace(provider='tinker',model='mock',judge_provider=None,
                                     judge_model=None,system_variant=variant)
                for route in ('native','document'):
                    job=next(j for j in registry['jobs'] if j['route']==route and not j['blockers'])
                    with patch('run_competition_batch.inspect_contest_run',return_value=('new',{'settings':{'evaluation':{'task_judges':{}}}})), \
                         patch('contest_adapters.grade_contest_result',return_value={'tasks':{}}), \
                         patch('otc_artifact_pipeline.prepare_artifact_run',return_value={'identity':{}}) as prepare:
                        cmd=pipeline.command(job,out,args,expected_identities={})
                        self.assertEqual(cmd[cmd.index('--system-variant')+1],variant)
                        self.assertEqual(cmd[cmd.index('--provider')+1], 'tinker')
                        self.assertEqual(cmd[cmd.index('--judge-provider')+1], 'tinker')
                        if route=='native':self.assertIn('--judge-collab',cmd)
                        else:
                            self.assertEqual(prepare.call_args.kwargs['system_variant'],variant)
                            self.assertEqual(prepare.call_args.kwargs['judge_provider'], 'tinker')

    def test_summary_exports_required_native_fields_and_pending_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            job=dict(id='case',competition='arml_local',session='test',route='native',blockers=[])
            identity={'settings':{'evaluation':{'judge_collab':True}}}
            result=dict(system_variant='centralized',run_identity=identity,grade={'score':8,'max_score':10},
                        metrics={'communication_score':4,'planning_score':3,'coordination_score':3.5},
                        coordination={'communication_score':4,'planning_score':3,'coordination_score':3.5},
                        budget={'turns_used':3,'api_calls_used':8,'tokens_used':120,'wall_seconds_used':12})
            path=out/'runs/case/contest_session.json';path.parent.mkdir(parents=True)
            path.write_text(json.dumps(result),encoding='utf-8')
            with patch('contest_run_identity.read_completed_contest_result',return_value=result):
                pipeline.report(out,{'jobs':[job]},{'case':{'status':'complete','run_identity':identity}})
            with (out/'summary.tsv').open(encoding='utf-8',newline='') as f:row=next(csv.DictReader(f,delimiter='\t'))
            self.assertEqual([row[k] for k in ('accuracy','Communication','Planning','CS','turns','api_calls','tokens','sec')],
                             ['0.8','4','3','3.5','3','8','120','12'])
            result['metrics']={}
            result['coordination']=None
            result['evaluation_pending']=True
            result['evaluation_stages']={'coordination':{'status':'failed','error':'fixture failure'}}
            with patch('contest_run_identity.read_finalized_contest_result',return_value=result):
                pipeline.report(out,{'jobs':[job]},{'case':{'status':'evaluation_pending','run_identity':identity}})
            with (out/'summary.tsv').open(encoding='utf-8',newline='') as f:row=next(csv.DictReader(f,delimiter='\t'))
            self.assertEqual(row['CS'],'N/A')
            self.assertEqual(row['api_calls'],'8')
            self.assertEqual(row['status'],'evaluation_pending')


if __name__=='__main__':unittest.main()
