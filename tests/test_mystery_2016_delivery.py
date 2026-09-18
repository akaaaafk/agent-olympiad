"""Real-catalog regression for reviewed 2016 PDF scope and deterministic grading."""
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from problem_pdf import approved_assets, read_problem_pdf, ProblemPdfError

ROWS = json.loads((ROOT / 'data/benchmarks/mystery_hunt/benchmark.json').read_text(encoding='utf-8'))
YEAR = [r for r in ROWS if r.get('year') == 2016]


def test_2016_has_only_eleven_reviewed_runnable_puzzles():
    assert len(YEAR) == 11
    assert all(r['evaluation']['status'] == 'ready_with_limitations' for r in YEAR)
    assert all(r['evaluation']['evaluator_id'] == 'gold_answer_v1' for r in YEAR)


@pytest.mark.parametrize('row', YEAR, ids=lambda r: r['problem_id'])
def test_correct_and_wrong_answers(row):
    parts = load_gold_parts(row['gold_label'])
    assert GoldAnswerEvaluator(parts, row['gold_label']['expected_answer']).evaluate().total_score == 1
    assert GoldAnswerEvaluator(parts, 'WRONG FIXTURE ANSWER').evaluate().total_score == 0


@pytest.mark.parametrize('row', YEAR, ids=lambda r: r['problem_id'])
def test_reviewed_pages_and_cross_puzzle_page_rejection(row):
    assets = approved_assets(row)
    assert len(assets) == 1
    pages = assets[0]['pages']
    for page in pages:
        payload, attachments = read_problem_pdf(row, pages=[page], render=False)
        assert payload['status'] == 'ok' and not attachments
    outside = next(n for n in range(1, 50) if n not in pages)
    with pytest.raises(ProblemPdfError):
        read_problem_pdf(row, pages=[outside], render=False)


def test_official_blazing_trails_answer_variants():
    row = next(r for r in YEAR if r['problem_id'] == 'mystery_hunt_02146')
    parts = load_gold_parts(row['gold_label'])
    for answer in ('INDIGO BLUE', 'BLUE INDIGO'):
        assert GoldAnswerEvaluator(parts, answer).evaluate().total_score == 1


def test_reviewed_ranges_cover_every_bundle_page_exactly_once():
    pages = [p for r in YEAR for p in approved_assets(r)[0]['pages']]
    assert sorted(pages) == list(range(1, 50))
