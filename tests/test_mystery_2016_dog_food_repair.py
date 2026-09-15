import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2016_dog_food_20260913 import ROOT,CACHE,SELECTED,PAGE,COUNTS,BAG_SHA,read,sha,sanitize,localize_html,localize_css,localize_inline,check_html,check_css,parse_bags,bag_html


class Mystery2016DogFoodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/'plan.json');cls.u=cls.plan['updates'][0];cls.r=cls.u['after'];cls.folder=ROOT/CACHE/cls.r['problem_id']/'input';ss=cls.plan['publisher_snapshots'];cls.bags,cls.css=parse_bags((ROOT/ss[PAGE+'images/bag.html?b=1']['path']).read_bytes(),(ROOT/ss[PAGE+'images/d.js']['path']).read_bytes())
    def test_selection_and_mapping_count(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(self.bags,self.plan['bag_projection']);self.assertEqual(len(self.bags),18);self.assertEqual(sum(COUNTS),157)
    def test_exact_main_page_projection(self):
        payload,styles=sanitize((ROOT/self.u['before']['source_file']).read_bytes(),PAGE);payload,deps=localize_html(payload,PAGE);cssdeps={}
        for n,u in styles.items():self.assertEqual((self.folder/n).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][u]['path']).read_bytes(),u,cssdeps))
        self.assertEqual((self.folder/'puzzle.html').read_bytes(),localize_inline(payload,PAGE,cssdeps))
    def test_eighteen_identical_query_responses(self):
        for u in self.r['source_review']['bag_query_urls']:self.assertEqual(sha(ROOT/self.plan['publisher_snapshots'][u]['path']),BAG_SHA)
    def test_exact_generated_bags(self):
        for b in self.bags:self.assertEqual((self.folder/f"bag-{b['bag']}.html").read_bytes(),bag_html(b,self.css))
    def test_dot_geometry_and_target_identity(self):
        for b in self.bags:
            s=BeautifulSoup((self.folder/f"bag-{b['bag']}.html").read_bytes(),'html.parser');self.assertEqual(s.select_one('.diagram img')['width'],str(b['width']));dots=s.select('a.r');self.assertEqual(len(dots),COUNTS[b['bag']-1])
            for d,xy,n in zip(dots,b['coordinates'],b['targets']):self.assertEqual(d['href'],n);self.assertEqual(d['style'],f'left:{xy[0]-15}px;top:{xy[1]-15}px')
    def test_literal_clue_wording(self):
        self.assertIn('<i>HO TDO GS</i>',self.bags[8]['clue']);self.assertIn('<i>H O, T-D O G</i>',self.bags[11]['clue']);self.assertIn('<i>H OT, DO G</i>',self.bags[15]['clue']);self.assertEqual(BeautifulSoup((self.folder/'puzzle.html').read_bytes(),'html.parser').select('span.e')[7].get_text(),'8 5 & 10 4')
    def test_all_asset_hashes(self):
        for n,u in self.r['source_review']['dependency_urls'].items():self.assertEqual(sha(self.folder/n),self.plan['publisher_snapshots'][u]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        self.assertEqual(sha(ROOT/self.u['before']['source_file']),self.r['source_review']['original_sha256'])
    def test_no_active_scripts_or_remote_links(self):
        allowed={p.resolve() for p in self.folder.iterdir()}
        for p in self.folder.glob('*.html'):s=check_html(p,allowed);self.assertFalse(s.find_all(['script','nav']))
        for p in self.folder.glob('*.css'):check_css(p,allowed)
    def test_limitations_explicit(self):self.assertIn('not pixel-identical hover/viewport behavior',self.r['asset_policy']);self.assertFalse(self.r['source_review']['font_binary_historical_version_certified'])
    def test_scores_and_readiness(self):
        for k in ('gold_label','total_points','split','license','year','team_size','title'):self.assertEqual(self.u['before'][k],self.r[k])
        self.assertEqual(self.u['before']['evaluation']['status'],self.r['evaluation']['status'])


if __name__=='__main__':unittest.main()
