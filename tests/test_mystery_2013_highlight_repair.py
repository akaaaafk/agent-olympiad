import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2013_highlight_20260913 import ROOT,CACHE,PID,PAGE,CUE,read,sha,cues_and_sanitize,make_vtt,localize_css,localize_inline,compile_less,check_html,check_css,video_review


class Mystery2013HighlightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.row=cls.plan['updates'][0]['after'];cls.old=cls.plan['updates'][0]['before'];cls.folder=ROOT/CACHE/PID/'input'
    def test_selection_and_title(self):
        self.assertEqual([u['after']['problem_id'] for u in self.plan['updates']],[PID]);self.assertEqual(self.row['problem_description'].splitlines()[0],'# Highlight Reel')
    def test_all_original_captions_and_times(self):
        data=(ROOT/self.old['source_file']).read_bytes();cues=[dict(start=int(m[1]),end=int(m[2]),text=m[3].decode()) for m in CUE.finditer(data)];self.assertEqual(len(cues),26);self.assertEqual(cues,self.row['source_review']['captions']);self.assertEqual((self.folder/'captions.vtt').read_bytes(),make_vtt(cues));self.assertEqual(cues[-1]['end'],319)
    def test_exact_sanitized_html_and_styles(self):
        payload,styles,_=cues_and_sanitize((ROOT/self.old['source_file']).read_bytes());deps={}
        for name,target in styles.items():
            data=(ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes()
            if target.endswith('.less'):data=compile_less(data)
            self.assertEqual((self.folder/name).read_bytes(),localize_css(data,target,deps))
        self.assertEqual((self.folder/'puzzle.html').read_bytes(),localize_inline(payload,PAGE,deps))
    def test_original_video_and_asset_bytes(self):
        self.assertEqual(sha(ROOT/self.old['source_file']),self.row['source_review']['original_sha256'])
        for name,target in self.row['source_review']['dependency_urls'].items():self.assertEqual(sha(self.folder/name),self.plan['publisher_snapshots'][target]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_video_decode_without_equality_claim(self):
        reviews=self.row['source_review']['video_review']
        for name,expected in reviews.items():self.assertEqual(video_review(self.folder/name),expected);self.assertFalse(expected['transcoded']);self.assertFalse(expected['semantic_equivalence_between_formats_certified'])
        self.assertEqual([reviews[n]['streams'][0]['frames'] for n in ('video.mp4','video.webm')],[7857,7856]);self.assertTrue(all(r['container_duration_seconds']<319 for r in reviews.values()))
    def test_native_player_and_local_allowlist(self):
        allowed={p.resolve() for p in self.folder.iterdir()};s=check_html(self.folder/'puzzle.html',allowed);self.assertFalse(s.find_all('script'));self.assertFalse(s.find_all(class_='answer'));self.assertFalse(s.find(id='fixie-nav'));video=s.find('video');self.assertEqual(video.get('preload'),'none');self.assertFalse(video.has_attr('autoplay'));self.assertEqual([x['src'] for x in video.find_all('source')],['video.webm','video.mp4']);self.assertEqual(video.find('track')['src'],'captions.vtt')
        for p in self.folder.glob('*.css'):check_css(p,allowed)
    def test_unreviewed_caption_logic_rejected(self):
        data=(ROOT/self.old['source_file']).read_bytes()
        with self.assertRaises(ValueError):cues_and_sanitize(data.replace(b'var pop = Popcorn',b'fetch("https://unreviewed.invalid"); var pop = Popcorn'))
        self.assertEqual([r['http_status'] for r in self.plan['failed_video_paths']],[404,404])
    def test_scoring_and_membership_unchanged(self):
        for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(self.old[k],self.row[k])
        self.assertEqual(self.old['evaluation']['status'],self.row['evaluation']['status'])


if __name__=='__main__':unittest.main()
