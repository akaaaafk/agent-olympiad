"""Printed allocation and page-boundary regression checks; no grading invented."""
from copy import deepcopy
import unittest

from scripts.repair_ijso_2005_packet_20260913 import extract_allocations, PAGES


def fixture(inline=False):
    separator = " " if inline else "\n"
    def item(key, text):
        return key + separator + text + "\n"
    first = "Experiment-I : Effects of Light (5.5 points)\n"
    first += item("I-1", "Prepare the apparatus.")
    first += item("I-2", "Record (1 point). Plot (1.5 points).")
    first += item("I-3", "Record (1 points). Plot (1.5 points).")
    first += item("I-4", "Choose (0.5 point).")
    second = "Experiment-II : Effects of Wind (3 points)\n"
    second += item("II-1", "Prepare the apparatus.")
    second += item("II-2", "Record (1 point). Plot (1.5 points).")
    second += item("II-3", "Choose (0.5 point).")
    second += "Experiment-III : Effects of Medium (3 points)\n"
    second += item("III-1", "Prepare the apparatus.")
    second += item("III-2", "Prepare the apparatus.")
    second += item("III-3", "Record (1 point). Plot (1.5 points).")
    second += item("III-4", "Choose (0.5 point).")
    pages = ["EXPERIMENTAL EXAMINATION\nMaximum points for problem is 20", "Objectives", first, second]
    for nums in (range(1, 4), range(4, 8), range(8, 13), range(13, 16)):
        pages.append("".join(item(str(n) + ".", f"Question ({0.75 if n <= 2 else 1 if n == 3 else 0.5} points).") for n in nums))
    return pages


class IJSO2005PacketTests(unittest.TestCase):
    def test_totals_and_components(self):
        result = extract_allocations(fixture())
        self.assertEqual(result["total_points"], 20)
        self.assertEqual(len(result["criteria"]), 26)
        self.assertEqual(result["section_totals"], {"I": 5.5, "II": 3, "III": 3, "E": 8.5})

    def test_poppler_inline_and_mupdf_line_layout_agree(self):
        self.assertEqual(extract_allocations(fixture()), extract_allocations(fixture(inline=True)))

    def test_no_answer_or_measurement_is_created(self):
        result = extract_allocations(fixture())
        for c in result["criteria"]:
            self.assertNotIn("expected", c)
            self.assertNotIn("reference_answer", c)
        missing = [c["id"] for c in result["criteria"] if c.get("answer_sheet_choices_missing")]
        self.assertEqual(missing, ["I-4.conclusion_choice", "II-3.conclusion_choice", "III-4.conclusion_choice"])

    def test_reject_wrong_header(self):
        pages = fixture()
        pages[0] = pages[0].replace("20", "40")
        with self.assertRaises(ValueError):
            extract_allocations(pages)

    def test_reject_altered_point(self):
        pages = fixture()
        pages[2] = pages[2].replace("(1.5 points)", "(2 points)", 1)
        with self.assertRaises(ValueError):
            extract_allocations(pages)

    def test_reject_missing_question(self):
        pages = fixture()
        pages[-1] = pages[-1].replace("15.\n", "16.\n")
        with self.assertRaises(ValueError):
            extract_allocations(pages)

    def test_does_not_mutate_input(self):
        pages = fixture()
        before = deepcopy(pages)
        extract_allocations(pages)
        self.assertEqual(pages, before)

    def test_page_selection_excludes_both_other_rounds(self):
        self.assertEqual(PAGES, list(range(7, 15)))
        self.assertEqual(len(set(range(24)) - set(PAGES)), 16)


if __name__ == "__main__":
    unittest.main()
