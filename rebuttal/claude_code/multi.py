"""Setting 2: N Claude Code agents with a plain multi-agent setup (no OTC).

N independent, persistent Claude Code instances (N = the OTC roster, 3 by
default) work the same packet in round-robin rounds. What they share:

* a team message board (each turn's ``message`` is posted to everyone);
* one shared answer sheet (any agent may set an answer; last write wins);
* a shared ``team/`` directory that every agent can read/write with its file
  tools, in addition to its private workspace.

There is no Coach, no rule card, no review gate, no memory module, no
private messages and no leader: the shared sheet at the end is submitted.
Restrictions and per-invocation limits are identical to setting 1.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import policy
from .cc_client import ClaudeCodeAgent

SYSTEM = (
    "You are {agent}, one of {n} contestants on a team in a timed competition run as a benchmark. "
    "Your teammates are separate agents; you can only reach them through the team message board "
    "(your structured `message`) and the shared directory {team_dir}. There is no internet. Your "
    "own working directory is private scratch paper. Work only from the problems given in the "
    "prompt; do not look for answer keys or other files."
)


def _turn_prompt(agent, manifest, rules, fmt, n, round_no, rounds, board, seen, sheet, first):
    head = ""
    if first:
        head = (f"OFFICIAL COMPETITION RULES\n{rules}\n\nBENCHMARK ADAPTATION: multi-agent, {n} contestants "
                f"({', '.join(f'Agent_{i}' for i in range(1, n + 1))}), {rounds} rounds, agents act in order "
                f"each round. Deliverable format: {fmt}\n\nPROBLEMS\n{policy.task_sheet(manifest)}\n")
    new = board[seen:]
    msgs = "\n".join(f"[round {m['round']}] {m['agent']}: {m['message']}" for m in new) or "(no new messages)"
    sheet_view = {k: f"{v['answer']}  (set by {v['by']})" for k, v in sheet.items()}
    return (
        f"{head}\nROUND {round_no} of {rounds}, your turn ({agent}).\nNEW TEAM MESSAGES\n{msgs}\n"
        f"SHARED ANSWER SHEET\n{sheet_view or '{}'}\n"
        "Work on whatever helps the team most. Finish your turn with the structured output: "
        "`message` to the team (coordinate, share results, flag disagreements), `answers` for tasks "
        "whose shared answer you want to set or change (omit tasks you leave as they are), and "
        "`done` true only if you think the team should hand in now. The shared sheet when rounds run "
        "out (or when every agent says done in the same round) is submitted."
    )


def run_multi(manifest, *, workspace_root: Path, model: str, rounds: int, team_size: int = 3,
              max_inner_turns: int = 8, max_output_tokens: int | None = None,
              rules_root: Path | None = None, runner=None) -> dict[str, Any]:
    cid = manifest.competition_id
    task_ids = [t.task_id for t in manifest.tasks]
    team_dir = (workspace_root / "team").resolve()
    team_dir.mkdir(parents=True, exist_ok=True)
    tools = policy.claude_code_tools(cid, rules_root)
    agents = [
        ClaudeCodeAgent(name=f"Agent_{i}", workspace=workspace_root / f"Agent_{i}", model=model, tools=tools,
                        shared_dirs=(team_dir,), denied_paths=policy.denied_paths(),
                        max_inner_turns=max_inner_turns, max_output_tokens=max_output_tokens, runner=runner)
        for i in range(1, team_size + 1)
    ]
    rules, fmt = policy.public_rules_text(cid, rules_root), policy.deliverable_format(cid, rules_root)
    schema = policy.answers_schema(task_ids, with_message=True)
    board: list[dict[str, Any]] = []
    seen = {a.name: 0 for a in agents}
    sheet: dict[str, dict[str, str]] = {}
    log = []
    rounds_used = 0
    for round_no in range(1, rounds + 1):
        rounds_used = round_no
        done_votes = 0
        for agent in agents:
            prompt = _turn_prompt(agent.name, manifest, rules, fmt, team_size, round_no, rounds,
                                  board, seen[agent.name], sheet, first=agent.session_id is None)
            seen[agent.name] = len(board)
            res = agent.run(prompt, json_schema=schema, purpose="multi_turn",
                            append_system_prompt=SYSTEM.format(agent=agent.name, n=team_size, team_dir=team_dir))
            out = res.structured if isinstance(res.structured, dict) else {}
            for tid, ans in (out.get("answers") or {}).items():
                if tid in task_ids and str(ans).strip():
                    sheet[tid] = {"answer": str(ans), "by": agent.name}
            if str(out.get("message") or "").strip():
                board.append({"round": round_no, "agent": agent.name, "message": str(out["message"])})
            done_votes += bool(out.get("done"))
            log.append({"round": round_no, "agent": agent.name, "done": bool(out.get("done")),
                        "is_error": res.is_error, "answers_set": sorted((out.get("answers") or {}).keys())})
        if done_votes == len(agents):
            break
    totals: dict[str, float] = {}
    for agent in agents:
        for k, v in agent.totals().items():
            totals[k] = round(totals.get(k, 0) + v, 6)
    return {"setting": "multi", "agents": [a.name for a in agents], "team_size": team_size,
            "submissions": {t: (sheet.get(t) or {}).get("answer", "") for t in task_ids},
            "answer_authors": {t: v["by"] for t, v in sheet.items()},
            "rounds_used": rounds_used, "board": board, "turn_log": log,
            "calls": [c for a in agents for c in a.calls], "usage": totals, "tools": list(tools)}
