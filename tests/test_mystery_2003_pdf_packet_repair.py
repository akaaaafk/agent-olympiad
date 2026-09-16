import unittest
from scripts.repair_mystery_2003_pdf_packets_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,check_html

class Mystery2003PDFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selected(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_source_markup_preserved(self):
        for u in self.plan['updates']:
            self.assertEqual((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),sanitize((ROOT/u['before']['source_file']).read_bytes())[0])
    def test_local_dependencies_only(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
    def test_all_eight_pdfs_and_two_inert_ps_files(self):
        self.assertEqual(len(self.plan['pdf_inventory']),8)
        self.assertEqual(sum(c['destination'].endswith('.ps') for c in self.plan['copies']),2)
        for u in self.plan['updates']:self.assertFalse(u['after']['source_review']['postscript_executed'])
    def test_gold_score_and_status_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):
                self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')
            self.assertIn(u['before']['evaluation']['limitations'],u['after']['evaluation']['limitations'])
    def test_bytes_match_frozen_plan(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        for p in self.plan['publisher_snapshots'].values():self.assertEqual(sha(ROOT/p['path']),p['sha256'])

if __name__=='__main__':unittest.main()
