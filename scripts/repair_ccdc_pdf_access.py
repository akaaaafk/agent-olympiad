"""Expose reviewed CCDC scenario pages and retire the empty-map 2022 packet."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import update_track_index

REVIEWED = {2013: (21, 25), 2014: (21, 25), 2015: (22, 27),
    2016: (21, 26), 2017: (21, 26), 2018: (21, 27), 2019: (20, 26),
    2020: (14, 20), 2021: (13, 18), 2026: (15, 21)}
RETIRED = 'ccdc_2022-NCCDC-TeamPacket-missing-page13-network-map'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / 'tmp' / ('before_ccdc_pdf_access_' + stamp)
    archive = ROOT / 'data/excluded/ccdc_2022_missing_map_20260917'
    staged, before = {}, {}
    def put(p, value):
        before[p] = p.read_bytes() if p.exists() else None
        staged[p] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    path = ROOT / 'data/benchmarks/ccdc/benchmark.json'
    rows = read(path)
    retired = [r for r in rows if r['problem_id'] == RETIRED]
    remaining = [r for r in rows if r['problem_id'] != RETIRED]
    if retired:
        assert len(retired) == 1
        source = (ROOT / retired[0]['assets'][0]['path']).resolve()
        assert source.is_relative_to(ROOT / 'data/raw/ccdc/nationals')
        import pymupdf
        with pymupdf.open(source) as doc:
            page = doc[12]
            assert not page.get_images() and not page.get_drawings()
            assert len(page.get_text().strip()) < 110
        archive.mkdir(parents=True, exist_ok=True)
        target = archive / source.name
        assert not target.exists(), 'Do not overwrite an existing exclusion archive'
        shutil.copy2(source, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == retired[0]['assets'][0]['sha256']
        put(archive / 'manifest.json', dict(reason='User requested removal when missing map cannot be recovered from PDF.',
            evidence='PDF page 13 contains only its footer; zero raster images and zero vector drawings.',
            archived_pdf=target.relative_to(ROOT).as_posix(), original_record=retired[0], timestamp_utc=stamp))
        put(path, remaining)
    registry_path = ROOT / 'data/problem_pdf_allowlist.json'
    registry = read(registry_path)
    changed = []
    for row in remaining:
        if row['year'] not in REVIEWED or not row['problem_id'].endswith('TeamPacket'):
            continue
        asset = next(a for a in row['assets'] if a['mime_type'] == 'application/pdf' and a['role'] == 'agent_visible')
        start, end = REVIEWED[row['year']]
        entry = dict(problem_id=row['problem_id'], path=asset['path'], sha256=asset['sha256'],
            pages=list(range(start, end + 1)), review_status='approved_problem_only',
            review_evidence='2026-09-17: reviewed original contestant network map, scenario, network details and service requirements; no solution key. See tmp/ccdc_review_20260917 and tmp/ccdc_scanned_review_20260917. OCR is not authoritative.')
        registry['assets'] = [a for a in registry['assets'] if a.get('problem_id') != row['problem_id']] + [entry]
        changed.append(row['problem_id'])
    registry['assets'] = [a for a in registry['assets'] if a.get('problem_id') != RETIRED]
    put(registry_path, registry)
    for base in [ROOT / 'data', ROOT / 'data/mini_data']:
        p = base / 'rules/ccdc/evaluation.json'
        rules = read(p)
        for key in ['record_evaluator_overrides', 'record_rubric_overrides']:
            rules['scoring'].get(key, {}).pop(RETIRED, None)
        selected = remaining if base.name == 'data' else read(base / 'benchmarks/ccdc/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = dict(Counter(r['evaluation']['status'] for r in selected))
        put(p, rules)
    p = ROOT / 'data/benchmarks/index.json'
    index = read(p)
    update_track_index(index, 'ccdc', remaining)
    put(p, index)
    put(ROOT / 'tmp/ccdc_pdf_access_20260917.json', dict(registered=changed, removed=[r['problem_id'] for r in retired],
        archive=archive.relative_to(ROOT).as_posix(), paid_calls=0))
    for p, value in before.items():
        assert (p.read_bytes() if p.exists() else None) == value, f'Concurrent change: {p}'
    for p, value in staged.items():
        if before[p] is not None:
            dest = backup / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(before[p])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value)
    if retired:
        assert source.is_relative_to((ROOT / 'data/raw/ccdc/nationals').resolve())
        assert source.read_bytes() == target.read_bytes()
        source.unlink()
    print(json.dumps(dict(registered=len(changed), removed=len(retired), backup=str(backup))))


if __name__ == '__main__':
    main()
