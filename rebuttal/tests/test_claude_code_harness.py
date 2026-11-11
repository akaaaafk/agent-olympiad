"""Offline tests for the Claude Code rebuttal settings (no model calls).

Run with the ARML data available, e.g.
    AGENT_OLYMPIAD_DATA_ROOT=/path/to/data python -m pytest rebuttal/tests -q
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_code import policy  # noqa: E402
from claude_code.cc_client import ALWAYS_DENIED, ClaudeCodeAgent  # noqa: E402

MANIFEST = policy.data_root() / "contest_manifests" / "arml_local_2009.json"
needs_data = pytest.mark.skipif(not MANIFEST.is_file(), reason="ARML data not available")


def _flag(cmd, name):
    i = cmd.index(name)
    out = []
    for item in cmd[i + 1:]:
        if item.startswith("--"):
            break
        out.append(item)
    return out


class FakeRunner:
    """Answers every task with '0' and records each command."""

    def __init__(self):
        self.commands = []

    def __call__(self, cmd, cwd, env, timeout):
        self.commands.append(cmd)
        schema = json.loads(cmd[cmd.index("--json-schema") + 1]) if "--json-schema" in cmd else None
        base = {"session_id": "fake-session-0001", "usage": {"input_tokens": 10, "output_tokens": 5},
                "total_cost_usd": 0.001, "num_turns": 1, "is_error": False}
        if schema is None:
            return {**base, "result": "private plan: work on the first open problem"}
        if "action" in schema["properties"]:
            variants = schema["properties"]["action"]["anyOf"]
            names = [v["properties"]["name"]["const"] for v in variants]
            pick = next((v for v in variants if v["properties"]["name"]["const"] == "rest"), variants[0])
            params = pick["properties"]["arguments"]
            args = {k: ("ok" if params["properties"][k].get("type", "string") == "string" else 0)
                    for k in params.get("required", [])}
            return {**base, "result": "", "structured_output": {"action": {"name": pick["properties"]["name"]["const"],
                                                                               "arguments": args}}, "_names": names}
        tids = list(schema["properties"]["answers"]["properties"])
        out = {"answers": {t: "0" for t in tids}, "done": True}
        if "message" in schema["properties"]:
            out["message"] = "I set every answer to 0."
        return {**base, "result": json.dumps(out), "structured_output": out}


def test_command_is_restricted(tmp_path):
    agent = ClaudeCodeAgent(name="A", workspace=tmp_path / "ws", tools=("Read", "Write"),
                            denied_paths=(tmp_path / "data",), runner=FakeRunner())
    cmd = agent.build_command("hi", append_system_prompt=None, json_schema=None, resume=False)
    assert _flag(cmd, "--tools") == ["Read", "Write"]
    denied = _flag(cmd, "--disallowedTools")
    for tool in ("WebSearch", "WebFetch", "Task", "Agent"):
        assert tool in denied and tool in ALWAYS_DENIED
    assert any(str((tmp_path / "data").resolve()) in d for d in denied)
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    assert "--strict-mcp-config" in cmd and "--disable-slash-commands" in cmd
    allowed = _flag(cmd, "--allowedTools")
    assert all(str((tmp_path / "ws").resolve()) in a for a in allowed)


@needs_data
def test_arml_tools_have_no_bash():
    assert policy.claude_code_tools("arml_local") == policy.FILE_TOOLS


@needs_data
def test_single_and_multi_offline(tmp_path):
    from claude_code.multi import run_multi
    from claude_code.single import run_single
    manifest = policy.load_manifest(MANIFEST)
    single = run_single(manifest, workspace_root=tmp_path / "s", model="fake", rounds=3, runner=FakeRunner())
    assert single["rounds_used"] == 1 and len(single["calls"]) == 1
    assert set(single["submissions"]) == {t.task_id for t in manifest.tasks}
    runner = FakeRunner()
    multi = run_multi(manifest, workspace_root=tmp_path / "m", model="fake", rounds=3, team_size=3, runner=runner)
    assert multi["agents"] == ["Agent_1", "Agent_2", "Agent_3"] and len(multi["board"]) == 3
    team_dir = str((tmp_path / "m" / "team").resolve())
    assert all(c[c.index("--add-dir") + 1] == team_dir for c in runner.commands)
    assert policy.grade(manifest, multi["submissions"])["graded"]


@needs_data
def test_otc_engine_uses_claude_code_seats(tmp_path):
    from claude_code.otc import run_otc
    runner = FakeRunner()
    session = run_otc(MANIFEST, output=tmp_path / "out", workspace_root=tmp_path / "ws", model="fake",
                      team_size=3, max_turns=10, runner=runner)
    harness = session["run"]["harness"]
    assert harness["backend"] == "claude_code"
    assert set(harness["seats"]) <= {"Coach", "Agent_1", "Agent_2", "Agent_3"}
    assert {"Agent_1", "Agent_2", "Agent_3"} <= set(harness["seats"])
    assert len(runner.commands) == harness["total"]["api_calls"]
