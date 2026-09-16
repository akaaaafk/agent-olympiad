import unittest
from scripts.repair_debate_event_year_20260913 import ROOT,CACHE,read


class DebateEventYearRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')

    def test_2025_filename_not_event_year(self):
        self.assertEqual(self.plan['before']['year'],2025)
        self.assertEqual(self.plan['after']['year'],2020)
        self.assertIn('Jan-08-2025',self.plan['after']['problem_id'])
        self.assertEqual(self.plan['before']['title'],self.plan['after']['title'])

    def test_corroborated_source_dates(self):
        self.assertEqual(self.plan['evidence']['event_dates'],['2020-11-07','2020-11-08'])
        self.assertEqual(self.plan['evidence']['round'],3)
        self.assertEqual(self.plan['after']['source_review']['motion_source']['year'],2020)

    def test_no_gold_or_status_change(self):
        a,b=self.plan['before'],self.plan['after']
        for k in ('gold_label','total_points','problem_description','solution_file','split','license'):
            self.assertEqual(a[k],b[k])
        self.assertEqual(a['evaluation']['status'],b['evaluation']['status'])

    def test_evidence_judge_only(self):
        old={a['path'] for a in self.plan['before']['assets']}
        self.assertTrue(all(a['role']=='judge_only' for a in self.plan['after']['assets'] if a['path'] not in old))


if __name__=='__main__':unittest.main()
