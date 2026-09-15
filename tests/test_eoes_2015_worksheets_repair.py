import unittest
from pathlib import Path
import pymupdf
from scripts import repair_eoes_2015_worksheets_20260913 as m


class Eoes2015Worksheets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=m.read(m.ROOT/m.CACHE/'plan.json')
        cls.rows={u['after']['problem_id']:u['after'] for u in cls.plan['updates']}

    def test_full_readback(self):
        self.assertEqual(m.verify()['records'],3)

    def test_original_bytes(self):
        for p,h in self.plan['protected'].items():self.assertEqual(m.sha(m.ROOT/p),h)
        for name,n in [('answersheet1.pdf',27),('answersheet2.pdf',27),('template_diagrampaper.pdf',1)]:
            with pymupdf.open(m.ROOT/m.RAW/name) as d:self.assertEqual(len(d),n)

    def test_worksheets_are_not_gold(self):
        for u in self.plan['updates']:
            a,b=u['before'],u['after']
            for k in ('gold_label','solution_file','total_points','year','split','license'):self.assertEqual(a.get(k),b.get(k))
            r=b['source_review']['eoes_2015_worksheet_review']
            self.assertFalse(r['grading_key_recovered']);self.assertFalse(r['experimental_results_added'])
            self.assertIn('not a solution key',b['problem_description'])

    def test_original_givens_not_removed_or_solved(self):
        with pymupdf.open(m.ROOT/m.RAW/'answersheet2.pdf') as d:
            self.assertIn('Mesembryanthemum',d[2].get_text());self.assertIn('9',d[2].get_text())
            self.assertIn('12,50',d[19].get_text());self.assertIn('6,25',d[19].get_text())
        with pymupdf.open(m.ROOT/m.RAW/'template_diagrampaper.pdf') as d:self.assertIn('TEAM A',d[0].get_text())

    def test_variant_difference_not_normalized(self):
        for pid,total,a in [('eoes_ExpBlowingintheWind',306,92),('eoes_tasksheet1',304,90)]:
            r=self.rows[pid];review=r['source_review']['eoes_2015_worksheet_review']
            self.assertEqual(r['total_points'],total);self.assertEqual(review['task_sheet_task_a_total'],a)
            self.assertEqual(sum(review['worksheet_task_a_printed_submarks']),90)
            self.assertFalse(review['edition_equivalence_certified'])

    def test_rf_transcription_and_drift(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id']=='eoes_tasksheet2')
        self.assertEqual(u['after']['problem_description'].count(m.FORMULA),1)
        self.assertEqual(m.repair_rf(u['before']['problem_description']).text.count(m.FORMULA),1)
        with self.assertRaises(ValueError):m.repair_rf(u['after']['problem_description'])
        with self.assertRaises(ValueError):m.repair_rf('unknown text')

    def test_deferred_release_and_rubrics_preserved(self):
        for u in self.plan['updates']:
            for k in ('staged_source_release','official_max_score','official_problem_maxima','rubric_path','status'):
                self.assertEqual(u['before']['evaluation'].get(k),u['after']['evaluation'].get(k))
            for asset in u['before']['assets']:self.assertIn(asset,u['after']['assets'])

    def test_scorecards_current(self):
        scores=m.read(m.ROOT/'data/rubrics/task_scorecards/eoes.json')['records']
        for pid,r in self.rows.items():self.assertEqual(next(s for s in scores if s['problem_id']==pid),m.scorecard(r,m.ROOT))

    def test_unrelated_cards_preserved(self):
        backup=m.ROOT/m.read(m.ROOT/m.REPORT)['backup'];tasks={'eoes/'+p for p in m.SELECTED}
        for layout in ('base','last_exam'):
            path=f'data/{layout}/task_cards.json'
            before=m.read(backup/path)['tasks'];after=m.read(m.ROOT/path)['tasks']
            from scripts import repair_debate_infoslide_scope_20260913 as later
            if (m.ROOT/later.REPORT).exists():
                later.verify();task='debatebench/'+later.PID
                later_before=m.read(m.ROOT/m.read(m.ROOT/later.REPORT)['backup']/path)['tasks']
                self.assertEqual(next(c for c in before if c['task_id']==task),next(c for c in later_before if c['task_id']==task))
                tasks.add(task)
            from scripts import repair_debate_header_year_20260913 as header
            if (m.ROOT/header.REPORT).exists():
                header.verify();later_before=m.read(m.ROOT/m.read(m.ROOT/header.REPORT)['backup']/path)['tasks']
                for pid in header.SELECTED:
                    task='debatebench/'+pid
                    self.assertEqual(next(c for c in before if c['task_id']==task),next(c for c in later_before if c['task_id']==task))
                    tasks.add(task)
            self.assertEqual([c for c in before if c['task_id'] not in tasks],[c for c in after if c['task_id'] not in tasks])

    def test_no_deletion_or_readiness_promotion(self):
        report=m.read(m.ROOT/m.REPORT)
        self.assertEqual(report['record_count_change'],0);self.assertEqual(report['readiness_promotions'],0)
        self.assertEqual(report['removed_from_initial_inputs'],[])
        for r in self.rows.values():self.assertEqual(r['evaluation']['status'],'not_ready')


if __name__=='__main__':unittest.main()
