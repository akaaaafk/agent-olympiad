"""Source-bound IOL staged disclosure, media and score regression guards."""
from copy import deepcopy
import unittest
from pathlib import Path

from scripts.repair_iol_followup_20260913 import (
    ROOT,CACHE,IDS,INITIAL,RELEASE,RUBRIC,FORBIDDEN,read,sha,pdf_text,
    printed_2022,check_packages,
)


class IOLFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/"plan.json")
        cls.rows={r["problem_id"]:r for r in cls.plan["rows"]}

    def test_exact_scope_no_year_deletion(self):
        self.assertEqual(set(self.rows),{r["problem_id"] for r in self.plan["before_rows"]})
        self.assertEqual(len(self.rows),18)
        self.assertEqual([r for r in self.plan["rows"] if r["problem_id"] not in IDS],
                         [r for r in self.plan["before_rows"] if r["problem_id"] not in IDS])

    def test_2011_release_not_submission_time(self):
        manifest=read(ROOT/RELEASE)
        self.assertEqual(manifest["outputs"][0]["release_minute"],0)
        self.assertEqual(manifest["outputs"][0]["original_pages"],[1,2])
        self.assertEqual([v["release_minute"] for v in manifest["withheld_page_releases"]],[30,60,90,120,150])
        self.assertEqual([v["original_pages"] for v in manifest["withheld_page_releases"]],[[3],[4],[5],[6],[7]])
        self.assertEqual(manifest["final_solution_release_minute"],180)
        self.assertFalse(manifest["runtime_release_implemented"])

    def test_initial_pdf_excludes_later_hints(self):
        pages=pdf_text(ROOT/INITIAL)
        self.assertEqual(len(pages),2)
        self.assertIn("Distribute at 0 minutes",pages[1])
        self.assertIn("Answers as of 30 minutes",pages[1])
        self.assertFalse(any(term in "\n".join(pages) for term in FORBIDDEN))
        row=self.rows["iol_team_2011"]
        self.assertEqual([a["path"] for a in row["assets"] if a["role"]=="agent_visible"],[INITIAL])
        self.assertEqual(sha(ROOT/INITIAL),sha(ROOT/"output/pdf/iol_2011_initial.pdf"))

    def test_videos_cover_exact_given_examples(self):
        manifest=read(ROOT/CACHE/"video_manifest.json")
        expected={4,7,9,11,13,14,16,20,22,23,26,27,28,36,38,39,44,48}
        self.assertEqual(len(manifest["videos"]),18)
        self.assertEqual({v["example_id"] for v in manifest["videos"]},expected)
        self.assertTrue(all(v["full_decode_passed"] for v in manifest["videos"]))
        self.assertTrue(expected.isdisjoint(range(49,78)))
        row=self.rows["iol_team_2019"]
        assets=[a for a in row["assets"] if a["mime_type"]=="video/x-msvideo"]
        self.assertEqual({a["sha256"] for a in assets},{v["sha256"] for v in manifest["videos"]})

    def test_2022_four_official_subtotals(self):
        pages=pdf_text(ROOT/self.rows["iol_team_2022"]["source_file"])
        criteria=printed_2022(pages)
        self.assertEqual([c["max_score"] for c in criteria],[25]*4)
        self.assertEqual([c["id"] for c in criteria],["I","II","III","IV"])
        self.assertEqual(self.rows["iol_team_2022"]["total_points"],100)
        self.assertEqual(self.plan["writes"][RUBRIC]["criteria"],criteria)
        self.assertFalse(self.plan["writes"][RUBRIC]["within_part_weights_verified"])

    def test_altered_2022_subtotal_rejected(self):
        pages=pdf_text(ROOT/self.rows["iol_team_2022"]["source_file"])
        pages[1]=pages[1].replace("(25 points)","(30 points)")
        with self.assertRaisesRegex(ValueError,"allocation differs"):
            printed_2022(pages)

    def test_domain_marks_not_official_weights(self):
        row=self.rows["iol_team_2019"]
        self.assertIsNone(row["total_points"])
        self.assertIn("not evaluation weights",row["evaluation"]["score_basis"])
        self.assertEqual(row["gold_label"]["reference_format"],"pdf_images_required")
        self.assertIsNone(row["gold_label"]["expected_answer"])

    def test_no_false_readiness(self):
        overrides=self.plan["writes"]["data/rules/iol_team/evaluation.json"]["scoring"]["record_evaluator_overrides"]
        for pid in IDS:
            self.assertEqual(self.rows[pid]["evaluation"]["status"],"not_ready")
            self.assertIsNone(self.rows[pid]["evaluation"]["evaluator_id"])
            self.assertIn(pid,overrides)
            self.assertIsNone(overrides[pid])

    def test_public_hidden_isolation(self):
        check_packages(list(self.rows.values()),ROOT/CACHE/"stage")

    def test_baselines_and_identity_preserved(self):
        original={r["problem_id"]:r for r in self.plan["before_rows"]}
        for pid in IDS:
            for key in ("year","team_size","split","license","status","eval_unit","solution_file"):
                self.assertEqual(self.rows[pid][key],original[pid][key])
            self.assertEqual(self.rows[pid]["gold_label"]["human_baseline"],original[pid]["gold_label"]["human_baseline"])


if __name__=="__main__":
    unittest.main()
