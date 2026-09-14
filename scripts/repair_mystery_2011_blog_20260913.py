"""Restore exactly the 21 blog entries explicitly allowed by the initial puzzle."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urljoin
import re
import subprocess
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image
from scripts.repair_mystery_2011_static_20260913 import sanitize,local_css,check_css,reset_snapshot,RESET_URL,RESET_REPO
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,download,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2011_blog_20260913/'
RAW='data/raw/mystery_hunt/separated_2011_blog_20260913/'
REPORT='data/benchmarks/mystery_2011_blog_repair_20260913.json'
PID='mystery_hunt_01469';SELECTED={PID}
BLOG='https://stuffnerdpeoplelike.blogspot.com/'
FEED=BLOG+'feeds/posts/default?alt=json&max-results=100'


def blog_snapshot(url):
    require(url==FEED or re.fullmatch(re.escape(BLOG)+r'2010/12/[a-z0-9-]+\.html',url),'Unreviewed blog target');p=ROOT/CACHE/'publisher'/(hashlib.sha256(url.encode()).hexdigest()+'.bin');meta=p.with_suffix('.json')
    if p.exists():d=read(meta);require(d['source_url']==url and sha(p)==d['sha256'],'Blog snapshot drift');return d
    r=requests.get(url,timeout=30);r.raise_for_status();require(r.url==url,'Unexpected blog redirect');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(r.content)
    d=dict(source_url=url,final_url=r.url,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(r.content),retrieved_at_utc=Store(ROOT).stamp);Store(ROOT).save(meta.relative_to(ROOT).as_posix(),d);return d


def entries(data):
    result={}
    for e in data['feed']['entry']:
        m=re.fullmatch(r'#\s*(\d+) .+',e['title']['$t']);require(m is not None,'Unreviewed post numbering');n=int(m[1])
        if not 1<=n<=21:continue
        require(n not in result and e['published']['$t'].startswith('2010-12-19T') and e['updated']['$t']<'2011-01-11','Post scope/date drift');s=BeautifulSoup(e['content']['$t'],'html.parser');require({t.name for t in s.find_all()}<={'br','span','b','i'},'Unreviewed post HTML')
        for tag in s.find_all():require(not tag.attrs or tag.name=='span' and tag.attrs=={'style':'font-size: small;'},'Unreviewed post formatting')
        require(re.search(r'\d Nerds? Likes? This\s*$',s.get_text(' ',strip=True)) is not None,'Missing printed like-count clue');result[n]=e
    require(set(result)==set(range(1,22)),'Incomplete initial post set');return result


def page(title,body):
    return ('<!doctype html><html><head><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>body{max-width:900px;margin:40px auto;padding:0 24px;font:18px/1.6 Georgia,serif;color:#111;background:white}h1{font-size:28px}article{margin:32px 0 48px}h2{font-size:23px}</style></head><body>'+body+'</body></html>').encode('utf-8')


def permalink_body(data):
    s=BeautifulSoup(data,'html.parser');body=s.select_one('.post-body');require(body is not None,'Missing post body');clears=body.find_all('div');require(len(clears)==1 and clears[0].attrs=={'style':'clear: both;'} and not clears[0].contents,'Unreviewed platform wrapper');clears[0].decompose();return s,body.decode_contents().strip()


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);old=next(r for r in before if r['problem_id']==PID);source=ROOT/old['source_file'];url='https://puzzles.mit.edu/'+old['puzzle_url'].rstrip('/')+'/';snapshots={s['source_url']:s for s in map(reset_snapshot,(RESET_URL,RESET_REPO))};feed=blog_snapshot(FEED);snapshots[FEED]=feed;posts=entries(read(ROOT/feed['path']));posturls={n:next(x['href'] for x in e['link'] if x['rel']=='alternate') for n,e in posts.items()}
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(blog_snapshot,posturls.values())})
    for n,e in posts.items():
        s,body=permalink_body((ROOT/snapshots[posturls[n]]['path']).read_bytes());title=s.select_one('.post-title');require(title and title.get_text(strip=True)==e['title']['$t'],'Post title mismatch')
        expected=BeautifulSoup(e['content']['$t'],'html.parser').decode_contents().strip();require(body==expected,'Feed/permalink body mismatch: '+str(n))
    payload,styleurls=sanitize(source.read_bytes(),url);token=b'href="http://stuffnerdpeoplelike.blogspot.com"';require(payload.count(token)==1 and 'entries 1\u201321' in BeautifulSoup(payload,'html.parser').get_text(),'Initial blog limit drift');payload=payload.replace(token,b'href="blog.html"');img=b'src="../images/biomanicon.png"';require(payload.count(img)==1 and len(BeautifulSoup(payload,'html.parser').find_all('img'))==1,'Puzzle image scope drift');payload=payload.replace(img,b'src="biomanicon.png"');deps={'biomanicon.png':urljoin(url,'../images/biomanicon.png')}
    urls={url,*styleurls.values(),*deps.values()}-set(snapshots)
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(urls))})
    styles={}
    for name,u in styleurls.items():
        css,links=local_css((ROOT/snapshots[u]['path']).read_bytes(),u);styles[name]=css
        for n,v in links.items():require(n not in deps or deps[n]==v,'CSS/content collision');deps[n]=v
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(download,sorted(set(deps.values())-set(snapshots)))})
    remote=ROOT/snapshots[url]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher puzzle drift');folder=ROOT/CACHE/PID/'input';folder.mkdir(parents=True,exist_ok=True);new_assets=[];copies=[]
    def add(data,name,mime,role='agent_visible'):
        sub='input' if role=='agent_visible' else 'judge';p=ROOT/CACHE/PID/sub/name;p.parent.mkdir(exist_ok=True)
        if p.exists():require(p.read_bytes()==data,'Prepared bytes differ')
        else:
            with p.open('xb') as f:f.write(data)
        dest=RAW+PID+'/'+sub+'/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));new_assets.append(dict(path=dest,role=role,mime_type=mime,sha256=sha(p)))
    add(payload,'puzzle.html','text/html')
    for name,data in styles.items():add(data,name,'text/css')
    for name,u in deps.items():
        p=ROOT/snapshots[u]['path']
        with Image.open(p) as im:im.verify()
        add(p.read_bytes(),name,'image/png' if name.endswith('.png') else 'image/jpeg')
    links=[];reviews=[]
    for n in sorted(posts,reverse=True):
        e=posts[n];title=e['title']['$t'];body=e['content']['$t'];name=f'post-{n:02}.html';add(page(title,'<h1>'+html.escape(title)+'</h1><article class="original-post-body">'+body+'</article>'),name,'text/html');links.append('<li><a href="'+name+'">'+html.escape(title)+'</a></li>');reviews.append(dict(number=n,title=title,published=e['published']['$t'],updated=e['updated']['$t'],url=posturls[n],body_sha256=hashlib.sha256(body.encode()).hexdigest(),feed_matches_permalink=True))
    add(page('Stuff Nerd People Like - original entries 1–21','<h1>Stuff Nerd People Like</h1><p>Original entries 1–21, as specified by the puzzle. Posts are listed in the archive\'s reverse chronological order. The post bodies and their printed like counts are unchanged; site navigation, comments, later posts and blog platform controls are not included.</p><ol>'+''.join(links)+'</ol>'),'blog.html','text/html')
    add((ROOT/feed['path']).read_bytes(),'blog-feed.json','application/json','judge_only');allowed={p.resolve() for p in folder.iterdir()}
    for p in folder.glob('*.html'):check_html(p,allowed)
    for name in styles:check_css(folder/name,allowed)
    row=deepcopy(old);assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    note='Exactly blog entries 1–21 are restored, as the initial puzzle explicitly requires. Each unchanged body is checked against its individual publisher page; printed like counts and the unusual # 8 title spacing are preserved. Neutral offline wrappers replace the blog platform, not its content. Later entries and comments are not initial input. Historical external rankings and any host performance are not recreated.'
    row.update(source_url=url,source_file=RAW+PID+'/input/puzzle.html',problem_description='# Stuff Nerd People Like\n\nOpen `puzzle.html`, then its local blog link for exactly the 21 original entries.\n\nArchive limitation: '+note,assets=new_assets+assets,source_visibility='explicit_initial_blog_cutoff_later_feed_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Gold, scores and readiness unchanged, not recertified. Prior limitations: '+old['evaluation']['limitations'];row['source_review']=deepcopy(old.get('source_review') or {});row['source_review'].update(batch='mystery_2011_blog_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[url]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,post_review=reviews,blog_feed_snapshot=feed,answers_and_scores_unchanged=True);provenance(row)
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots);Store(ROOT).save(CACHE+'plan.json',plan);print(json.dumps(dict(records=1,roles=writer().copy_role_counts(plan),publisher_files=len(snapshots))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True)
    for name in ['puzzle.html','blog.html',*[f'post-{n:02}.html' for n in range(1,22)]]:
        path=ROOT/CACHE/PID/'input'/name;dest=out/(Path(name).stem+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,1100','--virtual-time-budget=1000',path.as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(name,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify()))
    else:raise ValueError(mode)
