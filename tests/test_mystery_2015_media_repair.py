import hashlib
from pathlib import Path
import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2015_media_20260913 import ROOT,CACHE,SELECTED,VIDEO_BASE,read,sha,localize_packet,localize_css,localize_inline,replace_ref,check_html,check_css,video_review


class Mystery2015MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def soup(self,n,name='puzzle.html'):return BeautifulSoup((ROOT/CACHE/f'mystery_hunt_{n:05}/input'/name).read_bytes(),'html.parser')
    def test_selection(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
    def test_exact_html_and_styles(self):
        for u in self.plan['updates']:
            r=u['after'];n=int(r['problem_id'][-5:]);folder=ROOT/CACHE/r['problem_id']/'input';payload,styles,deps=localize_packet((ROOT/u['before']['source_file']).read_bytes(),r['source_url'],n);cssdeps={}
            for name,target in r['source_review']['stylesheet_urls'].items():self.assertEqual((folder/name).read_bytes(),localize_css((ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes(),target,cssdeps))
            self.assertEqual((folder/'puzzle.html').read_bytes(),localize_inline(payload,r['source_url'],cssdeps))
    def test_coin_sides_counts_and_banner(self):
        s=self.soup(1997);self.assertEqual([i['src'] for i in s.select('.solution-table img')],[f'{n}{side}.jpg' for n in range(1,17) for side in ('front','back')]);counts=[int(tr.find_all('td')[-1].get_text()) for tr in s.select('.solution-table tr')[1:]];self.assertEqual(counts,[5,2,1,3,4,7,2,4,7,8,5,8,6,1,3,6]);self.assertEqual(sum(counts),72);self.assertEqual([a['href'] for a in s.find_all('a')],['clickbait.html','clickbait.html']);self.assertEqual(len(s.select('.clickbaitbannerbox')),1)
    def test_original_linked_article(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_01997');url=u['after']['source_review']['linked_article_url'];original=(ROOT/self.plan['publisher_snapshots'][url]['path']).read_bytes();s=BeautifulSoup(original,'html.parser');self.assertEqual((ROOT/CACHE/'mystery_hunt_01997/input/clickbait.html').read_bytes(),replace_ref(original,'href',s.link['href'],'clickbait.css'));self.assertEqual(len(self.soup(1997,'clickbait.html').find_all('li')),4)
    def test_asset_hashes(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,url in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_both_videos_decode_without_retiming(self):
        for ext in ('mp4','webm'):
            url=VIDEO_BASE+ext;actual=video_review(ROOT/self.plan['publisher_snapshots'][url]['path']);self.assertEqual(actual,self.plan['asset_reviews'][url]);self.assertTrue(91<actual['container_duration_seconds']<92);self.assertEqual(next(s['frames'] for s in actual['streams'] if s['type']=='video'),2192)
        s=self.soup(1994);self.assertNotIn('autoplay',s.video.attrs);self.assertEqual(s.video.get('preload'),'none');self.assertEqual([x['type'] for x in s.find_all('source')],['video/webm','video/mp4']);self.assertFalse(s.find_all('track'))
    def test_extensionless_attachment_preserved(self):
        p=ROOT/CACHE/'mystery_hunt_02037/input/image';self.assertEqual(p.stat().st_size,3542016);self.assertEqual(hashlib.md5(p.read_bytes()).hexdigest(),'f5ac27a1a43331d1e47662928028dc4a');self.assertEqual([a['href'] for a in self.soup(2037).find_all('a')],['image']);self.assertFalse((p.parent/'image-qa.png').exists())
    def test_static_assets_and_answer_isolation(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()}
            for p in folder.glob('*.html'):
                s=check_html(p,allowed);self.assertFalse(s.find_all(['script','nav']));self.assertFalse(s.select('.puzzle-page-header .answer, .puzzle-page-header .sol'))
            for p in folder.glob('*.css'):check_css(p,allowed)
    def test_clue_text_unchanged(self):
        for u in self.plan['updates']:
            old=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').select_one('.puzzle');new=self.soup(int(u['after']['problem_id'][-5:])).select_one('.puzzle');self.assertEqual(old.get_text().split(),new.get_text().split())
    def test_scores_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for key in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][key],u['after'][key])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])


if __name__=='__main__':unittest.main()
