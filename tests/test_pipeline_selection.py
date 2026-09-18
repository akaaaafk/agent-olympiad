import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'scripts'), str(Path(__file__).resolve().parents[1] / 'src')]
from run_pipeline import select_jobs


class PipelineSelectionTests(unittest.TestCase):
    def setUp(self):
        self.registry = {'jobs': [
            dict(competition='arml_local', session='arml_local_2009', years=['2009']),
            dict(competition='arml_local', session='arml_local_2010', years=['2010']),
            dict(competition='icpc', session='icpc_wf_2009', years=['2009'])]}

    def test_filters_intersect_and_do_not_match_other_competitions(self):
        args=SimpleNamespace(competitions='arml_local', years='2009', sessions=None)
        self.assertEqual([r['session'] for r in select_jobs(self.registry,args)], ['arml_local_2009'])
        args.years='2009, 2010'
        self.assertEqual(len(select_jobs(self.registry,args)),2)
        args.sessions='arml_local_2010'
        self.assertEqual([r['session'] for r in select_jobs(self.registry,args)], ['arml_local_2010'])

    def test_no_match_and_stale_registry_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'No sessions match'):
            select_jobs(self.registry,SimpleNamespace(competitions='arml_local',years='1999'))
        del self.registry['jobs'][0]['years']
        with self.assertRaisesRegex(ValueError, 'Registry lacks year'):
            select_jobs(self.registry,SimpleNamespace(competitions='arml_local',years='2009'))

    def test_no_filter_preserves_all_jobs(self):
        self.assertEqual(select_jobs(self.registry,SimpleNamespace()),self.registry['jobs'])
