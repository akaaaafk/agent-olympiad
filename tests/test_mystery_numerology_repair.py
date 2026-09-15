import unittest
from scripts.repair_mystery_numerology_20260913 import ROOT,CACHE,PID,read,sanitize,check_html


class NumerologyRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/'plan.json');cls.update=cls.plan['updates'][0]
        cls.folder=ROOT/CACHE/PID/'input'

    def test_complete_dependencies(self):
        self.assertEqual({p.name for p in self.folder.iterdir()},
            {'puzzle.html','index2.html','gridsmall.gif','gridlarge.gif','img1.gif','img2.gif','img3.gif'})
        self.assertEqual(len(self.plan['copies']),7)

    def test_bidirectional_links_and_allowlists(self):
        allow={p.resolve() for p in self.folder.iterdir()}
        a=check_html(self.folder/'puzzle.html',allow);b=check_html(self.folder/'index2.html',allow)
        self.assertEqual([t['href'] for t in a.find_all('a')],['index2.html'])
        self.assertEqual([t['href'] for t in b.find_all('a')],['puzzle.html'])

    def test_example_bytes_preserved_except_script(self):
        source=ROOT/self.update['before']['source_file']
        self.assertEqual((self.folder/'puzzle.html').read_bytes(),sanitize(source.read_bytes())[0])

    def test_full_page_bytes_preserved_except_backlink(self):
        source=ROOT/self.update['after']['source_review']['full_puzzle_snapshot']['path']
        self.assertEqual((self.folder/'index2.html').read_bytes(),source.read_bytes().replace(b'href="index.html"',b'href="puzzle.html"'))

    def test_no_scores_gold_or_ready_claim_added(self):
        a,b=self.update['before'],self.update['after']
        for k in ('gold_label','total_points','split','license','year','team_size','title'):self.assertEqual(a[k],b[k])
        self.assertEqual(b['evaluation']['status'],'not_ready')

    def test_original_puzzle_symbols_not_removed(self):
        self.assertIn('full puzzle',self.update['after']['problem_description'])
        text=(self.folder/'index2.html').read_text(encoding='cp1252')
        for name in ('gridlarge.gif','img3.gif','img2.gif'):self.assertIn(name,text)

    def test_styled_hint_not_promoted_to_plain_prompt(self):
        self.assertNotIn('Need a clue?',self.update['after']['problem_description'])
        self.assertIn('Need a clue?',(self.folder/'index2.html').read_text(encoding='cp1252'))


if __name__=='__main__':unittest.main()
