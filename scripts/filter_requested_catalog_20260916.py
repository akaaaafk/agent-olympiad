"""Apply requested year exclusions; archive every removed record before mutation."""
import collections
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from dataset_catalog import update_track_index

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup = ROOT/'data/excluded'/f'requested_year_filter_{stamp}'
base = ROOT/'data/benchmarks'
policy = {'odyssey_of_the_mind': (2010, True), 'qanta': (2010, True),
          'science_bowl': (None, True), 'wharton_investment': (None, True),
          'cfa_research_challenge': (2010, False)}
changes = {}
for cid, (minimum, drop_unknown) in policy.items():
    path = base/cid/'benchmark.json'
    rows = read(path)
    removed = [r for r in rows if (drop_unknown and not isinstance(r.get('year'), int)) or
               (minimum is not None and isinstance(r.get('year'), int) and r['year'] < minimum)]
    removed_ids = {r['problem_id'] for r in removed}
    kept = [r for r in rows if r['problem_id'] not in removed_ids]
    changes[cid] = dict(before=len(rows), removed=len(removed), after=len(kept),
                        removed_ids=sorted(removed_ids), minimum_year=minimum,
                        drop_unknown=drop_unknown)
    write(backup/cid/'removed_records.json', removed)
    write(backup/cid/'benchmark.before.json', rows)
    changes[cid]['retained_ids'] = [r['problem_id'] for r in kept]

# Audit exact identities and source content within NYU. Year/event is an edition;
# different challenges in the same edition must remain separate.
nyu_path = base/'nyu_ctf_bench/benchmark.json'
nyu = read(nyu_path)
groups = collections.defaultdict(list)
for r in nyu:
    groups[(r['year'], r['event'], r['category'], r['challenge'].casefold())].append(r)
duplicates = [g for g in groups.values() if len(g)>1]
assert not duplicates, 'Ambiguous NYU identities require manual source review'
assert len({r['problem_id'] for r in nyu}) == len(nyu)
assert len({r['source_file'] for r in nyu}) == len(nyu)
editions = collections.Counter((r['year'],r['event']) for r in nyu)
nyu_report = dict(records=len(nyu), exact_duplicate_records=0,
    annual_editions=len({r['year'] for r in nyu}), stage_sessions=len(editions),
    editions=[dict(year=y,event=e,questions=n) for (y,e),n in sorted(editions.items())],
    counting_policy='Year counts annual CSAW editions; year/event counts Quals and Finals separately. Challenges are not duplicates merely because they share an edition.')
write(backup/'nyu_dedup_audit.json',nyu_report)
index_path = base/'index.json'
index = read(index_path)
write(backup/'index.before.json',index)
codeforces = (base/'codeforces').resolve()
assert codeforces.is_relative_to(base.resolve()) and codeforces.name == 'codeforces'
if codeforces.exists():
    changes['codeforces'] = dict(before=len(read(codeforces/'benchmark.json')), after=0,
                                 removed_ids=[r['problem_id'] for r in read(codeforces/'benchmark.json')])
write(backup/'manifest.json',dict(timestamp_utc=stamp,changes=changes,nyu=nyu_report,
    scope='Canonical catalog only; historical paid runs and active frozen runtime preserved.'))

for cid in policy:
    original = read(backup/cid/'benchmark.before.json')
    retained = set(changes[cid]['retained_ids'])
    kept = [r for r in original if r['problem_id'] in retained]
    write(base/cid/'benchmark.json', kept)
    assert {r['problem_id'] for r in read(base/cid/'benchmark.json')} == retained
    update_track_index(index, cid, kept)
if codeforces.exists():
    destination = (backup/'codeforces_catalog').resolve()
    assert destination.is_relative_to(backup.resolve())
    shutil.move(str(codeforces), str(destination))
index['olympiads'] = [t for t in index['olympiads'] if t['id'] != 'codeforces']
index['total_records'] = sum(t['problems_collected'] for t in index['olympiads'])
index['description'] = f"Agent Olympiad - {len(index['olympiads'])} tracks; mixed-unit team-task corpus. Readiness is per record."
track = next(t for t in index['olympiads'] if t['id']=='nyu_ctf_bench')
track['edition_coverage'] = nyu_report
write(index_path,index)
write(base/'nyu_ctf_bench/edition_coverage.json',nyu_report)
print(json.dumps(dict(backup=str(backup),changes=changes,nyu=nyu_report),ensure_ascii=False,indent=2))
