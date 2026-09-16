"""Bind remembered claims to contestant-visible draft and review evidence.

No evaluator, submissions, scores or hidden tasks participate in this view.
The returned values are copies; reading memory never changes a contest draft.
"""
from __future__ import annotations

import hashlib
import json

from evaluation.final_answer import extract_final_answer


def visible_tasks(session):
    return {task.task_id: task for task in session.visible_tasks} if session is not None else {}


def binding(task) -> dict:
    version = task.versions[-1] if task is not None and task.versions else None
    reviews = [(r.reviewer, r.decision, r.body) for r in task.reviews
               if not r.stale and version is not None and r.version_hash == version.version_hash
               and r.reviewer != version.author] if task is not None else []
    return {
        'version_hash': version.version_hash if version else None,
        'review_digest': hashlib.sha256(json.dumps(reviews, ensure_ascii=False).encode()).hexdigest(),
    }


def team_binding(tasks) -> str:
    """Team observations expire when any visible draft or review changes."""
    board = {task_id: binding(task) for task_id, task in tasks.items()}
    return hashlib.sha256(json.dumps(board, sort_keys=True).encode()).hexdigest()


def answer_state(task) -> dict:
    if task is None or not task.versions:
        return {'version_hash': None, 'review_status': 'no_candidate', 'final_answer': None}
    version = task.versions[-1]
    reviews = [r for r in task.reviews if not r.stale and r.version_hash == version.version_hash
               and r.reviewer != version.author]
    status = ('rejected' if any(r.decision == 'reject' for r in reviews) else
              'approved' if any(r.decision == 'approve' for r in reviews) else 'unreviewed')
    value = extract_final_answer(version.content, part_id=task.task_id) if task.kind != 'programming' else None
    # Put counterevidence first so a budgeted prompt does not hide it behind approvals.
    evidence = sorted(reviews, key=lambda r: r.decision != 'reject')[:3]
    return {
        'version_hash': version.version_hash, 'author': version.author,
        'review_status': status,
        'final_answer': value.final_answer if value and value.method != 'unstructured' else None,
        'reviews': [{'reviewer': r.reviewer, 'decision': r.decision, 'reason': r.body[:320]}
                    for r in evidence],
        'status': 'live draft and peer reviews; approval is not proof of correctness',
    }


def accepted_work_version(task, event):
    """Work is logged before dispatch; only actual matching versions count."""
    if task is None or task.kind == 'programming':
        return None
    return next((v for v in reversed(task.versions)
                 if v.content == event.payload.get('content') and v.author == event.actor), None)


def grounded_row(event, task, *, compact=False) -> dict:
    state = event.payload
    live = binding(task)
    essence = state.get('essence')
    if essence is not None and essence.get('answer_binding') != live:
        essence = None
    exchanges = [row for row in state['exchanges'] if row.get('answer_binding') == live
                 and not (row['kind'] == 'work' and not row.get('accepted_version_hash'))
                 and not (essence and row['kind'] == 'think'
                          and row['source_event_id'] <= essence['through_event_id'])]
    return {
        'task_id': event.task_id, 'memory_id': event.event_id,
        'answer_state': answer_state(task), 'essence': essence,
        # The exact current candidate is already in answer_state. Keep work
        # receipts in the archive without a second, potentially stale answer.
        'candidate_claim': None, 'exchanges': exchanges[-1:] if compact else exchanges[-3:],
    }
