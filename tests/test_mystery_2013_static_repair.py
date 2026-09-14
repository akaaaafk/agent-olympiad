import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2013_static_20260913 import ROOT,CACHE,SELECTED,ORIGIN,read,sha,sanitize,localize_html,localize_css,localize_inline,compile_less,check_html,check_css,packet_title


class Mystery2013StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection_and_titles(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(r['problem_description'].splitlines()[0],'# '+packet_title(self.soup(int(r['problem_id'][-5:]))))
        self.assertEqual(packet_title(self.soup(1727)),'Travels With Charlie')
    def test_exact_html_and_style_compilation(self):
        for u in self.plan['updates']:
            r=u['after'];pid=r['problem_id'];url=r['source_url'];folder=ROOT/CACHE/pid/'input';payload,styles=sanitize((ROOT/u['before']['source_file']).read_bytes(),url,int(pid[-5:]));payload,deps=localize_html(payload,url);cssdeps={}
            for name,target in styles.items():
                data=(ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes()
                if target.endswith('.less'):data=compile_less(data)
                self.assertEqual((folder/name).read_bytes(),localize_css(data,target,cssdeps))
            self.assertEqual((folder/'puzzle.html').read_bytes(),localize_inline(payload,url,cssdeps))
    def test_clue_text_unchanged(self):
        for u in self.plan['updates']:
            r=u['after'];old=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').find(id='content');new=self.soup(int(r['problem_id'][-5:])).find(id='content')
            for el in old.find_all(class_='answer'):el.decompose()
            for tree in (old,new):
                for el in tree.find_all(['style','script']):el.decompose()
            # BS merges adjacent whitespace nodes differently after removal;
            # exact serialized input bytes are checked separately above.
            self.assertEqual(old.get_text().split(),new.get_text().split())
    def test_assets_and_source_hashes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_static_allowlist_and_navigation(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()};s=check_html(folder/'puzzle.html',allowed)
            self.assertFalse(s.find(id='fixie-nav'));self.assertFalse(s.find_all(class_='answer'));self.assertFalse(s.find_all('script'));self.assertFalse(s.select('#evilbg, #evilbar1'))
            for p in folder.glob('*.css'):check_css(p,allowed)
    def test_image_and_feed_order(self):
        expected=[f'{c}{n}.jpg' for c,count in [('a',16),('b',24)] for n in range(1,count+1)]
        self.assertEqual([a['href'] for a in self.soup(1687).find_all('a',href=True)],expected)
        self.assertEqual([i['src'] for i in self.soup(1687).find_all('img')][1:],[p.replace('.jpg','-small.jpg') for p in expected])
        self.assertEqual([len(c.find_all('img')) for c in self.soup(1727).find_all('center')],[72,51,80,77])
        self.assertEqual([i['src'] for i in self.soup(1775).find(id='content').find_all('img')],[f'{i}.png' for i in range(1,6)])
    def test_blank_cells_and_fiction_preserved(self):
        self.assertIn('W♄ite Magic',self.soup(1802).get_text());self.assertEqual(len(self.soup(1807).select('.letter, .response')),40)
        self.assertEqual(len(self.soup(1684).find_all('tr')),18)
        self.assertIn('Diesenachricht',self.soup(1820).get_text());self.assertIn('federalreserve.meta.gov',self.soup(1810).get_text())
    def test_missing_decoration_and_font_limits(self):
        self.assertEqual({d['source_url'] for d in self.plan['unavailable_dependencies']},{ORIGIN+'feynman/gptile.jpg',ORIGIN+'get_smart/evilfg.png'})
        self.assertTrue(all(d['http_status']==404 for d in self.plan['unavailable_dependencies']))
        for u in self.plan['updates']:
            r=u['after'];self.assertFalse(r['source_review']['font_binary_historical_version_certified'])
            for name in r['source_review']['dependency_urls']:
                if name.endswith('-OFL.txt'):self.assertIn('SIL OPEN FONT LICENSE',(ROOT/CACHE/r['problem_id']/'input'/name).read_text(encoding='utf-8'))
    def test_compiler_is_pinned_and_rejects_active_input(self):
        item=self.plan['less_tool_lock'];self.assertEqual(sha(ROOT/item['path']),item['sha256'])
        self.assertEqual(read(ROOT/CACHE/'less_tool/package-lock.json')['packages']['node_modules/less']['version'],'1.3.0')
        for data in (b'@import "x.less";',b'p {color:`process.exit()`}',b'p{background:expression(1)}'):
            with self.assertRaises(ValueError):compile_less(data)
    def test_scores_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for key in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][key],u['after'][key])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])


if __name__=='__main__':unittest.main()
