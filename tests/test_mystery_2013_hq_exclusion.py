"""Do not certify an HQ performance instruction as a final answer."""
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def test_hq_record_excluded_without_promoting_other_2013_tasks():
    rows = json.loads((ROOT / 'data/benchmarks/mystery_hunt/benchmark.json').read_text(encoding='utf-8'))
    assert not any(r['problem_id'] == 'mystery_hunt_01692' for r in rows)
    # Later catalog cleanup may retire the other pending records. Verify this
    # scoped repair's immutable report, not a historical live-catalog count.
    report = json.loads((ROOT / 'output/mystery_2013_repair_20260917.json').read_text(encoding='utf-8'))
    assert report['promoted'] == []
    assert [r['record']['problem_id'] for r in report['removed']] == ['mystery_hunt_01692']


def test_original_record_and_hq_evidence_preserved():
    report = json.loads((ROOT / 'output/mystery_2013_repair_20260917.json').read_text(encoding='utf-8'))
    assert report['promoted'] == [] and len(report['removed']) == 1
    excluded = report['removed'][0]
    assert excluded['record']['gold_label']['expected_answer'] == 'SING ABOUT COINS'
    assert (ROOT / excluded['record']['source_file']).is_file()
    evidence = (ROOT / excluded['source_evidence']).read_text(encoding='utf-8')
    assert 'Teams who came to HQ and sang about coins' in evidence
    assert 'AVENGERS' in evidence


def test_score_export_preserves_all_three_original_pages():
    source = ROOT / 'data/raw/mystery_hunt/separated_2013_attachments_20260913/mystery_hunt_01692/input/puzzle.pdf'
    exported = ROOT / 'data/raw/mystery_hunt/reviewed_2013_20260917/puzzles.pdf'
    with pymupdf.open(source) as original, pymupdf.open(exported) as output:
        assert len(original) == len(output) == 3
        for a, b in zip(original, output, strict=True):
            assert a.get_pixmap().samples == b.get_pixmap().samples
