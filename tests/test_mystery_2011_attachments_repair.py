import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2011_attachments_20260913 import ROOT,CACHE,SELECTED,TEXT_SIZES,read,sha,sanitize,localize,check_html,check_css


class Mystery2011AttachmentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html_and_full_content(self):
        for u in self.plan['updates']:
            r=u['after'];data=(ROOT/u['before']['source_file']).read_bytes();expected,styles=sanitize(data,r['source_url']);expected,_=localize(expected,r['source_url']);folder=ROOT/CACHE/r['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),expected);a=BeautifulSoup(data,'html.parser');b=BeautifulSoup(expected,'html.parser')
            for t in a.find_all(['img','a']):attr='src' if t.name=='img' else 'href';t[attr]=Path(t[attr]).name
            self.assertIsNotNone(a.find(id='puzzlecontent'));self.assertEqual(str(a.find(id='puzzlecontent')),str(b.find(id='puzzlecontent')));allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name in styles:check_css(folder/name,allowed)
    def test_all_fragments_in_order(self):
        s=BeautifulSoup((ROOT/CACHE/'mystery_hunt_01395/input/puzzle.html').read_bytes(),'html.parser');self.assertEqual([a['href'] for a in s.find_all('a')],[f'{n:02}.txt' for n in range(1,19)])
    def test_opaque_text_not_rewritten_or_executed(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('01395'));self.assertEqual(len(row['source_review']['attachment_review']),18)
        for n,size in enumerate(TEXT_SIZES,1):
            p=ROOT/CACHE/f'mystery_hunt_01395/input/{n:02}.txt';self.assertEqual(p.stat().st_size,size);self.assertFalse(row['source_review']['attachment_review'][p.name]['executed'])
        self.assertTrue((ROOT/CACHE/'mystery_hunt_01395/input/17.txt').read_bytes().startswith(b'login'));self.assertIn(b'\r\n',(ROOT/CACHE/'mystery_hunt_01395/input/04.txt').read_bytes())
    def test_original_grid_pdf(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('01398'));self.assertEqual(row['source_review']['attachment_review']['grid.pdf']['pages'],1);self.assertTrue((ROOT/CACHE/'mystery_hunt_01398/input/grid.pdf').read_bytes().startswith(b'%PDF-'))
    def test_original_byte_identity(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_scores_and_status_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
    def test_no_active_controls(self):
        for pid in SELECTED:self.assertFalse(BeautifulSoup((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),'html.parser').find_all(['script','form','object','embed','iframe']))


if __name__=='__main__':unittest.main()
