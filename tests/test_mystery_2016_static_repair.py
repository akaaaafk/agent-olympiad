import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2016_static_20260913 import ROOT,CACHE,SELECTED,FONT_REPAIRS,LOGO_REPAIRS,ORIGIN,read,sha,sanitize,localize_html,localize_css,localize_inline,check_html,check_css


class Mystery2016StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection_and_titles(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(r['problem_description'].splitlines()[0],'# '+self.soup(int(r['problem_id'][-5:])).select_one('.header h2').get_text(' ',strip=True))
    def test_exact_html_and_styles(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input';payload,styles=sanitize((ROOT/u['before']['source_file']).read_bytes(),r['source_url']);payload,deps=localize_html(payload,r['source_url']);cssdeps={}
            for name,target in styles.items():self.assertEqual((folder/name).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes(),target,cssdeps))
            self.assertEqual((folder/'puzzle.html').read_bytes(),localize_inline(payload,r['source_url'],cssdeps))
    def test_all_clue_text_and_attributes_preserved(self):
        for u in self.plan['updates']:
            old=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').select_one('.content');new=self.soup(int(u['after']['problem_id'][-5:])).select_one('.content');self.assertEqual(old.get_text().split(),new.get_text().split())
            for selector in ('td','sub','li','b','h4'):
                self.assertEqual([(x.get_text(),dict(x.attrs)) for x in old.select(selector)],[(x.get_text(),dict(x.attrs)) for x in new.select(selector)])
    def test_original_image_order_and_large_grid(self):
        self.assertEqual([e['src'] for e in self.soup(2218).select('.content image')],[f'rfts{n}.png' for n in range(1,11)])
        self.assertEqual(self.plan['asset_reviews'][ORIGIN+'puzzle/replication/images/sudoku.png']['size'],[16290,4720]);self.assertEqual([a['href'] for a in self.soup(2220).select('.content a')],['sudoku.png'])
        self.assertEqual([a['href'] for a in self.soup(2241).select('.content a')],['hunt.png','hunt_example.png','hunt.png'])
    def test_assets_and_original_hashes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_static_allowlists_and_credit(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()};s=check_html(folder/'puzzle.html',allowed);self.assertFalse(s.find_all(['script','nav']));self.assertFalse(s.select('.header .answer'));self.assertFalse(s.select('a.back-to-round[href]'))
            for p in folder.glob('*.css'):check_css(p,allowed)
            if s.select('.footer'):self.assertEqual(s.select_one('.footer').get_text(' ',strip=True),'Puzzle artwork designed and produced by ahc.com');self.assertFalse(s.select('.footer a[href]'))
    def test_source_backed_broken_path_repairs(self):
        self.assertEqual({d['source_url']:d['recovered_url'] for d in self.plan['failed_font_paths']},FONT_REPAIRS);self.assertTrue(all(d['http_status']==404 for d in self.plan['failed_font_paths']));d=self.plan['failed_logo_path'];self.assertEqual(LOGO_REPAIRS[d['source_url']],d['recovered_url']);self.assertEqual(d['http_status'],404)
        for url in [*FONT_REPAIRS.values(),*LOGO_REPAIRS.values()]:self.assertEqual(sha(ROOT/self.plan['publisher_snapshots'][url]['path']),self.plan['publisher_snapshots'][url]['sha256'])
    def test_special_symbols_and_enumeration(self):
        self.assertEqual(len(self.soup(2200).select('.content sub')),64);self.assertIn('[Ch→Co]',self.soup(2200).get_text());self.assertIn('[•→F]',self.soup(2200).get_text());self.assertIn('ohter',self.soup(2166).get_text());self.assertEqual(len(self.soup(2166).select('.content table')),11);self.assertEqual(len(self.soup(2258).select('.content tr')),17)
    def test_team_rules_and_font_limits(self):
        s=self.soup(2241);self.assertIn('For teams of 61–110',s.get_text());self.assertIn('111–125: 35',s.get_text());self.assertIn('two or three days',s.get_text())
        for u in self.plan['updates']:
            self.assertFalse(u['after']['source_review']['font_binary_historical_version_certified'])
            for name in u['after']['source_review']['dependency_urls']:
                if name.endswith('-OFL.txt'):self.assertIn('SIL OPEN FONT LICENSE',(ROOT/CACHE/u['after']['problem_id']/'input'/name).read_text(encoding='utf-8'))
    def test_scores_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for key in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][key],u['after'][key])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])


if __name__=='__main__':unittest.main()
