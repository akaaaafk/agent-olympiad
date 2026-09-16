"""Frozen source-bound checks for IOL 2017, not dependent on later catalog counts."""
import unittest

from scripts.repair_iol_emoji_20260913 import (
    ROOT, CACHE, PID, LABELS, SOURCE, SOLUTION, SOURCE_SHA, SOLUTION_SHA,
    REFERENCE, RULE, CARDS, UNMATCHED, read, sha, pdf_text, poppler_text,
    descriptions, answer_map, reference_data, check_packages,
)


class IOLEmojiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read(ROOT/CACHE/"plan.json")
        cls.row = next(r for r in cls.plan["rows"] if r["problem_id"] == PID)
        cls.before = next(r for r in cls.plan["before_rows"] if r["problem_id"] == PID)
        cls.reference = cls.plan["writes"][REFERENCE]

    def test_exact_scope_no_year_deletion(self):
        before, after = self.plan["before_rows"], self.plan["rows"]
        self.assertEqual(len(after), 18)
        self.assertEqual({r["problem_id"] for r in before}, {r["problem_id"] for r in after})
        self.assertEqual([r for r in before if r["problem_id"] != PID], [r for r in after if r["problem_id"] != PID])

    def test_original_sources_preserved(self):
        self.assertEqual(sha(ROOT/SOURCE), SOURCE_SHA)
        self.assertEqual(sha(ROOT/SOLUTION), SOLUTION_SHA)
        self.assertEqual(len(pdf_text(ROOT/SOURCE)), 4)
        self.assertEqual(len(pdf_text(ROOT/SOLUTION)), 3)

    def test_public_descriptions_two_independent_extractors(self):
        native = descriptions(pdf_text(ROOT/SOURCE)[1])
        independent = descriptions(poppler_text(ROOT/SOURCE).split("\f")[1])
        self.assertEqual(native, independent)
        self.assertEqual(list(native), LABELS)
        self.assertEqual(native["CV"], "telapak tangan terbuka dengan jari rapat")
        for label, phrase in native.items():
            self.assertIn(label+" "+phrase, self.row["problem_description"])

    def test_all_four_tasks_preserved_without_font_controls(self):
        prompt = self.row["problem_description"]
        for part in "abcd":
            self.assertIn("("+part+")", prompt)
        self.assertFalse(any(ord(ch) < 32 and ch not in "\n\t\r" for ch in prompt))
        self.assertIn("Some emoji are not described at all", prompt)
        self.assertIn("English text: Boris Iomdin", prompt)

    def test_full_mapping_matches_visual_transcription(self):
        expected = "AA84 AB7 AC19 AD13 AE15 AF85 AG62 AH36 AI34 AJ47 AK48 AL50 AM49 AN51 AO35 AP30 AQ25 AR33 AS45 AT2 AU4 AV52 AW53 AX67 AY46 AZ57 BA82 BB78 BC74 BD56 BE44 BF9 BG22 BH6 BI3 BJ54 BK41 BL58 BM8 BN28 BO32 BP5 BQ70 BR87 BS31 BT23 BU1 BV43 BW42 BX37 BY68 BZ11 CA38 CB12 CC28 CD86 CE83 CF39 CG17 CH20 CI55 CJ75 CK60 CL40 CM14 CN10 CO16 CP26 CQ7 CR13 CS19 CT29 CU61 CV62 CW76 CX69 CY52 CZ10 DA16 DB63 DC72 DD71 DE77 DF40 DG29 DH18 DI27 DJ64 DK65 DL80 DM66 DN24 DO21"
        mapping = {token[:2]:int(token[2:]) for token in expected.split()}
        self.assertEqual(self.reference["label_to_emoji_id"], mapping)
        self.assertEqual(reference_data()[1], self.reference)

    def test_duplicates_preserved_not_collapsed_into_scores(self):
        mapping = self.reference["label_to_emoji_id"]
        self.assertEqual(len(mapping), 93)
        self.assertEqual(len(set(mapping.values())), 83)
        self.assertEqual(len(self.reference["duplicate_description_groups"]), 10)
        self.assertEqual(self.reference["duplicate_description_groups"]["28"], ["BN", "CC"])
        self.assertTrue(self.row["scoring_components"]["description_count_is_not_a_score"])

    def test_exact_unmatched_complement(self):
        mapping = self.reference["label_to_emoji_id"]
        self.assertEqual(set(range(1,88))-set(mapping.values()), set(UNMATCHED))
        self.assertEqual({r["emoji_id"]:r["indonesian"] for r in self.reference["unlabelled_emoji_descriptions"]}, UNMATCHED)

    def test_missing_label_rejected(self):
        text = "\n".join(pdf_text(ROOT/SOLUTION)).replace("AA", "XX", 1)
        with self.assertRaisesRegex(ValueError, "Answer labels differ"):
            answer_map(text)

    def test_wrong_complement_rejected(self):
        text = poppler_text(ROOT/SOLUTION)
        text = text.replace("84   ", "59   ", 1)
        with self.assertRaisesRegex(ValueError, "Unmatched emoji differ"):
            answer_map(text)

    def test_black_blue_identity_not_inferred_from_unicode(self):
        self.assertEqual(self.reference["label_to_emoji_id"]["AX"], 67)
        self.assertEqual(UNMATCHED[73], "hati biru")
        self.assertIn("not extracted Unicode", self.reference["emoji_identity_policy"])
        self.assertNotIn("💙", str(self.reference))

    def test_official_score_unknown_and_proxy_disabled(self):
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

    def test_no_false_readiness_or_fabricated_grammar(self):
        self.assertEqual(self.row["evaluation"]["status"], "not_ready")
        self.assertIsNone(self.row["evaluation"]["evaluator_id"])
        self.assertIsNone(self.plan["writes"][RULE]["scoring"]["record_evaluator_overrides"][PID])
        self.assertIsNone(self.row["gold_label"]["expected_answer"])
        self.assertEqual(self.row["gold_label"]["parts"], [])
        self.assertIn("No explicit short-grammar", self.reference["coverage"]["d"])

    def test_public_hidden_isolation(self):
        check_packages(self.row, ROOT/CACHE/"stage")
        self.assertEqual([a["original_pdf_page"] for a in self.row["assets"] if a["mime_type"] == "image/png"], [3,4])
        self.assertEqual([a["path"] for a in self.row["assets"] if a["role"] == "judge_only"], [SOLUTION, REFERENCE])

    def test_identity_licensing_and_baseline_preserved(self):
        for key in ("year", "team_size", "split", "license", "status", "eval_unit", "source_file", "solution_file"):
            self.assertEqual(self.row[key], self.before[key])
        self.assertEqual(self.row["gold_label"]["human_baseline"], self.before["gold_label"]["human_baseline"])


if __name__ == "__main__":
    unittest.main()
