"""Stable, human-readable communication views for contest memory events."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Iterable


COMMUNICATION_KINDS = frozenset({
    "speak",
    "direct_message",
    "share_note",
    "request_review",
    "review_answer",
    "propose",
    "challenge",
    "provide_evidence",
    "decide",
})


def _event_text(event: dict[str, Any]) -> str:
    payload = event.get("payload") or {}
    if not isinstance(payload, dict):
        return str(payload).strip()
    for key in ("content", "message", "report", "reason", "note"):
        value = payload.get(key)
        if value not in (None, ""):
            if event.get("kind") == "decide" and payload.get("outcome"):
                return f"{payload['outcome']} | {value}".strip()
            return str(value).strip()
    if event.get("kind") == "decide" and payload.get("outcome"):
        return str(payload["outcome"]).strip()
    return ""


def communication_history(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project visible and directed agent communication from archival events.

    The compatibility keys ``sender`` and ``message`` remain present for older
    transcript consumers. Extra provenance keeps structured OTC actions intact.
    Private thoughts and automatic-memory summaries are deliberately excluded.
    """
    rows: list[dict[str, Any]] = []
    for event in events:
        kind = str(event.get("kind") or "")
        if kind not in COMMUNICATION_KINDS:
            continue
        actor = str(event.get("actor") or "")
        if not actor.startswith("Agent_"):
            continue
        text = _event_text(event)
        if not text:
            continue
        payload = event.get("payload") or {}
        recipients = event.get("recipients") or (
            payload.get("recipients") if isinstance(payload, dict) else None
        ) or []
        rows.append({
            "event_id": event.get("event_id"),
            "turn": event.get("turn"),
            "sender": actor,
            "message": text,
            "action": kind,
            "visibility": event.get("visibility") or (
                "direct" if kind == "direct_message" else "team"
            ),
            "recipients": list(recipients),
            "task_id": event.get("task_id"),
        })
    return rows


def communication_sidecar(payload: dict[str, Any], *, source: str = "contest_session.json") -> dict[str, Any]:
    events = ((payload.get("memory") or {}).get("events") or [])
    # Keep the runtime's filtered communication view separate from this full archive.
    chat = []
    for event in events:
        body = event.get("payload")
        text = _event_text(event)
        if isinstance(body, dict):
            text = body.get("raw_content") or body.get("guidance") or text
        chat.append({
            **event,
            "sender": event.get("actor"),
            "action": event.get("kind"),
            "message": text or json.dumps(body, ensure_ascii=False, indent=2),
        })
    if not events:
        chat = list(payload.get("chat_history") or [])
    observed = {row["turn"] for row in chat if isinstance(row.get("turn"), int)}
    last_turn = max(observed | {int((payload.get("budget") or {}).get("turns_used") or 0)})
    turns = []
    for turn in sorted(set(range(1, last_turn + 1)) | observed):
        indices = [i for i, row in enumerate(chat) if row.get("turn") == turn]
        agents = {}
        for i in indices:
            row = chat[i]
            actor = row.get("sender") or "unknown"
            entry = agents.setdefault(actor, {"actions": Counter(), "task_ids": []})
            entry["actions"][row.get("action") or "unknown"] += 1
            task = row.get("task_id")
            if task and task not in entry["task_ids"]:
                entry["task_ids"].append(task)
        turns.append({"turn": turn, "event_count": len(indices),
                      "chat_history_indices": indices, "actors": agents,
                      "status": "recorded" if indices else "no_archived_events"})
    return {
        "schema_version": "agent-olympiad.contest-chat/v2",
        "source": source,
        "session_id": payload.get("session_id"),
        "competition_id": payload.get("competition_id"),
        "system_variant": payload.get("system_variant"),
        "precontest_coach_guidance": payload.get("precontest_coach_guidance") or "",
        "chat_history": list(chat),
        "turns": turns,
        "action_transport_log": payload.get("action_transport_log") or [],
        "event_count": len(chat),
        "source_event_count": len(events),
        "note": "Full archived public/private events, including think, work, tools and automatic memory. Original visibility and payload are preserved; missing source content is not reconstructed.",
    }


def communication_markdown(payload: dict[str, Any]) -> str:
    rows = payload.get("chat_history") or []
    title = payload.get("session_id") or "Contest session"
    variant = payload.get("system_variant") or "unknown"
    lines = [f"# Contest transcript: {title}", "", f"Variant: `{variant}`", ""]
    coach = payload.get("precontest_coach_guidance")
    if coach and not any(row.get("action") == "precontest_coach_guidance" for row in rows):
        lines.extend(["## Turn 0 - Coach", "",
                      "Action: `precontest_coach_guidance`", "", str(coach), ""])
    if not rows:
        lines.extend([
            "No agent communication events were recorded.",
            "",
            "The run may still contain private `think`, shared `work`, or automatic-memory events.",
        ])
        return "\n".join(lines) + "\n"
    if "turns" in payload:
        groups = [(item["turn"], [rows[i] for i in item["chat_history_indices"]])
                  for item in payload["turns"]]
        unassigned = [row for row in rows if not isinstance(row.get("turn"), int)]
        if unassigned:
            groups.append(("unknown", unassigned))
        for turn, entries in groups:
            lines.extend([f"## Turn {turn}", ""])
            if not entries:
                lines.extend(["No events were archived for this turn.", ""])
            for row in entries:
                lines.extend([f"### {row.get('sender')} - {row.get('action')}", "",
                              f"Visibility: `{row.get('visibility', 'unknown')}`  ",
                              f"Task: `{row.get('task_id')}`  ",
                              f"Recipients: {', '.join(map(str, row.get('recipients') or []))}",
                              "", str(row.get("message") or ""), ""])
        return "\n".join(lines)
    for row in rows:
        recipients = row.get("recipients") or []
        target = f" -> {', '.join(map(str, recipients))}" if recipients else ""
        lines.extend([
            f"## Turn {row.get('turn')} - {row.get('sender')}{target}",
            "",
            f"Action: `{row.get('action')}`  ",
            f"Visibility: `{row.get('visibility')}`",
            "",
            str(row.get("message") or ""),
            "",
        ])
    return "\n".join(lines)
