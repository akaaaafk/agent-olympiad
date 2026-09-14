import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2008_dossier_20260913 import ROOT,CACHE,read,sha,sanitize,local_css,CSS_URL,LABEL_LINKS,check_html,check_css


class Mystery2008DossierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/'plan.json');cls.u=cls.plan['updates'][0];cls.row=cls.u['after'];cls.folder=ROOT/CACHE/cls.row['problem_id']/'input'
    def test_selection_and_files(self):
        self.assertEqual(len(self.plan['updates']),1);self.assertEqual(self.row['problem_id'],'mystery_hunt_00994');self.assertEqual(len(self.plan['copies']),11)
    def test_exact_bounded_html(self):
        self.assertEqual((self.folder/'puzzle.html').read_bytes(),sanitize((ROOT/self.u['before']['source_file']).read_bytes())[0])
    def test_post_meta_narrative_withheld(self):
        data=(self.folder/'puzzle.html').read_text();late=self.row['source_review']['deferred_post_meta_section']
        for text in ('meta had been solved','vintage Jaguar E-Series','West Garage'):
            self.assertNotIn(text,data);self.assertNotIn(text,self.row['problem_description']);self.assertIn(text,late)
    def test_initial_paragraphs_and_labels_kept(self):
        before=BeautifulSoup((ROOT/self.u['before']['source_file']).read_bytes(),'html.parser');after=BeautifulSoup((self.folder/'puzzle.html').read_bytes(),'html.parser')
        self.assertEqual([str(p) for p in before.select('td.dossier2 > p')[:2]],[str(p) for p in after.select('td.dossier2 > p')[:2]])
        self.assertEqual([a.get_text() for a in before.find_all('a') if a['href'] in LABEL_LINKS],[a.get_text() for a in after.select('.archive-puzzle-label')]);self.assertEqual(len(after.select('.archive-puzzle-label')),11);self.assertFalse(after.find_all('a'))
    def test_unused_style_rules_only_and_guard(self):
        css=(ROOT/self.plan['publisher_snapshots'][CSS_URL]['path']).read_bytes();html=(self.folder/'puzzle.html').read_bytes()
        self.assertEqual((self.folder/'mydossier.css').read_bytes(),local_css(css,html)[0]);self.assertEqual(len(self.row['source_review']['unused_css_rules_removed']),14)
        with self.assertRaises(ValueError):local_css(css,html+b'<div class="dossier1"></div>')
    def test_every_dependency_local_no_active_scripts(self):
        allowed={p.resolve() for p in self.folder.iterdir()};s=check_html(self.folder/'puzzle.html',allowed);check_css(self.folder/'mydossier.css',allowed);self.assertFalse(s.find_all('script'))
    def test_original_image_and_copy_hashes(self):
        for name,url in self.row['source_review']['dependency_urls'].items():self.assertEqual(sha(self.folder/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_gold_scores_metadata_and_original_preserved(self):
        for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(self.u['before'][k],self.row[k])
        self.assertEqual(self.u['before']['evaluation']['status'],self.row['evaluation']['status']);self.assertEqual(sha(ROOT/self.u['before']['source_file']),self.row['source_review']['original_sha256'])


if __name__=='__main__':unittest.main()
