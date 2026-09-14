"""Bounded, read-only network checks; receipts and response bytes remain private."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode,urlsplit,parse_qs
import requests
from bs4 import BeautifulSoup
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require

CACHE='data/.cache/mystery_remaining_review_20260913/'
URLS=[
 'https://rebel-sky.glitch.me/',
 'http://dynamic.coinheist.com/snow_day/',
 'https://www.alexirpan.com/puzzles/',
 'https://raw.githubusercontent.com/rspeer/analogy_farm/master/README.md',
 'https://raw.githubusercontent.com/rspeer/analogy_farm/master/server.py',
 'https://web.mit.edu/puzzle/www/2001/phase4/06/eschatology.exe',
 'https://puzzles.mit.edu/2001/phase4/06/eschatology.exe',
 'https://hea-www.cfa.harvard.edu/SoT2016/files/Rapid_Transit.pdf',
 'http://www.marvelcomics.com/fun/coloring_pages/xtras/ff4_team.gif',
 'https://archive.org/wayback/available?'+urlencode(dict(url='http://www.marvelcomics.com/fun/coloring_pages/xtras/ff4_team.gif',timestamp='20010115')),
 'https://archive.org/wayback/available?'+urlencode(dict(url='http://www.wmata.com/rail/docs/colormap_lettersize.pdf',timestamp='20100115')),
]


def probe(url):
    base=ROOT/CACHE/'responses'/hashlib.sha256(url.encode()).hexdigest();meta=base.with_suffix('.json');binary=base.with_suffix('.bin')
    if meta.exists():return read(meta)
    row=dict(source_url=url,checked_at_utc=Store(ROOT).stamp,method='GET',executed=False)
    try:
        with requests.get(url,timeout=(8,20),stream=True) as r:
            row.update(final_url=r.url,http_status=r.status_code,content_type=r.headers.get('Content-Type'),history=[dict(url=h.url,status=h.status_code) for h in r.history]);chunks=[];size=0
            for c in r.iter_content(65536):
                size+=len(c);require(size<=5000000,'Response exceeded bounded 5 MB');chunks.append(c)
            data=b''.join(chunks);base.parent.mkdir(parents=True,exist_ok=True)
            if binary.exists():require(binary.read_bytes()==data,'Existing response drift')
            else:
                with binary.open('xb') as out:out.write(data)
            row.update(bytes=len(data),path=binary.relative_to(ROOT).as_posix(),sha256=sha(binary))
            if 'html' in (row['content_type'] or ''):
                soup=BeautifulSoup(data,'html.parser');row['title']=soup.title.get_text(' ',strip=True) if soup.title else None
                for s in soup.find_all(['script','style']):s.decompose()
                row['text_excerpt']=soup.get_text(' ',strip=True)[:1500]
            elif 'json' in (row['content_type'] or ''):row['json']=json.loads(data)
    except Exception as e:row.update(error_type=type(e).__name__,error=str(e)[:700])
    Store(ROOT).save(meta.relative_to(ROOT).as_posix(),row);return row


def main():
    r=next(r for r in read(ROOT/PATH) if r['problem_id']=='mystery_hunt_01497');s=BeautifulSoup((ROOT/r['source_file']).read_bytes(),'html.parser');areas=[dict(a.attrs) for a in s.find_all('area')];videos=[]
    for a in areas:
        u=a['href'];parts=urlsplit(u);v=parts.path.lstrip('/') if parts.hostname=='youtu.be' else parse_qs(parts.query)['v'][0];videos.append(dict(original_url=u,video_id=v,coords=a['coords'],probe_url='https://www.youtube.com/oembed?'+urlencode(dict(url='https://www.youtube.com/watch?v='+v,format='json'))))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(probe,URLS+[v['probe_url'] for v in videos]))
    report=dict(network_receipts=rows,pattern_recognition=dict(original_source_file=r['source_file'],original_sha256=sha(ROOT/r['source_file']),video_links=videos,scope='oEmbed metadata only; success does not certify playable/full historical media. No player scripts are executed, no videos downloaded or substituted.'))
    Store(ROOT).save(CACHE+'network-review.json',report)
    for row in rows:print(json.dumps({k:row.get(k) for k in ('source_url','http_status','final_url','bytes','title','error_type','json') if k in row}),flush=True)


if __name__=='__main__':main()
