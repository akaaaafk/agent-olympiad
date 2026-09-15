import unittest
from io import BytesIO
import zipfile
from bs4 import BeautifulSoup
import pymupdf as fitz
from scripts.repair_mystery_2013_attachments_20260913 import ROOT,CACHE,SELECTED,PIECES,read,sha,sanitize,localize,localize_css,localize_inline,compile_less,check_html,check_css,zip_review


class Mystery2013AttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection_and_titles(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertEqual([u['after']['problem_description'].splitlines()[0] for u in self.plan['updates']],['# Space Monkey Mafia','# Pulse Pulse Wave Noise'])
    def test_exact_localized_html_and_css(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input';payload,urls=sanitize((ROOT/u['before']['source_file']).read_bytes(),r['source_url'],int(r['problem_id'][-5:]));payload,deps=localize(payload,r['source_url']);cssdeps={}
            for name,target in urls.items():
                data=(ROOT/self.plan['publisher_snapshots'][target]['path']).read_bytes()
                if target.endswith('.less'):data=compile_less(data)
                self.assertEqual((folder/name).read_bytes(),localize_css(data,target,cssdeps))
            self.assertEqual((folder/'puzzle.html').read_bytes(),localize_inline(payload,r['source_url'],cssdeps))
    def test_original_and_attachment_byte_identity(self):
        for u in self.plan['updates']:
            r=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),r['source_review']['original_sha256'])
            for name,target in r['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/r['problem_id']/'input'/name),self.plan['publisher_snapshots'][target]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_three_original_pdf_pages(self):
        with fitz.open(ROOT/CACHE/'mystery_hunt_01692/input/puzzle.pdf') as doc:
            self.assertEqual(len(doc),3);self.assertFalse(doc.is_encrypted);self.assertIn('Space Monkey Mafia',doc[0].get_text())
            for page in doc:self.assertFalse(page.get_links());self.assertGreater(len(page.get_text()),25)
    def test_zip_crc_names_order_and_frames(self):
        folder=ROOT/CACHE/'mystery_hunt_01719/input';review=zip_review((folder/'pieces.zip').read_bytes());expected=self.plan['updates'][1]['after']['source_review']['attachment_review']['pieces.zip'];self.assertEqual(review,expected);self.assertEqual([r['name'] for r in review['entries']],PIECES)
        self.assertTrue(review['zip_crc_verified']);self.assertFalse(review['decoded']);self.assertFalse(review['listened']);self.assertFalse(review['extracted_to_disk']);self.assertFalse(list(folder.glob('*.mp3')))
    def test_invalid_archive_rejected(self):
        data=(ROOT/CACHE/'mystery_hunt_01719/input/pieces.zip').read_bytes()
        with self.assertRaises(zipfile.BadZipFile):zip_review(data[:-50])
        stream=BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('../escape.mp3',b'fake')
        with self.assertRaises(ValueError):zip_review(stream.getvalue())
    def test_static_allowlist_and_explicit_links(self):
        for u in self.plan['updates']:
            r=u['after'];folder=ROOT/CACHE/r['problem_id']/'input';allowed={p.resolve() for p in folder.iterdir()};s=check_html(folder/'puzzle.html',allowed);self.assertFalse(s.find_all('script'));self.assertFalse(s.find_all(class_='answer'));self.assertFalse(s.find(id='fixie-nav'))
            self.assertEqual([a['href'] for a in s.find_all('a',href=True)],['puzzle.pdf' if r['problem_id'].endswith('01692') else 'pieces.zip'])
            for p in folder.glob('*.css'):check_css(p,allowed)
    def test_scores_readiness_and_licenses_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status']);self.assertFalse(u['after']['source_review']['font_binary_historical_version_certified'])


if __name__=='__main__':unittest.main()
