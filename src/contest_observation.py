"""Agent observations for the strict OTC control; archives remain canonical.

A turn is one team round (budget.turns_used), not an individual API call.
These detached views are for reading only, never for permissions or judging.
"""
from copy import copy
from dataclasses import replace

from contest_session import TaskState

VERSION = 1
# These events are newly stamped summaries of archival state, not this
# round's observations. The current task board is rendered separately.
_ARCHIVAL_SUMMARIES = {'scoreboard', 'coach_opening_summary', 'coach_personal_assignment'}
GUIDANCE = (
    "CURRENT-TURN-ONLY CONTEXT: You have no memory across team rounds. "
    "Only this round's thoughts, messages, drafts, reviews and tool results are "
    "readable. Private, group and public history all expire at the round boundary. "
    "inspect_problem cannot retrieve earlier rounds. Solve from the question and "
    "this round's evidence; review only a version shown in this round. Official "
    "contest state, resource limits and the static pre-contest brief still apply. "
    "The environment retains recorded answers for grading, but their contents "
    "are unavailable to you in later rounds."
)


def current_memory(memory, turn):
    view = copy(memory)
    view._events = [event for event in memory._events
                    if event.turn == turn and event.kind not in _ARCHIVAL_SUMMARIES]
    view._digests = []
    return view


def open_proposals(memory, session, config):
    from otc_runtime import deliberation_ledger
    ids = tuple(deliberation_ledger(memory).report()['open_proposals'])
    if not config.current_turn_only:
        return ids
    created = {e.payload.get('proposal_id') for e in
               current_memory(memory, session.budget.turns_used)._events if e.kind == 'propose'}
    return tuple(pid for pid in ids if pid in created)


def current_version_hashes(session):
    return {event['version_hash'] for event in session.events
            if event['type'] == 'answer_created'
            and event.get('turn') == session.budget.turns_used}


def current_session(session):
    view = copy(session)
    visible = current_version_hashes(session)
    turn = session.budget.turns_used
    view.budget = copy(session.budget)
    view._events = [event for event in session.events if event.get('turn') == turn]
    view._tasks = {}
    for task in session.tasks:
        projected = copy(task)
        projected.versions = [replace(v, parent_hash=v.parent_hash if v.parent_hash in visible else None)
                              for v in task.versions if v.version_hash in visible]
        projected.reviews = [copy(r) for r in task.reviews if r.version_hash in visible]
        projected.submissions = [copy(s) for s in task.submissions if s.turn == turn]
        if task.triaged_turn != turn:
            projected.priority, projected.triage_reason = 'normal', ''
            projected.triaged_by = projected.triaged_turn = None
        if not projected.versions and not projected.submissions and not task.locked:
            projected.state = TaskState.ACTIVE if task is session.active_task else TaskState.UNSEEN
        view._tasks[task.task_id] = projected
    return view


def observe(session, memory, config):
    if not config.current_turn_only:
        return session, memory
    return current_session(session), current_memory(memory, session.budget.turns_used)


def policy_metadata(config):
    return ({'context_scope': 'current_team_round_only',
             'current_turn_context_version': VERSION,
             'cross_turn_private_group_public': False} if config.current_turn_only else {})


def require_current_version(session, task_id):
    task = session.task(task_id)
    if not task.versions or task.versions[-1].version_hash not in current_version_hashes(session):
        raise ValueError('current-turn-only context: this action requires a draft created in this round')


def require_current_action(action, arguments, session, memory, config):
    """Fail before request logging or side effects; never rehydrate old artifacts."""
    if not config.current_turn_only:
        return
    target = str(arguments.get('problem_id') or
                 (session.active_task.task_id if session.active_task else ''))
    if action in {'review_answer', 'request_review', 'submit_code'} and target:
        require_current_version(session, target)
    if action in {'challenge', 'provide_evidence', 'revise', 'decide'}:
        proposal_id = arguments.get('proposal_id')
        if not any(e.kind == 'propose' and e.payload.get('proposal_id') == proposal_id
                   for e in current_memory(memory, session.budget.turns_used)._events):
            raise ValueError('current-turn-only context: proposal is not from this round')


def filter_actions(actions, session, memory, config):
    """Intersect canonical permissions with this round's readable artifacts."""
    if not config.current_turn_only:
        return actions
    visible = current_version_hashes(session)
    active = session.active_task
    current = bool(active and active.versions and active.versions[-1].version_hash in visible)
    proposals = current_memory(memory, session.budget.turns_used)._events if memory else ()
    have_proposal = any(e.kind == 'propose' for e in proposals)
    proposal_ids = {e.payload.get('proposal_id') for e in proposals if e.kind == 'propose'}
    result = set()
    for spec in actions:
        if spec.name in {'submit_code', 'request_review'} and not current:
            continue
        if spec.name in {'challenge', 'provide_evidence', 'revise', 'decide'} and not have_proposal:
            continue
        if spec.name in {'challenge', 'provide_evidence', 'revise', 'decide'}:
            args = tuple(replace(a, enum=tuple(pid for pid in a.enum if pid in proposal_ids))
                         if a.name == 'proposal_id' else a for a in spec.arguments)
            if any(a.name == 'proposal_id' and not a.enum for a in args):
                continue
            spec = replace(spec, arguments=args)
        if spec.name == 'review_answer':
            ids = tuple(t.task_id for t in session.visible_tasks
                        if t.versions and t.versions[-1].version_hash in visible)
            args = tuple(replace(a, enum=tuple(v for v in a.enum if v in
                         (visible if a.name == 'version_hash' else ids)))
                         if a.name in {'problem_id', 'version_hash'} and a.enum else a
                         for a in spec.arguments)
            if not ids or any(a.name == 'version_hash' and not a.enum for a in args):
                continue
            spec = replace(spec, arguments=args)
        if spec.name == 'inspect_problem':
            spec = replace(spec, description='Read a problem statement and this round only: drafts, reviews and tool results. Earlier rounds cannot be retrieved.')
        result.add(spec)
    return frozenset(result)
