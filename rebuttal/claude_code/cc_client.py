"""One restricted Claude Code instance driven through ``claude -p``.

Every rebuttal setting (single, multi, OTC) talks to Claude Code only through
:class:`ClaudeCodeAgent`, so all three share exactly the same restrictions:

* no web access: ``WebSearch`` / ``WebFetch`` are never offered and are also
  denied explicitly;
* no Claude Code subagents or team mode: ``Task`` / ``Agent`` are denied;
* no MCP servers, slash commands/skills, user/project settings or CLAUDE.md;
* file tools work only inside the agent's own workspace (plus explicitly
  shared directories). ``--permission-mode dontAsk`` refuses everything that
  is not pre-approved, and the benchmark data root / repository root are
  denied by path as a second line of defence, so gold answers cannot be read;
* ``Bash`` is offered only when the competition itself allows a calculator or
  code execution (see :func:`policy.claude_code_tools`).

The same object can run against a fake ``runner`` for offline tests.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

DEFAULT_MODEL = "claude-haiku-4-5"
CLAUDE_BIN = os.environ.get("CLAUDE_CODE_BIN") or shutil.which("claude") or "claude"


def _claude_command(binary: str) -> list[str]:
    """Argv prefix that runs ``binary`` without a shell in between.

    On Windows ``shutil.which("claude")`` finds npm's ``claude.cmd`` shim, and
    cmd.exe re-parses the JSON arguments (quotes, ``&``, ``|``, ``<``) and caps
    the line at 8191 characters. Go to the native ``claude.exe`` the shim wraps
    instead. A ``.py`` stand-in (``tests/fake_claude.py``) runs with this Python.
    """
    path = Path(binary)
    if path.suffix.lower() == ".py":
        return [sys.executable, str(path)]
    if path.suffix.lower() in (".cmd", ".bat"):
        native = path.parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if native.is_file():
            return [str(native)]
    return [binary]


CLAUDE_CMD = _claude_command(CLAUDE_BIN)
LAUNCH_RETRIES = 8  # about 70 s of backoff in total

# Never available, whatever the competition allows.
ALWAYS_DENIED = (
    "WebSearch", "WebFetch", "Task", "Agent", "NotebookEdit",
    "TodoWrite", "Skill", "SlashCommand", "KillShell", "BashOutput",
)

# Environment variables that would leak the outer session's memory, extra
# directories or project instructions into the contestant.
_SCRUBBED_ENV = (
    "CLAUDE_ADDITIONAL_DIRECTORIES",
    "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD",
    "CLAUDE_MEMORY_STORES",
    "CLAUDE_COWORK_MEMORY_PATH_OVERRIDE",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_REMOTE_SESSION_ID",
)

# runner(cmd, cwd, env, timeout_s, stdin_text) -> parsed JSON result of ``claude -p``
# The engine insists on a judge API key for its provider route; the Claude Code
# route sets this placeholder, which must never reach the real CLI.
KEY_PLACEHOLDER = "claude-code-route-no-key"

Runner = Callable[[list[str], Path, dict[str, str], float, str], dict[str, Any]]


@dataclass
class CCResult:
    text: str
    structured: Any
    session_id: str
    usage: dict[str, Any]
    cost_usd: float
    num_turns: int
    is_error: bool
    permission_denials: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def usage_row(self) -> dict[str, Any]:
        """Usage in the engine's provider-neutral shape (one call = one invocation)."""
        u = self.usage or {}
        input_tokens = int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0) \
            + int(u.get("cache_creation_input_tokens") or 0)
        return {
            "api_calls": 1,
            "input_tokens": input_tokens,
            "output_tokens": int(u.get("output_tokens") or 0),
            "cc_inner_turns": self.num_turns,
            "cc_cost_usd": self.cost_usd,
            "cc_session_id": self.session_id,
            "cc_permission_denials": len(self.permission_denials),
            "tokens_basis": "provider_reported",
        }


def _subprocess_runner(cmd: list[str], cwd: Path, env: dict[str, str], timeout: float,
                       stdin_text: str) -> dict[str, Any]:
    # The prompt goes through stdin and the system prompt through a file, so
    # long contest prompts never hit the Windows command-line length limit.
    # A launch that fails with OSError never reached the model, so it is safe
    # to retry. This covers the CLI binary being replaced by an update or
    # reinstall (missing file, or a half-written exe: WinError 216) for a few
    # seconds while a long batch is running.
    for attempt in range(LAUNCH_RETRIES + 1):
        try:
            proc = subprocess.run(cmd, cwd=str(cwd), env=env, input=stdin_text, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=timeout)
            break
        except OSError:
            if attempt == LAUNCH_RETRIES:
                raise
            time.sleep(min(2 ** attempt, 15))
    out = proc.stdout.strip()
    try:
        return json.loads(out.splitlines()[-1] if out else "{}")
    except json.JSONDecodeError:
        return {"is_error": True, "result": (out or proc.stderr)[-2000:], "subtype": "invalid_json"}


@dataclass
class ClaudeCodeAgent:
    """A named, persistent Claude Code contestant with its own workspace."""

    name: str
    workspace: Path
    model: str = DEFAULT_MODEL
    tools: tuple[str, ...] = ("Read", "Write", "Edit", "Glob", "Grep")
    shared_dirs: tuple[Path, ...] = ()
    denied_paths: tuple[Path, ...] = ()
    max_inner_turns: int = 8
    max_output_tokens: int | None = None
    timeout_s: float = 900.0
    persistent: bool = True
    runner: Runner | None = None
    session_id: str | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.workspace = Path(self.workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    # -- command construction -------------------------------------------------
    def _permission_rules(self) -> tuple[list[str], list[str]]:
        allow, deny = [], list(ALWAYS_DENIED)
        roots = [self.workspace, *[Path(p).resolve() for p in self.shared_dirs]]
        for root in roots:
            for tool in ("Read", "Edit", "Write"):
                if tool in self.tools:
                    allow.append(f"{tool}(/{root}/**)")
        for tool in ("Glob", "Grep"):
            if tool in self.tools:
                allow.append(tool)
        if "Bash" in self.tools:
            allow.append("Bash")
        for path in self.denied_paths:
            path = Path(path).resolve()
            deny += [f"Read(/{path}/**)", f"Edit(/{path}/**)", f"Write(/{path}/**)"]
        return allow, deny

    def _prompt_file(self, text: str) -> Path:
        # Outside the workspace so the file never shows up in the agent's own scratch dir.
        folder = self.workspace.parent / "_system_prompts"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{self.name}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def build_command(self, prompt: str, *, append_system_prompt: str | None,
                      json_schema: dict[str, Any] | None, resume: bool) -> list[str]:
        """Command line for one invocation; the prompt itself is sent on stdin."""
        allow, deny = self._permission_rules()
        cmd = [
            *CLAUDE_CMD, "-p",
            "--model", self.model,
            "--output-format", "json",
            "--max-turns", str(self.max_inner_turns),
            "--permission-mode", "dontAsk",
            "--setting-sources", "",
            "--strict-mcp-config",
            "--disable-slash-commands",
            "--tools", *(self.tools or ("",)),
            "--allowedTools", *allow,
            "--disallowedTools", *deny,
        ]
        for shared in self.shared_dirs:
            cmd += ["--add-dir", str(Path(shared).resolve())]
        if append_system_prompt:
            cmd += ["--append-system-prompt-file", str(self._prompt_file(append_system_prompt))]
        if json_schema is not None:
            cmd += ["--json-schema", json.dumps(json_schema, ensure_ascii=False)]
        if resume and self.session_id:
            cmd += ["--resume", self.session_id]
        else:
            self.session_id = str(uuid.uuid4())
            cmd += ["--session-id", self.session_id]
        if not self.persistent:
            cmd += ["--no-session-persistence"]
        return cmd

    def _env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in _SCRUBBED_ENV}
        if env.get("ANTHROPIC_API_KEY") == KEY_PLACEHOLDER:
            env.pop("ANTHROPIC_API_KEY")
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
        env["DISABLE_AUTOUPDATER"] = "1"
        if self.max_output_tokens:
            env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(self.max_output_tokens)
        return env

    # -- invocation -------------------------------------------------------------
    def run(self, prompt: str, *, append_system_prompt: str | None = None,
            json_schema: dict[str, Any] | None = None, new_session: bool = False,
            purpose: str = "turn") -> CCResult:
        resume = self.persistent and not new_session and self.session_id is not None
        cmd = self.build_command(prompt, append_system_prompt=append_system_prompt,
                                 json_schema=json_schema, resume=resume)
        runner = self.runner or _subprocess_runner
        try:
            data = runner(cmd, self.workspace, self._env(), self.timeout_s, prompt)
        except subprocess.TimeoutExpired:
            data = {"is_error": True, "result": "Claude Code invocation timed out", "subtype": "timeout"}
        result = CCResult(
            text=str(data.get("result") or ""),
            structured=data.get("structured_output"),
            session_id=str(data.get("session_id") or self.session_id or ""),
            usage=dict(data.get("usage") or {}),
            cost_usd=float(data.get("total_cost_usd") or 0.0),
            num_turns=int(data.get("num_turns") or 0),
            is_error=bool(data.get("is_error")),
            permission_denials=list(data.get("permission_denials") or []),
            raw=data,
        )
        if result.session_id:
            self.session_id = result.session_id
        self.calls.append({
            "agent": self.name, "purpose": purpose, "resumed": resume,
            "is_error": result.is_error, "subtype": data.get("subtype"),
            **result.usage_row(),
        })
        return result

    def totals(self) -> dict[str, Any]:
        keys = ("api_calls", "input_tokens", "output_tokens", "cc_inner_turns", "cc_cost_usd",
                "cc_permission_denials")
        return {k: round(sum(c.get(k, 0) for c in self.calls), 6) for k in keys}
