import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2010_media_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,localize,flv_structure,check_html,check_css


class Mystery2010MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html_and_main_content(self):
        for u in self.plan['updates']:
            row=u['after'];n=int(row['problem_id'][-5:]);data=(ROOT/u['before']['source_file']).read_bytes();expected,name=sanitize(data,n);expected,_=localize(expected,row['source_url']);folder=ROOT/CACHE/row['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),expected)
            a=BeautifulSoup(data,'html.parser');b=BeautifulSoup(expected,'html.parser')
            for img in a.find_all('img'):img['src']=img['src'].split('/')[-1]
            self.assertIsNotNone(a.find(id='main'));self.assertEqual(str(a.find(id='main')),str(b.find(id='main')));allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed);check_css(folder/name,allowed)
    def test_video_link_order(self):
        for n,prefix,count in [(1286,'dr_oxs_experiment',8),(1372,'obligatory_dance_video',14)]:
            s=BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser');self.assertEqual([a['href'] for a in s.find_all('a')],[f'{prefix}_{i:02}.flv' for i in range(1,count+1)])
    def test_pdf_and_video_counts(self):
        media=[(k,v) for u in self.plan['updates'] for k,v in u['after']['source_review']['media_structure'].items()];self.assertEqual(len(media),23);self.assertEqual(sum(v.get('pages',0) for k,v in media),2)
        for k,v in media:
            if k.endswith('.flv'):self.assertFalse(v['decoded']);self.assertFalse(v['watched']);self.assertEqual(v['source_flags_hex'],'0d')
    def test_structure_and_truncation(self):
        for u in self.plan['updates']:
            r=u['after']
            for name,expected in r['source_review']['media_structure'].items():
                if not name.endswith('.flv'):continue
                data=(ROOT/CACHE/r['problem_id']/'input'/name).read_bytes();self.assertEqual(flv_structure(data),expected)
                with self.assertRaises(ValueError):flv_structure(data[:-1])
    def test_byte_identity(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_no_player_execution(self):
        for pid in SELECTED:self.assertFalse(BeautifulSoup((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),'html.parser').find_all(['script','form','object','embed','iframe']))
    def test_scores_and_status_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])


if __name__=='__main__':unittest.main()
