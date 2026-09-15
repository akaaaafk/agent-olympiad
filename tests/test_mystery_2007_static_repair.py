import unittest
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2007_static_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,check_html,check_css,SYMBOLS,CSS_URL,CSS_IMAGES,SPIRAL_HASHES,local_css


class Mystery2007StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection_and_files(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),131)
    def test_exact_html_and_local_dependencies(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),sanitize((ROOT/u['before']['source_file']).read_bytes()))
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
    def test_story_and_content_preserved(self):
        for u in self.plan['updates']:
            a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');b=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser')
            for im in a.find_all('img'):
                for name in SYMBOLS:
                    if im['src']=='../../images/'+name:im['src']=name
            for key in ('story-text','content'):
                self.assertIsNotNone(a.find(id=key));self.assertEqual(str(a.find(id=key)),str(b.find(id=key)))
    def test_all_original_symbols_kept(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_00887')
        before=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');after=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser')
        self.assertEqual([str(p).replace('../../images/','') for p in before.select('p.symbols')],[str(p) for p in after.select('p.symbols')])
        self.assertEqual(len(after.find_all('img')),173)
    def test_styles_follow_verified_official_redirects(self):
        for old,new in CSS_IMAGES.items():
            self.assertEqual(self.plan['publisher_snapshots'][old]['final_url'],new);self.assertEqual(self.plan['publisher_snapshots'][old]['sha256'],self.plan['publisher_snapshots'][new]['sha256'])
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';self.assertEqual((folder/'puzzle.css').read_bytes(),local_css((ROOT/self.plan['publisher_snapshots'][CSS_URL+'puzzle.css']['path']).read_bytes()))
            self.assertEqual(sha(folder/'print.css'),self.plan['publisher_snapshots'][CSS_URL+'print.css']['sha256'])
    def test_spiral_filename_collision_repaired_recoverably(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_00930');c=row['source_review']['legacy_image_conflicts'][0]
        old=ROOT/c['path'];new=ROOT/CACHE/row['problem_id']/'input/spiral.png';self.assertEqual((sha(old),sha(new)),SPIRAL_HASHES)
        with Image.open(old) as im:self.assertEqual(im.size,(472,419))
        with Image.open(new) as im:self.assertEqual(im.size,(1798,1867))
        self.assertEqual(next(a for a in row['assets'] if a['path']==c['path'])['role'],'judge_only')
    def test_publisher_bytes_and_sources(self):
        for u in self.plan['updates']:
            row=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),row['source_review']['original_sha256'])
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/row['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_metadata_and_no_interpretive_hint_added_to_prompt(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
            self.assertNotIn('counterfactual',u['after']['problem_description'])


if __name__=='__main__':unittest.main()
