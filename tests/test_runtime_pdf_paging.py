"""Regression coverage for bounded, hash-bound artifact PDF delivery."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from otc_artifact_pipeline import prepare_artifact_run
from contest_config import ContestRunConfig
from rules.loader import load_rule_card
from rules.views import agent_view
import problem_pdf


def packet(path, count=62):
    with pymupdf.open() as pdf:
        for page in range(1, count + 1):
            pdf.new_page().insert_text((60, 60), f'Official task page {page}')
        pdf.save(path)
    return path


def test_long_artifact_exposes_all_pages_through_existing_reader(tmp_path):
    prepared = prepare_artifact_run(competition='vis_moot',
        task_pdf=packet(tmp_path / 'task.pdf'), output=tmp_path / 'run',
        provider='tinker', model='Qwen/Qwen3.6-35B-A3B')
    manifest = prepared['manifest']
    row = problem_pdf.visible_benchmark(manifest, SimpleNamespace(), manifest.tasks[0])
    assert problem_pdf.describe(row) == [{'document': 1, 'pages': list(range(1, 63))}]
    result, _ = problem_pdf.read_problem_pdf(row, [61, 62], render=False)
    assert result['pages'] == [61, 62]
    with pytest.raises(problem_pdf.ProblemPdfError):
        problem_pdf.read_problem_pdf(row, [60, 61, 62], render=False)
    with pytest.raises(problem_pdf.ProblemPdfError):
        problem_pdf.read_problem_pdf(row, [63], render=False)
    # A raw benchmark row must not gain the prepared-run host capability.
    assert not problem_pdf.describe(dict(row))
    with prepared['task_asset'].path.open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(problem_pdf.ProblemPdfError, match='changed'):
        problem_pdf.read_problem_pdf(row, [61, 62], render=False)


@pytest.mark.parametrize('competition', ['arml_local', 'ieo_business_case', 'cfa_research_challenge'])
def test_runtime_card_shows_actual_budget_without_mutating_source(competition):
    card = load_rule_card(competition, required=True)
    previous = dict(card.simulation)
    config = ContestRunConfig('otc', card.team_size_default, 73, rule_card=card)
    assert agent_view(config.rule_card)['simulation']['max_turns'] == 73
    assert config.rule_card.max_turns == 73
    assert card.simulation == previous


def test_ieo_has_no_invented_turn_21_research_ban():
    from rules.phases import PhaseSchedule
    for root in (ROOT / 'data/rules', ROOT / 'data/mini_data/rules'):
        card = load_rule_card('ieo_business_case', rules_root=root, required=True)
        assert 'web_search' in card.allowed_tools
        assert PhaseSchedule.from_simulation(card.simulation) is None


def test_judge_reads_every_page_in_bounded_batches_and_reuses_evidence(tmp_path):
    import json
    from evaluation.pdf_paging import paged_judge
    from llm import LLMRequest, LLMAttachment, LLMResponse
    task = packet(tmp_path / 'task.pdf', 7)
    submission = packet(tmp_path / 'submission.pdf', 3)
    seen = []
    def judge(request):
        seen.append(request)
        if request.metadata.get('pdf_paging_stage') == 'evidence':
            assert sum(a.page_end - a.page_start + 1 for a in request.attachments) <= 2
            return LLMResponse(json.dumps({'evidence': 'Specific facts from these pages.',
                                          'unreadable_pages': []}), 'mock', 'mock',
                               usage={'input_tokens': 10, 'output_tokens': 5})
        assert not request.attachments
        assert 'PAGINATED DOCUMENT EVIDENCE' in request.user_prompt
        return LLMResponse('{"score": 4}', 'mock', 'mock',
                           usage={'input_tokens': 10, 'output_tokens': 5})
    request = LLMRequest('Grade carefully.', 'Apply this rubric.', purpose='evaluation',
        attachments=(LLMAttachment(task, 'application/pdf'),
                     LLMAttachment(submission, 'application/pdf', role='judge_only')))
    response = paged_judge(judge, tmp_path / 'cache')(request)
    coverage = [(r.attachments[0].path.name, p) for r in seen if r.attachments
                for p in range(r.attachments[0].page_start, r.attachments[0].page_end + 1)]
    assert coverage == [('task.pdf', p) for p in range(1, 8)] + [('submission.pdf', p) for p in range(1, 4)]
    assert response.usage['api_calls'] == 7  # 4 task batches, 2 submission batches, final judge
    assert response.usage['output_tokens'] == 35
    seen.clear()
    response = paged_judge(judge, tmp_path / 'cache')(request)
    assert len(seen) == 1  # All verified page evidence survives a resume.
    assert response.usage['api_calls'] == 1


@pytest.mark.parametrize('variant', ['single_agent', 'decentralized', 'centralized', 'vallina_otc', 'otc'])
def test_real_artifact_loop_delivers_requested_last_pages_and_completes(tmp_path, variant):
    import json
    from llm import LLMResponse, LLMToolCall
    from otc_artifact_pipeline import run_artifact_contest
    from evaluation.models import load_rubric
    prepared = prepare_artifact_run(competition='vis_moot',
        task_pdf=packet(tmp_path / 'task.pdf', 7), output=tmp_path / 'run',
        provider='tinker', model='Qwen/Qwen3.6-35B-A3B',
        system_variant=variant, max_turns=4)
    reads, delivered, candidate_pages = set(), set(), set()
    def agent(request):
        if not request.tools:
            if request.purpose == 'coach':
                assert not request.attachments
                assert 'Official task page' not in request.user_prompt
            return LLMResponse('Coordinate and verify.', 'mock', 'mock')
        who = request.metadata['agent']
        names = {tool['name'] for tool in request.tools}
        selection = request.metadata.get('problem_pdf_read')
        if selection and selection['document'] == 1:
            assert selection['pages'] == [6, 7]
            assert len(request.attachments) == 2
            assert all(a.mime_type == 'image/png' and a.path.exists() for a in request.attachments)
            delivered.add(who)
        if selection and selection['document'] == 2:
            candidate_pages.add(who)
        if 'read_problem_pdf' in names and who not in reads:
            reads.add(who)
            action, arguments = 'read_problem_pdf', dict(problem_id='deliverable', pages=[6, 7])
        elif 'render_pdf' in names and who == 'Agent_1':
            action, arguments = 'render_pdf', dict(content='A complete research note with evidence, assumptions and a supported conclusion.')
        elif 'read_problem_pdf' in names and '"document": 2' in request.user_prompt:
            action, arguments = 'read_problem_pdf', dict(problem_id='deliverable', pages=[1], document=2)
        elif 'select_problem' in names:
            action, arguments = 'select_problem', dict(problem_id='deliverable')
        elif 'submit' in names and len(names) == 1:
            action, arguments = 'submit', {}
        else:
            action, arguments = 'rest', dict(reason='Wait for the candidate.')
        return LLMResponse('', 'mock', 'mock', usage={'output_tokens': 10},
                           tool_calls=(LLMToolCall(action, arguments),))
    rubric = load_rubric(prepared['rubric'])
    def judge(request):
        if request.metadata.get('pdf_paging_stage') == 'evidence':
            text = json.dumps(dict(evidence='Page-specific fixture evidence.', unreadable_pages=[]))
        elif request.purpose.startswith('collaboration_'):
            text = json.dumps(dict(score=4, justification='Synthetic plumbing check.'))
        else:
            text = json.dumps(dict(criteria=[dict(id=c.id, score=c.min_score, max_score=c.max_score,
                evidence=['Fixture evidence'], justification='Synthetic plumbing check.',
                confidence=1, observable=c.observable) for c in rubric.criteria],
                total_score=sum(c.min_score for c in rubric.criteria), max_score=rubric.total_points,
                warnings=[], limitations=[]))
        return LLMResponse(text, 'mock', 'mock', usage={'output_tokens': 10})
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    assert result['status'] == 'complete'
    assert reads and delivered
    if variant != 'single_agent':
        assert candidate_pages
    assert result['pdf_paging']['coverage'][0]['pages'] == [1, 7]
    assert 'compression' in str(result['evaluation']['limitations'])
    def no_calls(request):
        raise AssertionError('A completed resume must not call a model')
    resumed = run_artifact_contest(prepared, agent_request=no_calls, judge_request=no_calls, resume=True)
    assert resumed['evaluation'] == result['evaluation']


def test_unreadable_judge_pages_never_produce_a_final_grade_and_are_metered(tmp_path):
    import json
    from evaluation.pdf_paging import paged_judge, PagedJudgeError
    from contest_reporting import metered_judge
    from llm import LLMRequest, LLMAttachment, LLMResponse
    def unreadable(request):
        assert request.metadata['pdf_paging_stage'] == 'evidence'
        return LLMResponse(json.dumps(dict(evidence='Cannot read.', unreadable_pages=[1])),
                           'mock', 'mock', usage={'output_tokens': 9})
    state = {}
    judge = metered_judge(paged_judge(unreadable, tmp_path / 'cache'), state)
    with pytest.raises(PagedJudgeError, match='final judgment was not run'):
        judge(LLMRequest('Grade.', '', purpose='evaluation', attachments=(
            LLMAttachment(packet(tmp_path / 'task.pdf', 3), 'application/pdf'),)))
    assert state['evaluation_usage']['api_calls'] == 2
    assert state['evaluation_usage']['output_tokens'] == 18


def test_every_mini_card_uses_runtime_budget_in_both_coach_and_contestant_views():
    import json
    from contest_budget import resolve_contest_budget
    from action_modules.coach import _card_text as coach_card
    from otc_runtime import _card_text as contestant_card
    root = ROOT / 'data/mini_data'
    tracks = json.loads((root / 'benchmarks/index.json').read_text(encoding='utf-8'))['olympiads']
    for track in tracks:
        card = load_rule_card(track['id'], rules_root=root / 'rules', required=True)
        budget = resolve_contest_budget(track['id'])
        config = ContestRunConfig('otc', card.team_size_default, budget.max_turns, rule_card=card)
        for render in (coach_card, contestant_card):
            view = json.loads(render(config.rule_card, config.team_size))
            assert view['simulation']['max_turns'] == budget.max_turns, track['id']
