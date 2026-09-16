import unittest
from scripts import repair_debate_header_year_20260913 as m


class DebateHeaderYear(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=m.read(m.ROOT/m.CACHE/'plan.json')

    def test_readback(self):
        self.assertEqual(m.verify()['records'],6)

    def test_five_natolin_years(self):
        rows=[u for u in self.plan['updates'] if u['after']['problem_id']!=m.CAMBRIDGE]
        self.assertEqual(len(rows),5)
        for u in rows:
            self.assertEqual(u['before']['year'],2017);self.assertEqual(u['after']['year'],2019)
            self.assertEqual(u['after']['evaluation']['rubric_reuse']['target_year'],2019)

    def test_primary_review_note_honest(self):
        s=next(s for s in self.plan['sources'] if s['key']=='event');r=m.read(m.ROOT/s['path'])
        self.assertEqual(r['direct_http_status'],403)
        self.assertEqual(r['source_type'],'review_note_from_web_reader_not_original_html')
        self.assertEqual(r['event_start'],'2019-07-05');self.assertFalse(r['recordings_played'])

    def test_original_transcript_headings_only(self):
        self.assertEqual(len(self.plan['public_texts']),4)
        for u in self.plan['updates']:
            b=u['after'];pid=b['problem_id']
            if not b['source_review']['motion_recovered']:continue
            text=(m.ROOT/b['solution_file']).read_text(encoding='utf-8-sig')
            self.assertEqual(b['motion'],m.header_motion(pid,text))
            self.assertFalse(b['source_review']['header_year_review']['motion_inferred_from_arguments'])

    def test_no_motion_invented_for_rounds_4_5(self):
        for n in (4,5):
            u=next(u for u in self.plan['updates'] if u['after']['problem_id']==m.PREFIX+str(n))
            self.assertEqual(u['before']['problem_description'],u['after']['problem_description'])
            self.assertFalse(u['after']['source_review']['motion_recovered'])
            with self.assertRaises(ValueError):m.header_motion(u['after']['problem_id'],'<pm>Arguments only')

    def test_drift_rejected(self):
        with self.assertRaises(ValueError):m.header_motion(m.PREFIX+'1','<pm>There are families and debt.')
        with self.assertRaises(ValueError):m.header_motion(m.CAMBRIDGE,'<pm>Okay. Motion not explicitly stated.')

    def test_no_background_slide_or_gold_invented(self):
        for u in self.plan['updates']:
            for k in ('infoslide','gold_label','total_points','solution_file','split','license'):self.assertEqual(u['before'].get(k),u['after'].get(k))
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')

    def test_sources_private_and_bytes_preserved(self):
        for p,h in self.plan['protected'].items():self.assertEqual(m.sha(m.ROOT/p),h)
        for s in self.plan['sources']:self.assertEqual(m.sha(m.ROOT/s['path']),s['sha256'])
        for u in self.plan['updates']:
            for a in u['after']['assets']:
                if a['role']=='agent_visible':self.assertIn(a['path'],self.plan['public_texts'])

    def test_unrelated_cards_unchanged(self):
        report=m.read(m.ROOT/m.REPORT);tasks={'debatebench/'+p for p in m.SELECTED}
        for layout in ('base','last_exam'):
            path=f'data/{layout}/task_cards.json';before=m.read(m.ROOT/report['backup']/path)['tasks'];after=m.read(m.ROOT/path)['tasks']
            self.assertEqual([c for c in before if c['task_id'] not in tasks],[c for c in after if c['task_id'] not in tasks])

    def test_scorecards_current(self):
        scores=m.read(m.ROOT/'data/rubrics/task_scorecards/debatebench.json')['records']
        for u in self.plan['updates']:
            b=u['after'];self.assertEqual(next(s for s in scores if s['problem_id']==b['problem_id']),m.scorecard(b,m.ROOT))


if __name__=='__main__':unittest.main()
