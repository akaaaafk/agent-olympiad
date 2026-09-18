"""Scoped regeneration must not delete stale entries belonging to other work."""
import unittest
from scripts.sync_written_track_packages_20260916 import merge_track_entries


class BoundedTrackSyncTests(unittest.TestCase):
    def test_preserves_unrelated_stale_record_and_replaces_target(self):
        for field in ['category', 'competition_id']:
            with self.subTest(field=field):
                other = {field:'other', 'task_id':'other/stale', 'evaluation':{'status':'not_ready'}}
                before = [other, {field:'cybench','task_id':'cybench/old'}]
                replacement = [{field:'cybench','task_id':'cybench/new'}]
                actual = merge_track_entries(before,replacement,{'cybench'})
                self.assertEqual(actual,[other,*replacement])
                self.assertEqual(before,[other,{field:'cybench','task_id':'cybench/old'}])

    def test_manifest_uses_task_id_prefix(self):
        keep = {'task_id':'other/a','path':'asset.bin'}
        self.assertEqual(merge_track_entries([keep,{'task_id':'cybench/a'}],[],{'cybench'}),[keep])


if __name__ == '__main__':
    unittest.main()
