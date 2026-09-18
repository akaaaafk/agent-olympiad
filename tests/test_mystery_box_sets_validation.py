"""Box Sets source completeness, solution isolation, rendering and grading."""
import json
from pathlib import Path
import sys
import unittest
import pymupdf
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from problem_pdf import read_problem_pdf
PID='mystery_hunt_01271'
def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))

class BoxSetsValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row=next(r for r in read('data/benchmarks/mystery_hunt/benchmark.json') if r['problem_id']==PID)
        cls.folder=(ROOT/cls.row['source_file']).parent

    def test_original_flavor_and_full_image_preserved(self):
        source=BeautifulSoup((self.folder/'puzzle.html').read_bytes(),'html.parser')
        original=BeautifulSoup((ROOT/self.row['source_review']['original_source_file']).read_bytes(),'html.parser')
        self.assertEqual(source.select_one('.flavortext').get_text(' ',strip=True),original.select_one('.flavortext').get_text(' ',strip=True))
        asset=next(a for a in self.row['assets'] if a['mime_type']=='application/pdf')
        with pymupdf.open(ROOT/asset['path']) as doc:
            self.assertEqual(len(doc),1)
            images=doc[0].get_images(); self.assertEqual(len(images),1)
            self.assertEqual(doc.extract_image(images[0][0])['image'],(self.folder/'box_sets.jpg').read_bytes())
            text=' '.join(doc[0].get_text().split())
            for p in source.select('.flavortext p'): self.assertIn(p.get_text(' ',strip=True),text)
            self.assertNotIn('SMACK',text.upper()); self.assertEqual(doc.embfile_count(),0)

    def test_official_answer_and_grading_boundaries(self):
        solution=BeautifulSoup((ROOT/self.row['solution_file']).read_bytes(),'html.parser').get_text(' ',strip=True)
        self.assertIn('ANSWER: SMACK',solution)
        self.assertEqual(self.row['gold_label']['expected_answer'],'SMACK')
        parts=load_gold_parts(self.row['gold_label'])
        for answer,expected in [('SMACK',1),(' smack ',1),('Final answer: SMACK',1),('',0),('SMACKX',0),('NOT SMACK',0),('SMACK was considered.\nFinal answer: WRONG',0)]:
            with self.subTest(answer=answer): self.assertEqual(GoldAnswerEvaluator(parts,answer).evaluate().total_score,expected)

    def test_solution_is_judge_only_and_base_inputs_complete(self):
        public={a['path'] for a in self.row['assets'] if a['role']=='agent_visible'}
        self.assertNotIn(self.row['solution_file'],public)
        entries=[e for e in read('data/base/input_asset_manifest.json')['files'] if e['task_id']=='mystery_hunt/'+PID]
        self.assertEqual({e['source'] for e in entries},public)
        for e in entries:
            self.assertEqual((ROOT/'data/base'/e['staged']).read_bytes(),(ROOT/e['source']).read_bytes())
        folder=ROOT/f'data/base/tasks/mystery_hunt/{PID}/base/input'
        for p in folder.iterdir():
            if p.suffix in ('.md','.html','.json','.txt'):
                self.assertNotRegex(p.read_text(encoding='utf-8'),r'(?i)\bSMACK\b')

    def test_pdf_reader_returns_actual_visual_input(self):
        result,images=read_problem_pdf(self.row,pages=[1])
        self.assertEqual(result['available_pages'],[1]); self.assertEqual(len(images),1)
        self.assertEqual(images[0].role,'agent_visible'); self.assertEqual(images[0].mime_type,'image/png')
        self.assertTrue(images[0].path.is_file())
        self.assertEqual(self.row['evaluation']['evaluator_id'],'gold_answer_v1')

if __name__=='__main__': unittest.main()
