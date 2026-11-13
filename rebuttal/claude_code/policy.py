"""Shared contest context for the three Claude Code settings.

Everything a contestant sees is built here from the same public sources the
OTC engine uses (manifest task prompts and the public fields of
``data/rules/<competition>/competition.json``), so the three settings differ
only in team structure, never in information or tools.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dataset_paths import data_root  # noqa: E402

# Competition tools that map to Claude Code's Bash tool. Everything else
# (web_search, environment tools, prepare_* sheet helpers) is not given to
# Claude Code: web is always off, and helper actions are an OTC-engine
# feature reached through the engine's action interface in setting 3.
BASH_TOOLS = {"execute_code", "use_calculator"}
FILE_TOOLS = ("Read", "Write", "Edit", "Glob", "Grep")
PUBLIC_RULE_FIELDS = ("competition_id", "team", "execution", "resources", "deliverable",
                      "human_constraints", "rules_text")


def competition_json(competition_id: str, rules_root: Path | None = None) -> dict[str, Any]:
    root = Path(rules_root) if rules_root else data_root() / "rules"
    path = root / competition_id / "competition.json"
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else {}


def claude_code_tools(competition_id: str, rules_root: Path | None = None) -> tuple[str, ...]:
    """Claude Code tool set equivalent to the competition's current restrictions.

    File tools are scratch paper confined to the agent's workspace. Bash is
    added only if the contest allows a calculator or code execution. Web tools
    are never added (same as the current runs, which block search).
    """
    allowed = set(competition_json(competition_id, rules_root).get("allowed_tools") or ())
    return FILE_TOOLS + (("Bash",) if allowed & BASH_TOOLS else ())


def official_team_size(competition_id: str, rules_root: Path | None = None) -> int:
    """The competition's own active roster (team.active_default), the one OTC uses."""
    size = (competition_json(competition_id, rules_root).get("team") or {}).get("active_default")
    if type(size) is not int or size < 1:
        raise ValueError(f"{competition_id}: competition.json has no integer team.active_default")
    return size


def public_rules_text(competition_id: str, rules_root: Path | None = None) -> str:
    raw = competition_json(competition_id, rules_root)
    if not raw:
        return "No competition.json is available; do not invent official constraints."
    public = {k: raw[k] for k in PUBLIC_RULE_FIELDS if k in raw}
    return json.dumps(public, ensure_ascii=False, sort_keys=True)


def load_manifest(manifest_path: Path, benchmark_root: Path | None = None):
    from contest_manifest import load_contest_manifest
    return load_contest_manifest(manifest_path, benchmark_root=benchmark_root or data_root() / "benchmarks")


def contest_rounds(competition_id: str, override: int | None = None) -> int:
    from contest_budget import resolve_contest_budget
    return resolve_contest_budget(competition_id, max_turns=override).max_turns


def task_sheet(manifest) -> str:
    lines = []
    for task in manifest.tasks:
        lines.append(f"### {task.task_id}  (max_score {task.max_score:g})\n{task.prompt.strip()}\n")
    return "\n".join(lines)


def deliverable_format(competition_id: str, rules_root: Path | None = None) -> str:
    deliverable = competition_json(competition_id, rules_root).get("deliverable") or {}
    return str(deliverable.get("answer_format") or "One final answer per task id.")


def denied_paths() -> tuple[Path, ...]:
    """Paths that hold gold answers, rubrics or harness code."""
    return tuple({data_root().resolve(), REPO_ROOT.resolve()})


def answers_schema(task_ids: list[str], *, with_message: bool) -> dict[str, Any]:
    props: dict[str, Any] = {
        "answers": {
            "type": "object",
            "description": "Your current answer for each task id you have an answer for. "
                           "Omit tasks you have no answer for yet.",
            "properties": {tid: {"type": "string"} for tid in task_ids},
            "additionalProperties": False,
        },
        "done": {"type": "boolean",
                 "description": "true only when you would hand in the sheet now."},
    }
    required = ["answers", "done"]
    if with_message:
        props["message"] = {"type": "string",
                            "description": "Message posted to the whole team (may be empty)."}
        required.append("message")
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


def team_rules_overlay(competition_id: str | None, team_size: int, out_dir: Path,
                       rules_root: Path | None = None) -> Path:
    """Copy the rules tree with the active roster pinned to ``team_size``.

    Used so the OTC engine and the multi setting run with the same number of
    Claude Code instances. ``competition_id=None`` pins every competition. The original rules are left untouched; the overlay
    path and the size are recorded in the run outputs.
    """
    src_root = Path(rules_root) if rules_root else data_root() / "rules"
    if not src_root.is_dir():  # mini_data may keep rules at the canonical data/rules path
        src_root = REPO_ROOT / "data" / "rules"
    dst_root = out_dir / "rules_overlay"
    if dst_root.exists():
        shutil.rmtree(dst_root)
    shutil.copytree(src_root, dst_root)
    paths = ([dst_root / competition_id / "competition.json"] if competition_id
             else sorted(dst_root.glob("*/competition.json")))
    for path in paths:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        team = raw.setdefault("team", {})
        team.update(active_min=team_size, active_default=team_size, active_max=team_size,
                    roster_max=max(team_size, int(team.get("roster_max") or 0)),
                    rebuttal_override=f"active roster pinned to {team_size} Claude Code instances")
        path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst_root


def grade(manifest, submissions: dict[str, str]) -> dict[str, Any]:
    from contest_adapters import grade_contest_result
    return grade_contest_result(manifest, {"submissions": submissions})
