"""Verify scoped historical defense-plan grading without fake execution evidence."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ArchivedDefensePlanningTests(unittest.TestCase):
    def test_five_packets_have_bound_year_specific_written_rubrics(self):
        rows = json.loads((ROOT / 'data/benchmarks/ccdc/benchmark.json').read_text(encoding='utf-8'))
        selected = [r for r in rows if 'before_main_report_review' in r['evaluation'] and r['year'] in {2013, 2014, 2020, 2021, 2026}]
        self.assertEqual({r['year'] for r in selected}, {2013, 2014, 2020, 2021, 2026})
        self.assertEqual(len(selected), 5)
        titles = set()
        for row in selected:
            ev = row['evaluation']
            rubric = json.loads((ROOT / ev['rubric_path']).read_text(encoding='utf-8'))
            source = rubric['provenance']['sources'][0]
            self.assertEqual(hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest(), source['sha256'])
            self.assertIn(source['network_map_page'], source['pages'])
            self.assertEqual([c['max_score'] for c in rubric['criteria']], [50, 50])
            self.assertEqual(ev['reference_policy'], 'rubric_only')
            self.assertFalse(ev['official_score_equivalent'])
            self.assertIn('not an operational cyber-defense run', ' '.join(ev['limitations']))
            self.assertIn('cite the conflicting passages', row['problem_description'])
            self.assertIn('No live network or event-day injects', row['problem_description'])
            titles.add(rubric['title'])
        self.assertEqual(len(titles), 5)

    def test_scanned_sources_keep_ocr_subordinate_and_bind_original_map_pages(self):
        rows = json.loads((ROOT / 'data/benchmarks/ccdc/benchmark.json').read_text(encoding='utf-8'))
        maps = {2015: 22, 2016: 21, 2017: 21, 2018: 21, 2019: 20}
        selected = [r for r in rows if r['year'] in maps]
        self.assertEqual(len(selected), 5)
        for row in selected:
            ev = row['evaluation']
            rubric = json.loads((ROOT / ev['rubric_path']).read_text(encoding='utf-8'))
            self.assertEqual(ev['status'], 'ready_with_limitations')
            self.assertFalse(ev['official_score_equivalent'])
            self.assertEqual(rubric['provenance']['visual_review']['network_map_pdf_page'], maps[row['year']])
            sources = rubric['provenance']['sources']
            self.assertEqual(len(sources), 2)
            self.assertEqual(sources[1]['role'], 'searchable_ocr_not_authoritative')
            for source in sources:
                self.assertEqual(hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest(), source['sha256'])
            self.assertIn('Verify exact values against the original PDF', row['problem_description'])
            self.assertEqual(sum(c['max_score'] for c in rubric['criteria']), 100)
        self.assertIn('N7 branding', next(r for r in selected if r['year'] == 2017)['problem_description'])

    def test_incomplete_packets_stay_blocked_and_mini_selection_stays_2025(self):
        rows = json.loads((ROOT / 'data/benchmarks/ccdc/benchmark.json').read_text(encoding='utf-8'))
        self.assertFalse(any(r['year'] == 2022 for r in rows))
        self.assertFalse(any(r['problem_id'] == 'ccdc_2026-NCCDC-Wildcard' for r in rows))
        mini = json.loads((ROOT / 'data/mini_data/benchmarks/ccdc/benchmark.json').read_text(encoding='utf-8'))
        self.assertEqual([r['year'] for r in mini], [2025])

    def test_ready_packets_expose_reviewed_original_pdf_pages(self):
        import sys
        sys.path.insert(0, str(ROOT / 'src'))
        from problem_pdf import describe
        rows = json.loads((ROOT / 'data/benchmarks/ccdc/benchmark.json').read_text(encoding='utf-8'))
        ready = [r for r in rows if r['evaluation']['status'] == 'ready_with_limitations']
        self.assertEqual(len(ready), 12)
        for row in ready:
            self.assertTrue(describe(row), row['problem_id'])

    def test_wildcard_pairs_inputs_and_preserves_vm_specific_exceptions(self):
        import sys
        sys.path.insert(0, str(ROOT / 'src'))
        from problem_pdf import describe
        rows = json.loads((ROOT / 'data/benchmarks/ccdc/benchmark.json').read_text(encoding='utf-8'))
        row = next(r for r in rows if r['problem_id'] == 'ccdc_Wildcard26_Readme_http')
        self.assertEqual(len(row['assets']), 2)
        self.assertEqual([len(d['pages']) for d in describe(row)], [24, 3])
        rubric = json.loads((ROOT / row['evaluation']['rubric_path']).read_text(encoding='utf-8'))
        self.assertEqual(sum(c['max_score'] for c in rubric['criteria']), 100)
        self.assertEqual(len(rubric['criteria']), 9)
        criteria = {c['id']: c['description'] for c in rubric['criteria']}
        self.assertIn('rootful', criteria['mint'])
        self.assertIn('vsftpd', criteria['ubuntu_a'])
        self.assertIn('Squid', criteria['ubuntu_b'])
        self.assertIn('anonymous access', criteria['server2019'])
        self.assertIn('Do not install Windows Updates', criteria['windows11'])
        self.assertIn('Do not install Windows Updates', criteria['server2022'])
        self.assertIn('no new snapshots or clones', criteria['common'])
        self.assertFalse(row['evaluation']['official_score_equivalent'])
        self.assertEqual(row['evaluation']['reference_policy'], 'rubric_only')


if __name__ == '__main__':
    unittest.main()
