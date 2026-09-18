import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
spec = importlib.util.spec_from_file_location('status_write_pipeline', ROOT / 'scripts/run_pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class StatusWriteTests(unittest.TestCase):
    def test_transient_windows_read_lock_keeps_old_status_then_replaces(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            path.write_text('{"old": true}')
            replace = Path.replace
            attempts = []
            def locked_once(source, target):
                attempts.append(1)
                if len(attempts) == 1:
                    self.assertEqual(path.read_text(), '{"old": true}')
                    raise PermissionError('sharing violation')
                return replace(source, target)
            with patch.object(Path, 'replace', locked_once), patch.object(pipeline.time, 'sleep'):
                pipeline.write(path, {'new': True})
            self.assertEqual(pipeline.read(path), {'new': True})
            self.assertEqual(len(attempts), 2)

    def test_persistent_denial_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            path.write_text('{"old": true}')
            with patch.object(Path, 'replace', side_effect=PermissionError('denied')), patch.object(pipeline.time, 'sleep'):
                with self.assertRaises(PermissionError):
                    pipeline.write(path, {'new': True})
            self.assertEqual(pipeline.read(path), {'old': True})


if __name__ == '__main__':
    unittest.main()
