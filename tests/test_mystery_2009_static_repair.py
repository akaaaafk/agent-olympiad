import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2009_static_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,styles,localize,CSS_URL,check_html,check_css


class Mystery2009StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_exact_selection(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),252)
    def test_html_and_content_preserved(self):
        for u in self.plan['updates']:
            row=u['after'];data=(ROOT/u['before']['source_file']).read_bytes();expected,_=localize(sanitize(data),row['source_url']);folder=ROOT/CACHE/row['problem_id']/'input'
            self.assertEqual((folder/'puzzle.html').read_bytes(),expected)
            a=BeautifulSoup(data,'html.parser');b=BeautifulSoup(expected,'html.parser')
            for im in a.find_all('img'):im['src']=Path(im['src']).name
            for im in a.find_all('a'):im['href']=Path(im['href']).name
            self.assertIsNotNone(a.find(id='content'));self.assertEqual(str(a.find(id='content')),str(b.find(id='content')))
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
    def test_all_groups_and_fullsize_links(self):
        counts={1150:(31,31,33),1151:(1,0,0),1152:(1,1,0),1180:(410,373,0),1189:(18,17,0),1206:(69,0,0)}
        for n,(imgs,links,cells) in counts.items():
            s=BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser').find(id='content')
            self.assertEqual((len(s.find_all('img')),len(s.find_all('a')),len(s.find_all('td'))),(imgs,links,cells))
        s=BeautifulSoup((ROOT/CACHE/'mystery_hunt_01180/input/puzzle.html').read_bytes(),'html.parser');self.assertEqual(len(s.find_all('li')),36)
    def test_css_only_omits_unmatched_image_rules(self):
        snapshots=self.plan['publisher_snapshots'];main=(ROOT/snapshots[CSS_URL+'puzzle.css']['path']).read_bytes();images=(ROOT/snapshots[CSS_URL+'puzzle-page-images.css']['path']).read_bytes()
        for u in self.plan['updates']:
            row=u['after'];folder=ROOT/CACHE/row['problem_id']/'input';html=sanitize((ROOT/u['before']['source_file']).read_bytes());expected,_,review=styles(main,images,html)
            self.assertEqual((folder/'puzzle.css').read_bytes(),expected);self.assertEqual(row['source_review']['style_review'],review)
            self.assertEqual(len(review['retained_image_selectors']),int(row['problem_id']!='mystery_hunt_01189'))
            s=BeautifulSoup(html,'html.parser')
            for selector in review['omitted_unmatched_image_selectors']:self.assertEqual(s.select(selector),[])
            self.assertEqual(sha(folder/'print.css'),snapshots[CSS_URL+'print.css']['sha256'])
    def test_all_downloaded_bytes_and_originals(self):
        for u in self.plan['updates']:
            row=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),row['source_review']['original_sha256'])
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/row['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_no_answer_links_or_executable_tags(self):
        for pid in SELECTED:
            s=BeautifulSoup((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),'html.parser');self.assertFalse(s.find_all(['script','form','iframe','object','embed']))
            self.assertFalse(s.select('#header a'))
            for a in s.find_all('a'):self.assertIn(Path(a['href']).suffix,('.png','.jpg','.gif'))
    def test_gold_scores_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
    def test_unreviewed_extra_source_script_rejected(self):
        source=ROOT/self.plan['updates'][0]['before']['source_file']
        with self.assertRaises(Exception):sanitize(source.read_bytes()+b'<script type="module" src="/checkanswer.js"></script>')


if __name__=='__main__':unittest.main()
