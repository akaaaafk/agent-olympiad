"""The refreshed document separates current inventory from historical experiments."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_mini_data import question_units


def test_current_inventory_table_matches_all_active_tracks():
    text = (ROOT / 'docs/from_zhongzheng/benchmark_distribution_and_completed_runs_20260916.md').read_text(encoding='utf-8-sig')
    index = json.loads((ROOT / 'data/benchmarks/index.json').read_text(encoding='utf-8'))
    table = {}
    for line in text.splitlines():
        match = re.match(r'^\| .*\(`([^`]+)`\) \|', line)
        if match:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            table[match[1]] = (int(cells[5]), int(cells[6].replace(',', '')))
    expected = {}
    for track in index['olympiads']:
        rows = json.loads((ROOT / track['benchmark_path']).read_text(encoding='utf-8'))
        expected[track['id']] = (len(rows), sum(question_units(r)[0] for r in rows))
    assert table == expected
    assert text.count('## Refreshed saved-run inventory') == 1
    assert text.count('### Current readiness and delivery') == 1


def test_refreshed_run_totals_and_snapshot_labels():
    text = (ROOT / 'docs/from_zhongzheng/benchmark_distribution_and_completed_runs_20260916.md').read_text(encoding='utf-8-sig')
    report = json.loads((ROOT / 'output/benchmark_distribution_refresh_20260918.json').read_text(encoding='utf-8'))
    outputs = [r['output'] for kind in ['native', 'artifact'] for r in report[kind]]
    assert len(outputs) == len(set(outputs))
    for kind in ['native', 'artifact']:
        rows = report[kind]
        assert f"Total: {sum(r['saved_finished'] for r in rows)} saved/finished out of {len(rows)} unique registered outputs" in text
    assert 'Retained prior PDF-text artifact completion snapshot' in text
    assert 'Current-ID eligibility checks record membership only' in text
    assert report['paid_model_calls'] == 0
