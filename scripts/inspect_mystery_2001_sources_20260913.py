"""Read-only inventory of the next Mystery Hunt packet cohort."""
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]


def main():
    rows=json.loads((ROOT/"data/benchmarks/mystery_hunt/benchmark.json").read_text(encoding="utf-8"))
    year=int(sys.argv[1]) if len(sys.argv)>1 else 2001
    ids=set(sys.argv[2:])
    for row in rows:
        if row["year"] != year: continue
        if ids and row['problem_id'] not in ids: continue
        soup=BeautifulSoup((ROOT/row["source_file"]).read_bytes(),"html.parser")
        print(json.dumps(dict(id=row["problem_id"],source=row["source_file"],
              links=[dict(tag=t.name,attrs=t.attrs) for t in soup.find_all(["a","img","script","link","iframe","form","object","embed","audio","video"])],
              text=soup.get_text("\n",strip=True)),ensure_ascii=True),flush=True)


if __name__=="__main__": main()
