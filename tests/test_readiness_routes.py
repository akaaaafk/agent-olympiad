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

    def test_stale_artifact_job_blocked_before_launch(self):
        job=next(j for j in self.registry['jobs'] if j['competition']=='gcch_harvard')
        stale={**job,'blockers':[]}
        with self.assertRaisesRegex(ValueError,'Record not ready'):
            run_pipeline.command(stale,Path(self.temp.name)/'runs',SimpleNamespace())

    def test_direct_live_native_entry_blocks_unready_packet(self):
        from run_competition_batch import inspect_contest_run
        job=next(j for j in self.registry['jobs'] if j['competition']=='iiot' and j['blockers'])
        with self.assertRaisesRegex(ValueError,'Record not ready'):
            inspect_contest_run(['--live','--contest-manifest',job['manifest'],
                                 '--provider','perplexity','--model','mock',
                                 '--output',str(Path(self.temp.name)/'must-not-exist')])
        self.assertFalse((Path(self.temp.name)/'must-not-exist').exists())

    def test_wsc_all_native_single_response(self):
        jobs=[j for j in self.registry['jobs'] if j['competition']=='wsc_writing']
        self.assertEqual(len(jobs),42)
        for j in jobs:
            self.assertEqual(j['route'],'native');self.assertFalse(j['blockers'])
            manifest=load_contest_manifest(j['manifest'],benchmark_root=ROOT/'data/benchmarks')
            self.assertEqual(len(manifest.tasks),1)
            self.assertNotIn('Clarity, Content, Style',manifest.tasks[0].prompt)
        card=load_rule_card('wsc_writing')
        self.assertNotIn('check_writing_prompt_allocation',card.allowed_tools)
        self.assertIn('one complete',card.answer_format)

    def test_wsc_submission_reaches_judge(self):
        from test_conditional_task_judge import ConditionalJudgeTests
        job=next(j for j in self.registry['jobs'] if j['competition']=='wsc_writing')
        task=load_contest_manifest(job['manifest'],benchmark_root=ROOT/'data/benchmarks').tasks[0]
        fixture=ConditionalJudgeTests()
        result=judge_task(task,'Fixture essay responding to the question.',fixture.judge)
        self.assertTrue(result['graded']);self.assertEqual(result['max_score'],100)
        self.assertFalse(result['official_score_equivalent'])

    def test_history_whole_packet_mapping_and_score(self):
        jobs=[j for j in self.registry['jobs'] if j['competition']=='history_olympiad']
        self.assertEqual(len(jobs),28)
        ready=[j for j in jobs if not j['blockers']]
        self.assertEqual(len(ready),28)
        for j in ready:
            manifest=load_contest_manifest(j['manifest'],benchmark_root=ROOT/'data/benchmarks')
            self.assertEqual(len(manifest.tasks),1)
            task=manifest.tasks[0];parts=task.benchmark['gold_label']['parts']
            self.assertNotIn('ANSWER:',task.prompt)
            answer='\n'.join(f"{p['id']}: {p['expected']}" for p in parts)
            perfect=grade_contest_result(manifest,{'submissions':{task.task_id:answer}})
            blank=grade_contest_result(manifest,{'submissions':{}})
            self.assertEqual(perfect['score'],perfect['max_score'],j['id'])
            self.assertEqual(blank['score'],0)
            self.assertFalse(any(a['role']=='agent_visible' and a['path'].endswith('.pdf') for a in task.benchmark['assets']))

    def test_history_known_leak_repaired(self):
        rows=json.loads((ROOT/'data/benchmarks/history_olympiad/benchmark.json').read_text(encoding='utf-8'))
        prompt=rows[0]['problem_description']
        self.assertNotIn('[Q3] Jamaica',prompt)
        self.assertNotIn('(accept Battle of the Ardennes',prompt)
        self.assertIsNone(rows[0]['gold_label']['expected_answer'])


if __name__=='__main__':unittest.main()
