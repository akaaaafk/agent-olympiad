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

## The three settings (standalone loops for single/multi, see below for the engine presets)

1. **single** (`claude_code/single.py`): one persistent Claude Code session
   gets the whole packet. One `claude -p` invocation per round, resuming the
   same session. It returns its answer sheet as structured output each round
   and may stop early with `done`.
2. **multi** (`claude_code/multi.py`): N persistent Claude Code instances
   (`--team-size`, default `official` = the competition's own roster, the same one OTC uses), round-robin each round. They
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

## Two implementations of single / multi

`run_rebuttal.py --impl engine` is the default, and it is the only one the
mini pipeline uses. It runs single and multi as contest-engine presets, with
every call going to Claude Code:

| setting | engine preset | seats |
|---|---|---|
| single | `single_agent` | 1 |
| multi | `decentralized` (open table: no Coach, rule card, review or memory) | competition roster (= OTC) |
| otc | `otc` / `vallina_otc` | competition roster |

So the three settings share the task executor, which covers answer sheets,
ICPC/Kattis, CTF and PDF artifacts, as well as the grader and budgets. Only the
team protocol differs. `--impl standalone` keeps the earlier Claude Code
loops (`single.py` / `multi.py`), which handle answer-sheet contests only.

## Full mini catalog

```bash
python rebuttal/run_mini_cc.py all --setting single --model claude-haiku-4-5 --output results/mini_cc_single
python rebuttal/run_mini_cc.py all --setting multi  --model claude-haiku-4-5 --output results/mini_cc_multi
python rebuttal/run_mini_cc.py all --setting otc    --model claude-haiku-4-5 --output results/mini_cc_otc
```

This is `scripts/run_mini_dataset.py` (that is, `run_pipeline.py` on
`data/mini_data`) with three changes:

- each child job runs through `rebuttal/cc_child.py`;
- `--setting` picks the preset;
- every competition's roster is pinned to `--team-size` through
  `<output>/rules_overlay`.

Everything else is the pipeline's own code: registration, Docker and
VJudge/Kattis checks for ICPC, the CTF image check, artifact routes, resume
(rerun the same command) and `report`. Pipeline filters such as
`--competitions`, `--years`, `--sessions` and `--limit` pass through.

Judges (task rubric, collaboration, CCE) also go to Claude Code. They use a
`Judge` instance with the same model, a fresh session per call, and only
`Read` access to the attachments staged in its own folder. This follows the
repo rule that solver and judges use the same provider. `--provider anthropic`
is only the internal route. The adapter sets a placeholder `ANTHROPIC_API_KEY`
for the engine's preflight and strips it before invoking `claude`, so the CLI
keeps using your normal login.

Environment knobs for child jobs: `AO_CC_MAX_INNER_TURNS` (default 8),
`AO_CC_SESSION_MODE` (`per_call` / `per_seat`), `AO_CC_WORKSPACE_ROOT`.
Each job writes `claude_code_harness.json` (seats, per-seat usage, cost) and
`claude_code_calls.json` next to its contest output.

## Run one manifest

```bash
export AGENT_OLYMPIAD_DATA_ROOT=/path/to/data      # needs benchmarks/, contest_manifests/, rules/
M=$AGENT_OLYMPIAD_DATA_ROOT/contest_manifests/arml_local_2009.json
python rebuttal/run_rebuttal.py --setting single --manifest $M                 # engine single_agent
python rebuttal/run_rebuttal.py --setting multi  --manifest $M --team-size 3   # engine decentralized
python rebuttal/run_rebuttal.py --setting otc    --manifest $M --team-size 3
python rebuttal/run_rebuttal.py --setting single --manifest $M --impl standalone
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

These tests run offline with a fake Claude Code runner. `rebuttal/tests/fake_claude.py`
can stand in for the CLI (`CLAUDE_CODE_BIN=rebuttal/tests/fake_claude.py`) to
dry-run the mini pipeline without model calls. They check that the
command is restricted (no web or subagents, dontAsk, path denies) and that all
three settings run end to end, including the real OTC engine with three
Claude Code seats.

## AWS Bedrock backend

All entry points accept `--bedrock-model <model id or inference-profile ARN>` (and
`--aws-region`, default `us-east-1`). Child jobs read it from `AO_CC_BEDROCK_MODEL` /
`AO_CC_AWS_REGION`. Claude Code then runs with its native Bedrock support
(`CLAUDE_CODE_USE_BEDROCK=1`, `ANTHROPIC_MODEL` and the small/fast model set to
that id). AWS credentials come from the normal AWS chain (env, `~/.aws`, SSO).
Every call records `cc_backend` (`bedrock` / `first_party`), and
`claude_code_harness.json` records `model_backend`.

The engine's `--model` label (for example `claude-haiku-4-5`) is unchanged, so
a resumed output root would mix backends silently. Use a fresh `--output` when
you switch backends.
