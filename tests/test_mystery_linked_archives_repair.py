import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_linked_archives_20260913 import ROOT,CACHE,SELECTED,TABLE,VARIATIONS,read,sha,check_html,sanitize_table,sanitize_variations,inspect_audio

class LinkedArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selected_and_file_count(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),11)
    def test_every_html_has_only_packaged_active_links(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';allowed={p.resolve() for p in folder.iterdir()}
            for p in folder.glob('*.html'):check_html(p,allowed)
    def test_table_cells_and_historical_values_preserved(self):
        source=(ROOT/self.plan['publisher_snapshots'][TABLE]['path']).read_bytes();target=(ROOT/CACHE/'mystery_hunt_00177/input/table.html').read_bytes()
        self.assertEqual(target,sanitize_table(source)[0]);a=BeautifulSoup(source,'html.parser');b=BeautifulSoup(target,'html.parser')
        for x,y in zip(a.find_all('a'),b.find_all('a')):self.assertEqual(x['href'],y['data-archive-href']);self.assertFalse(y.has_attr('href'))
        self.assertEqual([t.get_text() for t in a.find_all('td')],[t.get_text() for t in b.find_all('td')]);self.assertIn('Um',b.get_text());self.assertIn('290.5',b.get_text())
        self.assertEqual([t.attrs for t in a.find_all(['td','tr','table'])],[t.attrs for t in b.find_all(['td','tr','table'])])
    def test_linked_puzzle_and_playback_warning(self):
        source=(ROOT/self.plan['publisher_snapshots'][VARIATIONS]['path']).read_bytes();target=(ROOT/CACHE/'mystery_hunt_00383/input/variations.html').read_bytes()
        self.assertEqual(target,sanitize_variations(source));self.assertIn(b'double speed',target)
        primary=(ROOT/CACHE/'mystery_hunt_00383/input/puzzle.html').read_bytes();self.assertIn(b'href="variations.html"',primary);self.assertNotIn(b'solutions/',primary)
    def test_audio_original_hashes_and_full_frame_validation(self):
        for name,mime in [('Puzzle.wav','audio/wav'),('Puzzle.mp3','audio/mpeg')]:
            p=ROOT/CACHE/'mystery_hunt_00383/input'/name;self.assertEqual(sha(p),self.plan['publisher_snapshots'][VARIATIONS.replace('Puzzle.html',name)]['sha256'])
            r=inspect_audio(p,mime);self.assertGreater(r['frames'],3000);self.assertFalse(r['content_listened'])
    def test_no_claim_of_release_schedule(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('00177'))
        self.assertIn('No release schedule is inferred',u['after']['source_review']['scope_note']);self.assertIn(b'Check that link periodically',(ROOT/CACHE/'mystery_hunt_00177/input/puzzle.html').read_bytes())
    def test_gold_score_status_and_originals_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready');self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_all_prepared_hashes(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])

if __name__=='__main__':unittest.main()
