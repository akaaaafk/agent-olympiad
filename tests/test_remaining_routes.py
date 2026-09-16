import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import tempfile

import pymupdf

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from rules.loader import load_rule_card
from artifact_contract import delivery_route
from contest_config import ContestRunConfig
from problem_pdf import approved_assets
from contest_task_judge import task_pdf_asset
from contest_manifest import ManifestTask
import run_pipeline


class RemainingRoutesTests(unittest.TestCase):
    def test_proxy_routes_and_proof_budget(self):
        for cid in ('ethics_bowl_appe','ethics_bowl_nhseb','ichto'):
            self.assertEqual(delivery_route(load_rule_card(cid)),'native')
        card=load_rule_card('hmmt_team')
        self.assertEqual(ContestRunConfig('otc',card.team_size_default,10,rule_card=card).otc_policy.char_limit('work'),60000)

    def test_canonical_assets_override_legacy_source(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'input.pdf';p.write_bytes(b'%PDF-fixture')
            row={'source_file':str(p),'assets':[{'path':str(p),'role':'judge_only'}]}
            with self.assertRaises(ValueError):run_pipeline.artifact_task_pdf(row)

    def test_all_fyziklani_inputs_have_no_hidden_text_and_reach_judge(self):
        rows=json.loads((ROOT/'data/benchmarks/fyziklani/benchmark.json').read_text(encoding='utf-8'))
        for row in rows:
            self.assertGreater(len(row['problem_description']),10000)
            assets=approved_assets(row);self.assertEqual(len(assets),1)
            with pymupdf.open(assets[0]['resolved_path']) as doc:
                self.assertEqual(doc.embfile_count(),0)
                self.assertEqual(len(doc),len(assets[0]['pages']))
                for page in doc:
                    self.assertEqual(page.get_text().strip(),'')
                    self.assertEqual(len(page.get_images()),1)
            task=ManifestTask(row['problem_id'],row['problem_id'],None,row['problem_description'],'general',100,False,row)
            asset=task_pdf_asset(task)
            self.assertEqual(asset.sha256,assets[0]['sha256'])
            self.assertNotEqual(str(asset.path),str(ROOT/row['solution_file']))

    def test_all_iypt_have_pdf_and_generated_images_are_present(self):
        rows=json.loads((ROOT/'data/benchmarks/iypt/benchmark.json').read_text(encoding='utf-8'))
        for row in rows:
            path=run_pipeline.artifact_task_pdf(row)
            self.assertTrue(path.is_file())
            if row.get('input_pdf_derivation'):
                with pymupdf.open(path) as doc:
                    images=sum(len(page.get_image_info()) for page in doc)
                self.assertEqual(images,len(row['input_pdf_derivation']['images']),row['problem_id'])


if __name__=='__main__':unittest.main()
