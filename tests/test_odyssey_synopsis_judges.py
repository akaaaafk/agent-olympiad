"""Guard title-based selection and written-only scope of archived synopses."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from expand_main_odyssey_judges import CASES, select_synopsis


class OdysseySynopsisTests(unittest.TestCase):
    def test_selection_does_not_assume_archive_position_is_problem_number(self):
        cases = {
            2014: ('Seeing is Believing', 'The World'),
            2015: ('Silent Movie', 'Wacky Weather Warning'),
            2022: ('Life is a Circus!', 'Tri-Cycle Transport'),
            2023: ('The Most Dramatic Problem Ever!!!', 'Pirates and the Treasure'),
            2025: ('AstronOMical Odyssey!', 'Wonderful World'),
        }
        for year, (title, excluded) in cases.items():
            text = (ROOT / f'data/raw/odyssey_of_the_mind/{year}/long_term_synopses.md').read_text(encoding='utf-8')
            selected = select_synopsis(text, title)
            self.assertTrue(selected.startswith(title))
            self.assertNotIn(excluded, selected)
        with self.assertRaises(ValueError):
            select_synopsis('---\n1. Example text\n2. Example duplicate', 'Example')
        with self.assertRaises(ValueError):
            select_synopsis('---\n1. Other text', 'Example')

    def test_every_promoted_task_binds_exact_source_and_unique_rubric(self):
        rows = json.loads((ROOT / 'data/benchmarks/odyssey_of_the_mind/benchmark.json').read_text(encoding='utf-8'))
        selected = [r for r in rows if r['year'] in CASES and r['problem_id'].endswith('_synopses')]
        self.assertEqual(len(selected), 16)
        self.assertEqual(len({r['evaluation']['rubric_path'] for r in selected}), 16)
        for row in selected:
            ev = row['evaluation']
            rubric = json.loads((ROOT / ev['rubric_path']).read_text(encoding='utf-8'))
            source = rubric['provenance']['sources'][0]
            raw = (ROOT / source['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
            self.assertIn(select_synopsis(raw.decode('utf-8'), source['selected_title']), row['problem_description'])
            self.assertEqual(sum(c['max_score'] for c in rubric['criteria']), 100)
            self.assertEqual(ev['reference_policy'], 'rubric_only')
            self.assertFalse(ev['official_score_equivalent'])
            self.assertIn('do not claim live performance', row['problem_description'])
            self.assertNotIn('Opposites Distract', json.dumps(rubric))
        silent = next(r for r in selected if r['year'] == 2015)
        self.assertIn('Movie characters do not speak', silent['problem_description'])
        # Verified practice records were removed from the active catalog.
        self.assertTrue(all(r['problem_id'].endswith('_synopses') for r in rows))


if __name__ == '__main__':
    unittest.main()
