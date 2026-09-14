import unittest
from scripts.repair_iiot_2021_text_20260913 import ROOT,CACHE,SAMPLES,BOOKS,read,sha,repair,writer

class IIOT2021Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.before={r['problem_id']:r for r in cls.plan['before_rows']};cls.after={r['problem_id']:r for r in cls.plan['writes']['data/benchmarks/iiot/benchmark.json']}
    def test_eight_records_sixteen_sample_pairs(self):self.assertEqual(len(self.plan['changes']),8);self.assertEqual(sum(map(len,SAMPLES.values())),16)
    def test_book_colors_and_no_unicode_garbage(self):
        for n,colors in BOOKS.items():
            t=self.after[f'iiot_2021_{n:02}']['problem_description'];self.assertNotIn('ὖE',t)
            self.assertEqual(t.count('[book indicator:'),len(colors))
    def test_examples_preserve_line_boundaries(self):
        for n,pairs in SAMPLES.items():
            t=self.after[f'iiot_2021_{n:02}']['problem_description']
            for a,b in pairs:self.assertIn(a,t)
    def test_prior_task_five_diagrams_unchanged(self):
        a=self.before['iiot_2021_05']['problem_description'];b=self.after['iiot_2021_05']['problem_description'];self.assertEqual(a[a.index('Examples\n'):],b[b.index('Examples\n'):])
    def test_correct_exponents_and_fraction(self):
        for n in (1,3,7):self.assertIn('10^9',self.after[f'iiot_2021_{n:02}']['problem_description'])
        self.assertIn('M≤10^8',self.after['iiot_2021_04']['problem_description']);self.assertIn('x^2',self.after['iiot_2021_08']['problem_description']);self.assertIn('S_out / S_ref',self.after['iiot_2021_01']['problem_description'])
    def test_song_words_are_not_split_by_pdf_glyph_positions(self):
        self.assertIn('skuh marseille milano',SAMPLES[6][0][0])
        for a,b in SAMPLES[6]:
            lines=a.splitlines();n,length=map(int,lines[0].split());self.assertEqual(len(lines),n+1)
            for line in lines[1:]:
                tokens=line.split();self.assertEqual(int(tokens[0]),len(tokens)-1);self.assertTrue(all(len(w)<=length for w in tokens[1:]))
            self.assertEqual(len(b.split()),int(lines[1].split()[0]))
    def test_gold_score_status_only_prompt_changes(self):
        for pid,a in self.before.items():
            for k,v in a.items():
                if k=='problem_description' and a['year']==2021:continue
                self.assertEqual(v,self.after[pid][k])
    def test_exact_changes_reproducible(self):
        for pid,a in self.before.items():
            if a['year']==2021:self.assertEqual(repair(int(pid[-2:]),a['problem_description']).text,self.after[pid]['problem_description'])
    def test_source_hashes(self):
        for c in self.plan['changes']:self.assertEqual(sha(ROOT/c['source_file']),c['source_sha256'])
    def test_private_writer_leaves_2023_globals_alone(self):
        from scripts import repair_iiot_2023_text_20260913 as original
        writer();self.assertEqual(original.YEAR,2023);self.assertEqual(original.EXPECTED_RECORDS,9)

if __name__=='__main__':unittest.main()
