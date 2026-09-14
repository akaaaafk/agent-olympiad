"""Optional memory tools, visibility-safe recall and prompt augmentation."""
from __future__ import annotations
from functools import partial
import json
from .contracts import ActionSpec, ArgumentSpec, make_action, _TEXT, _OPTIONAL_PROBLEM_ID

MAX_SIDE_CALLS_PER_TURN = 3
_action = partial(make_action, module="memory", turns=0)


def is_auxiliary_action(spec: ActionSpec) -> bool:
    return spec.module == "memory" and spec.budget.turns == 0


def turn_guidance(used: int) -> str:
    remaining = max(0, MAX_SIDE_CALLS_PER_TURN - used)
    return (
        "MEMORY ACTION BUDGET: remember, recall and share_note are auxiliary "
        "calls, not your ordinary contest action. They do not advance the turn "
        "or simulated clock, but every request still costs API calls and tokens. "
        f"You have {remaining} memory calls left in this seat turn. "
        "Call exactly one function per response. After a memory result, continue "
        "in this same turn with another available memory call or your one "
        "ordinary action. When no memory calls remain, take an ordinary action."
    )

SPECS = (
    _action(
        "remember",
        (
"Zero-turn auxiliary: store a private note outside the visible transcript. "
            "Before switching tasks or handing off, preserve a useful intermediate "
            "result, failed approach, uncertainty, or next step with problem_id. "
            "Start a useful note even when the store is empty. Use work for "
            "candidate answers; do not duplicate a fully visible draft."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        visibility="private",
        # Text form: ``[<problem_id> |] <note>``; the optional tag comes first.
        text_payload=("problem_id", "content"),
    ),
    _action(
        "recall",
        (
"Zero-turn auxiliary: search your own notes and team-shared notes when "
            "needed prior information is missing from context. "
            "Nonempty query requires a whole-keyword match; omit query only to browse. "
            "An explicit problem_id restricts results to that task; omit it for "
            "cross-task methods. Results rank by keyword hits and recency."
        ),
        (
            ArgumentSpec(
                "query",
                description="Keywords for the missing prior result, failure or method; empty means browse.",
                required=False,
            ),
            ArgumentSpec(
                "problem_id",
                description="Optional exact problem id to filter; omit to search across tasks.",
                required=False,
            ),
        ),
        visibility="private",
        text_payload=("problem_id", "query"),
    ),
    _action(
        "share_note",
("Zero-turn auxiliary: publish one of your stored notes to the team when "
         "its finding, pitfall, or next step is useful and not already public. "
         "Use your actual note_id returned by remember or recall."),
        (
            ArgumentSpec(
                "note_id",
                description="Id of one of your private notes returned by remember or recall.",
            ),
        ),
        visibility="team",
    ),
)

# Runtime memory assistance is opt-in; the event ledger itself is always on.
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from contest_memory import ContestMemory
    from contest_session import ContestSession


def share_note(
    *,
    memory: ContestMemory,
    session: ContestSession,
    agent: str,
    note_id: str,
    max_chars: int | None = None,
) -> tuple[bool, int]:
    """Publish one of the agent's private notes as a public ``note_shared`` event."""
    source = next(
        (
            event
            for event in memory.view(agent)
            if event.event_id == note_id
            and event.kind == "note"
            and event.actor == agent
        ),
        None,
    )
    if source is None:
        raise ValueError(
            f"{note_id} is not one of your notes; use recall to list note ids"
        )
    already = any(
        event.kind == "note_shared"
        and isinstance(event.payload, dict)
        and event.payload.get("source_event_id") == note_id
        for event in memory.view(agent)
    )
    if already:
        raise ValueError(f"{note_id} has already been shared with the team")
    payload = source.payload if isinstance(source.payload, dict) else {}
    from rulecard_policy import clip_text
    original = str(payload.get("content") or "")
    content, cut = clip_text(original, max_chars)
    if cut:
        memory.append(
            task_id=source.task_id, question_id=None, actor="Contest_Control",
            visibility="private", recipients=(agent,), kind="card_content_clipped",
            payload={"action": "share_note", "original_chars": len(original),
                     "kept_chars": len(content), "limit": max_chars},
            turn=session.budget.turns_used,
        )
    memory.append(
        task_id=source.task_id,
        question_id=None,
        actor=agent,
        visibility="public",
        kind="note_shared",
        payload={
            "content": content,
            "problem_id": source.task_id,
            "author": agent,
            "source_event_id": note_id,
        },
        turn=session.budget.turns_used,
    )
    return False, 0


def recall_notes(
    memory: ContestMemory, *, agent: str, query: str, problem_id: str | None,
    event_task_id: str | None, turn: int,
) -> None:
    notes = memory.recall(agent, query=query, problem_id=problem_id)
    memory.append(
        task_id=event_task_id, question_id=None, actor="Tool",
        visibility="private", recipients=(agent,), kind="recall_result",
        payload={
            "query": query, "problem_id": problem_id, "notes": notes,
            "retrieval_policy": "visible_notes_scoped_keyword_match_v3",
            "note": "Empty means no visible matching note. Do not repeat the same query "
                    "unless notes changed; revise the query or continue solving.",
        }, turn=turn,
    )


_MEMORY_ONLY_EVENTS = frozenset({
    "note", "note_shared", "remember", "recall", "recall_result",
    "think", "procedural_lesson", "problem_digest", "memory_auxiliary_call",
    "automatic_memory",
})


def decision_guidance() -> str:
    return (
        "AUTOMATIC CONVERSATION MEMORY: The runtime saves visible dialogue, your "
        "private thinking and candidate claims by task, then supplies relevant "
        "automatic_memory before every decision. This works without remember or "
        "recall. Consolidate findings in the memory_update block of your existing "
        "think; if that block is absent, source-linked excerpts are still saved. "
        "Current-task findings, team_progress and recent_action_errors are separate. "
        "Correct prior failed calls; do not use another task's result as this task's answer. "
        "Old dialogue and agent summaries are unverified context; the live draft "
        "and review state remain authoritative. The following tools are optional "
        "supplements for curated notes and explicit sharing.\n"
        "MEMORY DECISION: Before choosing your ordinary action, check whether useful "
        "information should be saved, retrieved, or shared. These are contest-local "
        "scratchpad tools, not external assistance.\n"
        "MEMORY WRITE: When private reasoning yields a reusable intermediate result, "
        "a failed approach, a corrected assumption, or an unresolved next step that "
        "will matter after a task switch or handoff, call remember before your ordinary "
        "action. An empty note store is a reason to start a useful note, not to wait "
        "for recall. Tag problem_id and keep a compact finding, evidence or failed "
        "check, uncertainty, and next step. Do not copy every thought or duplicate "
        "a fully visible draft. A saved note is not a verified answer or submission.\n"
        "MEMORY READ: Use recall when a prior result, failed attempt, constraint or "
        "handoff is missing from the supplied context and recall_status reports "
        "visible notes that may contain it. Revisiting a task or repeating a failure "
        "is a reason to check, not an automatic recall. Do not recall when the needed "
        "information is already shown or the note store is empty. Write focused "
        "query keywords and use problem_id to restrict results to the relevant task. "
        "Omit problem_id only when seeking a method across tasks. Avoid "
        "repeating the last query when notes_changed_since_last_recall is false; "
        "an empty result means rephrase for a different fact or continue solving. "
        "recall reads only saved/shared notes, not all event history; inspect_problem "
        "reads candidate and submission history.\n"
        "MEMORY SHARE: After remember returns a note_id, use share_note if that "
        "finding, pitfall, or next step is useful to teammates and not already public. "
        "Use an actual id of your own note; never invent ids. Private notes and "
        "private thoughts are not teammate handoffs until explicitly shared. Memory "
        "does not replace work, independent review, or required discussion.\n"
        "MEMORY CONTROL: These are zero-turn auxiliary calls. They do not use your "
        "ordinary action or advance the simulated clock; API and token charges still "
        f"apply. At most {MAX_SIDE_CALLS_PER_TURN} memory calls are allowed per seat turn. "
        "Call one function per response. After its receipt, reassess the next tool "
        "instead of repeating an already completed save, and continue to your ordinary "
        "action in the same turn. No call quota: skip memory when there is nothing "
        "useful to preserve, retrieve, or share."
    )


def agent_context(
    memory: ContestMemory, *, viewer: str, enabled: bool,
    current_task_id: str | None, entries: Any = None, session: ContestSession | None = None,
) -> Any:
    """Return optional memory projection or ordinary visible conversation.

    A disabled module must not leak stored notes, retrieval results, historical
    private thoughts or digests, including after restoration from a checkpoint.
    The caller passes contest_observation.observe for the strict OTC control;
    its drafts and conversation are restricted to the current team round.
    Other plain baseline views and backend audit persistence are unchanged.
    """
    if enabled and current_task_id is not None:
        limits = {}
        if entries is not None:
            limits = {
                "max_current_events": entries.shared_work,
                "max_direct_messages": entries.group_messages,
                "max_team_messages": entries.public_messages,
                "max_chars": max(6000, 300 * (entries.shared_work + entries.public_messages)),
            }
        else:
            limits = {"max_chars": 6000}
        status = memory.recall_status(viewer, current_task_id=current_task_id)
        from automatic_memory import context as automatic_context
        automatic = automatic_context(memory, viewer=viewer, current_task_id=current_task_id,
                                      max_chars=min(3800, limits['max_chars'] // 2), session=session)
        allowance = len(json.dumps({'recall_status': status, 'automatic_memory': automatic},
                                   ensure_ascii=False)) + 32
        limits['max_chars'] = max(256, limits['max_chars'] - allowance)
        projection = memory.strategic_projection(
            viewer=viewer, current_task_id=current_task_id, **limits
        )
        projection['recall_status'] = status
        projection['automatic_memory'] = automatic
        return projection
    visible = memory.view(viewer)
    if not enabled:
        visible = [event for event in visible if event.kind not in _MEMORY_ONLY_EVENTS]
    return [
        {"turn": event.turn, "actor": event.actor,
         "kind": event.kind, "payload": event.payload}
        for event in visible[-12:]
    ]


def private_think_context(
    memory: ContestMemory, agent: str, *, enabled: bool,
    current_turn: int, limit: int, include_current: bool = True,
) -> list[dict[str, Any]]:
    """Transport this turn's thought; historical reasoning lives in automatic memory."""
    if not include_current:
        return []
    rows = [
        {"turn": event.turn, "task_id": event.task_id,
         "content": (event.payload or {}).get("content", "")}
        for event in memory.view(agent)
        if event.kind == "think" and event.actor == agent
        and event.turn == current_turn
    ]
    return rows[-limit:] if limit > 0 else []
