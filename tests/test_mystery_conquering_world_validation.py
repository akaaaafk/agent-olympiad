"""Source isolation and reviewed visual delivery for Conquering the World."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts

PID = 'mystery_hunt_01261'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConqueringWorldValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = next(r for r in read(ROOT / 'data/benchmarks/mystery_hunt/benchmark.json')
                       if r['problem_id'] == PID)
        cls.review = read(ROOT / f'data/judge_references/mystery_hunt/{PID}/review.json')
        cls.public = {ROOT / a['path']: a['sha256'] for a in cls.row['assets']
                      if a['role'] == 'agent_visible'}
        cls.page = ROOT / cls.row['source_file']

    def test_official_solution_agrees_with_gold(self):
        text = BeautifulSoup((ROOT / self.row['solution_file']).read_bytes(),
                             'html.parser').get_text(' ', strip=True)
        answer = re.search(r'ANSWER:\s*([A-Z]+)\b', text).group(1)
        self.assertEqual(answer, 'SOWETO')
        self.assertEqual(self.row['gold_label']['expected_answer'], answer)
        parts = load_gold_parts(self.row['gold_label'])
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].expected, answer)
        self.assertEqual(parts[0].points, 1)
        for ref in self.review['references']:
            self.assertEqual(ref['visibility'], 'judge_only')
            self.assertEqual(digest(ROOT / ref['path']), ref['sha256'])
            self.assertNotIn(ROOT / ref['path'], self.public)

    def test_declared_assets_match_hashes_and_images_decode(self):
        for asset in self.row['assets']:
            path = ROOT / asset['path']
            with self.subTest(path=path):
                self.assertEqual(digest(path), asset['sha256'])
                if asset.get('mime_type', '').startswith('image/'):
                    with Image.open(path) as image:
                        image.verify()
        for ref in self.review['references']:
            if ref['path'].endswith('.gif'):
                with Image.open(ROOT / ref['path']) as image:
                    image.verify()

    def assert_local_public_link(self, source, value):
        if value.startswith('#'):
            return
        url = urlsplit(value)
        self.assertFalse(url.scheme or url.netloc, value)
        target = (source.parent / unquote(url.path)).resolve()
        self.assertIn(target, self.public, value)
        self.assertTrue(target.is_file(), value)

    def test_html_and_css_dependencies_are_local_and_public(self):
        for path in self.public:
            if path.suffix == '.html':
                soup = BeautifulSoup(path.read_bytes(), 'html.parser')
                self.assertFalse(soup.find_all(['script', 'form', 'iframe', 'object', 'embed']))
                for tag in soup.find_all(True):
                    for attr in ('src', 'href', 'poster', 'data'):
                        if tag.get(attr):
                            self.assert_local_public_link(path, tag[attr])
            elif path.suffix == '.css':
                css = path.read_text(encoding='utf-8')
                self.assertNotRegex(css, r'(?i)@import')
                for value in re.findall(r'url\(([^)]+)\)', css):
                    self.assert_local_public_link(path, value.strip(' \t\r\n\"\''))

    def test_all_42_cards_and_image_map_geometry_preserved(self):
        soup = BeautifulSoup(self.page.read_bytes(), 'html.parser')
        original = BeautifulSoup((ROOT / self.row['source_review']['original_source_file']).read_bytes(),
                                 'html.parser')
        areas = soup.find_all('area')
        self.assertEqual([a['href'] for a in areas], [f'{i:02}.jpg' for i in range(1, 43)])
        self.assertEqual([(a['shape'], a['coords']) for a in areas],
                         [(a['shape'], a['coords']) for a in original.find_all('area')])
        self.assertEqual(soup.find('img', attrs={'usemap': True})['usemap'],
                         '#' + soup.find('map')['name'])

    def test_generated_inputs_preserve_public_files_and_exclude_solutions(self):
        hidden_hashes = {r['sha256'] for r in self.review['references']}
        hidden_hashes.update(a['sha256'] for a in self.row['assets'] if a['role'] != 'agent_visible')
        for layout in ('base',):
            base = ROOT / 'data' / layout
            manifest = read(base / 'input_asset_manifest.json')
            entries = [e for e in manifest['files'] if e['task_id'] == 'mystery_hunt/' + PID]
            self.assertEqual({ROOT / e['source']: e['sha256'] for e in entries}, self.public)
            folder = base / 'tasks/mystery_hunt' / PID / 'base/input'
            expected = {base / e['staged'] for e in entries}
            expected.update(folder / name for name in (
                'problem.md', 'task_sop.md', 'input_environment_spec.md',
                'ground_rules.md', 'collaboration.md'))
            self.assertEqual({p for p in folder.rglob('*') if p.is_file()}, expected)
            for entry in entries:
                self.assertEqual(digest(base / entry['staged']), entry['sha256'])
            for path in expected:
                self.assertNotIn(digest(path), hidden_hashes, str(path))
                if path.suffix in ('.md', '.html', '.css', '.txt', '.json'):
                    self.assertNotRegex(path.read_text(encoding='utf-8'), r'(?i)\bSOWETO\b')
            if layout == 'last_exam':
                reference = read(folder.parent.parent / 'eval/reference.json')
                self.assertEqual(reference['solution_file'], self.row['solution_file'])
                self.assertEqual(reference['evaluation'], self.row['evaluation'])

    def test_candidate_gold_grader_accepts_final_answer_and_rejects_distractors(self):
        parts = load_gold_parts(self.row['gold_label'])
        for submission in ('SOWETO', ' soweto ', 'Final answer: SOWETO'):
            with self.subTest(submission=submission):
                self.assertEqual(GoldAnswerEvaluator(parts, submission).evaluate().total_score, 1)
        for submission in ('', 'ROME', 'SOWETOX', 'NOT SOWETO',
                           'SOWETO was considered.\nFinal answer: ROME'):
            with self.subTest(submission=submission):
                self.assertEqual(GoldAnswerEvaluator(parts, submission).evaluate().total_score, 0)

    def test_reviewed_visual_packet_is_available(self):
        from problem_pdf import read_problem_pdf
        self.assertEqual(self.row['evaluation']['status'], 'ready_with_limitations')
        self.assertEqual(self.row['evaluation']['evaluator_id'], 'gold_answer_v1')
        for start in (1, 3, 5, 7):
            result, images = read_problem_pdf(self.row, pages=[start,start+1])
            self.assertEqual(result['available_pages'],list(range(1,9)))
            self.assertEqual(len(images),2)
            self.assertTrue(all(i.role=='agent_visible' and i.mime_type=='image/png' for i in images))
            for image in images:
                self.assertTrue(image.path.is_file())


if __name__ == '__main__':
    unittest.main()
