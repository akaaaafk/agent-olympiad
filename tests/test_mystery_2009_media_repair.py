import unittest
from pathlib import Path
from types import SimpleNamespace
from bs4 import BeautifulSoup
import pymupdf as fitz
from scripts.repair_mystery_2009_media_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,localize,audio_structure,flv_structure,check_html,check_css


class Mystery2009MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),101)
    def test_exact_html_and_content(self):
        for u in self.plan['updates']:
            row=u['after'];data=(ROOT/u['before']['source_file']).read_bytes();expected,_=localize(sanitize(data,row['problem_id']),row['source_url']);folder=ROOT/CACHE/row['problem_id']/'input'
            self.assertEqual((folder/'puzzle.html').read_bytes(),expected)
            a=BeautifulSoup(data,'html.parser');b=BeautifulSoup(expected,'html.parser')
            for el in a.find_all('img'):el['src']=Path(el['src']).name
            self.assertIsNotNone(a.find(id='content'));self.assertEqual(str(a.find(id='content')),str(b.find(id='content')))
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
    def test_audio_and_link_order(self):
        counts={1099:32,1110:1,1124:10,1173:3};total=0
        for u in self.plan['updates']:
            row=u['after'];folder=ROOT/CACHE/row['problem_id']/'input';media=row['source_review']['media_review'];n=int(row['problem_id'][-5:]);files=[p for p in folder.iterdir() if p.suffix in ('.mp3','.wav')]
            self.assertEqual(len(files),counts.get(n,0));total+=len(files)
            for p in files:self.assertEqual(audio_structure(p),media[p.name]);self.assertFalse(media[p.name]['content_listened'])
            a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').find(id='content');b=BeautifulSoup((folder/'puzzle.html').read_bytes(),'html.parser').find(id='content')
            self.assertEqual([x['href'] for x in a.find_all('a')],[x['href'] for x in b.find_all('a')])
        self.assertEqual(total,46)
    def test_pdf_character_sheets_and_cards(self):
        expected={'Escape_from_Zyzzlvaria_RPG.pdf':7,'Cards.pdf':4,'NumberCards.pdf':1};found={}
        for pid in SELECTED:
            for p in (ROOT/CACHE/pid/'input').glob('*.pdf'):
                with fitz.open(p) as doc:found[p.name]=len(doc)
        self.assertEqual(found,expected)
    def test_full_flv_tag_chain_without_execution(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('01226'));path=ROOT/CACHE/row['problem_id']/'input/puzzle.flv';r=flv_structure(path)
        self.assertEqual(r,row['source_review']['media_review']['puzzle.flv']);self.assertEqual(r['metadata']['width'],640);self.assertEqual(r['metadata']['height'],480);self.assertEqual(r['last_timestamp_ms'],411320);self.assertFalse(r['content_watched'])
        data=path.read_bytes()
        with self.assertRaises(ValueError):flv_structure(SimpleNamespace(read_bytes=lambda:data[:-1]))
    def test_sources_and_every_asset_hash(self):
        for u in self.plan['updates']:
            row=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),row['source_review']['original_sha256'])
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/row['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_metadata_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
    def test_no_program_or_inferred_phase_added(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';s=BeautifulSoup((folder/'puzzle.html').read_bytes(),'html.parser');self.assertFalse(s.find_all(['script','form','iframe','object','embed']));self.assertFalse(s.select('#header a'));self.assertFalse([p for p in folder.iterdir() if p.suffix in ('.swf','.js','.exe')])
        s=BeautifulSoup((ROOT/CACHE/'mystery_hunt_01173/input/puzzle.html').read_bytes(),'html.parser');self.assertEqual([a['href'] for a in s.find_all('a')],['Keith-MoonFF0000.wav','Keith-Moon00FF00.wav','Keith-Moon0000FF.wav'])


if __name__=='__main__':unittest.main()
