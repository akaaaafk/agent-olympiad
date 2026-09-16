"""Remove cache, retaining only evidence referenced by non-cache data files."""
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
CACHE=(DATA/'.cache').resolve()
assert CACHE==Path('E:/agent_olympiad/agent-olympiad/data/.cache').resolve()
assert CACHE.is_relative_to(DATA.resolve()) and CACHE.name=='.cache'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive=DATA/'raw/cache_referenced_evidence_20260916'
audit=DATA/'excluded'/f'cache_cleanup_{stamp}'
audit.mkdir(parents=True)
prefix='data/.cache/'
newprefix=archive.relative_to(ROOT).as_posix()+'/'
files=subprocess.run(['rg','-l','--hidden','-F','-e','data/.cache/','-e','data\\\\.cache\\\\',str(DATA),
    '-g','*.json','-g','*.md','-g','!**/.cache/**','-g','!**/excluded/**','-g','!**/raw/**'],
    capture_output=True,text=True,check=False)
assert files.returncode in (0,1),files.stderr
paths=[]
for line in files.stdout.splitlines():
    p=Path(line)
    relative=p.relative_to(DATA)
    if relative.parts[0] not in ('.cache','excluded','raw'):
        paths.append(p)

dependencies=set()
payloads={}
def strings(value):
    if isinstance(value,dict):
        for v in value.values():yield from strings(v)
    elif isinstance(value,list):
        for v in value:yield from strings(v)
    elif isinstance(value,str):yield value
for p in paths:
    text=p.read_text(encoding='utf-8-sig')
    payloads[p]=text
    try:
        values=list(strings(json.loads(text)))
    except json.JSONDecodeError:
        values=[text]
    for value in values:
        normalized=value.replace('\\','/')
        for match in re.finditer(r'data/\.cache/[^\s"\'<>`,;]+',normalized):
            reference=match.group().rstrip(').]')
            source=(ROOT/reference).resolve()
            if source.is_relative_to(CACHE) and source.exists():
                dependencies.add(source)

copied=[]
for source in sorted(dependencies):
    destination=archive/source.relative_to(CACHE)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if source.is_dir():
        shutil.copytree(source,destination,dirs_exist_ok=True)
        copied.append(dict(source=str(source.relative_to(ROOT)),destination=str(destination.relative_to(ROOT)),kind='directory'))
    else:
        shutil.copy2(source,destination)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        assert hashlib.sha256(destination.read_bytes()).hexdigest()==digest
        copied.append(dict(source=source.relative_to(ROOT).as_posix(),destination=destination.relative_to(ROOT).as_posix(),sha256=digest))
updates=[]
for p,text in payloads.items():
    rewritten=text
    # Replace exact existing dependency prefixes only; old historical/dead paths
    # are preserved as provenance instead of pretending they now exist.
    for entry in sorted(copied,key=lambda e:len(e['source']),reverse=True):
        old=entry['source'].replace('\\','/')
        new=entry['destination'].replace('\\','/')
        rewritten=rewritten.replace(old,new)
        rewritten=rewritten.replace(old.replace('/','\\\\'),new)
    if rewritten!=text:
        backup=audit/'before'/p.relative_to(ROOT)
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,backup)
        if p.suffix=='.json':json.loads(rewritten)
        p.write_text(rewritten,encoding='utf-8')
        updates.append(p.relative_to(ROOT).as_posix())

entries=[]
for p in CACHE.rglob('*'):
    if p.is_file():entries.append(dict(path=p.relative_to(CACHE).as_posix(),bytes=p.stat().st_size))
manifest=dict(target=str(CACHE),timestamp_utc=stamp,files=len(entries),bytes=sum(x['bytes'] for x in entries),
    retained_evidence=copied,updated_files=updates,deleted_inventory=entries)
(audit/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(entries),bytes=manifest['bytes'],retained_evidence=len(copied),updated_files=len(updates),manifest=str(audit/'manifest.json')),indent=2))
