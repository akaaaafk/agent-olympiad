import tempfile
import unittest
from pathlib import Path
from scripts.build_data_packages import write_text


class PackageNewlines(unittest.TestCase):
    def test_mixed_source_newlines_do_not_create_extra_blank_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'problem.md'
            write_text(path, 'first\r\nsecond\rthird\nfourth\r\n')
            self.assertEqual(path.read_bytes(), b'first\nsecond\nthird\nfourth\n')


if __name__ == '__main__':
    unittest.main()
