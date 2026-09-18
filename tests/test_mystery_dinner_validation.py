"""Thirteen at Dinner source completeness, solution isolation, rendering and grading."""
import json
from pathlib import Path
import sys
import unittest
import pymupdf
import io
from PIL import Image
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from problem_pdf import read_problem_pdf
PID='mystery_hunt_01278'
def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))

class DinnerValidation(unittest.TestCase):
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
            self.assertEqual(len(doc),2)
            images=doc[0].get_images(); self.assertEqual(len(images),1)
            embedded=Image.open(io.BytesIO(doc.extract_image(images[0][0])['image'])).convert('RGB')
            original=Image.open(self.folder/'thirteen_at_dinner.gif').convert('RGB')
            self.assertEqual(embedded.size,original.size)
            self.assertEqual(embedded.tobytes(),original.tobytes())
            expected_names=[td.get_text('\n',strip=True).splitlines() for td in source.select('#page-content table td')]
            self.assertEqual(doc[1].get_text().splitlines(),['GUEST LIST']+[n for col in expected_names for n in col])
            self.assertEqual(sum(map(len,expected_names)),78)
            text=' '.join(doc[0].get_text().split())
            for p in source.select('.flavortext p'): self.assertIn(p.get_text(' ',strip=True),text)
            self.assertNotIn('HURT',text.upper()); self.assertEqual(doc.embfile_count(),0)

    def test_official_answer_and_grading_boundaries(self):
        solution=BeautifulSoup((ROOT/self.row['solution_file']).read_bytes(),'html.parser').get_text(' ',strip=True)
        self.assertIn('ANSWER: HURT',solution)
        self.assertEqual(self.row['gold_label']['expected_answer'],'HURT')
        parts=load_gold_parts(self.row['gold_label'])
        for answer,expected in [('HURT',1),(' hurt ',1),('Final answer: HURT',1),('',0),('HURTX',0),('NOT HURT',0),('HURT was considered.\nFinal answer: WRONG',0)]:
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
                self.assertNotRegex(p.read_text(encoding='utf-8'),r'(?i)\bHURT\b')

    def test_pdf_reader_returns_actual_visual_input(self):
        result,images=read_problem_pdf(self.row,pages=[1,2])
        self.assertEqual(result['available_pages'],[1,2]); self.assertEqual(len(images),2)
        self.assertEqual(images[0].role,'agent_visible'); self.assertEqual(images[0].mime_type,'image/png')
        self.assertTrue(images[0].path.is_file())
        self.assertEqual(self.row['evaluation']['evaluator_id'],'gold_answer_v1')

if __name__=='__main__': unittest.main()
