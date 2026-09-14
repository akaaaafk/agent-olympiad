import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2012_media_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,localize,check_html,check_css,css_graph,audio_structure,ogg_structure


class Mystery2012MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html_and_styling(self):
        for u in self.plan['updates']:
            r=u['after'];n=int(r['problem_id'][-5:]);payload,styleurls=sanitize((ROOT/u['before']['source_file']).read_bytes(),r['source_url'],n);payload,_=localize(payload,r['source_url']);folder=ROOT/CACHE/r['problem_id']/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),payload);styles,_,urls=css_graph(styleurls,dict(self.plan['publisher_snapshots']));self.assertEqual(urls,r['source_review']['all_stylesheet_urls']);allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name,data in styles.items():self.assertEqual((folder/name).read_bytes(),data);check_css(folder/name,allowed)
    def test_original_bytes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_five_pdf_pages_and_grid_order(self):
        media=[(name,m) for u in self.plan['updates'] for name,m in u['after']['source_review']['media_structure'].items() if name.endswith('.pdf')];self.assertEqual(sorted((n,m['pages']) for n,m in media),[('1.pdf',4),('grid-lg.pdf',1)])
        self.assertEqual([i['src'] for i in self.soup(1585).find_all('img')],[f'{i}.png' for i in range(1,7)]);self.assertIn('MARQUEE',self.soup(1585).get_text());self.assertIn('no additional puzzle content',self.soup(1585).get_text())
    def test_equations_leading_zero_and_box_lengths(self):
        s=self.soup(1616);links=s.find_all('a',href=True);self.assertEqual([a['href'] for a in links],[f'{i}.mp3' for i in range(1,31)]);self.assertEqual(s.find('b').get_text(),'049981551/10016/89640/243599/8510719/89757/799');self.assertEqual([a.get_text().count('\u2610') for a in links],[5,5,5,4,5,5,5,4,5,5,5,4,5,5,4,5,5,5,5,5,5,5,5,5,5,4,5,4,5,5])
    def test_all_original_native_formats_no_autoload(self):
        s=self.soup(1618);players=s.find_all('audio');self.assertEqual(len(players),31)
        for i,p in enumerate(players,1):self.assertEqual([x['src'] for x in p.find_all('source')],[f'{i}.mp3',f'{i}.ogg']);self.assertEqual(p['preload'],'none');self.assertNotIn('autoplay',p.attrs)
        self.assertFalse(self.soup(1616).find_all(['audio','script']))
    def test_audio_boundaries_and_crc(self):
        count={'mp3':0,'ogg':0}
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input'
            for name,m in r['source_review']['media_structure'].items():
                if name.endswith('.mp3'):self.assertEqual(audio_structure(folder/name),m);count['mp3']+=1
                if name.endswith('.ogg'):self.assertEqual(ogg_structure((folder/name).read_bytes()),m);self.assertFalse(m['decoded']);count['ogg']+=1
        self.assertEqual(count,{'mp3':61,'ogg':31})
    def test_corrupt_ogg_rejected(self):
        data=(ROOT/CACHE/'mystery_hunt_01618/input/1.ogg').read_bytes()
        for damaged in (data[:-1],data[:-20],data[:100]+bytes([data[100]^1])+data[101:]):
            with self.assertRaises(ValueError):ogg_structure(damaged)
    def test_scores_readiness_and_licence_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status']);self.assertFalse(u['after']['source_review']['font_binary_historical_version_certified'])
    def test_navigation_and_scripts_not_active(self):
        for u in self.plan['updates']:
            s=self.soup(int(u['after']['problem_id'][-5:]));self.assertFalse(s.find_all(['script','iframe','object','embed','form']));self.assertEqual(len(s.find_all('a',attrs={'data-archive-href':True})),2)


if __name__=='__main__':unittest.main()
