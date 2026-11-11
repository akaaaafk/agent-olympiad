# Rebuttal: Claude Code harness settings

Three settings that swap the model backend for **Claude Code** (default model
`claude-haiku-4-5`). The expected ordering is

    single Claude Code  <  multi-agent Claude Code setup  <  OTC + Claude Code

Setting 3 is **not** Claude Code's subagent or team mode. It runs the OTC
contest engine unchanged and only replaces each API call with a call to that
seat's own Claude Code instance.

## What is the same in every setting

| | value |
|---|---|
| model | `--model` (default `claude-haiku-4-5`) |
| tools | file tools (`Read/Write/Edit/Glob/Grep`) on the agent's own workspace as scratch paper; `Bash` **only** if the competition allows `execute_code` / `use_calculator` (ARML: no Bash) |
| always off | `WebSearch`, `WebFetch`, `Task`/`Agent` (subagents), MCP servers, skills/slash commands, user/project settings, auto-memory |
| file access | `--permission-mode dontAsk`; only the workspace (and, in multi, the shared `team/` dir) is allowed. The data root and the repo are denied by path, so gold answers cannot be read |
| rounds | the competition's engine turn budget (`resolve_contest_budget`, ARML Local = 10), override with `--rounds` |
| per invocation | Claude Code `--max-turns` = `--max-inner-turns` (default 8) |
| grading | `contest_adapters.grade_contest_result` (same deterministic grader as the engine) |

## The three settings

1. **single** (`claude_code/single.py`): one persistent Claude Code session
   gets the whole packet. One `claude -p` invocation per round, resuming the
   same session. It returns its answer sheet as structured output each round
   and may stop early with `done`.
2. **multi** (`claude_code/multi.py`): N persistent Claude Code instances
   (`--team-size`, default 3 = the OTC roster), round-robin each round. They
   share a team message board, one shared answer sheet (last write wins), and
   a shared `team/` directory. There is no Coach, rule card, review gate,
   memory module, DM or leader. The shared sheet is submitted.
3. **otc** (`claude_code/otc.py`): `src/run_competition_batch.py` with
   `--system-variant otc` (or `vallina_otc`) runs unchanged: rule card, blind
   turn-0 Coach, private think, typed actions, review gate, memory and budgets.
   `Agent_1..Agent_N` each map to their own Claude Code instance with a
   persistent workspace, and the Coach is one more instance with no tools.
   Each engine call becomes one Claude Code invocation for that seat. Actions
   are forced with `--json-schema`, validated against the engine's function
   schemas, and get at most one repair in the same session. By default each
   call starts a fresh conversation, because the engine already decides what
   a seat remembers; `--session-mode per_seat` resumes one conversation per
   seat instead. The roster is pinned to `--team-size` through a copied rules
   tree (`<output>/rules_overlay`). The original rules are untouched, and ARML
   Local's official roster is 6.

## Run

```bash
export AGENT_OLYMPIAD_DATA_ROOT=/path/to/data      # needs benchmarks/, contest_manifests/, rules/
M=$AGENT_OLYMPIAD_DATA_ROOT/contest_manifests/arml_local_2009.json
python rebuttal/run_rebuttal.py --setting single --manifest $M
python rebuttal/run_rebuttal.py --setting multi  --manifest $M --team-size 3
python rebuttal/run_rebuttal.py --setting otc    --manifest $M --team-size 3
```

This needs the `claude` CLI on PATH and logged in (or `CLAUDE_CODE_BIN`).
Outputs go to `results/rebuttal_claude_code/<session>_<setting>_<time>/result.json`
(override with `--output`). OTC also writes the full engine output under
`engine/` (contest_session.json, chat, metrics) plus `claude_code_calls.json`.
Agent workspaces default to a temp dir outside the repo. Keep them there,
because the repo is denied to the agents.

Usage is reported per Claude Code invocation: `api_calls` (invocations),
`input_tokens` (including cache), `output_tokens`, `cc_inner_turns`
(Claude Code's own tool-loop steps) and `cc_cost_usd`. One engine API call
equals one Claude Code invocation, and the inner steps are reported separately.

In the OTC result the engine's `run.provider` reads `anthropic`. That is only
the internal route the adapter hooks into. `run.harness.backend` is
`claude_code`, and every call went to a Claude Code instance.

## Tests

```bash
AGENT_OLYMPIAD_DATA_ROOT=/path/to/data python -m pytest rebuttal/tests -q
```

These tests run offline with a fake Claude Code runner. They check that the
command is restricted (no web or subagents, dontAsk, path denies) and that all
three settings run end to end, including the real OTC engine with three
Claude Code seats.
