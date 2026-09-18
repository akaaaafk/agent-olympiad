from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment
from rules import PhaseSchedule, RulesMode


class ContestPhaseTests(unittest.TestCase):
    def fixture(self):
        # Synthetic phases exercise generic gating. The IEO preparation rules
        # do not establish a turn-21 internet ban or an early-submission ban.
        env = OlympiadEnvironment('ieo_business_case', 'ieo_business_case_2021',
                                  rules_mode=RulesMode.ENFORCED)
        env.phase_schedule = PhaseSchedule.from_simulation({'phases': [
            dict(id='prep', label='Preparation', turn_start=1, turn_end=20,
                 allow_submit_final=False),
            dict(id='lock', label='Slide lock', turn_start=21, turn_end=30,
                 banned_actions=['web_search'])]})
        return env

    def test_synthetic_schedule_blocks_early_submit(self) -> None:
        env = self.fixture()
        self.assertIsNotNone(env.phase_schedule)
        env.begin_turn()
        self.assertEqual(env.current_turn, 1)
        violation = env.validate_action("submit", "Agent_1")
        self.assertIsNotNone(violation)
        assert violation is not None
        self.assertIn("locked", violation)

    def test_synthetic_schedule_blocks_web_search_after_prep(self) -> None:
        env = self.fixture()
        env.current_turn = 21
        violation = env.validate_action("web_search", "Agent_1")
        self.assertIsNotNone(violation)
        assert violation is not None
        self.assertIn("banned", violation)

    def test_phase_transition_announced_in_chat(self) -> None:
        env = self.fixture()
        for _ in range(21):
            env.begin_turn()
        self.assertTrue(
            any(
                "Slide lock" in item.get("message", "")
                for item in env.chat_history
                if item.get("sender") == "Contest_Control"
            )
        )

    def test_off_mode_ignores_phases(self) -> None:
        env = OlympiadEnvironment("ieo_business_case", "ieo_business_case_2021")
        self.assertIsNone(env.phase_schedule)
        env.begin_turn()
        self.assertIsNone(env.validate_action("submit", "Solo"))


if __name__ == "__main__":
    unittest.main()
