import unittest
from scripts.repair_mystery_2016_orbits_20260913 import ROOT,CACHE,SELECTED,ORIGIN,read,sha,sanitize,localize_html,localize_css,localize_inline,check_html,check_css,zip_review


class Mystery2016OrbitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.u=cls.plan['updates'][0];cls.r=cls.u['after'];cls.folder=ROOT/CACHE/cls.r['problem_id']/'input'
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_source_html_preserved(self):
        payload,styles=sanitize((ROOT/self.u['before']['source_file']).read_bytes(),self.r['source_url']);payload,deps=localize_html(payload,self.r['source_url']);cssdeps={}
        for name,url in styles.items():self.assertEqual((self.folder/name).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][url]['path']).read_bytes(),url,cssdeps))
        self.assertEqual((self.folder/'puzzle.html').read_bytes(),localize_inline(payload,self.r['source_url'],cssdeps))
    def test_full_zip_crc_and_text(self):self.assertEqual(zip_review(self.folder/'orbits.zip'),self.plan['asset_reviews'][ORIGIN+'puzzle/orbits/orbits.zip'])
    def test_no_commented_link_activated(self):
        s=check_html(self.folder/'puzzle.html',{p.resolve() for p in self.folder.iterdir()});self.assertEqual([a['href'] for a in s.select('.content a[href]')],['orbits.zip']);self.assertFalse(s.find_all(['script','nav']))
    def test_style_allowlists(self):
        for p in self.folder.glob('*.css'):check_css(p,{q.resolve() for q in self.folder.iterdir()})
    def test_all_hashes(self):
        for n,u in self.r['source_review']['dependency_urls'].items():self.assertEqual(sha(self.folder/n),self.plan['publisher_snapshots'][u]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        self.assertEqual(sha(ROOT/self.u['before']['source_file']),self.r['source_review']['original_sha256'])
    def test_original_line_order_and_extent(self):
        z=self.plan['asset_reviews'][ORIGIN+'puzzle/orbits/orbits.zip'];self.assertEqual(z['entries'][1]['lines'],13853280);self.assertEqual(z['entries'][1]['first_line'],'BDLMMOTY');self.assertFalse(z['extracted_to_disk']);self.assertFalse(z['executed'])
    def test_scores_and_readiness(self):
        for k in ('gold_label','total_points','split','license','year','team_size','title'):self.assertEqual(self.u['before'][k],self.r[k])
        self.assertEqual(self.u['before']['evaluation']['status'],self.r['evaluation']['status'])


if __name__=='__main__':unittest.main()
