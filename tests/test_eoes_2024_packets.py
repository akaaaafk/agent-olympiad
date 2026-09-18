"""Verify original-page preservation and hidden-marking separation."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import pymupdf
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from problem_pdf import approved_assets


class EOESPacketTests(unittest.TestCase):
    def test_all_packet_pages_match_original_inputs(self):
        rows = json.loads((ROOT / 'data/benchmarks/eoes/benchmark.json').read_text(encoding='utf-8'))
        selected = [r for r in rows if r['year'] == 2024]
        self.assertEqual(len(selected), 2)
        for row in selected:
            review = row['source_review']['eoes_2024_packet']
            visible = [a for a in row['assets'] if a['role'] == 'agent_visible']
            self.assertEqual(len(visible), 1)
            with pymupdf.open(ROOT / visible[0]['path']) as merged:
                self.assertEqual(len(merged), review['task_pages'] + review['blank_answer_pages'])
                offset = 0
                for source in review['sources']:
                    raw = (ROOT / source['path']).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
                    with pymupdf.open(stream=raw, filetype='pdf') as original:
                        for i, page in enumerate(original):
                            copied = merged[offset + i]
                            self.assertEqual(page.rect, copied.rect)
                            self.assertEqual(page.get_text(), copied.get_text())
                            self.assertEqual(page.read_contents(), copied.read_contents())
                            # Resource copying can change MuPDF's low-level shade rounding.
                            # Keep exact drawing/text checks and tightly bound pixel changes.
                            a = page.get_pixmap(matrix=pymupdf.Matrix(.5,.5))
                            b = copied.get_pixmap(matrix=pymupdf.Matrix(.5,.5))
                            delta = ImageChops.difference(Image.frombytes('RGB', (a.width,a.height), a.samples),
                                                          Image.frombytes('RGB', (b.width,b.height), b.samples))
                            self.assertLessEqual(max(v[1] for v in delta.getextrema()), 5)
                            self.assertLess(max(ImageStat.Stat(delta).mean), .25)
                        offset += len(original)

    def test_marking_is_hidden_and_scope_is_runtime_visible(self):
        rows = json.loads((ROOT / 'data/benchmarks/eoes/benchmark.json').read_text(encoding='utf-8'))
        for row in [r for r in rows if r['year'] == 2024]:
            hidden = [a for a in row['assets'] if a['role'] == 'judge_only']
            self.assertTrue(hidden)
            readable = approved_assets(row)
            self.assertEqual(len(readable), 1)
            self.assertNotIn(readable[0]['sha256'], {a['sha256'] for a in hidden})
            ev = row['evaluation']
            self.assertFalse(ev['official_score_equivalent'])
            self.assertEqual(ev['reference_policy'], 'rubric_only')
            self.assertIn('NOT MEASURED', ev['benchmark_instructions'])
            self.assertIn('not the official practical', ev['benchmark_instructions'])
            rubric = json.loads((ROOT / ev['rubric_path']).read_text(encoding='utf-8'))
            self.assertEqual([c['max_score'] for c in rubric['criteria']], [30,25,30,15])


if __name__ == '__main__':
    unittest.main()
