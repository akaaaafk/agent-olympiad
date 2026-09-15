import unittest
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from scripts.repair_mystery_2015_static_20260913 import ROOT,CACHE,SELECTED,ORIGIN,MIRROR,URL,QUOTES,read,sha,sanitize,localize_html,localize_css,localize_inline,check_html,check_css,check_css_data,inspect_asset


class Mystery2015StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection_and_titles(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(r['problem_description'].splitlines()[0],'# '+self.soup(int(r['problem_id'][-5:])).select_one('.puzzle-page-header h1').get_text(' ',strip=True))
    def test_exact_html_and_css_relinking(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input';payload,styles=sanitize((ROOT/u['before']['source_file']).read_bytes(),r['source_url']);payload,deps=localize_html(payload,r['source_url']);cssdeps={}
            for name,target in styles.items():self.assertEqual((folder/name).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes(),target,cssdeps))
            self.assertEqual((folder/'puzzle.html').read_bytes(),localize_inline(payload,r['source_url'],cssdeps))
    def test_clue_text_and_blank_cells_unchanged(self):
        for u in self.plan['updates']:
            old=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').select_one('.puzzle');new=self.soup(int(u['after']['problem_id'][-5:])).select_one('.puzzle')
            for tree in (old,new):
                for el in tree.find_all(['style','script']):el.decompose()
            self.assertEqual(old.get_text().split(),new.get_text().split())
            for selector in ('td','div.bk','div.lt','div.nu','b'):
                self.assertEqual([(x.get_text(),x.get('class'),x.get('style')) for x in old.select(selector)],[(x.get_text(),x.get('class'),x.get('style')) for x in new.select(selector)])
    def test_assets_and_original_hashes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_static_allowlist_and_answer_isolation(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()};s=check_html(folder/'puzzle.html',allowed)
            self.assertFalse(s.find_all(['script','nav','a']));self.assertFalse(s.select('.puzzle-page-header .answer, .puzzle-page-header .sol'))
            for p in folder.glob('*.css'):check_css(p,allowed)
            for block in s.find_all('style'):
                check_css_data(block.get_text().encode())
                for m in URL.finditer(block.get_text().encode()):self.assertIn((folder/urlsplit(m[1].strip().strip(QUOTES).decode()).path).resolve(),allowed)
    def test_css_active_inputs_rejected(self):
        check_css_data(b'a[href^="javascript:"]:after {content:"";}')
        for data in (b'p{background:url(javascript:1)}',b'@import "other.css";',b'p{width:expression(1)}',b'p{behavior:url(x.htc)}'):
            with self.assertRaises(ValueError):check_css_data(data)
    def test_original_animation_frames_and_timing(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_01970');deps=u['after']['source_review']['dependency_urls'];counts=[1,81,53,79,59,49,69,83,71,69,65]
        for n,count in enumerate(counts):
            target=deps[f'{n}.gif'];review=self.plan['asset_reviews'][target];self.assertEqual(review['frames'],count)
            self.assertEqual(inspect_asset(ROOT/CACHE/u['after']['problem_id']/'input'/f'{n}.gif','.gif'),review)
        self.assertEqual([i['src'] for i in self.soup(1970).select('.puzzle img')],[f'{n}.gif' for n in range(1,11)]+['0.gif'])
    def test_fixed_geometric_clues(self):
        self.assertEqual(len(self.soup(1985).select('.bk')),81);self.assertEqual(len(self.soup(1985).select('.lt')),81)
        self.assertEqual(len(self.soup(2008).select('.bk')),225);self.assertEqual(len(self.soup(2008).select('.nu')),29)
        self.assertEqual(len(self.soup(2044).select('.puzzle-table')),5);self.assertEqual(len(self.soup(2044).select('.puzzle-table2')),1)
        self.assertEqual(len(self.soup(2124).select('.puzzle tr')),17)
    def test_dory_not_applied_as_global_errata(self):
        dory=self.soup(2007);other=self.soup(2044);self.assertIn('errata',dory.get_text().lower())
        self.assertNotEqual(dory.select_one('.puzzle-table').get_text().split(),other.select_one('.puzzle-table').get_text().split())
        self.assertIn('4 R09',self.soup(2045).get_text());self.assertNotIn('4-R09',self.soup(2045).get_text())
        self.assertIn('T[IM',self.soup(2109).get_text());self.assertIn('WOD',self.soup(2109).get_text())
    def test_meta_limitations_remain_explicit(self):
        for n in (1995,2062,2080):
            u=next(u for u in self.plan['updates'] if u['after']['problem_id']==f'mystery_hunt_{n:05}');self.assertIn('does not make the meta independently solvable',u['after']['asset_policy']);self.assertIn('call it in',self.soup(n).select_one('.puzzle').get_text())
    def test_publisher_redirect_and_original_fonts(self):
        for url,s in self.plan['publisher_snapshots'].items():
            self.assertEqual(sha(ROOT/s['path']),s['sha256'])
            if url.startswith(MIRROR):self.assertEqual(s['final_url'],ORIGIN+url[len(MIRROR):].lstrip('/'));self.assertTrue(s['redirects'])
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input'
            for p in folder.iterdir():
                if p.suffix in ('.ttf','.woff','.woff2','.eot','.svg'):self.assertTrue(inspect_asset(p,p.suffix))
    def test_scores_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for key in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][key],u['after'][key])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])


if __name__=='__main__':unittest.main()
