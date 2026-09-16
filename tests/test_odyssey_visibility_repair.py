import unittest
from scripts.repair_odyssey_visibility_20260913 import ROOT,CACHE,read,split_source,clean


class OdysseyVisibilityRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(ROOT/CACHE/'plan.json')
        cls.public=cls.plan['texts'][cls.plan['after_row']['source_file']]
        cls.parts,cls.hidden=split_source((ROOT/cls.plan['original_source']).read_text(encoding='utf-8'))

    def test_three_examples_only(self):
        self.assertEqual(len(self.parts),3)
        self.assertNotIn('Navigation Menu',self.public)

    def test_deferred_prompts_absent(self):
        for text in ['includes one item from each list','pick any two of the creations']:
            self.assertNotIn(text,self.public)
            self.assertTrue(any(text in (h['deferred_read_aloud'] or '') for h in self.hidden))

    def test_last_straw_test_rules_are_initially_disclosed(self):
        self.assertIsNone(self.hidden[2]['deferred_read_aloud'])
        self.assertIn('In Part II, you will place the coins',self.public)
        self.assertIn('6 points for any coin',self.public)

    def test_judge_material_absent(self):
        self.assertNotIn('C. FOR JUDGES ONLY',self.public)
        self.assertNotIn('Examples of Creative Responses',self.public)
        self.assertNotIn('Do not read material in parentheses',self.public)

    def test_control_character_removed(self):
        self.assertFalse(any(ord(c)<32 and c not in '\n\r\t' for c in self.public))

    def test_no_readiness_or_score_invention(self):
        before,after=self.plan['before_row'],self.plan['after_row']
        self.assertEqual(before['gold_label'],after['gold_label'])
        self.assertEqual(before['total_points'],after['total_points'])
        self.assertEqual(before['evaluation']['status'],after['evaluation']['status'])
        self.assertEqual(sum(a['role']=='agent_visible' for a in after['assets']),1)
        self.assertEqual(self.public.count('[printed scoring note: 1-10 points]'),2)

    def test_unrecognized_nested_directions_fail_closed(self):
        with self.assertRaises(ValueError): clean('(outer (inner) end)')


if __name__=='__main__': unittest.main()
