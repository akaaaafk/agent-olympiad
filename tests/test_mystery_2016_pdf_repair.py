import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2016_pdf_20260913 import ROOT,CACHE,SELECTED,PAGE_COUNTS,ORIGIN,read,sha,sanitize,localize_html,localize_css,localize_inline,check_html,check_css,pdf_review


class Mystery2016PdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection_and_seven_pages(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(sum(r['pages'] for r in self.plan['asset_reviews'].values() if 'pages' in r),7)
    def test_exact_html_and_styles(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input';payload,styles=sanitize((ROOT/u['before']['source_file']).read_bytes(),r['source_url']);payload,deps=localize_html(payload,r['source_url']);cssdeps={}
            for name,target in styles.items():self.assertEqual((folder/name).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes(),target,cssdeps))
            self.assertEqual((folder/'puzzle.html').read_bytes(),localize_inline(payload,r['source_url'],cssdeps))
    def test_pdf_bytes_pages_and_no_active_objects(self):
        for u in self.plan['updates']:
            r=u['after'];n=int(r['problem_id'][-5:]);folder=ROOT/CACHE/r['problem_id']/'input';pdfs=list(folder.glob('*.pdf'));self.assertEqual(len(pdfs),1);url=r['source_review']['dependency_urls'][pdfs[0].name];self.assertEqual(pdf_review(pdfs[0],PAGE_COUNTS[n]),self.plan['asset_reviews'][url]);self.assertEqual(sha(pdfs[0]),self.plan['publisher_snapshots'][url]['sha256'])
    def test_all_asset_hashes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_allowlists_and_no_solution_navigation(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()};s=check_html(folder/'puzzle.html',allowed);self.assertFalse(s.find_all(['script','nav']));self.assertEqual(len(s.select('.content a[href]')),1)
            for p in folder.glob('*.css'):check_css(p,allowed)
    def test_repeated_directions_and_properties_preserved(self):
        text=self.plan['asset_reviews'][ORIGIN+'puzzle/blazing_trails/images/blazing_trails.pdf']['text'][0];self.assertEqual(sum(line.strip().startswith('8W.') for line in text.splitlines()),2);self.assertIn('exactly two entries',text)
        pages=self.plan['asset_reviews'][ORIGIN+'puzzle/lost_skull/images/LostSkull.pdf']['text'];self.assertEqual(len(pages),3)
        for n,text in enumerate(pages,1):self.assertIn(f'Lost Skull (page {n} of 3)',text)
        self.assertIn('LETTER',pages[1]);self.assertIn('THUNDER',pages[2]);self.assertGreater(pages[0].count('is a word after removing'),1)
    def test_visual_limitations_precise(self):
        rows={int(u['after']['problem_id'][-5:]):u['after'] for u in self.plan['updates']};self.assertIn('blank/shaded answer-cell page',rows[2185]['asset_policy']);self.assertIn('No colored marks are invented',rows[2146]['asset_policy']);self.assertTrue(all(not r['source_review']['font_binary_historical_version_certified'] for r in rows.values()))
    def test_scores_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for key in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][key],u['after'][key])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])


if __name__=='__main__':unittest.main()
