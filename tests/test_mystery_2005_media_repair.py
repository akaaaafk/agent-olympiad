import unittest
import pymupdf as fitz
from scripts.repair_mystery_2005_media_20260913 import ROOT,CACHE,SELECTED,FILES,read,sha,check_html,initial_html,audio_structure

class Mystery2005MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_records_and_files(self):self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),9)
    def test_exact_source_edits_and_packaged_links(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id'];folder=ROOT/CACHE/pid/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),initial_html((ROOT/u['before']['source_file']).read_bytes(),int(pid[-5:]))[0]);check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
    def test_performer_script_not_initial_input(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('00612'));t=(ROOT/CACHE/'mystery_hunt_00612/input/puzzle.html').read_text(encoding='ascii')
        for s in ('CASTING:','NIGHTCLUB MEDLEY','EMCEE (Greg?)','As Hunters enter'):
            self.assertNotIn(s,t);self.assertNotIn(s,u['after']['problem_description']);self.assertIn(s,u['after']['source_review']['deferred_performer_section'])
        for s in ('FRIDAY NIGHT AT 2 AM','no more than two team','A to M, provide a beverage.'):self.assertIn(s,t)
    def test_four_pdf_pages_and_original_hashes(self):
        self.assertEqual(sum(p['pages'] for p in self.plan['pdf_inventory']),4)
        for p in self.plan['pdf_inventory']:
            path=ROOT/CACHE/p['problem_id']/'input'/p['name'];self.assertEqual(sha(path),p['sha256'])
            with fitz.open(path) as d:self.assertEqual(len(d),p['pages']);self.assertFalse(d.is_encrypted)
    def test_original_audio_frame_and_metadata_prefix(self):
        p=ROOT/CACHE/'mystery_hunt_00605/input/axtogrind.mp3';r=audio_structure(p);self.assertEqual(r['frames'],7516);self.assertEqual(r['zero_padding_bytes'],417);self.assertFalse(r['decoded']);self.assertFalse(r['content_listened']);self.assertTrue(r['original_prefix_preserved'])
    def test_gold_scores_status_and_legacy_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready');self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_copy_hashes_and_no_film_invention(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('00628'));self.assertIn('film itself',u['after']['evaluation']['limitations']);self.assertEqual(FILES[628],['lscpuzzle.pdf'])

if __name__=='__main__':unittest.main()
