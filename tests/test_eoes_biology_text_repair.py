from copy import deepcopy
import unittest
from scripts.repair_eoes_biology_text_20260913 import ROOT,CACHE,PID,read,repair


class EoesBiologyTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/"plan.json")
        cls.before=next(r for r in cls.plan["before_rows"] if r["problem_id"]==PID)
        cls.text=repair(cls.before["problem_description"]).text

    def test_q10_fraction_and_exponent(self):
        self.assertIn("Q_10 = [k(t_2) / k(t_1)]^(10 °C / (t_2 − t_1))",self.text)

    def test_population_not_flattened(self):
        self.assertIn("N = N_0 × 2^n",self.text)
        self.assertNotIn("0 2nN N = ×",self.text)

    def test_no_solutions_or_measurements_added(self):
        for s in ("you will \nlose 3 points", "lose 1.5 points", "at 4 °C which is 8 h", "500 bac-"):
            self.assertIn(s,self.text)
        self.assertIn("Generation time (h) at 24 °C 1.3",self.text)

    def test_only_prompt_changes(self):
        expected=deepcopy(self.plan["before_rows"])
        next(r for r in expected if r["problem_id"]==PID)["problem_description"]=self.text
        self.assertEqual(expected,self.plan["writes"]["data/benchmarks/eoes/benchmark.json"])
        self.assertEqual(len(self.plan["writes"]),3)
        self.assertEqual(self.before["total_points"],125)

    def test_specific_words_not_global_font_substitution(self):
        for s in ("NaOH","NaCl","mL","mV","e.g."):
            self.assertIn(s,self.text)
        for s in ("cuveCe","concentra.on","soluKon","boJle","objecKve","aBer"):
            self.assertNotIn(s,self.text)

    def test_drift_or_second_repair_rejected(self):
        with self.assertRaises(ValueError): repair(self.text)


if __name__=="__main__": unittest.main()
