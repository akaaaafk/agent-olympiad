import unittest
from scripts.repair_mystery_2003_static_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,check_html


class Mystery2003StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')

    def test_nine_selected_records(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(len(SELECTED),9)

    def test_source_bytes_preserved_except_reviewed_archive_edits(self):
        for u in self.plan['updates']:
            expected=sanitize((ROOT/u['before']['source_file']).read_bytes())[0]
            self.assertEqual((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),expected)

    def test_only_local_media_links_remain(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';s=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
            for a in s.find_all('a'):self.assertTrue(a['href'].endswith('.jpg'))
            self.assertFalse(s.find_all(['script','form','iframe']))

    def test_original_review_and_limitations_preserved(self):
        for u in self.plan['updates']:
            for k,v in (u['before'].get('source_review') or {}).items():self.assertEqual(u['after']['source_review'][k],v)
            self.assertIn(u['before']['evaluation']['limitations'],u['after']['evaluation']['limitations'])

    def test_answer_variants_remain_distinct_and_not_in_prompt(self):
        rows={u['after']['problem_id']:u['after'] for u in self.plan['updates']}
        a,b=rows['mystery_hunt_00408'],rows['mystery_hunt_00409']
        self.assertNotEqual(a['gold_label'],b['gold_label'])
        self.assertEqual(a['answer_group_id'],b['answer_group_id'])
        self.assertNotEqual(a['answer_variant'],b['answer_variant'])
        self.assertEqual(a['problem_description'],b['problem_description'])

    def test_full_size_paper_and_all_maps_present(self):
        folder=ROOT/CACHE/'mystery_hunt_00412/input'
        for color in ('red','orange','yellow','green','blue','purple'):
            self.assertTrue((folder/f'folderol-{color}.jpg').is_file())
            self.assertTrue((folder/f'folderol-{color}-small.jpg').is_file())
        maps=ROOT/CACHE/'mystery_hunt_00457/input'
        self.assertEqual(len(list(maps.glob('cartography-*.jpg'))),26)

    def test_gold_score_and_status_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title','answer_variant','answer_group_id'):
                self.assertEqual(u['before'].get(k),u['after'].get(k))
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')

    def test_prepared_hashes(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])


if __name__=='__main__':unittest.main()
