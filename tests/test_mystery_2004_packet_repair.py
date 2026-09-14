import unittest
from scripts.repair_mystery_2004_packets_20260913 import ROOT,CACHE,SELECTED,PAGES,read,sha,sanitize_root,check_html,check_css

class Mystery2004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_two_records_fifteen_pages(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(sum(c['destination'].endswith('.html') for c in self.plan['copies']),15)
    def test_complete_local_packets(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';allowed={p.resolve() for p in folder.iterdir()}
            for p in folder.glob('*.html'):check_html(p,allowed)
            for p in folder.glob('*.css'):check_css(p,allowed)
            for name in PAGES[int(pid[-5:])]:self.assertTrue((folder/name).is_file())
    def test_root_restored_not_single_subpage(self):
        for u in self.plan['updates']:
            self.assertTrue(u['after']['source_file'].endswith('/puzzle.html'))
            self.assertNotEqual(u['before']['source_file'],u['after']['source_file'])
    def test_only_exact_answer_page_excluded(self):
        for pid in SELECTED:
            self.assertFalse((ROOT/CACHE/pid/'input/answer.html').exists())
        path=ROOT/CACHE/'mystery_hunt_00586/input/_answer.html'
        self.assertIn('Iron Maiden',path.read_text(encoding='ascii'))
    def test_source_payloads_preserved(self):
        for pid,mapping in self.plan['source_map'].items():
            for name,url in mapping.items():
                data=(ROOT/self.plan['publisher_snapshots'][url]['path']).read_bytes()
                if name=='puzzle.html':data=sanitize_root(data)[0]
                self.assertEqual((ROOT/CACHE/pid/'input'/name).read_bytes(),data)
    def test_gold_score_status_and_originals_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')
            self.assertEqual(sha(ROOT/u['before']['source_file']),u['after']['source_review']['original_sha256'])
    def test_prepared_hashes(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])

if __name__=='__main__':unittest.main()
