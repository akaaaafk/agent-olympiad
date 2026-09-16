import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2012_scoped_20260913 import ROOT,CACHE,SELECTED,SOURCE_ONLY,read,sha,sanitize,localize,css_graph,check_html,check_css


class Mystery2012ScopedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_public_pages(self):
        for u in self.plan['updates']:
            r=u['after'];n=int(r['problem_id'][-5:])
            if r['problem_id']==SOURCE_ONLY:continue
            original=(ROOT/u['before']['source_file']).read_bytes();payload,_=sanitize(original,r['source_url'],n);payload,_=localize(payload,r['source_url']);self.assertEqual((ROOT/CACHE/r['problem_id']/'input/puzzle.html').read_bytes(),payload)
            self.assertEqual(BeautifulSoup(original,'html.parser').find(id='main').get_text(),self.soup(n).find(id='main').get_text())
    def test_source_only_correction_not_public(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id']==SOURCE_ONLY);r=u['after'];a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');b=BeautifulSoup((ROOT/CACHE/SOURCE_ONLY/'judge/round-original.html').read_bytes(),'html.parser');self.assertEqual(a.title.get_text(),'Borbonicus & Bodley');self.assertEqual(b.title.get_text(),'A Circus Line');self.assertTrue(r['source_review']['source_correction_only']);self.assertTrue(r['source_review']['public_packet_review_pending']);self.assertFalse([x for x in r['assets'] if x['role']=='agent_visible']);self.assertEqual(sha(ROOT/CACHE/SOURCE_ONLY/'judge/round-original.html'),r['source_review']['publisher_html_sha256'])
    def test_explicit_images_and_historical_context(self):
        self.assertEqual([i['src'] for i in self.soup(1558).find_all('img')],['1.jpg','diagram.png']);self.assertIn('Contact HQ',self.soup(1558).get_text());self.assertIn('8-pin IC',self.soup(1558).get_text());s=self.soup(1597);self.assertEqual(s.title.get_text(),'');self.assertEqual(s.find('h2').get_text(),'');self.assertEqual([i['src'] for i in s.find_all('img')],['banner.png','2.png']);self.assertIn('Six rings out of six.',s.get_text());self.assertEqual(s.find('h3').get_text(),"Betsy Johnson's Review")
    def test_cascade_and_all_local_dependencies(self):
        for u in self.plan['updates']:
            r=u['after']
            if r['problem_id']==SOURCE_ONLY:continue
            rev=r['source_review'];folder=ROOT/CACHE/r['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed);styles,_,urls=css_graph(rev['stylesheet_urls'],dict(self.plan['publisher_snapshots']));self.assertEqual(urls,rev['all_stylesheet_urls'])
            for name,data in styles.items():self.assertEqual((folder/name).read_bytes(),data);check_css(folder/name,allowed)
    def test_metadata_preserved_and_scope_recorded(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
        report=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('01558'));self.assertIn('firmware',report['asset_policy']);self.assertIn('have not been recovered',report['asset_policy'])
    def test_original_and_dependency_bytes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review'].get('dependency_urls',{}).items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_no_public_dynamic_controls_or_components(self):
        for n in (1558,1597):self.assertFalse(self.soup(n).find_all(['script','iframe','object','embed','form']))
        self.assertEqual(sum('/judge/' in c['destination'] for c in self.plan['copies']),1);self.assertFalse([c for c in self.plan['copies'] if c['destination'].endswith(('.exe','.bin','.hex','.js'))]);self.assertFalse([c for c in self.plan['copies'] if SOURCE_ONLY+'/input/' in c['destination']])


if __name__=='__main__':unittest.main()
