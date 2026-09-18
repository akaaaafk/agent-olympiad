import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from competition_guidance import fixed_team_size
from test_delivery_route_baselines import DeliveryRouteBaselineTests


class FixedRosterTests(unittest.TestCase):
    def test_all_active_main_and_mini_rosters_are_complete_and_equal(self):
        sizes = {}
        for base in (ROOT / 'data', ROOT / 'data/mini_data'):
            index = json.loads((base / 'benchmarks/index.json').read_text())
            for track in index['olympiads']:
                cid = track['id']
                raw = json.loads((base / 'rules' / cid / 'competition.json').read_text())
                expected = raw['team']['active_default']
                self.assertGreaterEqual(expected, 2)
                if cid in sizes:
                    self.assertEqual(expected, sizes[cid])
                sizes[cid] = expected
                for baseline in ('single_agent', 'centralized', 'decentralized', 'otc', 'vallina_otc'):
                    count = fixed_team_size(cid, baseline, rules_root=base / 'rules')
                    self.assertEqual(count, 1 if baseline == 'single_agent' else expected)
                    self.assertEqual(fixed_team_size(cid, baseline, requested=count,
                                                   rules_root=base / 'rules'), count)
                    with self.assertRaisesRegex(ValueError, 'fixed team size'):
                        fixed_team_size(cid, baseline, requested=count + 1, rules_root=base / 'rules')
        self.assertEqual(len(sizes), 39)

    def test_missing_or_invalid_configuration_never_defaults_to_three(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaisesRegex(ValueError, 'Missing competition roster'):
                fixed_team_size('absent', 'decentralized', rules_root=root)
            folder = root / 'bad'
            folder.mkdir()
            for value in (None, '3', True, 0):
                (folder / 'competition.json').write_text(json.dumps({'team': {'active_default': value}}))
                with self.assertRaisesRegex(ValueError, 'active_default'):
                    fixed_team_size('bad', 'centralized', rules_root=root)

    def test_native_entry_ignores_legacy_static_and_task_rosters(self):
        helper = DeliveryRouteBaselineTests()
        with tempfile.TemporaryDirectory() as d, patch('run_competition_batch.get_contest_rules',
                                                      side_effect=AssertionError('Legacy roster read')):
            for baseline in ('single_agent', 'decentralized', 'centralized', 'otc', 'vallina_otc'):
                _, config, _, _ = helper.prepare('arml_local', baseline, d)
                self.assertEqual(config.team_size, 1 if baseline == 'single_agent' else 6)


if __name__ == '__main__':
    unittest.main()
