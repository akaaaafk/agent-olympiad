from copy import deepcopy
import re
import unittest
from scripts.repair_iiot_2023_text_20260913 import ROOT,CACHE,SAMPLES,BOOKS,read,repair


class Iiot2023TextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/"plan.json")
        cls.rows={int(r["problem_id"][-2:]):r for r in cls.plan["before_rows"] if r.get("year")==2023}
        cls.text={n:repair(n,r["problem_description"]).text for n,r in cls.rows.items()}

    def test_nine_records_fourteen_samples(self):
        self.assertEqual(len(self.text),9)
        self.assertEqual(sum(map(len,SAMPLES.values())),14)
        self.assertEqual(len(self.plan["writes"]),19)

    def test_sample_boundaries_exact(self):
        for n,text in self.text.items():
            pairs=re.findall(r"Sample \d+ input:\n```text\n(.*?)\n```\n\nSample \d+ output:\n```text\n(.*?)\n```",text,re.S)
            self.assertEqual(pairs,SAMPLES[n])

    def test_large_sample_numbers_not_split(self):
        self.assertIn("105481704\n600000",self.text[1])
        self.assertIn("5000000000 0",self.text[2])

    def test_only_prompt_changes(self):
        expected=deepcopy(self.plan["before_rows"])
        for r in expected:
            if r.get("year")==2023: r["problem_description"]=self.text[int(r["problem_id"][-2:])]
        self.assertEqual(expected,self.plan["writes"]["data/benchmarks/iiot/benchmark.json"])

    def test_subtask_points_unchanged(self):
        for n,row in self.rows.items():
            pattern=r"Subtask \d+\s*\((\d+) points\)"
            self.assertEqual(re.findall(pattern,row["problem_description"]),re.findall(pattern,self.text[n]))
            self.assertEqual(sum(map(int,re.findall(pattern,self.text[n]))),100)

    def test_exponents_and_cipher_formula(self):
        self.assertEqual(self.text[3].count("2·10^5"),2)
        self.assertIn("4·10^5",self.text[3]); self.assertIn("10^6",self.text[3])
        self.assertIn("t_{i mod |t|}",self.text[3])
        self.assertIn("ai,j≤ 10^9",self.text[6])
        self.assertEqual(self.text[9].count("ci≤10^6"),2)

    def test_graph_does_not_invent_radial_wrap(self):
        self.assertIn("There is no (0,j)↔(2,j) edge",self.text[7])
        self.assertIn("cost 5 for every j",self.text[7])

    def test_tetromino_shapes_and_multiple_answers(self):
        self.assertIn("O: ##/##; I: #/#/#/#",self.text[8])
        self.assertIn("If there are multiple solutions, you can print any of them",self.text[8])
        for shape in ("##/##", "#/#/#/#", ".##/##.", "##./.##", "#./#./##", ".#/.#/##", "###/.#."):
            self.assertEqual(shape.count("#"),4)

    def test_printed_ktree_inconsistency_not_silently_changed(self):
        self.assertIn("4 3 1",self.text[5]); self.assertIn("fifth query in sample 1 has k=1",self.text[5])
        self.assertIn("The second largest of them is6",self.text[5])

    def test_book_colors_not_scores(self):
        for n,text in self.text.items():
            self.assertNotIn("ὖE",text)
            self.assertEqual([int(x) for x in re.findall(r"book indicator: (\d) orange",text)],BOOKS[n])

    def test_second_application_rejected(self):
        with self.assertRaises(ValueError): repair(1,self.text[1])


if __name__=="__main__": unittest.main()
