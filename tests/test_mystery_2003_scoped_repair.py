import re
import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2003_scoped_packets_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,check_html

class Mystery2003ScopedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selected(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_source_changes_are_exact(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id'];self.assertEqual((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),sanitize((ROOT/u['before']['source_file']).read_bytes(),pid)[0])
    def test_no_navigation_or_active_content(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';s=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()});self.assertFalse(s.find_all('a'))
    def test_original_grid_and_mark_positions_unchanged(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id']
            if pid.endswith(('00384','00433')):
                before=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');after=BeautifulSoup((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),'html.parser')
                self.assertEqual([str(t) for t in before.find_all('table') if not t.find('img')],[str(t) for t in after.find_all('table') if not t.find('img')])
    def test_late_hint_is_not_initial(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('00451'))
        data=(ROOT/CACHE/'mystery_hunt_00451/input/puzzle.html').read_text(encoding='ascii')
        for token in ('Saturday evening','Ace through King','King through Ace','AH, 2H'):
            self.assertNotIn(token,data);self.assertNotIn(token,u['after']['problem_description']);self.assertIn(token,u['after']['source_review']['deferred_section'])
        original=(ROOT/u['before']['source_file']).read_text(encoding='ascii')
        self.assertEqual(re.findall(r'[0-4]{100,}',data),re.findall(r'[0-4]{100,}',original))
    def test_gold_score_status_and_legacy_source_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')
            self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_prepared_hashes(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])

if __name__=='__main__':unittest.main()
