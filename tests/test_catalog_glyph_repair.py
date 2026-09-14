"""Record-local source-confirmed glyph repair guards."""
from copy import deepcopy
import unittest

from scripts.repair_catalog_glyphs_20260913 import ROOT, CACHE, PATCHES, SELECTED, CONTROLS, read, repair_text


class CatalogGlyphRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read(ROOT/CACHE/"plan.json")
        cls.before = {r["problem_id"]:r for rows in cls.plan["before_rows"].values() for r in rows}

    def test_exact_eleven_records_and_only_prompt_changes(self):
        self.assertEqual(len(self.plan["changes"]), 11)
        for cid, before in self.plan["before_rows"].items():
            after = self.plan["writes"][f"data/benchmarks/{cid}/benchmark.json"]
            self.assertEqual(len(before), len(after))
            for a,b in zip(before,after):
                expected = deepcopy(a)
                if a["problem_id"] in SELECTED[cid]:
                    expected["problem_description"] = repair_text(a["problem_id"],a["problem_description"])
                self.assertEqual(b, expected)

    def test_all_49_controls_repaired_without_stripping_math(self):
        self.assertEqual(sum(c["control_characters_repaired"] for c in self.plan["changes"]),49)
        for pid in PATCHES:
            text = repair_text(pid,self.before[pid]["problem_description"])
            self.assertIsNone(CONTROLS.search(text))

    def test_context_drift_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"context/count changed"):
            repair_text("arml_power_spring_2022", self.before["arml_power_spring_2022"]["problem_description"].replace("m + n", "m - n"))
        with self.assertRaisesRegex(ValueError,"No reviewed patch"):
            repair_text("not_reviewed", "example\x1b")

    def test_floor_and_ceiling_not_interchanged(self):
        ceiling = repair_text("arml_power_spring_2022", self.before["arml_power_spring_2022"]["problem_description"])
        floor = repair_text("arml_national_power_2023", self.before["arml_national_power_2023"]["problem_description"])
        self.assertIn("⌈(m + n)/2⌉", ceiling)
        self.assertIn("⌊k/4⌋", floor)
        self.assertIn("⌊log2(x)⌋", floor)
        self.assertIn("⌊log2(m)⌋", floor)

    def test_muffin_formula_grouping_preserved(self):
        text = repair_text("arml_power_spring_2024", self.before["arml_power_spring_2024"]["problem_description"])
        self.assertIn("max{1/3, min{m/(s⌈2m/s⌉), 1 − m/(s⌊2m/s⌋)}}", text)

    def test_modulus_exponents_are_not_plain_109(self):
        for pid in ("iiot_2021_02","iiot_2023_01"):
            text = repair_text(pid,self.before[pid]["problem_description"])
            self.assertNotIn("109 + 7",text)
            self.assertIn("10^9 + 7",text)
            self.assertIn("Note: The modulo operation",text)
        text = repair_text("iiot_2021_08",self.before["iiot_2021_08"]["problem_description"])
        self.assertNotIn("107 + 19",text)
        self.assertIn("10^7 + 19",text)

    def test_absolute_value_is_one_pair_not_five_pairs(self):
        text = repair_text("pumac_power_2021",self.before["pumac_power_2021"]["problem_description"])
        self.assertIn("|∑_{n∈A}(x_n − y_n)|",text)
        self.assertNotIn("|||||",text)

    def test_two_prompt_copies_per_record_and_no_score_writes(self):
        paths = list(self.plan["writes"])
        self.assertEqual(sum(p.endswith("/problem.md") for p in paths),22)
        self.assertEqual(len(paths),27)
        self.assertFalse(any(p.startswith(("data/rules/","data/rubrics/","data/raw/")) for p in paths))


if __name__ == "__main__":
    unittest.main()
