import unittest
from scripts.repair_mystery_2002_packets_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,check_html


class Mystery2002PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')

    def test_seven_records_all_year_members(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(SELECTED,{r['problem_id'] for r in self.plan['before_rows'] if r['year']==2002})

    def test_source_text_layout_byte_preservation(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id'];original=(ROOT/u['before']['source_file']).read_bytes()
            self.assertEqual((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),sanitize(original)[0])

    def test_all_links_local_and_no_scripts(self):
        for pid in SELECTED:
            folder=ROOT/CACHE/pid/'input';s=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
            self.assertFalse(s.find_all(['script','a','form','iframe']))

    def test_sixteen_music_images_and_extraction_labels(self):
        folder=ROOT/CACHE/'mystery_hunt_00220/input'
        self.assertEqual(len(list(folder.glob('sheet*.gif'))),16)
        s=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
        self.assertIn('9th, 15th',s.get_text());self.assertIn('4th, 5th',s.get_text())

    def test_no_meta_answers_or_physical_observations_added(self):
        rows={int(u['after']['problem_id'][-5:]):u['after'] for u in self.plan['updates']}
        self.assertIn('not inserted into the initial packet',rows[226]['problem_description'])
        self.assertIn('historical physical planet displays',rows[196]['problem_description'])

    def test_gold_score_status_and_membership_unchanged(self):
        for u in self.plan['updates']:
            for key in ('gold_label','total_points','split','license','year','title','team_size'):
                self.assertEqual(u['before'][key],u['after'][key])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')

    def test_prepared_copies_match(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])


if __name__=='__main__':unittest.main()
