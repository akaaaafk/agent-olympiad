import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2000_packets_20260913 import ROOT,CACHE,SELECTED,read,sanitize,check_html


class Mystery2000PacketRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.plan=read(ROOT/CACHE/'plan.json')

    def test_exact_scope_and_endgame_preserved(self):
        self.assertEqual({u['after']['problem_id'] for u in self.plan['updates']},SELECTED)
        self.assertNotIn('mystery_hunt_00068',SELECTED)
        self.assertEqual(len(self.plan['copies']),45)

    def test_layout_tags_and_text_not_rewritten(self):
        for u in self.plan['updates']:
            row=u['after']; pid=row['problem_id']
            original=(ROOT/row['source_review']['publisher_snapshot']).read_bytes()
            expected,edits=sanitize(original)
            self.assertEqual(expected,(ROOT/CACHE/pid/'input/puzzle.html').read_bytes())
            self.assertEqual(len(edits),3)
            for tag in ('pre','table'):
                old=BeautifulSoup(original,'html.parser').find_all(tag)
                new=BeautifulSoup(expected,'html.parser').find_all(tag)
                self.assertEqual(len(old),len(new))
                for a,b in zip(old,new):
                    # The title/navigation table intentionally loses two anchors.
                    if tag=='table' and a.find('a'): continue
                    self.assertEqual(str(a),str(b))

    def test_dependency_allowlist(self):
        for pid in SELECTED:
            p=ROOT/CACHE/pid/'input'
            check_html(p/'puzzle.html',{f.resolve() for f in p.iterdir()})

    def test_missing_card_art_restored(self):
        row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id']=='mystery_hunt_00103')
        self.assertEqual(row['source_review']['media_count'],21)
        self.assertGreater(len(row['source_review']['media_missing_from_legacy_archive']),0)

    def test_clue_words_not_highlighted_as_answers(self):
        for suffix,word in [('00112','isolation'),('00113','RISING')]:
            row=next(u['after'] for u in self.plan['updates'] if u['after']['problem_id'].endswith(suffix))
            prefix,body=row['problem_description'].split('## Source text',1)
            self.assertNotIn(word.lower(),prefix.lower())
            self.assertIn(word.lower(),body.lower())

    def test_gold_scoring_and_readiness_unchanged(self):
        for u in self.plan['updates']:
            for k in ('gold_label','total_points','split','license','team_size'):
                self.assertEqual(u['before'][k],u['after'][k])
            self.assertEqual(u['before']['evaluation']['status'],u['after']['evaluation']['status'])

    def test_source_drift_rejected(self):
        with self.assertRaises(ValueError):sanitize(b'<html>Unexpected edition</html>')


if __name__=='__main__':unittest.main()
