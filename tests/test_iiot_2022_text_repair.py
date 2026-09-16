import unittest
from scripts.repair_iiot_2022_text_20260913 import ROOT,CACHE,SAMPLES,BOOKS,read,sha,repair,writer

class IIOT2022Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.before={r['problem_id']:r for r in cls.plan['before_rows']};cls.after={r['problem_id']:r for r in cls.plan['writes']['data/benchmarks/iiot/benchmark.json']}
    def test_seven_records_fifteen_samples_twenty_pages(self):
        self.assertEqual(len(self.plan['changes']),7);self.assertEqual(sum(map(len,SAMPLES.values())),15);self.assertEqual(sum(len(c['reviewed_pages']) for c in self.plan['changes']),20)
    def test_book_colors(self):
        for n,colors in BOOKS.items():
            t=self.after[f'iiot_2022_{n:02}']['problem_description'];self.assertNotIn('ὖ∠',t);self.assertEqual(t.count('[book indicator:'),len(colors))
    def test_samples_exact_lines(self):
        for n,pairs in SAMPLES.items():
            t=self.after[f'iiot_2022_{n:02}']['problem_description']
            for a,b in pairs:self.assertIn('```text\n'+a+'\n```',t);self.assertIn('```text\n'+b+'\n```',t)
    def test_source_spelling_and_mini_format_not_normalized(self):
        self.assertIn('cheesecacke',SAMPLES[3][1][0]);self.assertNotIn('cheesecake',SAMPLES[3][1][0]);self.assertIn('MINI (Musical Instrument Note Information)',self.after['iiot_2022_06']['problem_description'])
    def test_row_counts_match_specifications(self):
        for n,pairs in SAMPLES.items():
            for a,b in pairs:
                lines=a.splitlines();head=list(map(int,lines[0].split()));N=head[0]
                expected={1:N+1,2:head[-1]+2,3:N+1,4:head[-1]+1,5:2,6:2*N+1,7:N+1}[n]
                self.assertEqual(len(lines),expected)
                if n==3:self.assertEqual(len(b.splitlines()),N)
                if n==5:self.assertEqual(len(lines[1].split()),N)
                if n==7:self.assertTrue(all(len(x.split())==2*head[1] for x in lines[1:]))
    def test_orientation_examples_preserve_edges_and_no_stars(self):
        for a,b in SAMPLES[4]:
            lines=a.splitlines();N,M=map(int,lines[0].split());ins=[tuple(map(int,x.split())) for x in lines[1:]];outs=[tuple(map(int,x.split())) for x in b.splitlines()]
            self.assertEqual(sorted(tuple(sorted(e)) for e in ins),sorted(tuple(sorted(e)) for e in outs))
            self.assertEqual(len(outs),M)
            self.assertEqual(set(x for x,y in outs),set(range(N)));self.assertEqual(set(y for x,y in outs),set(range(N)))
        self.assertIn('In case of multiple solutions, you can output any.',self.after['iiot_2022_04']['problem_description'])
    def test_fraction_and_float_inconsistency(self):
        a=self.after['iiot_2022_01']['problem_description'];b=self.after['iiot_2022_07']['problem_description']
        self.assertIn('P_discount / P_tot',a);self.assertIn('10^−6',a);self.assertIn('10^−6',b);self.assertIn('with an integer:',b);self.assertIn('source inconsistency',b)
    def test_metadata_scores_assets_unchanged(self):
        for pid,a in self.before.items():
            for k,v in a.items():
                if k=='problem_description' and a['year']==2022:continue
                self.assertEqual(v,self.after[pid][k])
    def test_reproducible_edits_and_hashes(self):
        for c in self.plan['changes']:
            pid=c['task_id'].split('/')[1];self.assertEqual(sha(ROOT/c['source_file']),c['source_sha256']);self.assertEqual(repair(int(pid[-2:]),self.before[pid]['problem_description']).text,self.after[pid]['problem_description'])
    def test_private_writer_does_not_change_2023(self):
        from scripts import repair_iiot_2023_text_20260913 as original
        m=writer();self.assertEqual(m.YEAR,2022);self.assertEqual(original.YEAR,2023)

if __name__=='__main__':unittest.main()
