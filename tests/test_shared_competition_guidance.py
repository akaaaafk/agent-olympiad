import json
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from competition_guidance import competition_guidance
from contest_config import ContestRunConfig
from contest_prompts import _system_prompt
from rules.loader import load_rule_card
from test_otc_rulecard import arml_manifest


class SharedCompetitionGuidanceTests(unittest.TestCase):
    def test_five_baselines_receive_same_official_rules_with_actual_roster(self):
        manifest = arml_manifest()
        card = load_rule_card('arml_local', required=True)
        official_blocks = []
        for baseline in ('single_agent', 'decentralized', 'centralized', 'vallina_otc', 'otc'):
            config = ContestRunConfig(baseline, 1 if baseline == 'single_agent' else 6, 7,
                rule_card=card if baseline in ('otc', 'vallina_otc') else None)
            guidance = competition_guidance(manifest, config)
            config = replace(config, rule_guidance=guidance)
            prompt = _system_prompt(config, 'Agent_1', frozenset(), answer_sheet_contest=True)
            self.assertIn(guidance, prompt)
            self.assertEqual(prompt.count('OFFICIAL COMPETITION RULES'), 1)
            official, adaptation = guidance.split('\nBENCHMARK ADAPTATION (actual settings for this run)\n')
            official_blocks.append(official)
            runtime = json.loads(adaptation.split('\n', 1)[0])
            self.assertEqual(runtime['active_agents'], config.team_size)
            self.assertEqual(runtime['max_turns'], 7)
            self.assertEqual(runtime['task_count'], len(manifest.tasks))
            self.assertIn('45', official)
            self.assertIn('calculator', official)
            self.assertNotIn('~1 hour', guidance)
            self.assertNotIn('10×4 pts typical', guidance)
            if baseline in ('single_agent', 'decentralized', 'centralized'):
                self.assertIsNone(config.rule_card)
                self.assertFalse(config.review_required)
                self.assertFalse(config.features.memory_actions)
        self.assertEqual(len(set(official_blocks)), 1)

    def test_reads_selected_dataset_competition_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / 'rules/arml_local'
            folder.mkdir(parents=True)
            (folder / 'competition.json').write_text(json.dumps({
                'competition_id': 'arml_local', 'rules_text': 'MINI EDITION RULE',
                'resources': {'internet': 'forbidden'}, 'provenance': {'private': 'DO NOT EXPOSE'}}))
            (folder / 'collaboration.json').write_text('invalid; must not read')
            (folder / 'evaluation.json').write_text('invalid; must not read')
            with patch('competition_guidance.data_root', return_value=root):
                guidance = competition_guidance(arml_manifest(), ContestRunConfig('single_agent', 1, 3))
            self.assertIn('MINI EDITION RULE', guidance)
            self.assertNotIn('DO NOT EXPOSE', guidance)


if __name__ == '__main__':
    unittest.main()
