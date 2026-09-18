import json
import sys
from copy import deepcopy
from pathlib import Path
import unittest
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import run_pipeline
from evaluation.slides_pipeline import resolve_problem_task_pdf

class IolBundleTests(unittest.TestCase):
    def row(self):
        return next(r for r in json.loads((ROOT/'data/benchmarks/iol_team/benchmark.json').read_text(encoding='utf-8')) if r['problem_id']=='iol_team_2014')

    def test_both_entry_points_deliver_all_seven_original_pages(self):
        row=self.row();path=run_pipeline.artifact_task_pdf(row)
        self.assertEqual(path,resolve_problem_task_pdf(row,ROOT))
        with pymupdf.open(path) as bundle:
            self.assertEqual(len(bundle),7)
            index=0
            for source in row['provenance']['pdftext_bundle']['original_contestant_pdfs']:
                with pymupdf.open(ROOT/source['path']) as original:
                    for page in original:
                        self.assertEqual(page.get_text(),bundle[index].get_text())
                        self.assertEqual(page.get_pixmap().samples,bundle[index].get_pixmap().samples)
                        index+=1
            self.assertEqual(index,7)

    def test_rejects_solution_or_incomplete_or_changed_bundle(self):
        original=self.row()
        for kind in ['solution','missing_supplement','changed']:
            row=deepcopy(original);bundle=row['provenance']['pdftext_bundle']
            if kind=='solution':bundle['path']=row['solution_file']
            elif kind=='missing_supplement':bundle['original_contestant_pdfs'].pop()
            else:bundle['sha256']='0'*64
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):run_pipeline.artifact_task_pdf(row)
                with self.assertRaises(ValueError):resolve_problem_task_pdf(row,ROOT)

if __name__=='__main__':unittest.main()
