"""Reproduced page-evidence failures, with offline provider responses."""
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from llm import LLMAttachment, LLMRequest, LLMResponse
from evaluation.pdf_paging import paged_judge, PagedJudgeError
from evaluation.models import Rubric, Criterion
from evaluation.structured_judge import evaluate_structured_response
from contest_reporting import metered_judge
from judge_references import with_rule_context


@pytest.fixture
def request_pdf(tmp_path):
    path = tmp_path / 'task.pdf'
    with pymupdf.open() as pdf:
        for i in range(3):
            pdf.new_page().insert_text((60, 60), f'Task page {i + 1}')
        pdf.save(path)
    return LLMRequest('Evaluate.', 'Grade criterion a.', purpose='evaluation',
        attachments=(LLMAttachment(path, 'application/pdf'),))


def score():
    return json.dumps(dict(criteria=[dict(id='a', score=1, max_score=1,
        evidence=['Page evidence'], justification='Supported.', confidence=1, observable=True)],
        total_score=1, max_score=1, warnings=[], limitations=[]))


@pytest.mark.parametrize('evidence', [
    r'{"evidence":"The equation is \sqrt{2}.","unreadable_pages":[]}',
    r'{"evidence":"The equation is \\sqrt{2}.\nNext line.","unreadable_pages":[]}',
])
def test_math_evidence_uses_conservative_common_json_parser(tmp_path, request_pdf, evidence):
    from evaluation.models import load_judge_json
    seen = []
    def judge(request):
        seen.append(request)
        return LLMResponse(evidence if request.attachments else score(), 'mock', 'mock',
                           usage={'output_tokens': 10})
    paged_judge(judge, tmp_path / 'cache')(request_pdf)
    assert len(seen) == 3
    expected = load_judge_json(evidence)['evidence']
    saved = [json.loads(p.read_text()) for p in (tmp_path / 'cache').glob('*.json')]
    assert all(row['evidence'] == expected for row in saved)


@pytest.mark.parametrize('evidence', ['{"evidence":',
    '{"evidence":"Unreadable","unreadable_pages":[1]}',
    '{"evidence":"","unreadable_pages":[]}',
    json.dumps({'evidence': 'x' * 3201, 'unreadable_pages': []})])
def test_invalid_evidence_still_cannot_produce_a_final_score(tmp_path, request_pdf, evidence):
    seen = []
    def judge(request):
        seen.append(request)
        return LLMResponse(evidence, 'mock', 'mock', usage={'output_tokens': 10})
    with pytest.raises(PagedJudgeError, match='failed validation'):
        paged_judge(judge, tmp_path / 'cache')(request_pdf)
    assert len(seen) == 2
    assert all(r.metadata['pdf_paging_stage'] == 'evidence' for r in seen)


@pytest.mark.parametrize('length', [1601, 1847, 1977, 3200])
def test_evidence_up_to_3200_characters_is_preserved(tmp_path, request_pdf, length):
    evidence = 'x' * length
    seen = []
    def judge(request):
        seen.append(request)
        if request.attachments:
            assert 'at most 3200 characters' in request.user_prompt
            text = json.dumps(dict(evidence=evidence, unreadable_pages=[]))
        else:
            notes = json.loads(request.user_prompt.split('\n')[-1])['batches']
            assert all(note['evidence'] == evidence for note in notes)
            text = score()
        return LLMResponse(text, 'mock', 'mock', usage={'output_tokens': 10})
    paged_judge(judge, tmp_path / 'cache')(request_pdf)
    assert [r.metadata['pdf_paging_stage'] for r in seen] == ['evidence', 'evidence', 'final']


def test_per_batch_limit_still_respects_total_evidence_budget(tmp_path, request_pdf):
    from evaluation.pdf_paging import _plan, EVIDENCE_CHARS
    # Eight two-page attachments share the same 24000-character total budget.
    attachment = replace(request_pdf.attachments[0], page_start=1, page_end=2)
    request = replace(request_pdf, attachments=(attachment,) * 8)
    _, batches, paginated, limit = _plan(request)
    assert paginated and len(batches) == 8
    assert limit == 3000
    assert limit * len(batches) <= EVIDENCE_CHARS == 24000
    seen = []
    def judge(current):
        seen.append(current)
        assert current.metadata['pdf_paging_stage'] == 'evidence'
        assert 'at most 3000 characters' in current.user_prompt
        return LLMResponse(json.dumps(dict(evidence='x' * 3001, unreadable_pages=[])),
                           'mock', 'mock', usage={'output_tokens': 10})
    with pytest.raises(PagedJudgeError, match='failed validation'):
        paged_judge(judge, tmp_path / 'cache')(request)
    assert len(seen) == 2


def test_changed_character_limit_invalidates_evidence_cache(tmp_path, request_pdf, monkeypatch):
    import evaluation.pdf_paging as paging
    seen = []
    def judge(request):
        seen.append(request)
        return LLMResponse(json.dumps(dict(evidence='Page facts.', unreadable_pages=[]))
                           if request.attachments else score(), 'mock', 'mock',
                           usage={'output_tokens': 10})
    call = paged_judge(judge, tmp_path / 'cache')
    with monkeypatch.context() as patch:
        patch.setattr(paging, 'MAX_BATCH_EVIDENCE_CHARS', 1600)
        call(request_pdf)
    seen.clear()
    call(request_pdf)
    assert [r.metadata['pdf_paging_stage'] for r in seen] == ['evidence', 'evidence', 'final']
    assert all('at most 3200 characters' in r.user_prompt for r in seen if r.attachments)


def test_final_format_retry_reuses_evidence_with_rule_wrapper(tmp_path, request_pdf):
    counts = Counter()
    def judge(request):
        stage = request.metadata['pdf_paging_stage']
        counts[stage] += 1
        if stage == 'evidence':
            assert 'Official scoring rules.' in request.user_prompt
            assert 'Your previous response failed output validation' not in request.user_prompt
            text = json.dumps(dict(evidence='Page facts.', unreadable_pages=[]))
        else:
            text = 'invalid final JSON' if counts[stage] == 1 else score()
            if counts[stage] == 2:
                assert 'Your previous response failed output validation' in request.user_prompt
        return LLMResponse(text, 'mock', 'mock', usage={'output_tokens': 10})
    result = evaluate_structured_response(
        with_rule_context(paged_judge(judge, tmp_path / 'cache'), 'Official scoring rules.'),
        request_pdf, rubric=Rubric('r', 'Test', 1, (Criterion('a', 'A', 1, 'A'),)),
        evaluator_id='test', evaluator_version='1', prompt_version='1')
    assert counts == {'evidence': 2, 'final': 2}
    assert result.total_score == 1
    assert result.usage['api_calls'] == 4
    assert result.usage['output_tokens'] == 40


def test_cache_checksum_failure_before_sampling_has_zero_api_usage(tmp_path, request_pdf):
    seen = []
    def judge(request):
        seen.append(request)
        return LLMResponse(json.dumps(dict(evidence='Facts.', unreadable_pages=[]))
                           if request.attachments else score(), 'mock', 'mock',
                           usage={'output_tokens': 10})
    cache = tmp_path / 'cache'
    paging = paged_judge(judge, cache)
    paging(request_pdf)
    for path in cache.glob('*.json'):
        data = json.loads(path.read_text())
        data['evidence_sha256'] = '0' * 64
        path.write_text(json.dumps(data))
    seen.clear()
    state = {}
    with pytest.raises(PagedJudgeError, match='binding mismatch'):
        metered_judge(paging, state)(request_pdf)
    assert not seen
    assert state['evaluation_usage']['api_calls'] == 0
    assert state['evaluation_usage']['output_tokens'] == 0
    assert state['evaluation_usage']['unmetered_calls'] == 0


@pytest.mark.parametrize('change', ['rubric', 'system', 'rules', 'source', 'pages', 'judge'])
def test_real_evaluation_input_changes_invalidate_page_evidence(tmp_path, request_pdf, change):
    seen = []
    def judge(request):
        seen.append(request.metadata['pdf_paging_stage'])
        return LLMResponse(json.dumps(dict(evidence='Facts.', unreadable_pages=[]))
                           if request.attachments else score(), 'mock', 'mock',
                           usage={'output_tokens': 10})
    cache = tmp_path / 'cache'
    original = with_rule_context(paged_judge(judge, cache, cache_namespace='judge-a'), 'Rules A')
    original(request_pdf)
    seen.clear()
    namespace, rules = 'judge-a', 'Rules A'
    if change == 'rubric':
        request_pdf = replace(request_pdf, user_prompt='Grade criterion b.')
    elif change == 'system':
        request_pdf = replace(request_pdf, system_prompt='Different grading instructions.')
    elif change == 'rules':
        rules = 'Rules B'
    elif change == 'source':
        with request_pdf.attachments[0].path.open('ab') as stream:
            stream.write(b'\n% Changed source bytes\n')
    elif change == 'pages':
        attachment = request_pdf.attachments[0]
        request_pdf = replace(request_pdf, attachments=(replace(attachment, page_start=1, page_end=2),
                                                        replace(attachment, page_start=3, page_end=3)))
    elif change == 'judge':
        namespace = 'judge-b'
    with_rule_context(paged_judge(judge, cache, cache_namespace=namespace), rules)(request_pdf)
    assert seen == ['evidence', 'evidence', 'final']


def test_unrecognized_feedback_span_keeps_full_prompt(tmp_path, request_pdf):
    from evaluation.pdf_paging import _evidence_user
    current = replace(request_pdf, metadata={'evaluation_format_feedback':
        {'start': 0, 'text': 'Not present in the actual prompt'}})
    assert _evidence_user(current) == request_pdf.user_prompt


@pytest.mark.parametrize('paginated', [False, True])
@pytest.mark.parametrize('failure', ['zero', 'known', 'unknown'])
def test_failed_provider_usage_is_counted_once(tmp_path, request_pdf, paginated, failure):
    class ProviderError(RuntimeError):
        pass
    def judge(request):
        error = ProviderError('Offline failure')
        if failure == 'zero':
            error.usage = {'api_calls': 0, 'output_tokens': 0}
        elif failure == 'known':
            error.usage = {'api_calls': 2, 'output_tokens': 17, 'unknown_usage_attempts': 1}
        raise error
    state = {}
    request_fn = paged_judge(judge, tmp_path / 'cache') if paginated else judge
    with pytest.raises((ProviderError, PagedJudgeError)):
        metered_judge(request_fn, state)(request_pdf)
    expected = {'zero': (0, 0, 0), 'known': (2, 17, 1), 'unknown': (1, 0, 1)}[failure]
    assert tuple(state['evaluation_usage'][key] for key in
                 ('api_calls', 'output_tokens', 'unmetered_calls')) == expected


def test_successful_cached_provider_response_can_report_zero_calls():
    state = {}
    metered_judge(lambda req: LLMResponse(score(), 'mock', 'mock',
        usage={'api_calls': 0, 'output_tokens': 0}), state)(None)
    assert state['evaluation_usage']['api_calls'] == 0
    assert state['evaluation_usage']['unmetered_calls'] == 0


def test_local_pdf_range_error_has_zero_calls(tmp_path, request_pdf):
    def judge(request):
        pytest.fail('Invalid PDF ranges must fail before sampling')
    request = replace(request_pdf, attachments=(replace(request_pdf.attachments[0], page_end=4),))
    state = {}
    with pytest.raises(ValueError, match='page range'):
        metered_judge(paged_judge(judge, tmp_path / 'cache'), state)(request)
    assert state['evaluation_usage']['api_calls'] == 0
    assert state['evaluation_usage']['unmetered_calls'] == 0


def test_valid_evidence_json_with_length_finish_cannot_be_cached_or_graded(tmp_path, request_pdf):
    sent, state = [], {}
    def judge(request):
        sent.append(request)
        return LLMResponse(json.dumps(dict(evidence='Partial facts.', unreadable_pages=[])),
            'mock', 'mock', usage={'api_calls': 1, 'output_tokens': 13, 'finish_reason': 'length'})
    cache = tmp_path / 'cache'
    with pytest.raises(PagedJudgeError):
        metered_judge(paged_judge(judge, cache), state)(request_pdf)
    assert len(sent) == state['evaluation_usage']['api_calls'] == 2
    assert state['evaluation_usage']['output_tokens'] == 26
    assert all(req.metadata['pdf_paging_stage'] == 'evidence' for req in sent)
    assert not list(cache.glob('*.json'))


def test_structured_retry_failure_retains_prior_usage_without_double_counting(request_pdf):
    sent, state = [], {}
    def judge(request):
        sent.append(request)
        if len(sent) == 1:
            return LLMResponse('Invalid JSON', 'mock', 'mock', usage={'output_tokens': 13})
        error = RuntimeError('Fixture failed retry')
        error.usage = {'api_calls': 2, 'unknown_usage_attempts': 2}
        raise error
    with pytest.raises(RuntimeError) as caught:
        evaluate_structured_response(metered_judge(judge, state), request_pdf,
            rubric=Rubric('r', 'Test', 1, (Criterion('a', 'A', 1, 'A'),)),
            evaluator_id='test', evaluator_version='1', prompt_version='1')
    assert caught.value.usage['api_calls'] == state['evaluation_usage']['api_calls'] == 3
    assert caught.value.usage['output_tokens'] == state['evaluation_usage']['output_tokens'] == 13
    assert caught.value.usage['unknown_usage_attempts'] == state['evaluation_usage']['unmetered_calls'] == 2
