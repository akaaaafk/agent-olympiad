"""Baseline-neutral draft limits and bounded, lossless answer reading."""
from typing import Any

from contest_manifest import ContestManifest, ManifestTask

VERSION = 3
DRAFT_MAX_CHARS = 8000
PREVIEW_CHARS = 800
DEFAULT_PAGE_CHARS = 2000
MAX_PAGE_CHARS = 4000


def is_source_task(task: ManifestTask) -> bool:
    return (task.programming or task.task_type in {'programming', 'algorithmic_programming'}
            or task.benchmark.get('evaluation', {}).get('grading_policy') == 'source_review_llm_v1')


def work_char_limit(manifest: ContestManifest, task_id: str | None) -> int | None:
    contract = manifest.metadata.get('artifact_contract')
    if contract:
        return int(contract['max_source_chars'])
    task = next((t for t in manifest.tasks if t.task_id == task_id), None)
    if task is None or is_source_task(task):
        return None
    # Some native proof packets have a larger text-deliverable cap without a
    # PDF artifact contract. Read only that resource setting, never attach OTC
    # strategy, roles or memory to an ordinary baseline. The loader respects
    # the selected data root, including isolated mini_data.
    from rules.loader import load_rule_card
    card = load_rule_card(manifest.competition_id)
    configured = (card.simulation.get('open_table_coach', {}).get(
        'contestant_turn_policy', {}).get('max_chars_by_action', {}).get('work')
        if card else None)
    return max(DRAFT_MAX_CHARS, configured) if type(configured) is int else DRAFT_MAX_CHARS


def action_argument_limits(manifest: ContestManifest) -> dict[str, dict[str, int]]:
    """Transport can only declare a field-wide cap; dispatch checks its target.

    Mixed source/draft requests must not cap source with a draft limit. There is
    still an exact target-aware guard at the mutation boundary for every provider.
    """
    limits = [work_char_limit(manifest, task.task_id) for task in manifest.tasks]
    if not limits or any(limit is None for limit in limits):
        return {}
    cap = max(limits)
    result = {'work': {'content': cap}, 'submit': {'answer': cap}}
    if manifest.metadata.get('artifact_contract'):
        result['render_pdf'] = {'content': cap}
    return result


def action_argument_limits_by_task(manifest: ContestManifest) -> dict:
    """Retain the selected draft's cap even in mixed source/draft packets."""
    result = {}
    for task in manifest.tasks:
        cap = work_char_limit(manifest, task.task_id)
        limits = {} if cap is None else {'work': {'content': cap}, 'submit': {'answer': cap}}
        if cap is not None and manifest.metadata.get('artifact_contract'):
            limits['render_pdf'] = {'content': cap}
        result[task.task_id] = limits
    return result


def action_payload_limits() -> dict:
    from action_modules.competition_tools import BY_NAME
    from argument_limits import PREPARATION_MAX_CHARS
    return {name: PREPARATION_MAX_CHARS for name in BY_NAME}


def validate_work_content(manifest: ContestManifest, task_id: str | None, content: Any) -> None:
    task = next((t for t in manifest.tasks if t.task_id == task_id), None)
    if manifest.metadata.get('artifact_contract') or task is None or not is_source_task(task):
        from answer_content import content_error
        error = content_error(content)
        if error:
            raise ValueError(error)
    limit = work_char_limit(manifest, task_id)
    if limit is not None and len(str(content)) > limit:
        raise ValueError(
            f'work exceeds the {limit}-character limit; rewrite explicitly and retain '
            'the complete final answer. Nothing was saved or clipped.')


def work_guidance(manifest: ContestManifest, task_id: str | None) -> str:
    limit = work_char_limit(manifest, task_id)
    if limit is None:
        return ''
    if manifest.metadata.get('artifact_contract') or limit > DRAFT_MAX_CHARS:
        return f'WORK DELIVERABLE LIMIT: {limit} characters under this task\'s delivery contract. Preserve the complete deliverable.\n\n'
    return (
        'WORK DRAFT LENGTH: Aim for 2,000-4,000 characters when a detailed explanation '
        'is useful; shorter complete answers are welcome. This is a soft target, not '
        f'a minimum or rejection threshold. The hard limit is {limit} characters, '
        'including spaces, newlines and formula source. Preserve essential reasoning, '
        'uncertainty and the complete final answer. Accepted drafts are stored in full; '
        'previews do not alter saved answers. These are character limits, not token limits.\n\n')


def text_page(text: str, offset: int = 0, limit: int = DEFAULT_PAGE_CHARS) -> dict[str, Any]:
    if type(offset) is not int or offset < 0:
        raise ValueError('offset must be a non-negative integer character position')
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_CHARS:
        raise ValueError(f'limit must be an integer between 1 and {MAX_PAGE_CHARS}')
    if offset > len(text):
        raise ValueError('offset exceeds the visible content length')
    end = min(len(text), offset + limit)
    return {'offset': offset, 'end': end, 'total_chars': len(text),
            'next_offset': end if end < len(text) else None, 'content': text[offset:end]}


def draft_preview(text: str) -> dict[str, Any]:
    page = text_page(text, limit=PREVIEW_CHARS)
    return {'content': page.pop('content'), 'content_page': page}


def event_preview(event) -> Any:
    """Bound repeated work in prompts without changing the event archive."""
    if event.kind == 'work' and isinstance(event.payload, dict):
        content = event.payload.get('content')
        if isinstance(content, str):
            return {**event.payload, **draft_preview(content),
                    'problem_id': event.task_id,
                    'reading': 'Use inspect_problem for version hashes and full answer pages.'}
    return event.payload
