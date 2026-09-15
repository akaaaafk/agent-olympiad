from copy import deepcopy
import unittest

from scripts.exclude_ijso_answerless_years_20260913 import (
    IDS, YEARS, has_answer_material, partition, score_membership,
)


def row(year):
    return dict(problem_id=f"ijso_practical_{year}_team_practical_{year}", year=year,
        total_points=None, gold_label=dict(expected_answer=None, parts=[]), assets=[],
        evaluation=dict(status="not_ready", judge_assets=[], rubric_path="generic.json"))


class IJSOAnswerlessExclusionTests(unittest.TestCase):
    def test_exact_years_only(self):
        self.assertEqual(YEARS, {2005, 2007, 2008, 2024, 2025})
        self.assertEqual(len(IDS), 5)
        self.assertNotIn(row(2011)["problem_id"], IDS)

    def test_partition_is_order_preserving_and_non_mutating(self):
        rows = [row(y) for y in [2004, 2005, 2007, 2008, 2011, 2024, 2025]]
        before = deepcopy(rows)
        active, removed = partition(rows)
        self.assertEqual([x["year"] for x in active], [2004, 2011])
        self.assertEqual([x["year"] for x in removed], [2005, 2007, 2008, 2024, 2025])
        self.assertEqual(rows, before)

    def test_a_newly_recovered_answer_blocks_exclusion(self):
        rows = [row(y) for y in sorted(YEARS)]
        rows[0]["solution_file"] = "recovered.pdf"
        with self.assertRaises(ValueError):
            partition(rows)

    def test_partial_reference_counts_as_material(self):
        r = row(2011)
        r["gold_label"]["parts"] = [dict(id="all", expected=None, reference="Biology marking")]
        self.assertTrue(has_answer_material(r))

    def test_judge_asset_counts_as_material(self):
        r = row(2007)
        r["assets"] = [dict(path="marking.pdf", role="judge_only")]
        self.assertTrue(has_answer_material(r))

    def test_generic_rubric_alone_is_not_an_answer(self):
        r = row(2005)
        r["gold_label"]["grading_rubric"] = "Report quality rubric"
        r["total_points"] = 20
        self.assertFalse(has_answer_material(r))

    def test_missing_selected_id_is_rejected(self):
        with self.assertRaises(ValueError):
            partition([row(2005)])

    def test_rubric_capacities_are_not_claimed_as_official_aggregate(self):
        r = row(2011)
        c = dict(problem_id=r["problem_id"], rubrics=[dict(path="generic.json", total_points=40)])
        result = score_membership([r], [c])
        self.assertIsNone(result["aggregate_official_max_score"])
        self.assertIsNone(result["records"][0]["official_total_points"])
        self.assertEqual(result["records"][0]["rubric_capacities"][0]["total_points"], 40)
        self.assertFalse(result["historical_scores_modified"])


if __name__ == "__main__":
    unittest.main()
