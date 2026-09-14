"""Project the 18 explicitly linked Dog Food bags without executing puzzle JS."""
import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw
from scripts.repair_mystery_2016_static_20260913 import ORIGIN,EXT_MIME,sanitize as common_sanitize,localize_css,localize_inline,snapshot,check_css,inspect_asset,replace_ref
from scripts.repair_mystery_2001_packets_20260913 import ROOT,PATH,Store,read,sha,require,check_html,provenance,writer as static_writer

CACHE='data/.cache/mystery_2016_dog_food_20260913/'
RAW='data/raw/mystery_hunt/separated_2016_dog_food_20260913/'
REPORT='data/benchmarks/mystery_2016_dog_food_repair_20260913.json'
SELECTED={'mystery_hunt_02156'}
PAGE=ORIGIN+'puzzle/dog_food/'
BAG_SHA='c0ca16d7179df85286e52f2ecb10e86ca3031ad02a65d447744a72567e206712'
JS_SHA='30e849b0de3adaf1db46dcc94dc7893f00c6c66b49f1514d0c16789b8d11eaac'
COUNTS=[7,12,11,8,7,7,7,12,6,3,11,8,6,11,5,13,18,5]
EXTRA_CSS='''
/* Offline archive: original hover targets are local image links. */
div.diagram {position:relative;margin:100px auto;overflow:visible;}
div.diagram img.i {display:block;margin:0;}
a.r {background-color:black;color:white;border-radius:100px;box-shadow:0 0 5px rgba(0,0,0,.5);text-align:center;font-family:sans-serif;font-weight:700;position:absolute;width:30px;height:30px;line-height:30px;text-decoration:none;}
'''


def sanitize(data,url):
    require(data.count(b'<script src="//code.jquery.com/jquery-1.11.3.min.js"></script>')==1 and b'<!--<script src="../..//code.jquery.com/ui/1.11.2/jquery-ui.js"></script>-->' not in data,'Dog Food library pattern drift')
    data=data.replace(b'<script src="//code.jquery.com/jquery-1.11.3.min.js"></script>',b'<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>');data=data.replace(b'</head>',b'<!--<script src="../..//code.jquery.com/ui/1.11.2/jquery-ui.js"></script>--></head>');return common_sanitize(data,url)


def parse_bags(data,js):
    require(hashlib.sha256(data).hexdigest()==BAG_SHA and hashlib.sha256(js).hexdigest()==JS_SHA,'Reviewed bag or script changed');s=BeautifulSoup(data,'html.parser');scripts=s.find_all('script');require([x.get('src') for x in scripts]==['//code.jquery.com/jquery-1.11.3.min.js','d.js',None],'Bag script scope drift')
    raw=re.search(r'var m = (\[.*?\n    \]);',scripts[2].get_text(),re.S);require(raw is not None,'Literal bag array missing');literal=re.sub(r'// \d+','',raw[1]);m=ast.literal_eval(literal);require(len(m)==19 and m[0]==[],'Bag count drift');imgs=s.select('img.i');require(len(imgs)==18,'Bag images drift');result=[]
    for b,(entry,img) in enumerate(zip(m[1:],imgs),1):
        require(len(entry)==2 and isinstance(entry[0],str) and len(entry[1])==COUNTS[b-1],'Bag entry drift');require(img['id']==f'i{b}' and img['src']==f'{b}/a.png','Bag source image drift')
        for xy in entry[1]:require(len(xy)==2 and all(type(v)==int and -100<v<1000 for v in xy),'Bad dot coordinate')
        result.append(dict(bag=b,clue=entry[0],coordinates=entry[1],width=int(img['width']),image=f'bag-{b}-a.png',targets=[f'bag-{b}-a{i}.jpg' for i in range(len(entry[1]))]))
    return result,s.find('style').get_text()


def bag_html(b,css):
    points=''.join(f'<a class="r" href="{name}" style="left:{xy[0]-15}px;top:{xy[1]-15}px" aria-label="Open original image at this dot">&#x25cf;</a>' for xy,name in zip(b['coordinates'],b['targets']))
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><title>Doggie Bag '+str(b['bag'])+'</title><style>'+css+EXTRA_CSS+'</style></head><body><h1>Doggie Bag '+str(b['bag'])+'</h1><div class="t"><div class="diagram" style="width:'+str(b['width'])+'px"><img class="i" src="'+b['image']+'" width="'+str(b['width'])+'">'+points+'</div><p>'+b['clue']+'</p></div><aside>Offline archive: each original dot opens its corresponding original hover image. No puzzle script is executed. <a href="puzzle.html">Back to bags</a>.</aside></body></html>\n').encode('utf-8')


def localize_html(payload,url):
    deps={};seen=set();s=BeautifulSoup(payload,'html.parser');require([a['href'] for a in s.select('.content a[href]')]==[f'images/bag.html?b={b}' for b in range(1,19)],'Initial bag links drift')
    for b in range(1,19):payload=replace_ref(payload,'href',f'images/bag.html?b={b}',f'bag-{b}.html')
    for img in s.find_all('img'):
        ref=img['src'];target=urljoin(url,ref);name=Path(urlsplit(target).path).name;require(target.startswith(ORIGIN) and re.fullmatch(r'[A-Za-z0-9_-]+\.(jpg|png)',name),'Image scope drift');require(name not in deps or deps[name]==target,'Image collision');deps[name]=target
        if ref not in seen:payload=replace_ref(payload,'src',ref,name);seen.add(ref)
    return payload,deps


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared');before=read(ROOT/PATH);chosen=[r for r in before if r['problem_id'] in SELECTED];require(len(chosen)==1,'Selection drift');old=chosen[0];row=deepcopy(old);pid=old['problem_id'];source=ROOT/old['source_file'];payload,styleurls=sanitize(source.read_bytes(),PAGE);payload,deps=localize_html(payload,PAGE);styles={};cssdeps={};snapshots={}
    for name,target in styleurls.items():snapshots[target]=snapshot(target);styles[name]=localize_css((ROOT/snapshots[target]['path']).read_bytes(),target,cssdeps)
    payload=localize_inline(payload,PAGE,cssdeps);require(not(set(deps)&set(cssdeps)),'CSS collision');deps.update(cssdeps)
    for target in list(cssdeps.values()):
        if target.startswith('https://fonts.gstatic.com/'):
            family=urlsplit(target).path.split('/')[2];deps[family+'-OFL.txt']='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt'
    queryurls=[PAGE+f'images/bag.html?b={b}' for b in range(1,19)];jsurl=PAGE+'images/d.js'
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,queryurls+[jsurl])})
    require(all(snapshots[u]['sha256']==BAG_SHA for u in queryurls),'Query responses differ');bags,bag_css=parse_bags((ROOT/snapshots[queryurls[0]]['path']).read_bytes(),(ROOT/snapshots[jsurl]['path']).read_bytes())
    for b in bags:
        deps[b['image']]=PAGE+f"images/{b['bag']}/a.png"
        for i,n in enumerate(b['targets']):deps[n]=PAGE+f"images/{b['bag']}/a{i}.jpg"
    with ThreadPoolExecutor(max_workers=4) as pool:snapshots.update({s['source_url']:s for s in pool.map(snapshot,sorted(({PAGE}|set(deps.values()))-set(snapshots)))})
    remote=ROOT/snapshots[PAGE]['path'];require(source.read_bytes().replace(b'\r',b'')==remote.read_bytes().replace(b'\r',b''),'Publisher HTML drift');folder=ROOT/CACHE/pid/'input';folder.mkdir(parents=True,exist_ok=True);copies=[];public=[];reviews={}
    def add(data,name,mime):
        p=folder/name
        if p.exists():require(p.read_bytes()==data,'Prepared drift')
        else:
            with p.open('xb') as out:out.write(data)
        dest=RAW+pid+'/input/'+name;copies.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest,sha256=sha(p)));public.append(dict(path=dest,role='agent_visible',mime_type=mime,sha256=sha(p)))
    add(payload,'puzzle.html','text/html')
    for name,data in styles.items():add(data,name,'text/css')
    for b in bags:add(bag_html(b,bag_css),f"bag-{b['bag']}.html",'text/html')
    for name,target in sorted(deps.items()):
        p=ROOT/snapshots[target]['path'];ext=Path(name).suffix
        if ext=='.txt':require(b'SIL OPEN FONT LICENSE' in p.read_bytes(),'Font license drift');mime='text/plain'
        else:reviews[target]=inspect_asset(p,ext);mime=EXT_MIME[ext]
        add(p.read_bytes(),name,mime)
    allowed={p.resolve() for p in folder.iterdir()}
    for p in folder.glob('*.html'):check_html(p,allowed)
    for p in folder.glob('*.css'):check_css(p,allowed)
    note='All 18 explicitly linked bags are mechanically projected from the hash-pinned original HTML literal array and reviewed d.js display logic. Their original diagram widths, dot coordinates, per-dot image mapping, recipe wording, letter spacing, punctuation and enumerations remain. Each dot is now a local link to the original hover image, without running the source scripts; this is not pixel-identical hover/viewport behavior. No answers or synthetic recipes are added. The original query responses and display script stay private; every served query returns the same original bag HTML. Archive solution navigation, shared sheep/status requests and scripts are removed; artwork attribution wording stays with its link inert. Source CSS retains its original harmless trailing less-than character. Same-year CSS dependency path repairs follow the static batch; current source-named Google fonts include OFL texts but are not certified 2016 binaries. Gold, total points, splits, license and grading/runtime readiness remain unchanged and are not recertified.'
    assets=deepcopy(old['assets'])
    if not any(a['path']==old['source_file'] for a in assets):assets.append(dict(path=old['source_file'],role='judge_only',mime_type='text/html',sha256=sha(source)))
    row.update(source_url=PAGE,source_file=RAW+pid+'/input/puzzle.html',assets=public+assets,problem_description='# Dog Food\n\nOpen `puzzle.html`, then each of its 18 bags. Dots on each diagram link to the corresponding original hover images.\n\nArchive limitation: '+note,source_visibility='explicit_bag_packet_original_archive_judge_only',asset_policy=note);row['evaluation']['limitations']=note+' Prior limitations: '+old['evaluation']['limitations'];row['source_review']=dict(deepcopy(old.get('source_review') or {}),batch='mystery_2016_dog_food_20260913',original_source_file=old['source_file'],original_sha256=sha(source),publisher_snapshot=snapshots[PAGE]['path'],publisher_html_sha256=sha(remote),dependency_urls=deps,stylesheet_urls=styleurls,bag_query_urls=queryurls,display_script_url=jsurl,font_binary_historical_version_certified=False,answers_and_scores_unchanged=True);provenance(row)
    Store(ROOT).save(CACHE+'plan.json',dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=before,updates=[dict(before=old,after=row)],copies=copies,publisher_snapshots=snapshots,asset_reviews=reviews,bag_projection=bags));print(json.dumps(dict(records=1,public_files=len(copies),publisher_files=len(snapshots),bags=len(bags),dot_images=sum(COUNTS))))


def writer():
    m=static_writer();m.CACHE=CACHE;m.RAW=RAW;m.REPORT=REPORT;m.SELECTED=SELECTED;return m


def render():
    out=ROOT/CACHE/'renders';out.mkdir(exist_ok=True);folder=ROOT/CACHE/'mystery_hunt_02156/input'
    for name in ['puzzle']+[f'bag-{b}' for b in range(1,19)]:
        dest=out/(name+'.png');p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(ROOT/CACHE/'chrome_review_profile'),'--screenshot='+str(dest),'--window-size=1400,'+('2600' if name=='puzzle' else '1200'),'--virtual-time-budget=1000',(folder/(name+'.html')).as_uri()],capture_output=True,timeout=45);require(p.returncode==0 and dest.exists(),'Render failed');print(name,flush=True)
    for b in range(1,19):
        files=[folder/f'bag-{b}-a{i}.jpg' for i in range(COUNTS[b-1])];canvas=Image.new('RGB',(1600,360*((len(files)+3)//4)),'#dddddd');draw=ImageDraw.Draw(canvas)
        for n,p in enumerate(files):
            with Image.open(p) as im:
                im.load();thumb=im.convert('RGB');thumb.thumbnail((390,325));x=(n%4)*400;y=(n//4)*360;canvas.paste(thumb,(x,y+25));draw.text((x+5,y+5),p.name,fill='black')
        canvas.save(out/f'bag-{b}-targets.png')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='render':render()
    elif mode=='apply':writer().apply()
    elif mode=='verify':print(json.dumps(writer().verify(),indent=2))
    else:raise ValueError(mode)
