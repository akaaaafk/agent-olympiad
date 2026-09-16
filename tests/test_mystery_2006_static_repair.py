import unittest
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2006_static_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,css_packet,check_html,check_css


class Mystery2006StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection_and_file_count(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(len(self.plan['copies']),139)
    def test_bounded_html_edits(self):
        for u in self.plan['updates']:
            self.assertEqual((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),sanitize((ROOT/u['before']['source_file']).read_bytes())[0])
    def test_complete_local_dependencies(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';allowed={p.resolve() for p in folder.iterdir()}
            check_html(folder/'puzzle.html',allowed);check_css(folder/'puzzle.css',allowed)
    def test_puzzle_body_preserved(self):
        for u in self.plan['updates']:
            a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes().replace(b'src="../shadow.jpg"',b'src="shadow.jpg"'),'html.parser')
            b=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser')
            self.assertIsNotNone(a.find(id='puzzlebody'))
            self.assertEqual(str(a.find(id='puzzlebody')),str(b.find(id='puzzlebody')))
    def test_city_styles_and_opaque_header(self):
        for u in self.plan['updates']:
            row=u['after'];folder=ROOT/CACHE/row['problem_id']/'input'
            self.assertEqual((folder/'puzzle.css').read_bytes(),css_packet((ROOT/row['source_review']['stylesheet_publisher']['path']).read_bytes())[0])
            if '/washington/' in row['source_url']:
                with Image.open(folder/'header.jpg') as im:self.assertEqual((im.size,im.mode),((615,240),'RGB'))
                self.assertNotIn(b'url(header.jpg)',(folder/'puzzle.css').read_bytes())
    def test_photograph_links_and_legality_warning(self):
        folder=ROOT/CACHE/'mystery_hunt_00843/input';soup=BeautifulSoup((folder/'puzzle.html').read_bytes(),'html.parser')
        self.assertEqual({a['href'] for a in soup.find_all('a')},{f'image{i:02}.jpg' for i in range(1,29)})
        self.assertIn('Please do not break any laws',soup.get_text())
        self.assertEqual(soup.find(id='nav').get_text(),'')
    def test_same_byte_media_and_source_hashes(self):
        for u in self.plan['updates']:
            row=u['after'];folder=ROOT/CACHE/row['problem_id']/'input'
            self.assertEqual(sha(ROOT/u['before']['source_file']),row['source_review']['original_sha256'])
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(folder/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_metadata_and_unreproduced_interaction(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_00805')
        self.assertIn('not reproduced',row['evaluation']['limitations'])


if __name__=='__main__':unittest.main()
