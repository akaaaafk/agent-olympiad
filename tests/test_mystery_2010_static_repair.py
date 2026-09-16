import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2010_static_20260913 import ROOT,CACHE,SELECTED,CSS_URL,read,sha,sanitize,localize,local_css,check_html,check_css


class Mystery2010StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),173)
    def test_exact_html_and_complete_main_content(self):
        for u in self.plan['updates']:
            row=u['after'];data=(ROOT/u['before']['source_file']).read_bytes();expected,name=sanitize(data);expected,_=localize(expected,row['source_url']);folder=ROOT/CACHE/row['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),expected)
            a=BeautifulSoup(data,'html.parser');b=BeautifulSoup(expected,'html.parser')
            for img in a.find_all('img'):img['src']=Path(img['src']).name
            self.assertIsNotNone(a.find(id='main'));self.assertEqual(str(a.find(id='main')),str(b.find(id='main')))
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed);check_css(folder/name,allowed)
    def test_all_42_imagemap_targets_and_coordinates(self):
        folder=ROOT/CACHE/'mystery_hunt_01261/input';s=BeautifulSoup((folder/'puzzle.html').read_bytes(),'html.parser');areas=s.find_all('area')
        self.assertEqual([a['href'] for a in areas],[f'{i:02}.jpg' for i in range(1,43)]);self.assertEqual(s.find('img',attrs={'usemap':True})['usemap'],'#conquering_the_world');self.assertEqual(s.find('map')['name'],'conquering_the_world')
        self.assertEqual(areas[0]['coords'],'1,1,97,146');self.assertEqual(areas[-1]['coords'],'503,893,599,1038')
    def test_all_composition_images_keep_order(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('01358'));a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').find(id='main');b=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser').find(id='main')
        self.assertEqual(len(b.find_all('img')),44);self.assertEqual([str(x) for x in a.find_all('img')],[str(x) for x in b.find_all('img')])
    def test_css_only_localized(self):
        for u in self.plan['updates']:
            row=u['after'];name=row['source_review']['css_name'];original=ROOT/self.plan['publisher_snapshots'][CSS_URL+name]['path'];expected,_=local_css(original.read_bytes());self.assertEqual((ROOT/CACHE/row['problem_id']/'input'/name).read_bytes(),expected)
    def test_byte_identity_and_originals(self):
        for u in self.plan['updates']:
            row=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),row['source_review']['original_sha256'])
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/row['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_scores_and_status_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
    def test_no_active_or_solution_navigation(self):
        for pid in SELECTED:
            s=BeautifulSoup((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),'html.parser');self.assertFalse(s.find_all(['script','form','object','iframe','embed']));self.assertFalse(s.find_all('a'))


if __name__=='__main__':unittest.main()
