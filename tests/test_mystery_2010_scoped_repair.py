import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2010_scoped_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,localize,check_html,check_css


class Mystery2010ScopedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html(self):
        for u in self.plan['updates']:
            row=u['after'];n=int(row['problem_id'][-5:]);expected,name,deferred=sanitize((ROOT/u['before']['source_file']).read_bytes(),n);expected,_=localize(expected,row['source_url']);folder=ROOT/CACHE/row['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),expected);self.assertEqual(deferred,row['source_review']['deferred_section'])
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed);check_css(folder/name,allowed)
    def test_nanohunt_initial_boundary(self):
        s=self.soup(1266);self.assertIn('Call HQ for an appointment',s.get_text());self.assertIn('No tools allowed',s.get_text());self.assertNotIn('Variation',s.get_text());self.assertFalse(s.find_all('table'));self.assertFalse(s.find_all('a'))
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('01266'));self.assertIn('Word based nanohunts',row['source_review']['deferred_section']);self.assertEqual({a['role'] for a in row['assets'] if 'nanohunts_cubes' in a['path']},{'judge_only'})
    def test_round_labels_coordinates_and_background(self):
        s=self.soup(1313);areas=s.find_all('area');self.assertEqual(len(areas),11);self.assertTrue(all(not a.has_attr('href') and a.has_attr('data-archive-href') for a in areas));self.assertEqual(areas[0]['coords'],'146,174,343,195');self.assertEqual(areas[-1]['coords'],'146,387,343,409');self.assertEqual(s.find('img',attrs={'usemap':True})['usemap'],'#overlay');self.assertIn("1952_top.jpg",s.find(id='page-top')['style']);self.assertTrue((ROOT/CACHE/'mystery_hunt_01313/input/1952_top.jpg').is_file())
    def test_dummy_answer_is_initial_instruction(self):self.assertIn('GONDRY',self.soup(1377).get_text())
    def test_historical_clues_not_modernized(self):
        for n in (1307,1337,1377):
            u=next(u for u in self.plan['updates'] if u['after']['problem_id']==f'mystery_hunt_{n:05}');a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');b=self.soup(n);self.assertIsNotNone(a.find(id='main'));self.assertEqual(a.find(id='main').get_text(),b.find(id='main').get_text())
    def test_bytes_and_originals(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for sub,key in [('input','dependency_urls'),('judge','judge_dependency_urls')]:
                for name,url in r['source_review'][key].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/sub/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_scores_status_and_safety(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status']);self.assertFalse(self.soup(int(u['after']['problem_id'][-5:])).find_all(['script','form','object','embed','iframe']))


if __name__=='__main__':unittest.main()
