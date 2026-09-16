import unittest
from scripts.repair_eoes_2025_score_metadata_20260913 import ROOT,CACHE,SELECTED,read


class EOESScoreMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.plan=read(ROOT/CACHE/'plan.json')

    def test_exact_distinct_totals(self):
        self.assertEqual([u['after']['total_points'] for u in self.plan['updates']],[120,125])

    def test_verified_section_sums(self):
        for u in self.plan['updates']:
            r=u['after']; parts=r['evaluation']['official_problem_maxima']
            self.assertEqual(sum(p['max_score'] for p in parts),r['total_points'])
            self.assertEqual([p['source_page'] for p in parts],SELECTED[r['problem_id']]['pages'])

    def test_not_executable(self):
        for f in self.plan['new_files']:
            rubric=read(ROOT/f['source'])
            self.assertFalse(rubric['executable'])
            self.assertEqual(rubric['criteria'],[])

    def test_old_year_reuse_is_not_active(self):
        for u in self.plan['updates']:
            self.assertNotIn('rubric_reuse',u['after']['evaluation'])
            self.assertIn('superseded_rubric_reuse',u['after']['evaluation'])

    def test_answers_and_readiness_retained(self):
        for u in self.plan['updates']:
            self.assertEqual(u['before']['gold_label'],u['after']['gold_label'])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')
            self.assertEqual(u['before']['problem_description'],u['after']['problem_description'])


if __name__=='__main__': unittest.main()
