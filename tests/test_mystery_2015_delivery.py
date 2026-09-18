"""2015 packet coverage, scope rejection and deterministic-answer regression."""
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from problem_pdf import approved_assets, read_problem_pdf, ProblemPdfError

ROWS = json.loads((ROOT / 'data/benchmarks/mystery_hunt/benchmark.json').read_text(encoding='utf-8'))
YEAR = [r for r in ROWS if r.get('year') == 2015]


def test_only_twelve_supported_puzzles_retained():
    assert len(YEAR) == 12
    assert all(r['evaluation']['status'] == 'ready_with_limitations' for r in YEAR)
    assert all(r['evaluation']['evaluator_id'] == 'gold_answer_v1' for r in YEAR)


@pytest.mark.parametrize('row', YEAR, ids=lambda r: r['problem_id'])
def test_gold_grading(row):
    parts = load_gold_parts(row['gold_label'])
    for answer, score in [(row['gold_label']['expected_answer'], 1),
                          (row['gold_label']['expected_answer'].lower(), 1), ('WRONG FIXTURE ANSWER', 0)]:
        assert GoldAnswerEvaluator(parts, answer).evaluate().total_score == score


@pytest.mark.parametrize('row', YEAR, ids=lambda r: r['problem_id'])
def test_page_access_is_task_scoped(row):
    assets = approved_assets(row)
    assert len(assets) == 1
    pages = assets[0]['pages']
    for page in pages:
        payload, attachments = read_problem_pdf(row, pages=[page], render=False)
        assert payload['status'] == 'ok' and not attachments
    outside = next(p for p in range(1, 20) if p not in pages)
    with pytest.raises(ProblemPdfError):
        read_problem_pdf(row, pages=[outside], render=False)


def test_every_bundle_page_has_one_puzzle_owner():
    assert sorted(p for r in YEAR for p in approved_assets(r)[0]['pages']) == list(range(1, 20))


def test_coins_includes_article_and_all_coin_rows():
    row = next(r for r in YEAR if r['problem_id'] == 'mystery_hunt_01997')
    assert approved_assets(row)[0]['pages'] == [2, 3, 4]
