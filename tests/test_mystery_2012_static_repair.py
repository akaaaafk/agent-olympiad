import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import ImageFont
from scripts.repair_mystery_2012_static_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,localize,css_graph,check_html,check_css


class Mystery2012StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input/puzzle.html').read_bytes(),'html.parser')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html_and_main(self):
        for u in self.plan['updates']:
            r=u['after'];data=(ROOT/u['before']['source_file']).read_bytes();expected,_=sanitize(data,r['source_url']);expected,_=localize(expected,r['source_url']);self.assertEqual((ROOT/CACHE/r['problem_id']/'input/puzzle.html').read_bytes(),expected)
            old=BeautifulSoup(data,'html.parser').find(id='main');new=BeautifulSoup(expected,'html.parser').find(id='main');self.assertIsNotNone(old)
            for el in old.find_all('a',href=True):
                if el['href']=='../..':el['data-archive-href']=el['href'];del el['href']
                else:el['href']=Path(el['href']).name
            for el in old.find_all('img'):el['src']=Path(el['src']).name
            self.assertEqual(str(old),str(new))
    def test_stylesheet_cascade_and_dependencies(self):
        for u in self.plan['updates']:
            r=u['after'];rev=r['source_review'];folder=ROOT/CACHE/r['problem_id']/'input';styles,deps,urls=css_graph(rev['stylesheet_urls'],dict(self.plan['publisher_snapshots']));self.assertEqual(urls,rev['all_stylesheet_urls']);self.assertEqual([l['href'] for l in self.soup(int(r['problem_id'][-5:])).find_all('link')],list(rev['stylesheet_urls']))
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name,data in styles.items():self.assertEqual((folder/name).read_bytes(),data);check_css(folder/name,allowed)
            for name,url in deps.items():self.assertEqual(rev['dependency_urls'][name],url)
    def test_asset_byte_identity(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_unicode_blanks_and_strings(self):
        s=self.soup(1591);self.assertIn('とき',s.get_text());self.assertIn('νοτα βενε',s.get_text());self.assertGreater(len(s.find_all('u')),10)
        self.assertEqual(self.soup(1645).find(id='doo-strings').get_text(' ',strip=True),'AABEHIPTZ EROMEVEHLAHPBASEEWINHEELRE EUGCHATERAPRIEINDIE GRSHTERVER ISCASYMOLSWIHCVEANSAIHSEMENS LMRSVVW NCORIFHTSUJPEK OLASOULLRS OMIEVEYFOTHYML RMHRRSHRHYMWHHWRKY WSPAEHCRIFOLT')
        self.assertEqual(self.soup(1645).find(id='doo-numbers').get_text(strip=True),'34, 7, 11, 13, 15, 33, 13, 6, 16, 9, 18')
    def test_full_size_links_and_image_order(self):
        self.assertEqual([a['href'] for a in self.soup(1640).find_all('a',href=True)],[f'{i}.jpg' for i in range(1,13)])
        self.assertEqual([i['src'] for i in self.soup(1647).find_all('img')],[f'{i}.png' for i in (0,1,6,2,7,3,8,4,9,5,10,11,12,13,14)])
        self.assertEqual([i['src'] for i in self.soup(1651).find_all('img')],[f'{i}_400.jpg' for i in range(1,12)])
        self.assertEqual([a['href'] for a in self.soup(1603).find_all('a',href=True)],['1.jpg','2.jpg','3.jpg'])
    def test_variants_not_merged(self):
        rows=[u['after'] for u in self.plan['updates'] if u['after']['problem_id'][-5:] in ('01666','01667')];self.assertEqual(len(rows),2);self.assertNotEqual(rows[0]['gold_label'],rows[1]['gold_label']);self.assertEqual(str(self.soup(1666)),str(self.soup(1667)))
    def test_font_provenance_and_licenses(self):
        families=set()
        for u in self.plan['updates']:
            r=u['after'];self.assertFalse(r['source_review']['font_binary_historical_version_certified']);folder=ROOT/CACHE/r['problem_id']/'input'
            for name,url in r['source_review']['dependency_urls'].items():
                if name.endswith('.ttf'):families.add(ImageFont.truetype(str(folder/name),16).getname()[0])
                if name.endswith('-OFL.txt'):self.assertIn('SIL OPEN FONT LICENSE',(folder/name).read_text(encoding='utf-8'))
        self.assertEqual(families,{'Alice','Inconsolata','Abril Fatface','Buenard','Coustard','Nothing You Could Do'})
    def test_scores_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
    def test_active_content_rejected(self):
        for u in self.plan['updates']:
            r=u['after'];s=self.soup(int(r['problem_id'][-5:]));self.assertFalse(s.find_all(['script','iframe','form','object','embed']));self.assertTrue(s.find_all('a',attrs={'data-archive-href':True}))
            data=(ROOT/u['before']['source_file']).read_bytes()
            with self.assertRaises(ValueError):sanitize(data.replace(b'/checkanswer.js',b'/unexpected.js'),r['source_url'])


if __name__=='__main__':unittest.main()
