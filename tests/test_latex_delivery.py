import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from artifact_contract import ArtifactContract, contract_for, delivery_route
from artifacts.contest_delivery import ArtifactRenderer
from artifacts.latex import renderer_identity
from rules.loader import load_rule_card
from evaluation.finalize import _reference_text
from evaluation.models import load_rubric


class LatexDeliveryTests(unittest.TestCase):
    def test_routes_and_budgets(self):
        for cid in ('mcm','icm'):
            card=load_rule_card(cid,required=True)
            contract=contract_for(card)
            self.assertEqual((contract.kind,contract.source_format),('document','latex'))
            self.assertEqual(contract.max_source_chars,60000)
            self.assertIn('submission.tex',contract.prompt())
        self.assertEqual(delivery_route(load_rule_card('hmmt_team',required=True)),'native')

    def test_missing_compiler_does_not_fall_back_to_plain_text(self):
        with patch('artifacts.latex.subprocess.run') as run:
            run.return_value.returncode=1
            with self.assertRaises(ValueError):renderer_identity()

    def test_real_compile_and_invalid_source(self):
        with tempfile.TemporaryDirectory() as folder:
            renderer=ArtifactRenderer(Path(folder),ArtifactContract('document',source_format='latex'))
            text=r'\documentclass{article}\usepackage{amsmath}\begin{document}Model: $x^2=4$.\end{document}'
            receipt=renderer(None,'render_pdf',{'content':text})
            self.assertEqual(Path(receipt['source']).suffix,'.tex')
            self.assertEqual(Path(receipt['source']).read_text(),text)
            self.assertEqual(receipt['pages'],1)
            self.assertEqual(renderer(None,'render_pdf',{'content':text}),receipt)
            with self.assertRaisesRegex(ValueError,'compilation failed'):
                renderer(None,'render_pdf',{'content':r'\documentclass{article}\begin{document}\undefinedcommand\end{document}'})
            with self.assertRaisesRegex(ValueError,'compilation failed'):
                renderer(None,'render_pdf',{'content':r'\documentclass{article}\begin{document}\input{/etc/passwd}\end{document}'})

    def test_fyziklani_does_not_require_or_send_partial_gold(self):
        rows=json.loads((ROOT/'data/benchmarks/fyziklani/benchmark.json').read_text(encoding='utf-8'))
        for row in rows:
            self.assertEqual(_reference_text(row),'')
            self.assertFalse(row['evaluation']['gold_answer_required'])
            rubric=load_rubric(ROOT/row['evaluation']['rubric_path'])
            self.assertEqual(rubric.total_points,100)


if __name__=='__main__':unittest.main()
