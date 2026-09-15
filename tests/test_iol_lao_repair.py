"""Frozen, source-bound regression guards for the IOL 2012 Lao repair."""
import unittest

from scripts.repair_iol_lao_20260913 import (
    ROOT, CACHE, PID, SOURCE, SOLUTION, SOURCE_SHA, SOLUTION_SHA,
    INPUT_IMAGE, JUDGE_IMAGE, REFERENCE, RULE, CARDS, read, sha,
    pdf_text, poppler_text, country_map, reference_data, check_packages,
)


class IOLLaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read(ROOT/CACHE/"plan.json")
        cls.row = next(r for r in cls.plan["rows"] if r["problem_id"] == PID)
        cls.before = next(r for r in cls.plan["before_rows"] if r["problem_id"] == PID)
        cls.reference = cls.plan["writes"][REFERENCE]

    def test_exact_scope_no_year_deletion(self):
        before, after = self.plan["before_rows"], self.plan["rows"]
        self.assertEqual(len(after), 18)
        self.assertEqual([r["problem_id"] for r in before], [r["problem_id"] for r in after])
        self.assertEqual([r for r in before if r["problem_id"] != PID], [r for r in after if r["problem_id"] != PID])

    def test_original_pdf_bytes_preserved(self):
        self.assertEqual(sha(ROOT/SOURCE), SOURCE_SHA)
        self.assertEqual(sha(ROOT/SOLUTION), SOLUTION_SHA)
        self.assertEqual(len(pdf_text(ROOT/SOURCE)), 1)
        self.assertEqual(len(pdf_text(ROOT/SOLUTION)), 1)
        self.assertTrue((ROOT/SOURCE).read_bytes().startswith(b"%PDF-"))
        self.assertTrue((ROOT/SOLUTION).read_bytes().startswith(b"%PDF-"))

    def test_all_57_country_names_match_visual_reference(self):
        expected = "Indonesia|North Korea|Nigeria|Afghanistan|Thailand|Finland|Slovakia|Latvia|China|Ghana|Iraq|Holland (The Netherlands)|Yemen|Pakistan|United States of America|Algeria|Iceland|Nepal|Denmark|Senegal|India|Azerbaijan|Norway|Guatemala|Cameroon|United Arab Emirates|Israel|Colombia|Somalia|South Korea|Ireland|Venezuela|Serbia|South Africa|Albania|Cuba|Peru|Jordan|Luxembourg|Vietnam|Saudi Arabia|New Zealand|Italy|Armenia|Syria|Iran|Bulgaria|Uzbekistan|Georgia|Turkey|Morocco|Canada|Laos|Kenya|Portugal|Bolivia|Moldova"
        self.assertEqual(self.reference["country_names_by_id"], {str(i):name for i,name in enumerate(expected.split("|"), 1)})

    def test_two_extractors_agree_on_country_names(self):
        self.assertEqual(country_map(pdf_text(ROOT/SOLUTION)[0]), country_map(poppler_text(ROOT/SOLUTION)))
        self.assertEqual(reference_data(), self.reference)

    def test_missing_country_id_rejected(self):
        text = pdf_text(ROOT/SOLUTION)[0].replace("57.", "XX.", 1)
        with self.assertRaisesRegex(ValueError, "Country ID membership"):
            country_map(text)

    def test_duplicate_country_id_rejected(self):
        text = pdf_text(ROOT/SOLUTION)[0].replace("57.", "56.", 1)
        with self.assertRaisesRegex(ValueError, "Country ID membership"):
            country_map(text)

    def test_public_source_image_and_two_tasks_preserved(self):
        prompt = self.row["problem_description"]
        self.assertIn("(a) Identify the countries.", prompt)
        self.assertIn("(b) Make a guess", prompt)
        self.assertIn("Boris Iomdin", prompt)
        self.assertIn("57", prompt)
        public = [a for a in self.row["assets"] if a["role"] == "agent_visible"]
        self.assertEqual([a["path"] for a in public], [SOURCE, INPUT_IMAGE])
        self.assertEqual(public[1]["original_pdf_page"], 1)
        evidence = read(ROOT/CACHE/"source_review.json")["sources"][0]
        self.assertEqual(sha(ROOT/INPUT_IMAGE), evidence["rendered_sha256"])

    def test_pronunciation_preserved_as_image_not_corrupted_text(self):
        pronunciation = self.reference["pronunciation_reference"]
        self.assertEqual(pronunciation["covers_ids"], list(range(1,58)))
        self.assertEqual(pronunciation["image_file"], JUDGE_IMAGE)
        self.assertFalse(pronunciation["text_transcription_verified"])
        self.assertNotIn("kawhl", str(self.reference))
        self.assertIsNone(self.row["gold_label"]["expected_answer"])
        self.assertEqual(self.row["gold_label"]["parts"], [])
        evidence = read(ROOT/CACHE/"source_review.json")["sources"][1]
        self.assertEqual(sha(ROOT/JUDGE_IMAGE), evidence["rendered_sha256"])

    def test_empty_judge_link_repaired_exactly(self):
        self.assertEqual(self.before["evaluation"]["judge_assets"], [])
        expected = [SOLUTION, JUDGE_IMAGE, REFERENCE]
        self.assertEqual(self.row["evaluation"]["judge_assets"], expected)
        self.assertEqual([a["path"] for a in self.row["assets"] if a["role"] == "judge_only"], expected)
        self.assertEqual(self.row["gold_label"]["reference_assets"], expected)

    def test_no_fabricated_57_114_or_100_point_maximum(self):
        self.assertIsNone(self.row["total_points"])
        self.assertIsNone(self.reference["total_points"])
        self.assertEqual(self.reference["criteria"], [])
        self.assertFalse(self.reference["official_weights_verified"])
        self.assertEqual(self.reference["legacy_proxy"]["total_points"], 100)
        self.assertFalse(self.reference["legacy_proxy"]["active_for_this_record"])
        card = next(c for c in self.plan["writes"][CARDS]["records"] if c["problem_id"] == PID)
        self.assertFalse(card["numeric_rubric_available"])
        self.assertIsNone(card["gold_max_score"])
        self.assertEqual(card["gold_part_weights"], [])

    def test_no_false_readiness(self):
        self.assertEqual(self.row["evaluation"]["status"], "not_ready")
        self.assertIsNone(self.row["evaluation"]["evaluator_id"])
        scoring = self.plan["writes"][RULE]["scoring"]
        self.assertIsNone(scoring["record_evaluator_overrides"][PID])
        self.assertEqual(scoring["record_rubric_overrides"][PID], REFERENCE)
        self.assertIsNone(scoring["record_score_basis_overrides"][PID]["max_score"])

    def test_public_and_judge_assets_isolated(self):
        check_packages(self.row, ROOT/CACHE/"stage")

    def test_identity_licensing_status_and_baseline_preserved(self):
        for key in ("year", "team_size", "split", "license", "status", "eval_unit", "source_file", "solution_file"):
            self.assertEqual(self.row[key], self.before[key])
        self.assertEqual(self.row["gold_label"]["human_baseline"], self.before["gold_label"]["human_baseline"])

    def test_no_need_to_rewrite_unchanged_statistics(self):
        self.assertIn("data/viz/summary.json", self.plan["protected_hashes"])
        self.assertFalse(any(path.startswith("data/viz/") for path in self.plan["writes"]))
        self.assertEqual(self.plan["writes"][RULE]["scoring"]["evaluation_status_counts"], {"not_ready":9, "ready":8, "ready_with_limitations":1})


if __name__ == "__main__":
    unittest.main()
