import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2005_static_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,sanitize_css,source_equal,check_html,check_css

class Mystery2005StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_fifteen_records_seventy_five_files(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),75)
    def test_html_is_exact_bounded_source_edit(self):
        for u in self.plan['updates']:
            p=ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html';self.assertEqual(p.read_bytes(),sanitize((ROOT/u['before']['source_file']).read_bytes())[0])
    def test_every_dependency_is_packaged(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for p in folder.glob('*.css'):check_css(p,allowed)
    def test_missing_css_rule_is_unused_and_only_rule_removed(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input'
            if not (folder/'grid.css').exists():continue
            original=ROOT/self.plan['publisher_snapshots'][r['source_url']+'grid.css']['path'];self.assertEqual((folder/'grid.css').read_bytes(),sanitize_css(original.read_bytes(),(folder/'puzzle.html').read_bytes()))
            with self.assertRaises(ValueError):sanitize_css(original.read_bytes(),b'<table class="grid"><td class="black"></td></table>')
    def test_layout_cells_and_monospace_text_preserved(self):
        for u in self.plan['updates']:
            a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');b=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser')
            self.assertEqual([str(t) for t in a.find_all('pre')],[str(t) for t in b.find_all('pre')]);self.assertEqual([str(t) for t in a.find_all('table') if not t.find('a')],[str(t) for t in b.find_all('table') if not t.find('a')][1:])
    def test_prior_utf8_repairs_match_publisher(self):
        for u in self.plan['updates']:
            source_equal(ROOT/u['before']['source_file'],ROOT/u['after']['source_review']['publisher_snapshot'])
        self.assertIn('Café',(ROOT/CACHE/'mystery_hunt_00617/input/puzzle.html').read_text(encoding='utf-8'));self.assertIn('Mociño',(ROOT/CACHE/'mystery_hunt_00652/input/puzzle.html').read_text(encoding='utf-8'))
    def test_scores_status_gold_and_sources_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready');self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_file_hashes_and_live_limits(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        r={u['after']['problem_id']:u['after'] for u in self.plan['updates']}
        self.assertIn('live performance',r['mystery_hunt_00687']['evaluation']['limitations']);self.assertIn('No host interaction',r['mystery_hunt_00691']['evaluation']['limitations'])

if __name__=='__main__':unittest.main()
