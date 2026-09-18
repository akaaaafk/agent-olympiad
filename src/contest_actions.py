"""Contest action effects and rule-card gates, independent of the turn loop."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Literal

import otc_runtime
from answer_identity import conflicting_answer_task, declared_answer_tasks
from evaluation.final_answer import extract_final_answer
from action_modules.memory import share_note as _share_note, recall_notes
from action_modules.task_specific import is_answer_sheet_contest as _is_answer_sheet_contest
from action_modules.competition_tools import ACTION_NAMES as PREPARATION_ACTIONS
from action_modules.competition_flow import ACTION_NAMES as FLOW_ACTIONS
from competition_tool_runtime import execute_preparation_tool, public_context
from computer_capacity import (
    COMPUTER_ACTIONS, COMPUTER_USE_EVENT, require_computer_slot,
    session_computer_state,
)
from contest_config import ContestRunConfig, TaskActionExecutor
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_session import ContestSession, TaskState, TaskUnit
from programming_candidates import execution_key, failed_execution
from rulecard_policy import OpenTablePolicy, WORKSTATION_ACTION_NAMES, clip_text
from strategy import StrategicPolicy
from tool_registry import ACTION_REGISTRY, DELIBERATION_ACTION_NAMES, DESK_ACTION_NAMES
from work_content import (DEFAULT_PAGE_CHARS, draft_preview, text_page,
                          validate_work_content, work_char_limit)

_INSPECT_STATEMENT_CHARS = 6000

_CARD_CLIPPED_FIELDS: dict[str, str] = {
    "work": "content",
    "speak": "content",
    "direct_message": "content",
    "rest": "reason",
    "propose": "content",
    "challenge": "content",
    "provide_evidence": "content",
    "revise": "content",
    "decide": "reason",
}


def _required_answer_sheet_task_ids(manifest: ContestManifest) -> set[str]:
    scored = {task.task_id for task in manifest.tasks if task.max_score > 0}
    return scored or {task.task_id for task in manifest.tasks}


def _local_run_reports(memory: ContestMemory) -> dict[str, str]:
    """Latest author speak report per version hash."""
    reports: dict[str, str] = {}
    for event in memory.archival_snapshot()["events"]:
        payload = event.get("payload", {})
        if event["kind"] == "local_run_report" and payload.get("version_hash"):
            reports[str(payload["version_hash"])] = str(payload.get("report") or "")
    return reports


def _sample_reports(memory: ContestMemory) -> dict[str, dict[str, Any]]:
    """Latest official-sample judge report per version hash."""
    reports: dict[str, dict[str, Any]] = {}
    for event in memory.archival_snapshot()["events"]:
        payload = event.get("payload", {})
        if event["kind"] == "sample_judge_result" and payload.get("version_hash"):
            reports[str(payload["version_hash"])] = {
                "sample_verdict": payload.get("sample_verdict"),
                "sample_summary": payload.get("sample_summary"),
                "sample_cases": payload.get("sample_cases") or [],
            }
    return reports


def _set_work_assignment(
    personal_assignments: dict[str, dict[str, Any]],
    agent: str,
    problem_ids: list[str],
) -> None:
    """Replace one seat's enforced work list (leader reassignment)."""
    current = personal_assignments.get(agent) or {
        "agent": agent,
        "work_tasks": [],
        "review_tasks": [],
        "summary": "",
        "switch_conditions": [],
        "final_check": [],
    }
    personal_assignments[agent] = {**current, "work_tasks": list(problem_ids)}


def _next_task(
    session: ContestSession,
    policy: StrategicPolicy | None = None,
    *,
    exclude_task_id: str | None = None,
) -> TaskUnit | None:
    candidates = [
        task
        for task in session.tasks
        if task.task_id != exclude_task_id
        and not task.locked
        and not _task_complete(task)
        and (
            task.state is not TaskState.BLOCKED
            or (
                policy is not None
                and policy.can_revisit(
                    task,
                    current_turn=session.budget.turns_used,
                )
            )
        )
    ]
    # Team triage reorders within the manifest order; hopeless tasks still
    # qualify, they simply come last.
    candidates.sort(key=lambda task: task.priority_rank)
    unseen = [task for task in candidates if not task.versions and not task.submissions]
    return (unseen or candidates or [None])[0]


def _task_complete(task: TaskUnit) -> bool:
    return (
        task.locked
        if task.kind == "programming"
        else task.latest_valid_submission is not None
    )


def _task_has_independent_approval(task: TaskUnit) -> bool:
    if not task.versions:
        return False
    version = task.versions[-1]
    reviews = [
        review
        for review in task.reviews
        if not review.stale and review.version_hash == version.version_hash
    ]
    return not any(review.decision == "reject" for review in reviews) and any(
        review.decision == "approve" and review.reviewer != version.author
        for review in reviews
    )


def _contest_complete(session: ContestSession) -> bool:
    return all(_task_complete(task) for task in session.tasks)


def _clip(text: str, limit: int) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def _inspect_problem_payload(
    manifest_task: ManifestTask,
    task: TaskUnit,
    memory: ContestMemory,
    *,
    focus: str = "",
    version_hash: str | None = None,
    offset: int = 0,
    limit: int = DEFAULT_PAGE_CHARS,
) -> dict[str, Any]:
    """Read-only snapshot of one task for ``inspect_problem``."""
    sample_reports = _sample_reports(memory)
    local_reports = _local_run_reports(memory)
    # Validate even for an empty task; a bad read must not silently succeed.
    if type(offset) is not int or offset < 0:
        raise ValueError('offset must be a non-negative integer character position')
    text_page('', limit=limit)
    if offset and not version_hash:
        raise ValueError('version_hash is required for a nonzero offset')
    versions = task.versions
    if version_hash:
        versions = [v for v in versions if v.version_hash == version_hash]
        if not versions:
            raise ValueError('requested hash is not a visible version of this problem')
    rows = []
    for version in versions:
        if version_hash:
            page = text_page(version.content, offset, limit)
            content = page.pop('content')
        else:
            preview = draft_preview(version.content)
            content, page = preview['content'], preview['content_page']
        rows.append({
            'version_hash': version.version_hash, 'parent_hash': version.parent_hash,
            'author': version.author, 'evidence_refs': list(version.evidence_refs),
            'content': content, 'content_page': page,
            'sample_report': sample_reports.get(version.version_hash),
            'author_report': local_reports.get(version.version_hash),
        })
    return {
        "problem_id": task.task_id,
        "focus": focus,
        "statement": _clip(manifest_task.prompt, _INSPECT_STATEMENT_CHARS),
        "task_type": manifest_task.task_type,
        "programming": manifest_task.programming or manifest_task.task_type in {
            "algorithmic_programming", "programming"},
        "execution_judge": manifest_task.programming,
        "grading_policy": manifest_task.benchmark.get("evaluation", {}).get("grading_policy"),
        "submission_format": (
            "Complete C++ source as a shared text artifact, with correctness and complexity explanation; static source review, not official execution."
            if manifest_task.benchmark.get("evaluation", {}).get("grading_policy") == "source_review_llm_v1"
            else "Follow the task's submission instructions."),
        "max_score": manifest_task.max_score,
        "state": task.state.value,
        "priority": task.priority,
        "triage_reason": task.triage_reason,
        "locked": task.locked,
        "versions": rows,
        "requested_version": version_hash,
        "reading": "Use problem_id, version_hash, offset=content_page.next_offset and limit=2000 to read more. Offsets count characters; saved content is never clipped.",
        "reviews": [asdict(review) for review in task.reviews],
        "submissions": [asdict(submission) for submission in task.submissions],
        "independent_approval": _task_has_independent_approval(task),
        "note": (
            "Self-verification context only; this does not create or replace "
            "an independent review, and the team's active problem is unchanged."
        ),
    }


def _apply_card_rules(
    *,
    action: str,
    arguments: dict[str, Any],
    agent: str,
    session: ContestSession,
    memory: ContestMemory,
    policy: OpenTablePolicy,
    work_limit_checked: bool = False,
) -> dict[str, Any]:
    """Character limits, message budget and deliberation validity from the card.

    Raises ``ValueError`` (recorded as an action error, the turn is spent) when
    the card forbids the action; otherwise returns the possibly clipped
    arguments.
    """
    turn = session.budget.turns_used
    target_id = str(arguments.get("problem_id") or "")
    target = session.task(target_id) if target_id else session.active_task
    if action in {"execute_code", "submit_code"} and target is not None:
        if target.submissions and target.submissions[-1].verdict == "PENDING":
            raise ValueError("rule card: source is frozen while the verdict is pending")
    if action in WORKSTATION_ACTION_NAMES and policy.workstation_lease:
        holder = otc_runtime.workstation_holder(memory, "", current_turn=turn)
        if holder is not None and holder != agent:
            raise ValueError("rule card: the team workstation is held by " + holder)
    if not policy.may_submit(agent) and action in {"submit", "submit_code", "finish_contest"}:
        raise ValueError(f"rule card: {agent}'s role may not {action}")
    counted = policy.counted_message_actions()
    budget = (
        otc_runtime.communication_budget(memory, policy) if action in counted else None
    )
    field_name = _CARD_CLIPPED_FIELDS.get(action)
    if action == 'work' and work_limit_checked:
        field_name = None
    if field_name and field_name in arguments:
        text = str(arguments[field_name] or "")
        limit = policy.char_limit(action)
        if budget is not None and budget.max_message_chars:
            # The card's per-message cap is a clip, not a rejection: a long
            # proposal loses its tail instead of the whole turn.
            limit = min(limit, int(budget.max_message_chars))
        clipped, cut = clip_text(text, limit)
        if cut:
            if action == "work" and target is not None and target.kind != "programming":
                # A candidate is an atomic deliverable. Tail clipping can drop
                # its final line or expose an obsolete intermediate answer.
                raise ValueError(
                    f"work exceeds the {limit}-character limit; shorten the reasoning "
                    "and retain the complete Final answer: <value> line. "
                    "The existing answer was not changed."
                )
            memory.append(
                task_id=session.active_task.task_id if session.active_task else None,
                question_id=None,
                actor="Contest_Control",
                visibility="private",
                recipients=(agent,),
                kind="card_content_clipped",
                payload={
                    "action": action,
                    "original_chars": len(text),
                    "kept_chars": len(clipped),
                    "limit": limit,
                },
                turn=turn,
            )
            arguments = {**arguments, field_name: clipped}
    if budget is not None:
        payload_text = str(arguments.get("content") or arguments.get("reason") or "")
        rejection = budget.check(
            agent_name=agent, action_type=action, payload=payload_text, turn=turn
        )
        if rejection:
            raise ValueError(f"rule card communication budget: {rejection}")
    if action in DELIBERATION_ACTION_NAMES:
        ledger = otc_runtime.deliberation_ledger(memory)
        if action == "propose":
            text = str(arguments.get("content") or "")
        elif action == "decide":
            text = (
                f"{arguments.get('proposal_id')} | {arguments.get('outcome')} | "
                f"{arguments.get('reason')}"
            )
        else:
            text = f"{arguments.get('proposal_id')} | {arguments.get('content')}"
        outcome = ledger.record(
            agent_name=agent,
            action_type=action,
            payload=text,
            turn=turn,
            may_decide=policy.may_decide(agent),
        )
        if outcome.startswith("Deliberation error"):
            raise ValueError(outcome)
        if action == "propose":
            arguments = {**arguments, "proposal_id": f"P{len(ledger.proposals)}"}
    return arguments


def _apply_action(
    *,
    action: str,
    arguments: dict[str, Any],
    agent: str,
    manifest: ContestManifest,
    session: ContestSession,
    memory: ContestMemory,
    config: ContestRunConfig,
    strategic_policy: StrategicPolicy,
    task_action_executor: TaskActionExecutor,
    work_task_ids: set[str] | None = None,
    review_task_ids: set[str] | None = None,
    final_review_complete: bool = True,
    personal_assignments: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, int]:
    if not config.modules.allows(ACTION_REGISTRY[action].module):
        raise ValueError(f"module {ACTION_REGISTRY[action].module!r} is disabled")
    if not config.allows_action(ACTION_REGISTRY[action]):
        raise ValueError(f"action {action!r} is unavailable in this baseline")
    from contest_observation import require_current_action
    require_current_action(action, arguments, session, memory, config)
    if (config.submission_turn is not None and session.budget.turns_used < config.submission_turn
            and (action == "finish_contest"
                 or (action == "submit" and _is_answer_sheet_contest(manifest)))):
        raise ValueError("final submission must wait for the contest submission_turn")
    flow = session.competition_flow
    if flow is not None:
        flow.require_action(action, arguments, agent)
    if action in FLOW_ACTIONS:
        from tool_registry import competition_permissions, validate_action_payload
        if flow is None or action not in (competition_permissions(manifest.competition_id, rule_card=config.rule_card) or set()):
            raise ValueError("competition flow action is not enabled/permitted")
        errors = validate_action_payload(action, arguments)
        if errors:
            raise ValueError("; ".join(errors))
        previous = session.active_task.task_id if session.active_task else None
        result = flow.apply(action, arguments, agent)
        private = ACTION_REGISTRY[action].visibility == "private"
        event_visibility = "private" if private else "public"
        recipients = (agent,) if private else ()
        event_task = arguments.get("problem_id") or previous
        memory.append(task_id=event_task, question_id=None, actor=agent,
                      visibility=event_visibility, recipients=recipients, kind=action, payload=arguments,
                      turn=session.budget.turns_used)
        memory.append(task_id=event_task, question_id=None, actor="Contest_Control",
                      visibility=event_visibility, recipients=recipients, kind=f"{action}_result", payload=result,
                      turn=session.budget.turns_used)
        return result["phase"] == "complete", 0
    task_by_id = {task.task_id: task for task in manifest.tasks}
    active = session.active_task
    if action in PREPARATION_ACTIONS:
        from tool_registry import competition_permissions
        if action not in (competition_permissions(manifest.competition_id, rule_card=config.rule_card) or set()):
            raise ValueError("preparation tool is not permitted by this competition")
        if active is None or active.locked:
            raise ValueError("select an unlocked task before using a preparation tool")
    if (
        config.features.leader_submits
        and agent != config.leader
        and action in {"submit", "submit_code", "finish_contest"}
    ):
        raise ValueError(f"only {config.leader} may {action} in this baseline")
    visibility: Literal["public", "private"] = (
        "private" if ACTION_REGISTRY[action].visibility == "private" else "public"
    )
    recipients: tuple[str, ...] = ()
    contract = manifest.metadata.get("artifact_contract")
    if action in {"work", "render_pdf"} and contract and len(str(arguments.get("content", ""))) > contract["max_source_chars"]:
        raise ValueError("Oversized artifact source; revise it explicitly instead of silently clipping")
    work_target = str(arguments.get('problem_id') or (active.task_id if active else ''))
    if action == 'work' or (action == 'render_pdf' and contract):
        validate_work_content(manifest, work_target, arguments.get('content', ''))
    elif action == 'render_pdf':
        from answer_content import content_error
        error = content_error(arguments.get('content', ''))
        if error:
            raise ValueError(error)
    elif action == 'submit' and arguments.get('answer') is not None:
        validate_work_content(manifest, work_target, arguments['answer'])
    if action == "work" and not contract:
        target_id = str(arguments.get("problem_id") or (active.task_id if active else "")).strip()
        target = task_by_id.get(target_id)
        if target is not None and not target.programming:
            declared = conflicting_answer_task(str(arguments.get("content", "")), target_id)
            if declared is not None:
                # Validate before card clipping, focus changes, memory events,
                # or answer mutation. A refused write leaves the old draft intact.
                raise ValueError(
                    f"answer task mismatch: content declares {declared!r}, "
                    f"but work targets {target_id!r}; correct the problem_id or content"
                )
            if (active is not None and active.task_id != target_id
                    and not declared_answer_tasks(str(arguments.get('content', '')))):
                raise ValueError(
                    f"cross-task work needs explicit task binding: current task is "
                    f"{active.task_id if active else None!r}, target is {target_id!r}. "
                    "Start content with 'Problem <target id>:' (or include a matching "
                    "problem_id in JSON content), or select_problem first and read "
                    "that task before writing. No draft or task selection was changed."
                )
            if _is_answer_sheet_contest(manifest):
                versions = session.task(target_id).versions
                if versions:
                    previous = extract_final_answer(versions[-1].content, part_id=target_id)
                    incoming = extract_final_answer(str(arguments.get("content", "")), part_id=target_id)
                    if (previous.method not in {"unstructured", "missing"}
                            and previous.final_answer and incoming.method in {"unstructured", "missing"}):
                        raise ValueError(
                            "work would replace a formatted answer with an unstructured note. "
                            "Include a separate Final answer: <value> line for a revision; "
                            "use Final answer: withdrawn to retract the candidate, or speak "
                            "for a progress report. The existing answer was not changed."
                        )
    if config.otc_policy is not None:
        arguments = _apply_card_rules(
            action=action,
            arguments=arguments,
            agent=agent,
            session=session,
            memory=memory,
            policy=config.otc_policy,
            work_limit_checked=work_char_limit(manifest, work_target) is not None,
        )
    if action in COMPUTER_ACTIONS and config.computer_capacity is not None:
        resource_state = session_computer_state(
            memory, session.budget.turns_used, config.computer_capacity,
        )
        # Reject before recording an action: a refused call must not renew a lease.
        require_computer_slot(
            config.computer_capacity, resource_state["computers_used_this_turn"],
        )
    requested_work = str(arguments.get("problem_id") or "").strip()
    if action == "work" and requested_work:
        # Single-move switch: work(problem_id=...) is select_problem + work in
        # one turn; the seat's focus follows it on later turns because the
        # focus logic replays this select_problem event.
        if requested_work not in task_by_id:
            raise ValueError(f"unknown problem: {requested_work}")
        if work_task_ids is not None and requested_work not in work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {agent} to work on {requested_work}"
            )
        target = session.task(requested_work)
        if target.locked:
            raise ValueError(f"{requested_work} is locked")
        if active is None or active.task_id != requested_work:
            if active is not None:
                memory.create_problem_digest(active.task_id, viewer=agent)
            memory.append(
                task_id=requested_work,
                question_id=None,
                actor=agent,
                visibility="public",
                kind="select_problem",
                payload={"problem_id": requested_work, "via": "work"},
                turn=session.budget.turns_used,
            )
            session.select_task(requested_work)
            active = session.active_task
        arguments = {key: value for key, value in arguments.items() if key != "problem_id"}
    elif action == "work":
        arguments = {key: value for key, value in arguments.items() if key != "problem_id"}
    if action == "direct_message":
        raw_recipients = arguments["recipients"]
        if isinstance(raw_recipients, str):
            raw_recipients = [raw_recipients]
        teammates = {
            f"Agent_{index}" for index in range(1, config.team_size + 1)
        }
        ordered: list[str] = []
        for recipient in raw_recipients:
            recipient = str(recipient)
            if recipient not in teammates:
                raise ValueError(f"unknown direct-message recipient: {recipient}")
            if recipient == agent:
                raise ValueError("direct_message recipients must be teammates")
            if recipient not in ordered:
                ordered.append(recipient)
        if not ordered:
            raise ValueError("direct_message needs at least one recipient")
        recipients = tuple(ordered)
        arguments = {**arguments, "recipients": ordered}
    if action in DESK_ACTION_NAMES:
        # Desk actions target an explicit problem or fall back to the shared
        # cursor; they never move it.
        requested = str(arguments.get("problem_id") or "").strip()
        if requested and requested not in task_by_id:
            raise ValueError(f"unknown problem: {requested}")
        event_task_id = requested or (active.task_id if active else None)
    else:
        event_task_id = (
            str(arguments.get("problem_id"))
            if action in {"select_problem", "review_answer"}
            else active.task_id
            if active
            else None
        )
    session.current_turn_only = config.current_turn_only
    context = _ActionContext(
        action=action,
        arguments=arguments,
        agent=agent,
        manifest=manifest,
        session=session,
        memory=memory,
        config=config,
        strategic_policy=strategic_policy,
        task_action_executor=task_action_executor,
        work_task_ids=work_task_ids,
        review_task_ids=review_task_ids,
        final_review_complete=final_review_complete,
        personal_assignments=personal_assignments,
        task_by_id=task_by_id,
        active=active,
        event_task_id=event_task_id,
        visibility=visibility,
        recipients=recipients,
    )
    pre_event = _PRE_EVENT_HANDLERS.get(action)
    if pre_event is not None:
        return pre_event(context)
    if action == "assign_problem":
        _prepare_assign_problem(context)
    memory.append(
        task_id=context.event_task_id,
        question_id=None,
        actor=agent,
        visibility=visibility,
        # ``remember`` is the note itself; other desk actions log the request
        # and append their result as a private tool event.
        kind="note" if action == "remember" else action,
        payload=(
            {"content": str(context.arguments["content"]), "problem_id": context.event_task_id}
            if action == "remember"
            else context.arguments
        ),
        turn=session.budget.turns_used,
        recipients=recipients,
    )
    handler = SESSION_HANDLERS.get(action, _session_task_tool)
    return handler(context)


@dataclass
class _ActionContext:
    """Everything one session action handler may read or mutate."""

    action: str
    arguments: dict[str, Any]
    agent: str
    manifest: ContestManifest
    session: ContestSession
    memory: ContestMemory
    config: ContestRunConfig
    strategic_policy: StrategicPolicy
    task_action_executor: TaskActionExecutor
    work_task_ids: set[str] | None
    review_task_ids: set[str] | None
    final_review_complete: bool
    personal_assignments: dict[str, dict[str, Any]] | None
    task_by_id: dict[str, ManifestTask]
    active: TaskUnit | None
    event_task_id: str | None
    visibility: Literal["public", "private"]
    recipients: tuple[str, ...]

    @property
    def turn(self) -> int:
        return self.session.budget.turns_used

    def require_active(self, message: str) -> TaskUnit:
        if self.active is None:
            raise RuntimeError(message)
        return self.active

    def require_work_allowed(self, task_id: str, verb: str) -> None:
        if self.work_task_ids is not None and task_id not in self.work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {self.agent} to {verb} {task_id}"
            )


SessionHandler = Callable[[_ActionContext], tuple[bool, int]]


def _session_noop(_: _ActionContext) -> tuple[bool, int]:
    return False, 0


def _session_share_note(ctx: _ActionContext) -> tuple[bool, int]:
    # The request contains an id, so _apply_card_rules cannot clip its message.
    # Apply the same public-message caps to the resolved note at publication.
    policy = ctx.config.otc_policy
    limit = policy.char_limit("share_note") if policy is not None else None
    if policy is not None and "share_note" in policy.counted_message_actions():
        message_limit = int(policy.communication.get("max_message_chars") or 0)
        if message_limit:
            limit = min(limit, message_limit) if limit else message_limit
    return _share_note(
        memory=ctx.memory,
        session=ctx.session,
        agent=ctx.agent,
        note_id=str(ctx.arguments["note_id"]),
        max_chars=limit,
    )


def _prepare_assign_problem(ctx: _ActionContext) -> None:
    """Leader reassignment: validate and apply before the request event."""
    if ctx.agent != ctx.config.leader:
        raise ValueError("only the team leader may reassign problems")
    if ctx.personal_assignments is None:
        raise RuntimeError("assign_problem needs the live assignment table")
    target = str(ctx.arguments["agent"])
    if target == ctx.agent or target not in {
        f"Agent_{index}" for index in range(1, ctx.config.team_size + 1)
    }:
        raise ValueError(f"unknown teammate: {target}")
    raw_ids = ctx.arguments["problem_ids"]
    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]
    problem_ids: list[str] = []
    for raw in raw_ids:
        task_id = str(raw)
        if task_id not in ctx.task_by_id:
            raise ValueError(f"unknown problem: {task_id}")
        if task_id not in problem_ids:
            problem_ids.append(task_id)
    if not problem_ids:
        raise ValueError("assign_problem needs at least one problem")
    _set_work_assignment(ctx.personal_assignments, target, problem_ids)
    ctx.arguments = {**ctx.arguments, "agent": target, "problem_ids": problem_ids}
    ctx.event_task_id = None


def _session_recall(ctx: _ActionContext) -> tuple[bool, int]:
    recall_notes(
        ctx.memory, agent=ctx.agent,
        query=str(ctx.arguments.get("query") or ""),
        problem_id=str(ctx.arguments.get("problem_id") or "") or None,
        event_task_id=ctx.event_task_id, turn=ctx.turn,
    )
    return False, 0


def _session_inspect_problem(ctx: _ActionContext) -> tuple[bool, int]:
    from contest_observation import observe
    session, memory = observe(ctx.session, ctx.memory, ctx.config)
    if ctx.event_task_id is None:
        raise RuntimeError("pass problem_id or select a problem before inspect_problem")
    if ctx.event_task_id not in {t.task_id for t in session.visible_tasks}:
        raise ValueError('Problem is not visible in this contest phase.')
    ctx.memory.append(
        task_id=ctx.event_task_id,
        question_id=None,
        actor="Tool",
        visibility="private",
        recipients=(ctx.agent,),
        kind="inspect_problem_result",
        payload=_inspect_problem_payload(
            ctx.task_by_id[ctx.event_task_id],
            session.task(ctx.event_task_id),
            memory,
            focus=str(ctx.arguments.get("focus") or ""),
            version_hash=ctx.arguments.get('version_hash'),
            offset=ctx.arguments.get('offset', 0),
            limit=ctx.arguments.get('limit', DEFAULT_PAGE_CHARS),
        ),
        turn=ctx.turn,
    )
    return False, 0


def _session_read_problem_pdf(ctx: _ActionContext) -> tuple[bool, int]:
    from problem_pdf import read_problem_pdf, visible_benchmark, ProblemPdfError
    if ctx.event_task_id not in {t.task_id for t in ctx.session.visible_tasks}:
        raise ValueError("Problem is not visible in this contest phase.")
    task = ctx.task_by_id[ctx.event_task_id]
    try:
        payload, _ = read_problem_pdf(
            visible_benchmark(ctx.manifest, ctx.session, task), ctx.arguments.get("pages"),
            ctx.arguments.get("document", 1), render=False)
    except ProblemPdfError as exc:
        payload = {"status": "unavailable", "reason": str(exc)}
    ctx.memory.append(task_id=ctx.event_task_id, question_id=None, actor="Tool",
                      visibility="private", recipients=(ctx.agent,),
                      kind="read_problem_pdf_result", payload=payload, turn=ctx.turn)
    return False, 0


def _session_triage_problem(ctx: _ActionContext) -> tuple[bool, int]:
    assert ctx.event_task_id is not None
    priority = str(ctx.arguments["priority"])
    previous_visible = ctx.session.task(ctx.event_task_id).triaged_turn == ctx.turn
    task, previous = ctx.session.set_triage(
        ctx.event_task_id,
        priority,  # type: ignore[arg-type]
        reason=str(ctx.arguments.get("reason") or ""),
        actor=ctx.agent,
        turn=ctx.turn,
    )
    if ctx.config.current_turn_only and not previous_visible:
        previous = "normal"
    ctx.memory.append(
        task_id=ctx.event_task_id,
        question_id=None,
        actor=ctx.agent,
        visibility="public",
        kind="task_triaged",
        payload={
            "problem_id": ctx.event_task_id,
            "priority": priority,
            "previous_priority": previous,
            "reason": task.triage_reason,
        },
        turn=ctx.turn,
    )
    return False, 0


def _session_select_problem(ctx: _ActionContext) -> tuple[bool, int]:
    task_id = str(ctx.arguments["problem_id"])
    if task_id not in ctx.task_by_id:
        raise ValueError(f"unknown problem: {task_id}")
    ctx.require_work_allowed(task_id, "work on")
    switched = ctx.active is not None and ctx.active.task_id != task_id
    if switched:
        ctx.memory.create_problem_digest(ctx.active.task_id, viewer=ctx.agent)
    ctx.session.select_task(task_id)
    return False, int(switched)


def _session_speak(ctx: _ActionContext) -> tuple[bool, int]:
    active = ctx.active
    if (
        active is not None
        and active.versions
        and active.versions[-1].author == ctx.agent
        and active.versions[-1].evidence_refs
        and (not ctx.config.current_turn_only
             or ctx.session.version_created_this_turn(active.versions[-1].version_hash))
    ):
        ctx.memory.append(
            task_id=active.task_id,
            question_id=None,
            actor=ctx.agent,
            visibility="public",
            kind="local_run_report",
            payload={
                "version_hash": active.versions[-1].version_hash,
                "report": str(ctx.arguments["content"]),
            },
            turn=ctx.turn,
        )
    return False, 0


def _session_work(ctx: _ActionContext) -> tuple[bool, int]:
    active = ctx.require_active("select a problem before work")
    ctx.require_work_allowed(active.task_id, "work on")
    if active.locked:
        raise ValueError(f"task {active.task_id!r} is locked")
    if active.kind == "programming" and ctx.config.review_required:
        # The work event above retains the note in team memory. It must not
        # replace executable source or invalidate its exact-version review.
        return False, 0
    if ctx.config.review_required and _task_has_independent_approval(active):
        raise ValueError(
            "preserve the independently approved version unless a review rejects it"
        )
    content = str(ctx.arguments["content"])
    duplicate = active.find_duplicate_answer(content)
    if (duplicate is not None and ctx.config.current_turn_only
            and not ctx.session.version_created_this_turn(duplicate.version_hash)):
        duplicate = None
    if duplicate is not None:
        from contest_observation import observe
        visible_session, visible_memory = observe(ctx.session, ctx.memory, ctx.config)
        # Same draft already on the sheet: no new version, tell the author
        # where it is and what is still blank instead of failing silently.
        recorded_turn = next(
            (
                event.turn
                for event in visible_memory.view(ctx.agent, task_id=active.task_id)
                if event.kind == "work"
                and isinstance(event.payload, dict)
                and event.payload.get("content") == content
            ),
            None,
        )
        blank = [task.task_id for task in visible_session.visible_tasks if not task.versions]
        ctx.memory.append(
            task_id=active.task_id,
            question_id=None,
            actor="Contest_Control",
            visibility="private",
            recipients=(ctx.agent,),
            kind="work_duplicate",
            payload={
                "version_hash": duplicate.version_hash,
                "recorded_by": duplicate.author,
                "recorded_turn": recorded_turn,
                "is_latest": duplicate is active.versions[-1],
                "blank_task_ids": blank,
                "note": (
                    f"This draft is already recorded on {active.task_id}"
                    f" by {duplicate.author or 'a teammate'}"
                    + (f" at turn {recorded_turn}" if recorded_turn is not None else "")
                    + f"; {len(blank)} tasks still have no draft."
                ),
            },
            turn=ctx.turn,
        )
        return False, 0
    evidence_refs = ()
    if ctx.manifest.metadata.get("artifact_contract"):
        receipt = ctx.task_action_executor(ctx.task_by_id[active.task_id],
                                           "render_pdf", {"content": content})
        if not receipt.get("valid"):
            raise ValueError("Artifact rendering failed; candidate not eligible for review")
        event = ctx.memory.append(task_id=active.task_id, question_id=None,
            actor="Artifact_Renderer", visibility="public", kind="artifact_rendered",
            payload=receipt, turn=ctx.turn)
        evidence_refs = (event.event_id,)
    ctx.session.create_answer(content, author=ctx.agent, evidence_refs=evidence_refs)
    return False, 0


def _session_render_pdf(ctx: _ActionContext) -> tuple[bool, int]:
    if ctx.manifest.metadata.get("artifact_contract"):
        # One version/render/review path, shared with artifact work.
        return _session_work(ctx)
    return _session_task_tool(ctx)


def _session_request_review(ctx: _ActionContext) -> tuple[bool, int]:
    active = ctx.active
    if active is None or not active.versions:
        raise RuntimeError("create a candidate before review")
    ctx.require_work_allowed(active.task_id, "own")
    ctx.memory.append(
        task_id=active.task_id,
        question_id=None,
        actor=ctx.agent,
        visibility="public",
        kind="review_requested",
        payload={
            "version_hash": active.versions[-1].version_hash,
            "reviewer": ctx.arguments.get("reviewer"),
            "content": str(ctx.arguments["content"]),
        },
        turn=ctx.turn,
    )
    return False, 0


def _session_review_answer(ctx: _ActionContext) -> tuple[bool, int]:
    task_id = str(ctx.arguments["problem_id"])
    if task_id not in ctx.task_by_id:
        raise ValueError(f"unknown problem: {task_id}")
    if ctx.review_task_ids is not None and task_id not in ctx.review_task_ids:
        raise ValueError(
            f"coach assignment does not route {task_id} review to {ctx.agent}"
        )
    decision = str(ctx.arguments["decision"])
    if decision not in {"approve", "reject"}:
        raise ValueError("review decision must be approve or reject")
    # Without a hash the review binds to the version currently recorded.
    version_hash = str(ctx.arguments.get("version_hash") or "").strip() or None
    ctx.session.record_task_review(
        task_id,
        ctx.agent,
        str(ctx.arguments["content"]),
        decision=decision,  # type: ignore[arg-type]
        version_hash=version_hash,
    )
    return False, 0


def _session_check_budget(ctx: _ActionContext) -> tuple[bool, int]:
    from contest_observation import observe
    session, _ = observe(ctx.session, ctx.memory, ctx.config)
    ctx.memory.append(
        task_id=ctx.event_task_id,
        question_id=None,
        actor="Tool",
        visibility="private",
        recipients=(ctx.agent,),
        kind="budget_result",
        payload={
            **asdict(session.budget),
            **session_computer_state(ctx.memory, ctx.turn, ctx.config.computer_capacity),
            "blank_tasks": [task.task_id for task in session.tasks if not task.versions],
            "tasks": [
                {
                    "task_id": task.task_id,
                    "state": task.state.value,
                    "versions": len(task.versions),
                    "submissions": len(task.submissions),
                    "locked": task.locked,
                    "priority": task.priority,
                }
                for task in session.tasks
            ],
        },
        turn=ctx.turn,
    )
    return False, 0


def _session_query_rules(ctx: _ActionContext) -> tuple[bool, int]:
    config = ctx.config
    payload: dict[str, Any] = {
        "competition_id": ctx.manifest.competition_id,
        "rule_guidance": config.rule_guidance,
        "team_size": config.team_size,
        "baseline": asdict(config.features),
    }
    from rules.loader import load_rule_card
    card = config.rule_card or load_rule_card(ctx.manifest.competition_id)
    if card is not None:
        payload["competition_rules"] = {
            "rules_text": card.rules_text,
            "allowed_tools": list(card.allowed_tools),
            "resources": card.raw.get("resources") or {},
            "deliverable": card.deliverable,
        }
    if config.otc_policy is not None:
        policy = config.otc_policy
        payload["rule_card"] = {
            "allowed_actions": sorted(policy.allowed_actions),
            "structured_deliberation": policy.structured_deliberation,
            "memory_entries": asdict(policy.memory_entries),
        }
    ctx.memory.append(
        task_id=ctx.event_task_id,
        question_id=None,
        actor="Tool",
        visibility="private",
        recipients=(ctx.agent,),
        kind="rules_result",
        payload=payload,
        turn=ctx.turn,
    )
    return False, 0


def _session_submit(ctx: _ActionContext) -> tuple[bool, int]:
    session, config, manifest = ctx.session, ctx.config, ctx.manifest
    if _is_answer_sheet_contest(manifest):
        required_ids = _required_answer_sheet_task_ids(manifest)
        required_tasks = [
            task for task in session.tasks if task.task_id in required_ids
        ]
        missing = [task for task in required_tasks if not task.versions]
        if missing:
            raise ValueError(
                "cannot submit answer sheet while "
                f"{len(missing)} tasks lack drafts"
            )
        if config.review_required:
            unreviewed = [
                task
                for task in required_tasks
                if not _task_has_independent_approval(task)
            ]
            if unreviewed:
                raise ValueError(
                    "cannot submit answer sheet while "
                    f"{len(unreviewed)} drafts lack independent approval"
                )
        if config.final_review_required and not ctx.final_review_complete:
            raise ValueError(
                "cannot submit answer sheet before final review completes"
            )
        for task in required_tasks:
            session.select_task(task.task_id)
            session.submit("SUBMITTED", score=0.0, valid=True)
        return True, 0
    active = ctx.require_active("select a problem before submit")
    ctx.require_work_allowed(active.task_id, "submit")
    if active.kind == "programming":
        raise ValueError("programming tasks must use submit_code")
    answer = str(ctx.arguments["answer"])
    if config.review_required:
        # Reject before mutation: a failed hand-in must preserve the exact
        # reviewed draft and its approval, not silently create a new version.
        if not session.has_independent_approval():
            raise ValueError("strategic submission requires an independent approval")
        if active.versions[-1].content != answer:
            raise ValueError("submit cannot replace the independently approved answer")
    elif not active.versions or active.versions[-1].content != answer:
        session.create_answer(answer, author=ctx.agent)
    if ctx.manifest.competition_id in FLAG_CHECK_COMPETITIONS:
        return _check_flag_submission(ctx, active, answer)
    session.submit("SUBMITTED", score=0.0, valid=True)
    return _contest_complete(session), 0


# NYU CTF Bench's reference agent checks a flag immediately and keeps working
# after a wrong one. Cybench's harness ends on the first answer, so it is absent.
FLAG_CHECK_COMPETITIONS = frozenset({"nyu_ctf_bench"})


def _check_flag_submission(ctx: _ActionContext, active: TaskUnit, answer: str) -> tuple[bool, int]:
    from contest_adapters import _grade_non_programming
    score, _ = _grade_non_programming(ctx.task_by_id[active.task_id], answer, ctx.manifest.competition_id)
    correct = score > 0
    # A wrong flag is recorded as an invalid attempt, so the challenge stays open.
    ctx.session.submit("AC" if correct else "WRONG_FLAG", score=score, valid=correct)
    attempts = len(active.submissions)
    ctx.memory.append(task_id=active.task_id, question_id=None, actor="Contest_Control",
                      visibility="public", kind="flag_check_result",
                      payload={"correct": correct, "attempts": attempts}, turn=ctx.turn)
    return _contest_complete(ctx.session), 0


def _session_skip_problem(ctx: _ActionContext) -> tuple[bool, int]:
    active = ctx.require_active("no active problem to skip")
    ctx.require_work_allowed(active.task_id, "skip")
    previous_id = active.task_id
    ctx.memory.create_problem_digest(active.task_id, viewer=ctx.agent)
    ctx.session.skip_task()
    ctx.memory.append(
        task_id=previous_id,
        question_id=None,
        actor="Contest_Control",
        visibility="public",
        kind="problem_switched",
        payload={
            "from": previous_id,
            "to": None,
            "reason": str(ctx.arguments.get("reason") or "manual_skip"),
        },
        turn=ctx.turn,
    )
    return False, 1


def _session_finish_contest(ctx: _ActionContext) -> tuple[bool, int]:
    if _is_answer_sheet_contest(ctx.manifest):
        raise ValueError(
            "math answer-sheet contests end only through final submit"
        )
    unfinished = [
        task
        for task in ctx.session.tasks
        if not (
            task.locked
            if task.kind == "programming"
            else task.latest_valid_submission is not None
        )
    ]
    if unfinished:
        raise ValueError(
            "cannot finish contest while "
            f"{len(unfinished)} tasks lack valid submissions"
        )
    if ctx.config.final_review_required and not ctx.final_review_complete:
        raise ValueError(
            "cannot finish contest before every task receives final approval"
        )
    return True, 0


def _session_task_tool(ctx: _ActionContext) -> tuple[bool, int]:
    """Task-pack tools (execute_code, submit_code, calculator, search, fixtures)."""
    action, agent, session, memory, config = (
        ctx.action, ctx.agent, ctx.session, ctx.memory, ctx.config
    )
    active = ctx.require_active("select a problem before using task tools")
    ctx.require_work_allowed(active.task_id, "use task tools on")
    arguments = ctx.arguments
    task_by_id = ctx.task_by_id

    if action == "submit_code":
        if config.review_required:
            if not active.versions:
                raise ValueError("strategic code submission requires a candidate")
            code = active.versions[-1].content
            arguments = {**arguments, "code": code}
            if not active.versions[-1].evidence_refs:
                raise ValueError(
                    "strategic code submission requires local run/test evidence"
                )
            if not (session.has_independent_approval() if config.otc_policy is not None
                    else session.has_independent_review()):
                raise ValueError(
                    "strategic code submission requires an independent review"
                )
        elif config.features.leader_submits:
            if agent != config.leader:
                raise ValueError(f"only {config.leader} may submit code")
            if "code" in arguments:
                raise ValueError("the leader submits the latest recorded version; do not paste source")
            if not active.versions:
                raise ValueError("no recorded source version to submit")
            code = active.versions[-1].content
            arguments = {**arguments, "code": code}
        else:
            code = str(arguments["code"])
            if not active.versions or active.versions[-1].content != code:
                session.create_answer(code, author=agent)

    if (action == "execute_code" and active.kind == "programming"
            and config.review_required
            and not str(arguments.get("code") or "").strip()):
        raise ValueError("execute_code requires nonempty candidate source, not an empty placeholder")
    execution_cache_key = None
    if (action == "execute_code" and active.kind == "programming"
            and config.review_required):
        execution_cache_key = execution_key(task_by_id[active.task_id], arguments, ctx.task_action_executor)
        from contest_observation import observe
        _, cache_memory = observe(session, memory, config)
        reused = failed_execution(cache_memory.archival_snapshot()["events"], active.task_id, execution_cache_key)
        if reused is not None:
            memory.append(task_id=active.task_id, question_id=None, actor="Tool",
                          visibility="private", recipients=(agent,), kind="execute_code_result",
                          payload=reused, turn=session.budget.turns_used)
            return False, 0  # No executor call, source overwrite, or new evidence.
    if action in COMPUTER_ACTIONS and config.computer_capacity is not None:
        # Cached failures above use no computer slot. Actual execution attempts
        # consume one even when the sandbox reports an execution failure.
        memory.append(
            task_id=active.task_id, question_id=None, actor=agent,
            visibility="public", kind=COMPUTER_USE_EVENT,
            payload={"action": action, "capacity": config.computer_capacity},
            turn=session.budget.turns_used,
        )
    if action in PREPARATION_ACTIONS:
        result = execute_preparation_tool(action, arguments, public_context(
            ctx.manifest.competition_id, active.task_id,
            expected_ids=[task.task_id for task in ctx.session.visible_tasks],
            metadata=ctx.manifest.metadata,
            task_metadata=task_by_id[active.task_id].benchmark,
        ))
    else:
        result = ctx.task_action_executor(task_by_id[active.task_id], action, arguments)
    if action == "submit_code" and config.otc_policy is not None and config.otc_policy.run_judging_latency_turns:
        from contest_judging import queue_verdict
        queue_verdict(session, memory, active, result,
                      config.otc_policy.run_judging_latency_turns,
                      task_by_id[active.task_id].benchmark.get("wrong_submission_penalty_minutes", 20))
        return False, 0
    evidence_event = memory.append(
        task_id=active.task_id,
        question_id=None,
        actor="Tool",
        visibility="public" if action == "submit_code" else "private",
        recipients=(agent,) if action != "submit_code" else (),
        kind=f"{action}_result",
        payload=result,
        turn=session.budget.turns_used,
    )
    if action != "submit_code":
        if action == "execute_code" and active.kind == "programming":
            code = str(arguments["code"])
            latest = active.versions[-1] if active.versions else None
            if (latest is not None and config.current_turn_only
                    and not session.version_created_this_turn(latest.version_hash)):
                latest = None
            # A local run only counts as evidence when the official samples pass
            # (or the task ships no samples and the run itself succeeded).
            sample_verdict = result.get("sample_verdict")
            counts_as_evidence = bool(result.get("valid", True)) and (
                sample_verdict is None or str(sample_verdict).upper() == "AC"
            )
            new_refs = (evidence_event.event_id,) if counts_as_evidence else ()
            if latest is None or latest.content != code:
                version = session.create_answer(
                    code,
                    author=agent,
                    evidence_refs=new_refs,
                )
            else:
                version = session.create_answer(
                    code,
                    author=latest.author or agent,
                    method_summary=latest.method_summary,
                    evidence_refs=(*latest.evidence_refs, *new_refs),
                )
            memory.append(
                task_id=active.task_id, question_id=None, actor="Tool",
                visibility="private", recipients=(agent,),
                kind="programming_source_recorded",
                payload={"version_hash": version.version_hash},
                turn=session.budget.turns_used,
            )
            if "sample_verdict" in result:
                memory.append(
                    task_id=active.task_id,
                    question_id=None,
                    actor="Judge",
                    visibility="public",
                    kind="sample_judge_result",
                    payload={
                        "version_hash": version.version_hash,
                        "author": version.author,
                        "sample_verdict": sample_verdict,
                        "sample_summary": result.get("sample_summary"),
                        "sample_cases": result.get("sample_cases") or [],
                        "evidence": counts_as_evidence,
                        "execution_key": execution_cache_key,
                        "execution_valid": bool(result.get("valid", True)),
                    },
                    turn=session.budget.turns_used,
                )
        return False, 0
    verdict = str(result.get("verdict") or "SUBMIT_FAILED")
    valid = bool(result.get("valid", True))
    session.submit(verdict, valid=valid)
    if valid and verdict.upper() != "AC":
        memory.append(
            task_id=active.task_id,
            question_id=None,
            actor="Judge",
            visibility="public",
            kind="reopen",
            payload={
                "verdict": verdict,
                "version_hash": active.versions[-1].version_hash,
            },
            turn=session.budget.turns_used,
        )
    if valid and verdict.upper() not in {"AC", "SUBMIT_FAILED", "PENDING"}:
        penalty = float(
            task_by_id[active.task_id]
            .benchmark.get("wrong_submission_penalty_minutes", 20)
        )
        session.add_penalty(penalty)
    if active.state is TaskState.BLOCKED:
        previous_id = active.task_id
        memory.create_problem_digest(active.task_id, viewer=agent)
        session.skip_task()
        next_task = _next_task(session, ctx.strategic_policy)
        if next_task is not None:
            session.select_task(next_task.task_id)
        memory.append(
            task_id=previous_id,
            question_id=None,
            actor="Contest_Control",
            visibility="public",
            kind="problem_switched",
            payload={
                "from": previous_id,
                "to": next_task.task_id if next_task else None,
                "reason": "three_consecutive_non_ac",
            },
            turn=session.budget.turns_used,
        )
        return False, 1
    return _contest_complete(session), 0


# Handlers that answer before the request event is appended to team memory.
_PRE_EVENT_HANDLERS: dict[str, SessionHandler] = {
    "share_note": _session_share_note,
}

# Canonical action name -> session handler. Task-pack tools (execute_code,
# submit_code, use_calculator, web_search, read_*) fall through to
# ``_session_task_tool``; anything else here is a desk or contest verb.
SESSION_HANDLERS: dict[str, SessionHandler] = {
    "remember": _session_noop,
    "assign_problem": _session_noop,
    "direct_message": _session_noop,
    "rest": _session_noop,
    # Validated against the replayed ledger in _apply_card_rules; the public
    # request event is the ledger entry itself.
    **{name: _session_noop for name in DELIBERATION_ACTION_NAMES},
    "recall": _session_recall,
    "inspect_problem": _session_inspect_problem,
    "read_problem_pdf": _session_read_problem_pdf,
    "triage_problem": _session_triage_problem,
    "select_problem": _session_select_problem,
    "speak": _session_speak,
    "work": _session_work,
    "render_pdf": _session_render_pdf,
    "request_review": _session_request_review,
    "review_answer": _session_review_answer,
    "check_budget": _session_check_budget,
    "query_rules": _session_query_rules,
    "submit": _session_submit,
    "skip_problem": _session_skip_problem,
    "finish_contest": _session_finish_contest,
}
