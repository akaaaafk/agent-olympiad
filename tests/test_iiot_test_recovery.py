from collections import Counter
import re
import unittest
from scripts.materialize_iiot_2023_tests_20260913 import ROOT,CACHE,read


class IIOTTestRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.plan=read(ROOT/CACHE/'apply_plan.json')

    def test_totals(self):
        s=self.plan['summary']
        self.assertEqual(s['official_test_pairs'],338)
        self.assertEqual(s['downloaded_files'],728)
        self.assertEqual(s['downloaded_bytes'],730823282)

    def test_all_new_assets_hidden(self):
        for u in self.plan['updates']:
            old={a['path'] for a in u['before']['assets']}
            self.assertTrue(all(a['role']=='judge_only' for a in u['after']['assets'] if a['path'] not in old))

    def test_same_id_pairing(self):
        for f in self.plan['new_files']:
            if not f['destination'].endswith('/test_source_manifest.json'): continue
            m=read(ROOT/f['source'])
            self.assertEqual(len(m['test_pairs']),m['official_test_pair_count'])
            self.assertEqual(len(set(p['id'] for p in m['test_pairs'])),m['official_test_pair_count'])
            for p in m['test_pairs']:
                self.assertTrue(p['input'].endswith('/input'+p['id']+'.txt'))
                self.assertTrue(p['output'].endswith('/output'+p['id']+'.txt'))

    def test_cipher_aliases_not_extra_cases(self):
        m=read(ROOT/CACHE/'cipher/test_source_manifest.json')
        self.assertEqual(len(m['input_aliases']),52)
        self.assertEqual(Counter(a['evidence'] for a in m['input_aliases']),
            {'identical_file_sha256':51,'byte_equality_after_removing_only_trailing_CR_LF':1})
        self.assertTrue(all(a['not_an_additional_case'] for a in m['input_aliases']))
        self.assertEqual(m['unresolved_alias_files'],[])

    def test_no_scoring_or_readiness_inference(self):
        for u in self.plan['updates']:
            for k in ('total_points','gold_label','problem_description'):
                self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')
            self.assertEqual(u['before']['evaluation']['official_subtasks'],u['after']['evaluation']['official_subtasks'])

    def test_tetris_checker_not_equality(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['task_code']=='tetris')
        self.assertIn('expected-output text equality is not a valid general checker',' '.join(row['evaluation']['limitations']))

    def test_ordinary_fifty_file_truncation_avoided(self):
        counts={t['task']:t['pairs'] for t in self.plan['summary']['tasks']}
        self.assertEqual(counts['matgame'],79)
        self.assertEqual(counts['publictransport'],53)
        self.assertEqual(counts['cipher'],52)


if __name__=='__main__': unittest.main()
