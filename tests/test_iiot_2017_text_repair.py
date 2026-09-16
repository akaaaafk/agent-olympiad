import unittest
from scripts.repair_iiot_2017_text_20260913 import ROOT,CACHE,PATH,SAMPLES,read,sha,repair

class IIOT2017Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.before={r['problem_id']:r for r in cls.plan['before_rows']};cls.after={r['problem_id']:r for r in cls.plan['writes'][PATH]}
    def test_seven_records_fifteen_samples(self):
        self.assertEqual(len(self.plan['changes']),7);self.assertEqual(sum(map(len,SAMPLES.values())),15)
    def test_repair_deterministic(self):
        for pid,r in self.before.items():
            if r['year']==2017:self.assertEqual(repair(int(pid[-2:]),r['problem_description']).text,self.after[pid]['problem_description'])
    def test_input_output_boundaries(self):
        for n,samples in SAMPLES.items():
            t=self.after[f'iiot_2017_{n:02}']['problem_description']
            self.assertNotIn('Examples input.txt output.txt',t)
            for i,(a,b) in enumerate(samples,1):self.assertIn(f'Sample {i} input:\n```text\n{a}\n```\n\nSample {i} output:\n```text\n{b}\n```',t)
    def test_partial_score_fractions(self):
        self.assertIn('(M − Δ_out) / (M + 10 Δ_out)',self.after['iiot_2017_02']['problem_description'])
        self.assertIn('(Δ_max − Δ_out) / (Δ_max + 10 Δ_out)',self.after['iiot_2017_04']['problem_description'])
    def test_string_samples_have_exactly_two_ascii_lines(self):
        for a,b in SAMPLES[4]:self.assertEqual(len(a.splitlines()),2);a.encode('ascii')
    def test_source_inconsistencies_not_silently_fixed(self):
        self.assertIn('V0, V1, . . . , VN −1',self.after['iiot_2017_03']['problem_description'])
        self.assertIn('original endpoint inconsistency',self.after['iiot_2017_03']['problem_description'])
        self.assertIn('through N−1',self.after['iiot_2017_02']['problem_description'])
    def test_graphs_are_directed_parent_arrays(self):
        t=self.after['iiot_2017_06']['problem_description'];self.assertIn('2→3→5→2',t);self.assertIn('[-1,0,0,2,9,9,10,10,2,2,8,1]',t)
    def test_title_corrected_in_both_cards(self):
        for layout in ('base','last_exam'):
            card=next(c for c in self.plan['writes'][f'data/{layout}/task_cards.json']['tasks'] if c['task_id']=='iiot/iiot_2017_05')
            self.assertEqual(card['title'],'Moving Paintings (paintings)')
    def test_only_prompt_and_one_title_changed(self):
        for pid,before in self.before.items():
            after=self.after[pid]
            for k in before:
                if k=='problem_description' and before['year']==2017:continue
                if k=='title' and pid=='iiot_2017_05':continue
                self.assertEqual(before[k],after[k])
    def test_source_hashes(self):
        for c in self.plan['changes']:self.assertEqual(sha(ROOT/c['source_file']),c['source_sha256'])

if __name__=='__main__':unittest.main()
