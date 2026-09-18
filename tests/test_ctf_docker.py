import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ctf_environment_runtime import controller, available, execute
from contest_manifest import ContestManifest, ManifestTask
from action_modules.task_specific import resolve_contest_interface
from action_modules.ctf_environment import NAMES

class DockerContracts(unittest.TestCase):
    def test_static_workspace_exposes_only_reviewed_assets(self):
        _,row=controller.select('nyu_ctf_2013f-cry-stfu')
        stage,_,_=controller.prepare(row['problem_id'],'contract-test')
        import yaml
        config=yaml.safe_load((stage/'compose.yaml').read_text())
        self.assertEqual(config['services']['contestant']['network_mode'],'none')
        self.assertNotIn('volumes',config['services']['contestant'])
        self.assertEqual(sorted(p.name for p in (stage/'inputs').iterdir()),['flag.stfu','stfu'])

    def test_socket_mount_is_not_replayed(self):
        row={'problem_id':'nyu_ctf_2018f-pwn-es1337', 'source_review':{
            'environment_kind':'service',
            'upstream_source_directory':'data/raw/external/NYU_CTF_Bench/test/2018/CSAW-Finals/pwn/ES1337'}}
        self.assertFalse(available(row))
        with self.assertRaisesRegex(ValueError,'volume'):
            controller.normalized_services(row)

    def test_describeme_runs_original_program_without_socket(self):
        _,row=controller.select('nyu_ctf_2023f-cry-describeme')
        service=controller.normalized_services(row)['game-server']
        self.assertNotIn('volumes',service)
        self.assertTrue(service['build']['context'].endswith('DescribeMe'))
        self.assertIn(('game-server',21200),controller.endpoints(row))

    def test_describeme_exception_rejects_changed_mount(self):
        from unittest.mock import patch
        _,row=controller.select('nyu_ctf_2023f-cry-describeme')
        path,root,config=controller.source_compose(row)
        config['services']['game-server']['volumes'].append('/etc:/host')
        with patch.object(controller,'source_compose',return_value=(path,root,config)):
            with self.assertRaisesRegex(ValueError,'mapping changed'):
                controller.normalized_services(row)

    def test_interoperable_uses_reviewed_source_without_socket(self):
        _,row=controller.select('nyu_ctf_2021f-cry-interoperable')
        service=controller.normalized_services(row)['game-server']
        self.assertNotIn('volumes',service)
        self.assertTrue(service['build']['context'].endswith('Interoperable'))
        self.assertIn(('game-server',5000),controller.endpoints(row))

    def test_service_has_no_host_ports_or_external_network(self):
        _,row=controller.select('nyu_ctf_2023f-msc-urkel')
        service=controller.normalized_services(row)['web']
        self.assertNotIn('ports',service)
        self.assertNotIn('container_name',service)
        self.assertEqual(list(service['networks']),['challenge'])
        self.assertIn('misc.chal.csaw.io',service['networks']['challenge']['aliases'])
        self.assertIn(('misc.chal.csaw.io',1337),controller.endpoints(row))

    def test_controller_never_interpolates_host_credentials(self):
        from unittest.mock import patch
        _,row=controller.select('nyu_ctf_2023f-msc-urkel')
        with patch.object(controller.yaml,'safe_load',return_value={
            'services':{'bad':{'image':'python:3.11-slim','environment':{'SECRET':'${OPENAI_API_KEY}'}}}}):
            with self.assertRaisesRegex(ValueError,'interpolation'):
                controller.normalized_services(row)

    def interface(self,problem):
        competition,row=controller.select(problem)
        task=ManifestTask(problem,problem,None,row['problem_description'],'ctf',1,False,row)
        return resolve_contest_interface(ContestManifest('test',competition,(task,)))

    def test_tools_are_available_only_with_reviewed_mapping(self):
        tools={s.name for s in self.interface('nyu_ctf_2013f-cry-stfu').actions}
        self.assertTrue(NAMES<=tools)
        _,row=controller.select('nyu_ctf_2023f-cry-describeme')
        from copy import deepcopy
        row=deepcopy(row)
        row['source_review']['environment_kind']='unresolved'
        task=ManifestTask('unresolved','unresolved',None,row['problem_description'],'ctf',1,False,row)
        blocked={s.name for s in resolve_contest_interface(ContestManifest('test','nyu_ctf_bench',(task,))).actions}
        self.assertFalse(NAMES&blocked)

    def test_missing_run_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity'):
            execute('nyu_ctf_bench','nyu_ctf_2013f-cry-stfu',None,'start_environment',{})
        with self.assertRaises(ValueError):
            controller.directory('problem','../../other')

    def test_nyu_exact_flag_grading(self):
        from contest_adapters import _grade_non_programming
        _,row=controller.select('nyu_ctf_2013f-cry-stfu')
        problem=row['problem_id']
        task=ManifestTask(problem,problem,None,row['problem_description'],'ctf',1,False,row)
        self.assertEqual(_grade_non_programming(task,row['gold_label']['expected_answer'],'nyu_ctf_bench'),(1,1))
        self.assertEqual(_grade_non_programming(task,'incorrect flag','nyu_ctf_bench'),(0,1))

    def test_all_archived_flag_keys_use_case_sensitive_grading(self):
        from contest_adapters import _grade_non_programming
        for competition,row in controller.records():
            problem=row['problem_id']
            task=ManifestTask(problem,problem,None,row['problem_description'],'ctf',1,False,row)
            expected=row['gold_label']['expected_answer']
            with self.subTest(problem=problem):
                self.assertEqual(_grade_non_programming(task,expected,competition),(1,1))
                wrong=expected.swapcase()
                if wrong!=expected:
                    self.assertEqual(_grade_non_programming(task,wrong,competition),(0,1))
                self.assertEqual(_grade_non_programming(task,'incorrect flag',competition),(0,1))

if __name__=='__main__': unittest.main()
