"""Setting 1: one Claude Code agent, its own harness, current run restrictions.

One persistent Claude Code session works the whole contest packet. Each
contest round is one ``claude -p`` invocation (resuming the same session), so
the number of rounds matches the engine's turn budget for the competition.
Inside a round Claude Code may use its own tool loop (file tools as scratch
paper, Bash only if the contest allows code/calculator), capped by
``max_inner_turns``. There are no teammates and no subagents.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import policy
from .cc_client import ClaudeCodeAgent

SYSTEM = (
    "You are the only contestant in a timed team competition run as a benchmark. "
    "You have no teammates, no internet, and no tools beyond those offered. "
    "Your working directory is your private scratch paper. Work only from the "
    "problems given in the prompt; do not look for answer keys or other files."
)


def _round_prompt(manifest, rules: str, fmt: str, round_no: int, rounds: int,
                  sheet: dict[str, str]) -> str:
    head = ""
    if round_no == 1:
        head = (f"OFFICIAL COMPETITION RULES\n{rules}\n\nBENCHMARK ADAPTATION: single_agent, 1 contestant, "
                f"{rounds} rounds. Deliverable format: {fmt}\n\nPROBLEMS\n{policy.task_sheet(manifest)}\n")
    return (
        f"{head}\nROUND {round_no} of {rounds}. Your current answer sheet: {sheet or '{}'}\n"
        "Use this round to solve or check problems. Finish the round by returning the structured "
        "output: `answers` maps task ids to your current final answers (keep earlier answers you still "
        "believe), `done` is true only if you want to hand in the sheet now. "
        "Unanswered tasks score zero; the last sheet is submitted when rounds run out."
    )


def run_single(manifest, *, workspace_root: Path, model: str, rounds: int,
               max_inner_turns: int = 8, max_output_tokens: int | None = None,
               rules_root: Path | None = None, runner=None) -> dict[str, Any]:
    cid = manifest.competition_id
    task_ids = [t.task_id for t in manifest.tasks]
    agent = ClaudeCodeAgent(
        name="Agent_1", workspace=workspace_root / "Agent_1", model=model,
        tools=policy.claude_code_tools(cid, rules_root), denied_paths=policy.denied_paths(),
        max_inner_turns=max_inner_turns, max_output_tokens=max_output_tokens, runner=runner,
    )
    rules, fmt = policy.public_rules_text(cid, rules_root), policy.deliverable_format(cid, rules_root)
    schema = policy.answers_schema(task_ids, with_message=False)
    sheet: dict[str, str] = {}
    log = []
    for round_no in range(1, rounds + 1):
        res = agent.run(_round_prompt(manifest, rules, fmt, round_no, rounds, sheet),
                        append_system_prompt=SYSTEM,
                        json_schema=schema, purpose="single_round")
        out = res.structured if isinstance(res.structured, dict) else {}
        sheet.update({k: str(v) for k, v in (out.get("answers") or {}).items() if k in task_ids and str(v).strip()})
        log.append({"round": round_no, "answers": dict(sheet), "done": bool(out.get("done")),
                    "is_error": res.is_error, "text": res.text[-2000:]})
        if out.get("done"):
            break
    return {"setting": "single", "agents": [agent.name], "submissions": {t: sheet.get(t, "") for t in task_ids},
            "rounds_used": len(log), "round_log": log, "calls": agent.calls,
            "usage": agent.totals(), "tools": list(agent.tools)}
