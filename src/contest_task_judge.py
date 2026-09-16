"""Post-submission rubric evaluation; references never enter contestant prompts."""
from dataclasses import replace
from pathlib import Path
import hashlib

from evaluation.models import load_rubric
from evaluation.finalize import _reference_text
from evaluation.rubric_llm import RubricDocumentEvaluator

ROOT = Path(__file__).resolve().parents[1]


def task_pdf_asset(task):
    if not (task.benchmark.get('evaluation') or {}).get('task_pdf_required'):
        return None
    from problem_pdf import approved_assets
    from artifacts.assets import Asset
    import pymupdf
    assets = approved_assets(task.benchmark)
    if len(assets) != 1:
        raise ValueError('Task judge requires exactly one reviewed contestant PDF')
    asset = assets[0]
    with pymupdf.open(asset['resolved_path']) as doc:
        count = len(doc)
    if set(asset['pages']) != set(range(1, count + 1)):
        raise ValueError('Full task PDF is not approved; refuse partial judging')
    return Asset(asset['resolved_path'], 'application/pdf', 'agent_visible', 1, count, asset['sha256'])


def task_judge_specs(manifest):
    specs = {}
    for task in manifest.tasks:
        config = task.benchmark.get('evaluation') or {}
        if task.programming or config.get('evaluator_id') != 'rubric_llm_v1':
            continue
        if config.get('status') == 'deferred':
            continue
        path = (ROOT / str(config.get('rubric_path') or '')).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f'{task.task_id}: missing registered rubric')
        specs[task.task_id] = {'rubric_path': str(path.relative_to(ROOT)),
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        asset = task_pdf_asset(task)
        if asset:
            specs[task.task_id]['task_pdf_sha256'] = asset.sha256
        from numeric_gold_check import numeric_identity
        numeric = numeric_identity(task.benchmark)
        if numeric:
            specs[task.task_id]['numeric_gold'] = numeric
    return specs


def judge_task(task, submission, request_fn):
    if task.question_id is not None:
        raise ValueError('Split-task rubric mapping is required before judging a packet rubric')
    original = load_rubric(ROOT / task.benchmark['evaluation']['rubric_path'])
    criteria = tuple(c for c in original.criteria if c.observable)
    excluded = [c.id for c in original.criteria if not c.observable]
    if not criteria:
        raise ValueError('No observable rubric criteria')
    rubric = replace(original, criteria=criteria,
                     total_points=sum(c.max_score for c in criteria),
                     rubric_id=original.rubric_id + ('_observable' if excluded else ''))
    if not submission.strip():
        value = dict(total_score=0, max_score=rubric.total_points,
                     method='empty_submission_zero', criteria=[],
                     limitations=['No submission was made; no LLM judge call.'])
    else:
        from judge_references import winner_references, with_winner_references, with_rule_context
        from rules.loader import load_rule_card
        card = load_rule_card(str(task.benchmark.get('competition_id') or ''))
        if card:
            request_fn = with_rule_context(request_fn, card.rules_text)
        examples = winner_references(task.parent_problem_id)
        if examples:
            request_fn = with_winner_references(request_fn, examples)
        task_asset = task_pdf_asset(task)
        value = RubricDocumentEvaluator(
            request_fn=request_fn, rubric=rubric, task_text=task.prompt,
            submission_text=submission, reference_text=_reference_text(task.benchmark),
            task_asset=task_asset, media='pdf' if task_asset else 'text',
        ).evaluate().to_dict()
    score, maximum = value['total_score'], value['max_score']
    result = dict(graded=True, status='rubric_proxy_scored', method='rubric_llm_v1',
                score=score, max_score=maximum, utility=score / maximum,
                partial_score=score, graded_max_score=maximum, graded_parts=1,
                ungraded_part_ids=[], original_rubric_max_score=original.total_points,
                excluded_criteria=excluded, official_score_equivalent=False,
                evaluation=value,
                submission_sha256=hashlib.sha256(submission.encode('utf-8')).hexdigest())
    from numeric_gold_check import check_submission
    numeric = check_submission(task.benchmark, submission)
    if numeric:
        result['numeric_gold_check'] = numeric
    return result
