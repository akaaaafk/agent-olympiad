"""Active problem data and mini PDF permissions are local and hash-bound."""
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from problem_pdf import approved_assets, read_problem_pdf


@pytest.mark.parametrize('base', ['data', 'data/mini_data'])
def test_active_pdf_locations_and_reviewed_ranges(base):
    index = json.loads((ROOT / base / 'benchmarks/index.json').read_text(encoding='utf-8'))
    rows = [r for t in index['olympiads'] for r in json.loads((ROOT / t['benchmark_path']).read_text(encoding='utf-8'))]
    by_id = {r['problem_id']: r for r in rows}
    for r in rows:
        for a in r.get('assets', []):
            if a.get('mime_type') == 'application/pdf':
                assert a['path'].startswith(base + '/'), (r['problem_id'], a['path'])
    reg = ROOT / base / 'problem_pdf_allowlist.json'
    for e in json.loads(reg.read_text())['assets']:
        row = by_id[e['problem_id']]
        approved = approved_assets(row, root=ROOT, registry=reg)
        match = next(a for a in approved if a['path'] == e['path'])
        for page in e['pages']:
            payload, _ = read_problem_pdf(row, [page], approved.index(match)+1, root=ROOT, registry=reg, render=False)
            assert payload['status'] == 'ok'


def test_mini_registry_cannot_authorize_parent_data(tmp_path):
    import hashlib
    parent = tmp_path / 'data/raw/puzzle.pdf'
    parent.parent.mkdir(parents=True)
    parent.write_bytes(b'not rendered; authorization test')
    digest = hashlib.sha256(parent.read_bytes()).hexdigest()
    row = dict(problem_id='x', assets=[dict(path='data/raw/puzzle.pdf', sha256=digest,
                role='agent_visible', mime_type='application/pdf')])
    registry = tmp_path / 'data/mini_data/problem_pdf_allowlist.json'
    registry.parent.mkdir()
    registry.write_text(json.dumps(dict(assets=[dict(problem_id='x', path='data/raw/puzzle.pdf',
                         sha256=digest, pages=[1], review_status='approved_problem_only', review_evidence='fixture') ])))
    assert approved_assets(row, root=tmp_path, registry=registry) == []
