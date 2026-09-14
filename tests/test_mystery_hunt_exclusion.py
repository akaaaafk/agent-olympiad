"""Set subtraction and scoring-denominator tests for the approved exclusion."""
from copy import deepcopy
import unittest

from scripts.exclude_mystery_hunt_subset_20260913 import IDS, partition, score_summary


def row(pid, year=1999, answer="EXAMPLE"):
    return dict(problem_id=pid, year=year, total_points=None, split="unspecified",
                gold_label=dict(parts=[dict(id="1", expected=answer, points=1.0)]))


class MysteryHuntExclusionTests(unittest.TestCase):
    def test_exact_partition_preserves_rows_order_and_scores(self):
        rows = [row("a"), row("b"), row("c")]
        original = deepcopy(rows)
        active, excluded = partition(rows, {"b"})
        self.assertEqual(active, [original[0], original[2]])
        self.assertEqual(excluded, [original[1]])
        self.assertEqual(rows, original)
        self.assertEqual(score_summary(active)["max_score"], 2.0)

    def test_missing_requested_id_is_rejected(self):
        with self.assertRaises(ValueError):
            partition([row("a")], {"b"})

    def test_duplicate_record_is_rejected(self):
        with self.assertRaises(ValueError):
            partition([row("a"), row("a")], {"a"})

    def test_denominators_are_by_retained_id_not_old_pool_size(self):
        rows = [row("a", 1999), row("b", 1999), row("c", 2006)]
        active, _ = partition(rows, {"a"})
        scores = score_summary(active)
        self.assertEqual(scores["max_score"], 2.0)
        self.assertEqual(scores["by_year"]["1999"]["max_score"], 1.0)
        self.assertEqual(scores["by_year"]["2006"]["max_score"], 1.0)
        self.assertEqual(set(scores["max_score_by_problem"]), {"b", "c"})

    def test_empty_pool_has_no_percentage_or_fabricated_earned_score(self):
        scores = score_summary([])
        self.assertEqual(scores["max_score"], 0)
        self.assertNotIn("score", scores)
        self.assertNotIn("percentage", scores)
        self.assertEqual(scores["by_year"], {})

    def test_different_scoring_contract_requires_review(self):
        changed = row("a")
        changed["gold_label"]["parts"][0]["points"] = 2
        with self.assertRaises(ValueError):
            score_summary([changed])

    def test_missing_answer_cannot_be_counted_as_verified_weight(self):
        with self.assertRaises(ValueError):
            score_summary([row("a", answer="")])

    def test_approved_set_has_only_the_fourteen_requested_ids(self):
        self.assertEqual(len(IDS), 14)
        self.assertIn("mystery_hunt_00819", IDS)
        self.assertNotIn("mystery_hunt_00009", IDS)
        self.assertNotIn("mystery_hunt_00015", IDS)


if __name__ == "__main__":
    unittest.main()
