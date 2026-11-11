"""Setting 3: the OTC contest engine with every API call replaced by Claude Code.

This is *not* Claude Code's subagent/team mode. The OTC engine
(``src/run_competition_batch.py`` -> ``contest_engine``) is run unchanged:
rule card, blind turn-0 Coach, private think call, typed actions, review
gate, automatic memory and budgets all stay as they are. The only change is
the model backend: each seat (``Agent_1`` .. ``Agent_N``) is its own Claude
Code instance with its own persistent workspace, and the Coach is one more
instance with no tools. Wherever the engine used to make an API call for a
seat, that seat's Claude Code instance is invoked once.

Per call, Claude Code gets the engine's system prompt (appended to Claude
Code's own system prompt) and user prompt. Action calls must return exactly
one engine function call; it is forced with ``--json-schema`` and validated
against the engine's function schemas, with at most one repair attempt in the
same session (charged as a second call).

By default every call starts a fresh Claude Code conversation
(``session_mode="per_call"``) because the engine already decides what each
seat remembers; the seat's workspace files still persist across its turns.
``session_mode="per_seat"`` resumes one conversation per seat instead.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from . import policy
from .cc_client import ClaudeCodeAgent

from llm import (  # noqa: E402  (policy puts src/ on sys.path)
    LLMRequest, LLMResponse, LLMToolCall, _coerce_emulated_tool_call, _validate_emulated_tool_call,
)

PROVIDER_LABEL = "claude_code"
_AGENT_RE = re.compile(r"\bYou are (Agent_\d+|Group_Leader)\b")

SEAT_NOTE = (
    "\n\nCLAUDE CODE SEAT NOTE: You are running inside a contest simulator. Your working directory "
    "is your own private scratch paper and persists across your turns; teammates cannot see it. "
    "Everything you share must go through the contest actions. There is no internet. Work only "
    "from the problems in the prompt; do not look for answer keys or other files."
)


def _action_schema(tools: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    variants = []
    for tool in tools:
        params = dict(tool.get("parameters") or {"type": "object", "properties": {}})
        params.setdefault("type", "object")
        variants.append({
            "type": "object",
            "properties": {"name": {"type": "string", "const": tool["name"]}, "arguments": params},
            "required": ["name", "arguments"],
            "additionalProperties": False,
        })
    return {"type": "object", "properties": {"action": {"anyOf": variants}}, "required": ["action"],
            "additionalProperties": False}


def _tool_contract(tools: tuple[dict[str, Any], ...]) -> str:
    compact = [{"name": t.get("name"), "description": t.get("description"), "parameters": t.get("parameters")}
               for t in tools]
    return ("\n\nACTION CONTRACT\nYou may think and use your scratch tools first, but end this turn by "
            "returning the structured output with exactly one contest action: "
            '{"action": {"name": <function>, "arguments": {...}}}. Use only these functions and their exact '
            f"argument fields:\n{json.dumps(compact, ensure_ascii=False)}")


def _merge_usage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"api_calls": 0, "input_tokens": 0, "output_tokens": 0, "cc_inner_turns": 0,
                           "cc_cost_usd": 0.0, "tokens_basis": "provider_reported"}
    for row in rows:
        for key in ("api_calls", "input_tokens", "output_tokens", "cc_inner_turns", "cc_cost_usd"):
            out[key] += row.get(key, 0)
    out["cc_session_ids"] = [r.get("cc_session_id") for r in rows]
    return out


class ClaudeCodeSeats:
    """Maps engine requests to one Claude Code instance per seat."""

    def __init__(self, *, competition_id: str, workspace_root: Path, model: str,
                 max_inner_turns: int = 8, max_output_tokens: int | None = None,
                 session_mode: str = "per_call", rules_root: Path | None = None, runner=None):
        if session_mode not in {"per_call", "per_seat"}:
            raise ValueError("session_mode must be per_call or per_seat")
        self.competition_id = competition_id
        self.workspace_root = Path(workspace_root)
        self.model = model
        self.max_inner_turns = max_inner_turns
        self.max_output_tokens = max_output_tokens
        self.session_mode = session_mode
        self.seat_tools = policy.claude_code_tools(competition_id, rules_root)
        self.runner = runner
        self.agents: dict[str, ClaudeCodeAgent] = {}
        # engine-facing attributes
        self.max_output_tokens_attr = max_output_tokens or 8192

    def agent(self, seat: str) -> ClaudeCodeAgent:
        if seat not in self.agents:
            tools = () if seat == "Coach" else self.seat_tools
            self.agents[seat] = ClaudeCodeAgent(
                name=seat, workspace=self.workspace_root / seat, model=self.model, tools=tools,
                denied_paths=policy.denied_paths(), max_inner_turns=self.max_inner_turns,
                max_output_tokens=self.max_output_tokens, runner=self.runner,
                persistent=True,
            )
        return self.agents[seat]

    @staticmethod
    def seat_of(request: LLMRequest) -> str:
        agent = (request.metadata or {}).get("agent")
        if agent:
            return str(agent)
        match = _AGENT_RE.search(request.system_prompt or "")
        return match.group(1) if match else "Coach"

    def _stage_attachments(self, agent: ClaudeCodeAgent, request: LLMRequest) -> str:
        if not request.attachments:
            return ""
        target = agent.workspace / "attachments"
        target.mkdir(exist_ok=True)
        names = []
        for att in request.attachments:
            dst = target / Path(att.path).name
            shutil.copyfile(att.path, dst)
            names.append(str(dst))
        return "\n\nATTACHED FILES (read them with your Read tool):\n" + "\n".join(names)

    def _new_session(self, agent: ClaudeCodeAgent) -> bool:
        return self.session_mode == "per_call" or agent.session_id is None

    # -- RequestFn for typed actions ------------------------------------------
    def request(self, request: LLMRequest) -> LLMResponse:
        seat = self.seat_of(request)
        agent = self.agent(seat)
        prompt = request.user_prompt + self._stage_attachments(agent, request)
        if not request.tools:
            res = agent.run(prompt, append_system_prompt=(request.system_prompt or "") + SEAT_NOTE,
                            new_session=self._new_session(agent), purpose=request.purpose)
            usage = res.usage_row()
            if res.is_error:
                usage["tool_error"] = f"Claude Code error: {res.raw.get('subtype') or res.text[:200]}"
            return LLMResponse(res.text, PROVIDER_LABEL, self.model, usage=usage)

        schema = _action_schema(request.tools)
        system = (request.system_prompt or "") + SEAT_NOTE
        rows, rejected = [], []
        res = agent.run(prompt + _tool_contract(request.tools), append_system_prompt=system,
                        json_schema=schema, new_session=self._new_session(agent), purpose=request.purpose)
        rows.append(res.usage_row())
        for attempt in range(2):
            call, error = self._parse_call(res, request.tools)
            if call is not None and error is None:
                usage = _merge_usage(rows)
                usage["tool_retries"] = attempt
                usage["rejected_tool_calls"] = rejected
                return LLMResponse("", PROVIDER_LABEL, self.model, usage=usage, tool_calls=(call,))
            rejected.append({"name": getattr(call, "name", None), "arguments": getattr(call, "arguments", None),
                             "executed": False, "rejection": error})
            if attempt == 1:
                break
            # one repair attempt in the same session
            res = agent.run(f"Your action was rejected: {error}. Return exactly one valid action now.",
                            append_system_prompt=system, json_schema=schema, purpose="action_repair")
            rows.append(res.usage_row())
        usage = _merge_usage(rows)
        usage.update(tool_retries=1, rejected_tool_calls=rejected,
                     tool_error=f"Claude Code returned no valid action: {rejected[-1]['rejection']}")
        return LLMResponse("", PROVIDER_LABEL, self.model, usage=usage)

    @staticmethod
    def _parse_call(res, tools) -> tuple[LLMToolCall | None, str | None]:
        if res.is_error:
            return None, f"Claude Code error ({res.raw.get('subtype')})"
        data = res.structured
        try:
            if isinstance(data, dict) and isinstance(data.get("action"), dict):
                raw = data["action"]
                call = LLMToolCall(name=str(raw.get("name") or ""), arguments=dict(raw.get("arguments") or {}))
            else:
                call = _coerce_emulated_tool_call(res.text)
        except (ValueError, TypeError) as exc:
            return None, str(exc)
        call = LLMToolCall(call.name, call.arguments, call_id=f"cc_{res.session_id[:8]}")
        return call, _validate_emulated_tool_call(call, tuple(tools))

    # -- QueryFn for think / coach text calls ---------------------------------
    def query_fn(self):
        def query(system_prompt: str, user_prompt: str) -> str:
            response = self.request(LLMRequest(system_prompt, user_prompt, purpose="contest_deliberation"))
            if response.usage.get("tool_error"):
                raise ValueError(response.usage["tool_error"])
            return response.text
        query.request = self.request
        query.supports_budgeted_requests = True
        query.max_output_tokens = self.max_output_tokens_attr
        return query

    def summary(self) -> dict[str, Any]:
        per_seat = {name: a.totals() for name, a in self.agents.items()}
        total: dict[str, float] = {}
        for row in per_seat.values():
            for k, v in row.items():
                total[k] = round(total.get(k, 0) + v, 6)
        return {"seats": sorted(self.agents), "per_seat": per_seat, "total": total,
                "session_mode": self.session_mode, "seat_tools": list(self.seat_tools),
                "calls": [c for a in self.agents.values() for c in a.calls]}


def run_otc(manifest_path: Path, *, output: Path, workspace_root: Path, model: str, team_size: int,
            variant: str = "otc", max_inner_turns: int = 8, max_output_tokens: int | None = None,
            max_turns: int | None = None, session_mode: str = "per_call", extra_args: list[str] | None = None,
            runner=None) -> dict[str, Any]:
    """Run the unchanged OTC engine with Claude Code seats; returns contest_session.json."""
    import run_competition_batch as rcb

    manifest = policy.load_manifest(manifest_path)
    output.mkdir(parents=True, exist_ok=True)
    rules_root = policy.team_rules_overlay(manifest.competition_id, team_size, output)
    seats = ClaudeCodeSeats(competition_id=manifest.competition_id, workspace_root=workspace_root, model=model,
                            max_inner_turns=max_inner_turns, max_output_tokens=max_output_tokens,
                            session_mode=session_mode, rules_root=rules_root, runner=runner)

    orig = (rcb._make_live_query, rcb.resolve_request_fn)
    rcb._make_live_query = lambda provider, model_, **kw: seats.query_fn()
    rcb.resolve_request_fn = lambda provider="anthropic", model=None, **kw: seats.request
    argv = ["run_competition_batch.py", "--live", "--provider", "anthropic", "--model", model,
            "--contest-manifest", str(manifest_path), "--system-variant", variant,
            "--rules-root", str(rules_root), "--output", str(output / "engine"),
            "--no-judge-task", "--no-judge-collab", "--action-calling", "native"]
    if max_turns is not None:
        argv += ["--max-turns", str(max_turns)]
    if max_output_tokens is not None:
        argv += ["--max-output-tokens", str(max_output_tokens)]
    argv += list(extra_args or [])
    old_argv = sys.argv
    try:
        sys.argv = argv
        rcb.main()
    finally:
        sys.argv = old_argv
        rcb._make_live_query, rcb.resolve_request_fn = orig

    session_path = output / "engine" / "contest_session.json"
    result = json.loads(session_path.read_text(encoding="utf-8"))
    harness = {"backend": "claude_code", "model": model, "team_size": team_size,
               "rules_overlay": str(rules_root), "max_inner_turns": max_inner_turns,
               "note": "provider label 'anthropic' in run/run_identity is the engine route; "
                       "every call actually went to a Claude Code instance", **seats.summary()}
    result["run"]["harness"] = {k: v for k, v in harness.items() if k != "calls"}
    session_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "claude_code_calls.json").write_text(json.dumps(harness["calls"], ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
    return result
