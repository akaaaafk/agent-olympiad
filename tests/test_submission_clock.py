"""The production final-hand-in clock gates every baseline at dispatch too."""
import sys
import unittest
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'src'), str(Path(__file__).parent)]
import test_plain_baseline_boundary as fixtures
from contest_config import ContestRunConfig, BASELINE_NAMES
from contest_actions import _apply_action
from rules.loader import load_rule_card


class SubmissionClockTests(unittest.TestCase):
    def test_no_baseline_can_bypass_final_handin_clock(self):
        for name in BASELINE_NAMES:
            with self.subTest(baseline=name):
                manifest, session, memory = fixtures.PlainBaselineBoundaryTests().state()
                card = load_rule_card('arml_local') if name in {'otc', 'vallina_otc'} else None
                config = ContestRunConfig(name, 1 if name == 'single_agent' else 6,
                    12, submission_turn=12, rule_card=card)
                before = session.checkpoint(), memory.to_checkpoint_json()
                with self.assertRaisesRegex(ValueError, 'submission_turn'):
                    _apply_action(action='submit', arguments={}, agent='Agent_1',
                        manifest=manifest, session=session, memory=memory, config=config,
                        strategic_policy=None, task_action_executor=None)
                self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)
