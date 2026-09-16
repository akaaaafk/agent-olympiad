import unittest
from bs4 import BeautifulSoup
from scripts.repair_mystery_2011_blog_20260913 import ROOT,CACHE,PID,FEED,entries,read,sha,check_html,check_css,permalink_body


class Mystery2011BlogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=read(ROOT/CACHE/'plan.json');cls.row=cls.plan['updates'][0]['after'];cls.folder=ROOT/CACHE/PID/'input';cls.posts=entries(read(ROOT/cls.plan['publisher_snapshots'][FEED]['path']))
    def test_exact_initial_set(self):
        self.assertEqual(len(self.plan['updates']),1);self.assertEqual({r['number'] for r in self.row['source_review']['post_review']},set(range(1,22)));a=BeautifulSoup((ROOT/self.plan['updates'][0]['before']['source_file']).read_bytes(),'html.parser');b=BeautifulSoup((self.folder/'puzzle.html').read_bytes(),'html.parser');self.assertIsNotNone(a.find(id='puzzlecontent'));self.assertEqual(a.find(id='puzzlecontent').get_text(),b.find(id='puzzlecontent').get_text())
    def test_all_post_bodies_exact(self):
        for n,e in self.posts.items():
            s=BeautifulSoup((self.folder/f'post-{n:02}.html').read_bytes(),'html.parser');self.assertEqual(s.find('h1').get_text(),e['title']['$t']);self.assertEqual(s.find('article').decode_contents(),BeautifulSoup(e['content']['$t'],'html.parser').decode_contents())
            url=next(x['href'] for x in e['link'] if x['rel']=='alternate');self.assertEqual(permalink_body((ROOT/self.plan['publisher_snapshots'][url]['path']).read_bytes())[1],s.find('article').decode_contents().strip())
    def test_like_counts_are_original_clues(self):
        for n,e in self.posts.items():self.assertIn('Nerd',BeautifulSoup((self.folder/f'post-{n:02}.html').read_bytes(),'html.parser').find('article').get_text())
        self.assertEqual(BeautifulSoup((self.folder/'post-08.html').read_bytes(),'html.parser').find('h1').get_text(),'# 8 Science Fiction Television')
    def test_index_order(self):
        s=BeautifulSoup((self.folder/'blog.html').read_bytes(),'html.parser');self.assertEqual([a['href'] for a in s.find_all('a')],[f'post-{n:02}.html' for n in range(21,0,-1)])
    def test_later_feed_not_public(self):
        assets=[a for a in self.row['assets'] if a['path'].endswith('blog-feed.json')];self.assertEqual([a['role'] for a in assets],['judge_only']);self.assertFalse((self.folder/'blog-feed.json').exists());self.assertFalse((self.folder/'post-22.html').exists())
    def test_offline_allowlist_and_no_controls(self):
        allowed={p.resolve() for p in self.folder.iterdir()}
        for p in self.folder.glob('*.html'):check_html(p,allowed)
        for p in self.folder.glob('*.css'):check_css(p,allowed)
    def test_originals_and_copies(self):
        old=self.plan['updates'][0]['before'];self.assertEqual(sha(ROOT/old['source_file']),self.row['source_review']['original_sha256'])
        for c in self.plan['copies']:self.assertEqual(sha(ROOT/c['source']),c['sha256'])
        self.assertTrue(all(p['feed_matches_permalink'] for p in self.row['source_review']['post_review']))
    def test_scores_status_preserved(self):
        old=self.plan['updates'][0]['before']
        for k in ('gold_label','total_points','year','split','license','team_size','title'):self.assertEqual(old[k],self.row[k])
        self.assertEqual(old['evaluation']['status'],self.row['evaluation']['status'])


if __name__=='__main__':unittest.main()
