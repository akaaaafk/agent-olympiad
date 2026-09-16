import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.repair_mystery_2009_attachments_20260913 import ROOT,CACHE,SELECTED,OPAQUE,OPAQUE_SIZES,read,sha,sanitize,localize,check_html,check_css


class Mystery2009AttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json')
    def test_selection(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED);self.assertEqual(len(self.plan['copies']),99)
    def test_exact_generated_html(self):
        for u in self.plan['updates']:
            row=u['after'];folder=ROOT/CACHE/row['problem_id']/'input';expected,_=localize(sanitize((ROOT/u['before']['source_file']).read_bytes(),row['problem_id']),row['source_url']);self.assertEqual((folder/'puzzle.html').read_bytes(),expected)
            allowed={p.resolve() for p in folder.iterdir()};check_html(folder/'puzzle.html',allowed)
            for p in folder.glob('*.css'):check_css(p,allowed)
    def test_all_32_sheets_and_original_order(self):
        folder=ROOT/CACHE/'mystery_hunt_01112/input';s=BeautifulSoup((folder/'puzzle.html').read_bytes(),'html.parser');self.assertEqual([a['href'] for a in s.find_all('a')],[f'{i:02}.png' for i in range(1,33)])
        self.assertEqual([i['src'] for i in s.find_all('img') if i['src'].startswith('200px-')],[f'200px-{i:02}.png' for i in range(1,33)])
    def test_initial_instructions_not_modified(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('01112'));a=BeautifulSoup((ROOT/u['before']['source_file']).read_bytes(),'html.parser');b=BeautifulSoup((ROOT/CACHE/u['after']['problem_id']/'input/puzzle.html').read_bytes(),'html.parser')
        self.assertEqual([p.get_text() for p in a.find_all('p') if p.get_text(strip=True) and not p.find('form')],[p.get_text() for p in b.find_all('p') if p.get_text(strip=True) and not p.find(class_='archive-verification')])
        self.assertEqual(b.find('input',attrs={'name':'last_phase'})['value'],'1');self.assertTrue(all(i.has_attr('disabled') for i in b.find_all('input')))
    def test_opaque_files_not_renamed_or_retyped(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith('01157'));folder=ROOT/CACHE/row['problem_id']/'input';self.assertEqual({p.name for p in folder.glob('file.*')},OPAQUE)
        self.assertEqual([(folder/f'file.{i:03}').stat().st_size for i in range(1,23)],OPAQUE_SIZES)
        for a in row['assets']:
            if Path(a['path']).name in OPAQUE:self.assertEqual(a['mime_type'],'application/octet-stream')
        for v in row['source_review']['opaque_review'].values():self.assertFalse(v['executed']);self.assertFalse(v['unpacked']);self.assertFalse(v['format_interpretation_added_to_public_packet'])
    def test_all_hashes_and_sources(self):
        for u in self.plan['updates']:
            row=u['after'];self.assertEqual(sha(ROOT/u['before']['source_file']),row['source_review']['original_sha256'])
            for name,url in row['source_review']['dependency_urls'].items():self.assertEqual(sha(ROOT/CACHE/row['problem_id']/'input'/name),self.plan['publisher_snapshots'][url]['sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
    def test_scoring_membership_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])
    def test_phase_drift_rejected(self):
        u=next(u for u in self.plan['updates'] if u['after']['problem_id'].endswith('01112'));data=(ROOT/u['before']['source_file']).read_bytes()
        with self.assertRaises(ValueError):sanitize(data.replace(b'name="last_phase" value="1"',b'name="last_phase" value="2"'),u['after']['problem_id'])


if __name__=='__main__':unittest.main()
