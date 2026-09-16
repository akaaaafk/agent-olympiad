import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2011_static_20260913 import ROOT,CACHE,SELECTED,RESET_URL,read,sha,sanitize,localize,local_css,check_html,check_css


class Mystery2011StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html_and_puzzle(self):
        for u in self.plan['updates']:
            row=u['after'];data=(ROOT/u['before']['source_file']).read_bytes();expected,styleurls=sanitize(data,row['source_url']);expected,_=localize(expected,row['source_url']);folder=ROOT/CACHE/row['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),expected)
            a=BeautifulSoup(data,'html.parser');b=BeautifulSoup(expected,'html.parser')
            for t in a.find_all(['img','a']):
                attr='src' if t.name=='img' else 'href';t[attr]=Path(t[attr]).name
            keys=('techtitle','techcontent','technote') if row['problem_id'].endswith('01408') else ('puzzlecontent',)
            for key in keys:self.assertIsNotNone(a.find(id=key));self.assertEqual(str(a.find(id=key)),str(b.find(id=key)))
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name in styleurls:check_css(folder/name,allowed)
    def test_reset_license_and_cascade(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input';self.assertEqual(sha(folder/'reset-min.css'),self.plan['publisher_snapshots'][RESET_URL]['sha256']);self.assertIn('Copyright (c) 2010, Yahoo!',(folder/'reset-min.css').read_text());self.assertEqual([x['href'] for x in self.soup(int(r['problem_id'][-5:])).find_all('link')],list(r['source_review']['stylesheet_urls']))
            for name,url in r['source_review']['stylesheet_urls'].items():self.assertEqual((folder/name).read_bytes(),local_css((ROOT/self.plan['publisher_snapshots'][url]['path']).read_bytes(),url)[0])
    def test_worked_example_not_filtered(self):
        s=self.soup(1410);self.assertIn('Solution to sample puzzle',s.get_text());self.assertIn('ShikakuroSampleSoln.png',[i['src'] for i in s.find_all('img')])
    def test_blanks_and_26_diagrams_preserved(self):
        self.assertEqual(len(self.soup(1521).find_all('em')),578);self.assertEqual([i['src'] for i in self.soup(1520).find_all('img')],[f'{i:02}.png' for i in range(1,27)])
    def test_answer_variants_not_merged(self):
        for ids in [(1431,1432),(1521,1523)]:
            rows=[u['after'] for u in self.plan['updates'] if int(u['after']['problem_id'][-5:]) in ids];self.assertEqual(len(rows),2);self.assertNotEqual(rows[0]['gold_label'],rows[1]['gold_label']);self.assertEqual(self.soup(ids[0]).get_text(),self.soup(ids[1]).get_text())
    def test_byte_identity(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_scores_and_safety(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status']);s=self.soup(int(u['after']['problem_id'][-5:]));self.assertFalse(s.find_all(['script','form','iframe','object','embed']));self.assertIsNone(s.find(id='puzzletopbar'))


if __name__=='__main__':unittest.main()
