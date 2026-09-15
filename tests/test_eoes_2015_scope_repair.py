import unittest
from copy import deepcopy
from pathlib import Path
from scripts import repair_eoes_2015_scope_20260913 as m


class Eoes2015ScopeRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=m.read(m.ROOT/m.CACHE/'plan.json')
        cls.rows={u['after']['problem_id']:u['after'] for u in cls.plan['updates']}

    def test_full_readback(self):
        self.assertEqual(m.verify()['records'],4)

    def test_exact_source_pages(self):
        m.verify_pdf(m.ROOT/m.PUBLIC)
        self.assertEqual(self.plan['pdf_derivation']['initial_source_pages'],[3,4])
        self.assertEqual(self.plan['pdf_derivation']['deferred_source_pages'],[1,2])

    def test_variant_maxima(self):
        self.assertEqual({p:self.rows[p]['total_points'] for p in m.MAXIMA},
                         {'eoes_ExpBlowingintheWind':306,'eoes_tasksheet1':304,'eoes_tasksheet2':306})
        for p in m.MAXIMA:
            r=self.rows[p];rub=m.read(m.ROOT/r['evaluation']['rubric_path'])
            self.assertFalse(rub['executable']);self.assertEqual(rub['criteria'],[])
            self.assertEqual(sum(s['max_score'] for s in rub['official_problem_maxima']),r['total_points'])

    def test_supplement_not_extra_score(self):
        r=self.rows[m.APPENDIX]
        self.assertIsNone(r['total_points'])
        self.assertFalse(r['source_review']['eoes_2015_review']['independently_scoreable'])
        self.assertEqual([a['path'] for a in r['assets'] if a['role']=='agent_visible'],[m.PUBLIC])
        self.assertIn('not an independent experiment',r['problem_description'])

    def test_three_formulas_and_population_denominator(self):
        t=self.rows['eoes_tasksheet2']['problem_description']
        for formula in ['sin(α_n) = n · λ / d','σ = sqrt(((x_m − x_1)^2 + (x_m − x_2)^2 + (x_m − x_3)^2) / 3)',
                        '[α] = (α / (l · c)) · 100']:
            self.assertEqual(t.count(formula),1)
        block=t.split('The general formula for the maxima of diffraction is:',1)[1].split('n: number of the maximum',1)[0]
        self.assertNotIn('𝑠𝑠𝑠𝑠𝑠𝑠',block);self.assertNotIn('Eating2 consistsand',t)

    def test_unexpected_prompt_drift_rejected(self):
        t=next(u['before']['problem_description'] for u in self.plan['updates'] if u['before']['problem_id']=='eoes_tasksheet2')
        with self.assertRaises(ValueError):m.repair_challenge2(t.replace('(formula 1)','(unknown equation)'))

    def test_gold_and_status_preserved(self):
        for u in self.plan['updates']:
            for k in ('gold_label','license','split','team_size','year','solution_file'):
                self.assertEqual(u['before'].get(k),u['after'].get(k))
            self.assertEqual(u['after']['evaluation']['status'],'not_ready')
        for p,h in self.plan['protected'].items():self.assertEqual(m.sha(m.ROOT/p),h)

    def test_derived_grading_and_unrelated_cards(self):
        report=m.read(m.ROOT/m.REPORT);backup=m.ROOT/report['backup']
        self.assertEqual(len(report['removed_from_initial_inputs']),2)
        for layout in ('base','last_exam'):
            path=f'data/{layout}/task_cards.json'
            current=m.read(m.ROOT/path)['tasks'];before=m.read(backup/path)['tasks']
            tasks={'eoes/'+p for p in m.SELECTED}
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
            self.assertEqual([c for c in current if c['task_id'] not in tasks],[c for c in before if c['task_id'] not in tasks])
            for c in current:
                if c['task_id'] not in {'eoes/'+p for p in m.SELECTED}:continue
                row=m.current_after(next(u for u in self.plan['updates'] if u['after']['problem_id']==c['task_id'].split('/')[1]))
                ev=c['evaluation'] if layout=='base' else m.read(m.ROOT/'data'/layout/c['source_repo_path']/'eval/reference.json')['evaluation']
                self.assertEqual(ev,row['evaluation'])
        for p in report['removed_from_initial_inputs']:
            self.assertFalse((m.ROOT/p).exists())
            self.assertEqual(m.sha(backup/p),m.sha(m.ROOT/m.ORIGINAL))


if __name__=='__main__':unittest.main()
