import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
from scripts import run_pipeline
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result
from contest_task_judge import judge_task
from rules.loader import load_rule_card


class ReadinessRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.registry=run_pipeline.register(Path(cls.temp.name))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_no_unready_job_registered_without_blocker(self):
        for job in self.registry['jobs']:
            try:run_pipeline.validate_job_readiness(job)
            except ValueError:
                self.assertTrue(job['blockers'],job['id'])


    def test_direct_live_native_entry_blocks_unready_packet(self):
        from run_competition_batch import inspect_contest_run
        from dataclasses import replace
        job=next(j for j in self.registry['jobs'] if j['competition']=='iiot')
        manifest=load_contest_manifest(job['manifest'], benchmark_root=ROOT/'data/benchmarks')
        task=manifest.tasks[0]
        unready=replace(task, benchmark={**task.benchmark,
            'evaluation': {**task.benchmark.get('evaluation', {}), 'status': 'not_ready'}})
        with patch('run_competition_batch.load_contest_manifest',
                   return_value=replace(manifest, tasks=(unready,))), \
             self.assertRaisesRegex(ValueError,'Record not ready'):
            inspect_contest_run(['--live','--contest-manifest',job['manifest'],
                                 '--provider','perplexity','--model','mock',
                                 '--output',str(Path(self.temp.name)/'must-not-exist')])
        self.assertFalse((Path(self.temp.name)/'must-not-exist').exists())


    def test_wsc_submission_reaches_judge(self):
        from test_conditional_task_judge import ConditionalJudgeTests
        job=next(j for j in self.registry['jobs'] if j['competition']=='wsc_writing')
        task=load_contest_manifest(job['manifest'],benchmark_root=ROOT/'data/benchmarks').tasks[0]
        fixture=ConditionalJudgeTests()
        result=judge_task(task,'Fixture essay responding to the question.',fixture.judge)
        self.assertTrue(result['graded']);self.assertEqual(result['max_score'],100)
        self.assertFalse(result['official_score_equivalent'])


if __name__=='__main__':unittest.main()
