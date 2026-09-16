import collections
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import update_track_index

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p,r):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

base=ROOT/'data/benchmarks'
path=base/'nyu_ctf_bench/benchmark.json'
rows=read(path)
assert {r['event'] for r in rows} <= {'CSAW-Quals','CSAW-Finals'}
keep=[r for r in rows if r['event']=='CSAW-Finals']
remove=[r for r in rows if r['event']=='CSAW-Quals']
backup=ROOT/'data/excluded'/('nyu_finals_only_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
write(backup/'benchmark.before.json',rows)
write(backup/'removed_records.json',remove)
write(backup/'index.before.json',read(base/'index.json'))
write(backup/'manifest.json',dict(before=len(rows),after=len(keep),removed_ids=[r['problem_id'] for r in remove],policy='CSAW-Finals only'))
write(path,keep)
assert read(path)==keep
coverage=dict(records=len(keep),annual_editions=len({r['year'] for r in keep}),stage_sessions=len({(r['year'],r['event']) for r in keep}),exact_duplicate_records=0,
 editions=[dict(year=y,event='CSAW-Finals',questions=n) for y,n in sorted(collections.Counter(r['year'] for r in keep).items())],counting_policy='Finals only; one edition per year.')
write(base/'nyu_ctf_bench/edition_coverage.json',coverage)
index=read(base/'index.json')
update_track_index(index,'nyu_ctf_bench',keep)
next(t for t in index['olympiads'] if t['id']=='nyu_ctf_bench')['edition_coverage']=coverage
write(base/'index.json',index)
removed={r['problem_id'] for r in remove}
for p in (ROOT/'data/contest_manifests/generated').glob('*.json'):
    m=read(p)
    if not removed.intersection(m.get('problem_ids',[])):
        continue
    write(backup/'generated_manifests'/p.name,m)
    m['problem_ids']=[pid for pid in m['problem_ids'] if pid not in removed]
    if m['problem_ids']:
        write(p,m)
    else:
        assert p.resolve().is_relative_to((ROOT/'data/contest_manifests/generated').resolve())
        p.unlink()
print(json.dumps(dict(before=len(rows),removed=len(remove),after=len(keep),backup=str(backup),coverage=coverage),indent=2))
