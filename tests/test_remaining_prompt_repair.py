"""Frozen-source regression cases for the remaining EOES and IIOT glyph repair."""
from copy import deepcopy
import re
import unittest
from scripts.repair_remaining_prompt_text_20260913 import ROOT,CACHE,PAGES,CONTROL,read,repair,Editor


class RemainingPromptRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/"plan.json")
        cls.before={r["problem_id"]:r for rows in cls.plan["before_rows"].values() for r in rows}
        cls.text={pid:repair(pid,cls.before[pid]["problem_description"]).text for pid in PAGES}
        cls.t1=cls.text["eoes_EOES2025_Task1_TaskSheet-final"]
        cls.t2=cls.text["eoes_EOES2025_Task2_TaskSheet_final"]

    def test_seven_records_and_759_controls(self):
        self.assertEqual(len(self.plan["changes"]),7)
        self.assertEqual(sum(c["controls_before"] for c in self.plan["changes"]),759)
        for t in self.text.values(): self.assertIsNone(CONTROL.search(t))

    def test_no_non_prompt_fields_changed(self):
        for cid,rows in self.plan["before_rows"].items():
            after=self.plan["writes"][f"data/benchmarks/{cid}/benchmark.json"]
            for a,b in zip(rows,after):
                expected=deepcopy(a)
                if a["problem_id"] in self.text: expected["problem_description"]=self.text[a["problem_id"]]
                self.assertEqual(expected,b)

    def test_only_sixteen_content_files(self):
        paths=self.plan["writes"]
        self.assertEqual(len(paths),16)
        self.assertEqual(sum(p.endswith("/problem.md") for p in paths),14)
        self.assertFalse(any(p.startswith(("data/raw/","data/rubrics/","data/rules/")) for p in paths))

    def test_context_drift_stops(self):
        with self.assertRaises(ValueError): Editor("abc").rep("abd","fixed")
        with self.assertRaises(ValueError): repair("unknown","\x01")

    def test_rerun_cannot_blindly_rewrite(self):
        with self.assertRaises(ValueError): repair("iiot_2021_05",self.text["iiot_2021_05"])

    def test_iodate_and_thiosulfate_charges(self):
        self.assertEqual(self.t1.count("IO_3^−(aq) + 5I^−(aq) + 6H^+(aq) → 3I_2(aq) + 3H_2O(l)"),3)
        self.assertIn("I_2(aq) + 2S_2O_3^{2−}(aq) → 2I^−(aq) + S_4O_6^{2−}(aq)",self.t1)

    def test_missing_oxidation_equation_restored(self):
        self.assertIn("I^−(aq) + 3ClO^−(aq) → IO_3^−(aq) + 3Cl^−(aq)",self.t1)

    def test_refraction_equations_and_coordinates(self):
        for s in ("n_1 sin(α_1) = n_2 sin(α_2)","w sin(α) / sqrt(n^2 − sin^2(α))", "sin(α_i) sqrt(w^2 + d_i^2) = n d_i", "Y_i = n X_i", "(x, y) = (0,0)"):
            self.assertIn(s,self.t1)

    def test_percentages_are_not_x_variables(self):
        self.assertIn("20 % mass fraction",self.t1)
        self.assertIn("d(cm) 20%",self.t1)
        self.assertIn("x exact (cm)",self.t1)
        self.assertNotIn("% exact",self.t1)

    def test_absorbance_and_natural_logs_are_distinct(self):
        self.assertIn("A_CV = log(U_BL / U_CV)",self.t2)
        self.assertIn("ln(A_t) = ln(A_0) − k′t",self.t2)
        self.assertIn("k′ = k[OH^−]",self.t2)

    def test_equations_no_longer_float_after_step_1_2(self):
        body=self.t2[self.t2.index("Step 1.2:"):self.t2.index("Step 1.3:")]
        self.assertNotIn("ln([CV]",body)
        self.assertIn("[CV] = A_CV / (ε · l)",self.t2)

    def test_division_slashes_survive_L_repair(self):
        for s in ("T = 2π sqrt(R/g)","γ = C L/m", "L_i m_0/(m_0 + m_{i,paper})", "(C/m_0)L_{ren,i}","m/s^2"):
            self.assertIn(s,self.t2)
        self.assertNotIn("RLg",self.t2)

    def test_pendulum_not_punctuation(self):
        self.assertIn("θ(t) = θ(0) exp(−γt)",self.t2)
        self.assertIn("Period T is",self.t2)
        self.assertIn("length R,",self.t2)

    def test_unreadable_source_not_fabricated(self):
        self.assertIn("[PDF page 2]",self.text["eoes_EUSO_I_2004_TaskB"])
        self.assertIn("unreadable in the original PDF",self.text["eoes_P1Tasks"])
        self.assertEqual(self.text["eoes_additionalfileschallenge1"].count("original header contains unreadable glyphs"),4)
        self.assertIn("two differently sized outline drawings",self.text["eoes_additionalfileschallenge1"])

    def test_2006_bullets_and_arrows(self):
        t=self.text["eoes_TEST2 final version English"]
        self.assertEqual(t.count("▪"),5)
        self.assertEqual(t.count("→"),3)

    def test_iiot_sample_blocks_and_outputs(self):
        t=self.text["iiot_2021_05"]
        blocks=re.findall(r"```text\n(.*?)\n```",t,re.S)
        self.assertEqual(blocks,["5 2\n3 10\n4 1\n3 5\n-1 20\n3 2","7 2\n1 10\n-1 1\n3 10\n1 3\n1 7\n0 7\n5 9"])
        self.assertIn("Sample 1 output: `5`",t)
        self.assertIn("Sample 2 output: `14`",t)

    def test_iiot_tree_directions_and_skips(self):
        t=self.text["iiot_2021_05"]
        self.assertIn("3→0, 3→4, 3→2, 4→1",t)
        self.assertIn("1→0, 1→3, 1→4, 0→5, 3→2, 5→6",t)
        self.assertIn("Tasks 0 and 5 are skipped",t)
        self.assertIn("0≤Ti≤10^9",t)

    def test_iiot_weights_unchanged(self):
        t=self.text["iiot_2021_05"]
        self.assertEqual([int(x) for x in re.findall(r"Subtask \d\((\d+) points\)",t)],[0,18,9,23,29,21])


if __name__=="__main__": unittest.main()
