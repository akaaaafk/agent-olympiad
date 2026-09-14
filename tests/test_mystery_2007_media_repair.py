import unittest
from bs4 import BeautifulSoup
import pymupdf as fitz
from scripts.repair_mystery_2007_media_20260913 import ROOT,CACHE,SELECTED,DEFERRED,read,sha,initial_html,audio_structure,check_html,check_css,writer,HANDOUT


class Mystery2007MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection_and_visibility_counts(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(writer().copy_role_counts(self.plan),{'agent_visible':40,'judge_only':2})
    def test_bounded_source_edits_and_dependencies(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id'];folder=ROOT/CACHE/pid/'input';self.assertEqual((folder/'puzzle.html').read_bytes(),initial_html((ROOT/u['before']['source_file']).read_bytes(),int(pid[-5:]))[0])
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for name in ('puzzle.css','print.css'):check_css(folder/name,allowed)
    def test_later_handouts_not_initial(self):
        for n,name in DEFERRED.items():
            pid=f'mystery_hunt_{n:05}';row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id']==pid);folder=ROOT/CACHE/pid/'input'
            self.assertNotIn(name,(folder/'puzzle.html').read_text());self.assertNotIn(name,row['problem_description']);self.assertFalse((folder/name).exists())
            self.assertIn(name,row['source_review']['deferred_section']);self.assertEqual(next(a for a in row['assets'] if a['path'].endswith('/'+name))['role'],'judge_only')
    def test_photos_and_internal_scoring_not_confused_with_gold_score(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_00868')
        soup=BeautifulSoup((ROOT/CACHE/row['problem_id']/'input/puzzle.html').read_bytes(),'html.parser')
        self.assertEqual({i['src'] for i in soup.find_all('img')},{f'image-{i}.jpg' for i in range(10)})
        r=row['source_review']['photo_challenge_rubric'];self.assertEqual((r['photos'],len(r['categories']),r['base_maximum'],r['pass_threshold']),(10,5,100,75));self.assertTrue(r['not_the_canonical_answer_score']);self.assertIsNone(row['total_points'])
    def test_original_audio_wrappers_and_frames(self):
        r=audio_structure(ROOT/CACHE/'mystery_hunt_00896/input/playlist.mp3')
        self.assertEqual((r['id3v2_bytes'],r['id3v1_bytes'],r['frames']),(4096,128,375));self.assertFalse(r['decoded']);self.assertFalse(r['content_listened']);self.assertTrue(r['original_wrappers_preserved'])
    def test_pdf_pages_and_roles(self):
        self.assertEqual(sum(p['pages'] for p in self.plan['pdf_inventory']),11)
        self.assertEqual(sum(p['pages'] for p in self.plan['pdf_inventory'] if p['role']=='agent_visible'),9)
        for p in self.plan['pdf_inventory']:
            path=ROOT/CACHE/p['problem_id']/('input' if p['role']=='agent_visible' else 'judge')/p['name'];self.assertEqual(sha(path),p['sha256'])
            with fitz.open(path) as d:self.assertEqual(len(d),p['pages']);self.assertFalse(d.is_encrypted)
    def test_originals_metadata_and_status_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status']);self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_handout_index_association_and_copy_hashes(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_00916')
        entry=BeautifulSoup(row['source_review']['handout_index_entry'],'html.parser');self.assertEqual([a['href'] for a in entry.find_all('a')],['../handouts/Hell4Handout.pdf','man_i_hate_these_sudokus'])
        self.assertEqual(row['source_review']['dependency_urls']['Hell4Handout.pdf'],HANDOUT)
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])


if __name__=='__main__':unittest.main()
