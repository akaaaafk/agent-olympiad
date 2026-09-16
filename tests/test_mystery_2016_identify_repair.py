import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2016_identify_20260913 import ROOT,CACHE,SELECTED,PAGE,UPSTREAM,UPSTREAM_SHA,ARCHIVE_JS_SHA,TEX,read,sha,sanitize,localize_html,localize_css,localize_inline,check_html,check_css,mathml


class Mystery2016IdentifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.u=cls.plan['updates'][0];cls.r=cls.u['after'];cls.folder=ROOT/CACHE/cls.r['problem_id']/'input';cls.s=BeautifulSoup((cls.folder/'puzzle.html').read_bytes(),'html.parser')
    def test_static_selection_and_extent(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.s.select('.content tr')),29)
    def test_exact_html_projection(self):
        payload,styles=sanitize((ROOT/self.u['before']['source_file']).read_bytes(),PAGE);payload,deps=localize_html(payload,PAGE);cssdeps={}
        for n,u in styles.items():self.assertEqual((self.folder/n).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][u]['path']).read_bytes(),u,cssdeps))
        self.assertEqual((self.folder/'puzzle.html').read_bytes(),localize_inline(payload,PAGE,cssdeps))
    def test_library_only_five_known_corruptions(self):
        ss=self.plan['publisher_snapshots'];a=ROOT/ss[UPSTREAM]['path'];b=ROOT/ss[PAGE+'puzzle.js']['path'];self.assertEqual(sha(a),UPSTREAM_SHA);self.assertEqual(sha(b),ARCHIVE_JS_SHA);self.assertEqual(b.read_bytes().count(br'\../../'),5);self.assertEqual(b.read_bytes().replace(br'\../../',br'\./'),a.read_bytes())
    def test_original_tex_annotations(self):
        tex=[t.decode('ascii') for t in TEX.findall((ROOT/self.u['before']['source_file']).read_bytes())];self.assertEqual(tex,self.plan['tex_fragments']);self.assertEqual([a.get_text() for a in self.s.find_all('annotation')],tex)
    def test_superscripts_and_arrows(self):
        formulas=self.s.find_all('math');self.assertEqual(len(formulas[2].find_all('msup')),5);self.assertEqual(len(formulas[7].find_all('msup')),6);self.assertEqual([m.get_text() for m in formulas[16].find_all('mo')],['=','↑','↑']);self.assertEqual([m.get_text() for m in formulas[25].find_all('mi')],['A','B','B','B','B'])
    def test_reject_non_source_tex_grammar(self):
        for t in [r'\input{file}',r'\href{url}{text}','2^3','{2','2}',r'\sqrt{2}']:
            with self.assertRaises(ValueError):mathml(t)
    def test_all_original_image_bytes_and_gif(self):
        for n,u in self.r['source_review']['dependency_urls'].items():self.assertEqual(sha(self.folder/n),self.plan['publisher_snapshots'][u]['sha256'])
        self.assertEqual(self.plan['asset_reviews'][PAGE+'images/square6.gif']['frames'],1)
        self.assertEqual([x['src'] for x in self.s.select('.content tr td:first-child img')],[f'a{n:02}.jpg' for n in range(1,30)])
    def test_allowlists_and_no_scripts(self):
        allowed={p.resolve() for p in self.folder.iterdir()};check_html(self.folder/'puzzle.html',allowed);self.assertFalse(self.s.find_all(['script','nav']));self.assertFalse(list(self.folder.glob('*.js')))
        for p in self.folder.glob('*.css'):check_css(p,allowed)
    def test_preserve_example_markers_and_blank_line(self):
        self.assertEqual(self.s.select_one('.content').get_text().count('(eg)'),6);self.assertIn('_____________________________',self.s.get_text());self.assertIn('not certified identical',self.r['asset_policy'])
    def test_hashes_scores_and_readiness(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        for k in ('gold_label','total_points','split','license','year','team_size','title'):self.assertEqual(self.u['before'][k],self.r[k])
        self.assertEqual(self.u['before']['evaluation']['status'],self.r['evaluation']['status'])


if __name__=='__main__':unittest.main()
