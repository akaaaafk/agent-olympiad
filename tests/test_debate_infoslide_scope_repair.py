import unittest
from scripts import repair_debate_infoslide_scope_20260913 as m


class DebateInfoslideScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=m.read(m.ROOT/m.CACHE/'plan.json');cls.a=cls.plan['updates'][0]['before'];cls.b=cls.plan['updates'][0]['after']

    def test_readback(self):
        self.assertEqual(m.verify()['records'],1)

    def test_actual_same_round_publication(self):
        s=self.a['source_review']['motion_source']
        m.verify_motion_source((m.ROOT/s['archived_snapshot']).read_bytes(),s)
        evidence=self.b['source_review']['infoslide_scope_review']['evidence']
        m.verify_motion_source((m.ROOT/evidence['current_snapshot']).read_bytes(),s)
        self.assertEqual(evidence['modal_id'],'info_32018')

    def test_missing_is_not_claimed_absent(self):
        r=self.b['source_review']['infoslide_scope_review']
        self.assertFalse(r['replacement_inferred']);self.assertFalse(r['original_round_had_no_slide_inferred'])
        self.assertIn('does not establish',self.b['problem_description'])
        self.assertEqual(self.b['infoslide'],'')

    def test_original_slide_preserved_not_active(self):
        self.assertEqual(self.b['source_review']['motion_source'],self.a['source_review']['motion_source'])
        self.assertEqual(self.b['source_review']['infoslide_scope_review']['original_published_slide'],self.a['infoslide'])
        self.assertNotIn(self.a['infoslide'],self.b['problem_description'])
        old=next(a for a in self.b['assets'] if a['path']==self.a['source_file']);self.assertEqual(old['role'],'judge_only')
        self.assertEqual(m.sha(m.ROOT/old['path']),old['sha256'])

    def test_motion_scores_and_status_preserved(self):
        for k in ('motion','gold_label','total_points','solution_file','year','split','license'):self.assertEqual(self.a.get(k),self.b.get(k))
        self.assertEqual(self.b['evaluation']['status'],'not_ready')
        self.assertEqual(self.a['evaluation']['historical_reference_path'],self.b['evaluation']['historical_reference_path'])

    def test_two_old_copies_recoverable(self):
        r=m.read(m.ROOT/m.REPORT);self.assertEqual(len(r['removed_from_initial_inputs']),2)
        for p in r['removed_from_initial_inputs']:
            self.assertFalse((m.ROOT/p).exists());self.assertEqual(m.sha(m.ROOT/r['backup']/p),m.sha(m.ROOT/self.a['source_file']))

    def test_unrelated_cards_preserved(self):
        r=m.read(m.ROOT/m.REPORT);task='debatebench/'+m.PID
        for layout in ('base','last_exam'):
            path=f'data/{layout}/task_cards.json';old=m.read(m.ROOT/r['backup']/path)['tasks'];new=m.read(m.ROOT/path)['tasks']
            tasks={task}
            from scripts import repair_debate_header_year_20260913 as later
            if (m.ROOT/later.REPORT).exists():
                later.verify();later_before=m.read(m.ROOT/m.read(m.ROOT/later.REPORT)['backup']/path)['tasks']
                for pid in later.SELECTED:
                    t='debatebench/'+pid
                    self.assertEqual(next(c for c in old if c['task_id']==t),next(c for c in later_before if c['task_id']==t));tasks.add(t)
            self.assertEqual([c for c in old if c['task_id'] not in tasks],[c for c in new if c['task_id'] not in tasks])

    def test_scorecards_synchronized(self):
        records=m.read(m.ROOT/'data/rubrics/task_scorecards/debatebench.json')['records']
        self.assertEqual(next(s for s in records if s['problem_id']==m.PID),m.scorecard(self.b,m.ROOT))


if __name__=='__main__':unittest.main()
