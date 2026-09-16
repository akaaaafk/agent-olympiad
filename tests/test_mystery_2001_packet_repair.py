from copy import deepcopy
import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2001_packets_20260913 import ROOT,CACHE,SELECTED,read,sha,sanitize,check_html,writer


class Mystery2001PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/'plan.json')

    def test_twelve_explicit_records(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual(len(SELECTED),12)
        self.assertEqual(len(self.plan['copies']),44)
        self.assertEqual(sum(v['media_count'] for v in self.plan['review'].values()),32)

    def test_only_reviewed_script_bytes_removed(self):
        for u in self.plan['updates']:
            pid=u['after']['problem_id']
            original=(ROOT/u['before']['source_file']).read_bytes()
            expected,edits=sanitize(original)
            self.assertEqual((ROOT/CACHE/pid/'input/puzzle.html').read_bytes(),expected)
            self.assertEqual(len(edits),1)
            self.assertNotIn(b'checkanswer.js',expected)

    def test_all_dependencies_explicit(self):
        for u in self.plan['updates']:
            folder=ROOT/CACHE/u['after']['problem_id']/'input'
            soup=check_html(folder/'puzzle.html',{p.resolve() for p in folder.iterdir()})
            self.assertEqual(len(soup.find_all('img')),u['after']['source_review']['media_count'])
            self.assertFalse(soup.find_all(['a','form','iframe','script','object','embed']))

    def test_no_answers_scores_or_readiness_changes(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','split','license','team_size','title','year'):
                self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')

    def test_live_start_not_invented(self):
        rows={int(u['after']['problem_id'][-5:]):u['after'] for u in self.plan['updates']}
        self.assertIn('starting room and later observations are not inferred',rows[165]['problem_description'])
        self.assertIn('live headquarters appointment',rows[144]['problem_description'])
        self.assertEqual(set(self.plan['deferred_records']),{f'mystery_hunt_{n:05}' for n in (138,177,182,184)})

    def test_duplicate_source_clue_is_preserved(self):
        soup=BeautifulSoup((ROOT/CACHE/'mystery_hunt_00179/input/puzzle.html').read_bytes(),'html.parser')
        self.assertEqual(soup.get_text().count('Strengthen with fresh additions (9)'),2)
        self.assertIn('séance',soup.get_text())

    def test_prepared_hashes_match(self):
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])

    def test_writer_does_not_mutate_frozen_2000_module(self):
        from scripts import repair_mystery_2000_packets_20260913 as old
        before=(old.CACHE,old.RAW,old.REPORT,deepcopy(old.SELECTED))
        private=writer()
        self.assertEqual(len(private.SELECTED),12)
        self.assertEqual((old.CACHE,old.RAW,old.REPORT,old.SELECTED),before)


if __name__=='__main__':unittest.main()
