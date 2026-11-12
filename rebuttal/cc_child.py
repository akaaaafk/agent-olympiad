"""Child-job entry point: run an existing runner with Claude Code as the model backend.

    python rebuttal/cc_child.py batch    <run_competition_batch.py args>
    python rebuttal/cc_child.py artifact <run_otc_artifact.py args>

The runner code is unchanged; every ``--provider anthropic`` model call
(contestant seats, Coach, judges) is routed to Claude Code instances by
:func:`claude_code.otc.install`. Claude Code options come from environment
variables so a parent pipeline can pass them through unchanged:

    AO_CC_MAX_INNER_TURNS   Claude Code --max-turns per invocation (default 8)
    AO_CC_SESSION_MODE      per_call (default) or per_seat
    AO_CC_WORKSPACE_ROOT    parent dir for agent workspaces (default: system temp)

The model is the runner's own ``--model``.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_code import policy  # noqa: E402  (also puts src/ on sys.path)
from claude_code.otc import ClaudeCodeSeats, install, write_harness_summary  # noqa: E402


def _arg(argv: list[str], name: str) -> str | None:
    for i, item in enumerate(argv):
        if item == name and i + 1 < len(argv):
            return argv[i + 1]
        if item.startswith(name + "="):
            return item.split("=", 1)[1]
    return None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in {"batch", "artifact"}:
        raise SystemExit(__doc__)
    kind, rest = argv[0], argv[1:]
    output = Path(_arg(rest, "--output") or ".").resolve()
    model = _arg(rest, "--model")
    if kind == "batch":
        manifest = _arg(rest, "--contest-manifest")
        competition = json.loads(Path(manifest).read_text(encoding="utf-8-sig"))["competition_id"]
    else:
        competition = _arg(rest, "--competition")
    rules_root = _arg(rest, "--rules-root")
    base = Path(os.environ.get("AO_CC_WORKSPACE_ROOT") or tempfile.gettempdir()) / "ao_cc_workspaces"
    seats = ClaudeCodeSeats(
        competition_id=competition, workspace_root=base / f"{output.name}_{hashlib.sha256(str(output).encode()).hexdigest()[:10]}",
        model=model,
        max_inner_turns=int(os.environ.get("AO_CC_MAX_INNER_TURNS") or 8),
        session_mode=os.environ.get("AO_CC_SESSION_MODE") or "per_call",
        rules_root=Path(rules_root) if rules_root else None,
    )
    restore = install(seats)
    code = 0
    try:
        if kind == "batch":
            import run_competition_batch as rcb
            old = sys.argv
            sys.argv = ["run_competition_batch.py", *rest]
            try:
                rcb.main()
            finally:
                sys.argv = old
        else:
            import run_otc_artifact
            code = run_otc_artifact.main(rest)
    finally:
        restore()
        if seats.agents:
            write_harness_summary(seats, output, runner=kind, rules_root=rules_root)
    return int(code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
