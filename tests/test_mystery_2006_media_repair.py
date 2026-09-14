import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2006_media_20260913 import ROOT,CACHE,SELECTED,read,sha,initial_html,inspect_audio,check_html,check_css,writer


class Mystery2006MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_records_and_visibility_counts(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(writer().copy_role_counts(self.plan),{'agent_visible':15,'judge_only':1})
    def test_exact_edits_and_public_dependencies(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id'];folder=ROOT/CACHE/pid/'input';allowed={p.resolve() for p in folder.iterdir()}
            self.assertEqual((folder/'puzzle.html').read_bytes(),initial_html((ROOT/u['before']['source_file']).read_bytes(),int(pid[-5:]))[0])
            check_html(folder/'puzzle.html',allowed);check_css(folder/'puzzle.css',allowed)
    def test_fortunes_not_initial(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('00766'))
        folder=ROOT/CACHE/row['problem_id']/'input';data=(folder/'puzzle.html').read_bytes()
        self.assertNotIn(b'fortunes',data);self.assertNotIn('fortune',row['problem_description']);self.assertFalse((folder/'fortunes.png').exists())
        self.assertIn('after teams brought us food',row['source_review']['deferred_section'])
        a=next(a for a in row['assets'] if a['path'].endswith('/fortunes.png'));self.assertEqual(a['role'],'judge_only')
    def test_cooking_and_music_body_preserved(self):
        for u in self.plan['updates']:
            a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser').find(id='puzzlebody')
            b=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser').find(id='puzzlebody')
            self.assertIsNotNone(a);self.assertIsNotNone(b)
            if u['after']['problem_id'].endswith('00766'):self.assertEqual([str(p) for p in a.find_all('p')[:3]],[str(p) for p in b.find_all('p')])
            else:self.assertEqual(str(a),str(b))
    def test_five_distinct_complete_original_audio_files(self):
        folder=ROOT/CACHE/'mystery_hunt_00833/input';hashes=set()
        for i in range(1,6):
            path=folder/f'{i}.mp3';r=inspect_audio(path,'audio/mpeg');hashes.add(sha(path))
            self.assertEqual(r['frames'],2297);self.assertFalse(r['decoded']);self.assertFalse(r['content_listened'])
            self.assertEqual(path.stat().st_size,1440078)
        self.assertEqual(len(hashes),5)
    def test_downloaded_files_byte_preserved(self):
        for u in self.plan['updates']:
            row=u['after'];folder=ROOT/CACHE/row['problem_id']/'input'
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(folder/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_gold_score_readiness_and_originals_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
            self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_unlisted_copy_rejected(self):
        with self.assertRaises(ValueError):writer().copy_role_counts(dict(updates=[],copies=[{'destination':'unlisted'}]))


if __name__=='__main__':unittest.main()
