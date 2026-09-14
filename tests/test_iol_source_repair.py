"""Regression guards for the bounded 2026-09-13 IOL source repair."""
import io
from pathlib import Path
import unittest
import zipfile

from scripts.repair_iol_sources_20260913 import (
    ROOT, CACHE, CHANGED, REMOVED, RAW, RUBRIC, RUBRIC16, KEY16,
    read, pdf_text, point_map, audio_map, zip_inventory, check_packages,
)


class IOLSourceRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read(ROOT / CACHE / "plan.json")
        cls.rows = {r["problem_id"]: r for r in cls.plan["active_rows"]}

    def test_exact_exclusion_and_preservation(self):
        self.assertEqual({r["problem_id"] for r in self.plan["removed_rows"]}, REMOVED)
        self.assertEqual(len(self.rows), 18)
        self.assertEqual([r for r in self.plan["active_rows"] if r["problem_id"] not in CHANGED],
                         [r for r in self.plan["before_rows"] if r["problem_id"] not in REMOVED | CHANGED])

    def test_html_is_not_a_solution_pdf(self):
        for year in (2004, 2005, 2007, 2024):
            with self.assertRaisesRegex(ValueError, "Not a PDF"):
                pdf_text(ROOT / f"data/raw/iol/iol-{year}-team-sol.en.pdf")

    def test_recovered_pdf_shapes(self):
        self.assertEqual(len(pdf_text(ROOT / RAW / "2007/iol-2007-team-sol.m.pdf")), 1)
        self.assertEqual(len(pdf_text(ROOT / RAW / "2024/iol-2024-t-1-slide.pdf")), 12)
        self.assertEqual(len(pdf_text(ROOT / RAW / "2014/iol-2014-team.m.pdf")), 3)

    def test_zip_traversal_and_non_audio_evidence(self):
        for name in ("../escape.wav", "/escape.wav", "C:/escape.wav", "..\\escape.wav"):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as archive:
                archive.writestr(name, b"test")
            stream.seek(0)
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP member"):
                zip_inventory(stream)
        for year in (2004, 2005):
            entries = zip_inventory(ROOT / RAW / f"{year}/iol-{year}-team.m.zip")
            payloads = [e["name"] for e in entries if not e["name"].endswith("/") and not e["name"].startswith("__MACOSX/")]
            self.assertTrue(payloads)
            self.assertTrue(all(n.endswith((".mp3", ".wav")) for n in payloads))

    def test_114_audio_codes_match_answer_map(self):
        row = self.rows["iol_team_2016"]
        wavs = [a for a in row["assets"] if a["mime_type"] == "audio/wav"]
        mapping = self.plan["writes"][KEY16]["word_number_to_audio_code"]
        self.assertEqual(len(wavs), 114)
        self.assertEqual({Path(a["path"]).stem for a in wavs}, set(mapping.values()))
        self.assertEqual(set(mapping), {str(i) for i in range(1, 115)})
        self.assertEqual(mapping, audio_map("\n".join(pdf_text(ROOT / row["solution_file"]))))
        self.assertFalse(self.plan["writes"][KEY16]["part_b_reference_available"])

    def test_printed_2016_denominator(self):
        row = self.rows["iol_team_2016"]
        value = point_map(pdf_text(ROOT / row["source_file"]), 2016)
        self.assertEqual(value["total_points"], 120)
        self.assertEqual([c["max_score"] for c in value["criteria"]], [114, 6])
        self.assertEqual(row["total_points"], self.plan["writes"][RUBRIC16]["total_points"])

    def test_2024_tiebreak_not_regular_denominator(self):
        row = self.rows["iol_team_2024"]
        value = point_map(pdf_text(ROOT / row["source_file"]), 2024)
        self.assertEqual(value["total_points"], 90)
        self.assertEqual(value["tie_breaker"]["max_score"], 10)
        self.assertFalse(value["tie_breaker"]["included_in_regular_total"])
        self.assertEqual([c["id"] for c in value["criteria"]], list("ABCDEFGHIJKL"))
        self.assertEqual(row["total_points"], self.plan["writes"][RUBRIC]["total_points"])

    def test_partial_references_are_not_promoted(self):
        for year in (2007, 2016, 2024):
            row = self.rows[f"iol_team_{year}"]
            self.assertEqual(row["evaluation"]["status"], "not_ready")
            self.assertIsNone(row["evaluation"]["evaluator_id"])
            self.assertFalse(row["gold_label"]["answer_reference_complete"])
        self.assertIn("parent-child", str(self.rows["iol_team_2007"]["evaluation"]["limitations"]))
        self.assertIn("Assignment E", str(self.rows["iol_team_2024"]["evaluation"]["limitations"]))

    def test_multilingual_and_clean_english_text(self):
        for year in (2014, 2016):
            self.assertEqual(self.rows[f"iol_team_{year}"]["source_review"]["solution_language"], "multilingual")
            self.assertNotIn("only archived solution is the Mongolian", str(self.rows[f"iol_team_{year}"]))
        text = self.rows["iol_team_2014"]["problem_description"]
        self.assertIn("effective remedy", text)
        self.assertIn("scientific advancement", text)
        self.assertNotIn("/x", text)
        self.assertFalse(any(ord(c) < 32 and c not in "\n\r\t" for c in text))

    def test_null_evaluator_overrides(self):
        rule = self.plan["writes"]["data/rules/iol_team/evaluation.json"]
        for row in self.rows.values():
            if row["evaluation"].get("evaluator_id") is None:
                self.assertIn(row["problem_id"], rule["scoring"]["record_evaluator_overrides"])
                self.assertIsNone(rule["scoring"]["record_evaluator_overrides"][row["problem_id"]])

    def test_no_judge_material_in_public_packages(self):
        check_packages(list(self.rows.values()), ROOT / CACHE / "stage")

    def test_identity_baselines_and_license_not_invented(self):
        before = {r["problem_id"]: r for r in self.plan["before_rows"]}
        for pid in CHANGED:
            row = self.rows[pid]
            for key in ("year", "team_size", "split", "eval_unit", "status"):
                self.assertEqual(row[key], before[pid][key])
            self.assertEqual(row["gold_label"]["human_baseline"], before[pid]["gold_label"]["human_baseline"])
            for key in ("status", "spdx_id", "redistribution_allowed"):
                self.assertEqual(row["license"][key], before[pid]["license"][key])


if __name__ == "__main__":
    unittest.main()
