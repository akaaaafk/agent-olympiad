# Vanilla and strategic contest sessions

Use an explicit manifest so unrelated benchmark years are never mixed into one
contest:

```powershell
python src/run_competition_batch.py `
  --live `
  --contest-manifest data/contest_manifests/icpc_wf_2012_5.json `
  --system-variant strategic_team `
  --max-api-calls 300 `
  --max-total-tokens 80000 `
  --output results/icpc_strategic
```

Run the matched baseline with the same model, manifest, team size, API limit,
token limit, turn limit, and starting seat; change only
`--system-variant vanilla_team`. Use `--start-seat` for repeated runs with a
different first agent.

The two variants now have explicit Python module interfaces:

- `src/vanilla_contest_runner.py` is the no-Coach baseline entry point. Its
  interface intentionally has no `coach_query_fn`, so Coach behavior cannot be
  enabled accidentally.
- `src/strategic_contest_runner.py` owns the strategic/Open-Coach entry point,
  including its Coach dependency.
- `src/contest_runner.py` contains the shared contest state machine and a
  compatibility dispatcher. Session state, judge adapters, budgets, action
  transport, checkpoints, and result serialization remain shared so matched
  comparisons do not drift.

Contest actions use one provider-neutral `LLMRequest(tools=...)` /
`LLMResponse(tool_calls=...)` interface. With `--action-calling auto`,
Perplexity uses provider-native function calling and Tinker uses
schema-validated emulated function calling because the current Tinker sampling
SDK does not expose native custom functions or constrained JSON output. The
Tinker adapter renders the same function schemas into the prompt, validates the
sampled name, argument types, required fields, and enums, and performs at most
two bounded correction attempts. Those additional API calls and output tokens
are charged to the shared budget. Use `--action-calling prompt-json` only for
compatibility experiments.

The selected transport is recorded as `native`, `emulated`, or `prompt_json`
in the `action_calling` field of `contest_session.json`. Calls are also
preserved in `action_transport_log` with turn, agent, provider `call_id`,
function name, and validated arguments. Diagnostics include transport API
calls, retries, and terminal transport failures.

## Canonical tools: common versus specialized

`src/tool_registry.py` contains one canonical registry of 17 typed actions.
Every action has a name, description, JSON-compatible argument schema,
visibility, capability pack, budget semantics, and runtime handler marker.
The same definitions are used for provider function schemas, prompt
instructions, validation, and dispatch.

All task families initially receive the **common** collaboration pack:

- `select_problem(problem_id)` selects or switches the shared active problem.
- `speak(content)` broadcasts a message to the team.
- `direct_message(recipient, content)` privately sends a message to one named
  teammate.
- `work(content)` records a durable answer or code draft.
- `request_review(content, reviewer?)` asks for review but does not approve a
  version.
- `review_answer(problem_id, version_hash, decision, content)` independently
  approves or rejects an immutable answer version.
- `submit(answer)` submits a non-programming answer.
- `skip_problem(reason?)` leaves the current problem.
- `finish_contest(reason?)` ends a contest only when completion gates permit it.
- `rest(reason?)` passes the current agent action.

Specialized actions are grouped into capability packs:

- **Math:** `use_calculator(expression)`.
- **Programming:** `execute_code(code, language?)`, `verify(focus?)`, and
  `submit_code(code, language?)`.
- **Research:** `web_search(query)`.
- **Physical resources:** `read_lab_equipment(resource?)` and
  `read_star_chart(resource?)`.

The initial specialized surface is resolved from competition, task type,
benchmark requirements, declared capabilities, and installed handlers:

- ICPC, IIOT, Codeforces, or programming/coding/algorithmic task types receive
  the programming pack.
- Purple Comet, Fyziklani, IJSO Practical, IOAA Group, IYPT, or
  math/proof/numeric task types receive the math pack.
- Fyziklani, MCM, ICM, IEO Business Case, Jessup, IYPT, or
  research/case-study/legal task types receive the research pack.
- A benchmark may explicitly request a known pack or individual action through
  its tool requirements or capabilities.
- Physical resource actions are never inferred from a broad task family. They
  require the exact declared capability and an installed handler.
- An action whose runtime handler is unavailable is omitted rather than shown
  to the model.

“Common” means shared across task families, not unconditionally visible on
every turn. The contest runner narrows the function list dynamically:

- `select_problem` is restricted to the acting agent's coach assignment and
  excludes the already-active problem.
- `direct_message` is available to multi-agent strategic teams, with the
  recipient enum restricted to actual teammates other than the sender. The
  recipient receives it in the `direct_messages` inbox of their next prompt;
  `speak` remains the public broadcast channel.
- `review_answer` is exposed only for eligible non-author versions routed to
  that reviewer.
- Strategic programming removes `request_review`; authors must report a
  sample-AC run with `speak` before another agent reviews the exact version.
- Strategic `submit_code` appears only after local evidence and independent
  approval, and submits the frozen reviewed source without asking the model to
  reproduce it.
- `finish_contest` is hidden while required tasks remain incomplete.
- Answer-sheet `submit` is gated until required drafts and reviews exist,
  except for the explicit deadline fallback.

`vanilla_team` has no Coach, rule card, private deliberation, review gate, or
cross-problem strategic summary. It makes one model call and executes at most
one public action per scheduled agent.

`strategic_team` adds bounded contest memory, immutable answer versions,
different-agent review, evidence-bound code review, stalled-task switching,
three-non-AC cooldown, and later revisits. These are experimental system
policies, not official ARML or ICPC rules.

Programming tasks also expose `verify(focus?)`. It returns the latest code,
version chain, visible run/submission history, and review history so the acting
Agent can re-check its work on the next step. `verify` is self-verification
context only and never satisfies the independent-review gate.

Every run writes `contest_session.json` and `contest_checkpoint.json`. The
result includes the frozen action set, shared budget ledger, task timeline,
latest valid per-task submissions, answer/review versions, visibility-tagged
memory, switch reasons, TaskUtility, AAR, AB, review coverage, attempts-to-AC,
stalled turns, and switch count. Live runs evaluate Communication, Planning,
and coordination score (CS) by default; `--no-judge-collab` disables this.
`--judge-cce` adds CCE for live runs.

Multi-problem non-programming contests use answer-sheet semantics: `work`
updates a per-problem draft, the strategic variant reviews every draft and then
the complete sheet, and one argument-free `submit` atomically submits all latest
drafts and terminates the contest. Individual math problems are never submitted
mid-contest. Normally `submit` remains gated on review completion. On the final
available strategic action, a deadline fallback exposes only `submit` and hands
in all existing latest drafts, leaving missing tasks blank, so unfinished review
cannot turn partial credit into an automatic zero. Programming contests retain
per-problem `submit_code` semantics.

Every answer version also has shared review history keyed by its immutable
`version_hash`. Agents can see the answer author, review decisions and comments,
and whether each review became stale after a revision. The complete untruncated
history is persisted as `shared_review_history` in `contest_session.json`.

The team keeps one global active-task cursor, but it is not an ownership lock.
Before a strategic live run, the pre-contest coach receives the task set, rules,
team size, and shared budget, then produces a persisted structured operational
brief with work assignments, review routes, task order, switch conditions, and
the final checklist. The coach may assign one problem per agent, group several
agents on one problem, or focus the whole team together. Each assignment is
copied into that agent's private memory. Before each call, the scheduler moves
the shared active-task cursor to the agent's next assigned work or review target;
task actions outside the assignment are rejected. The coach call consumes the
same API/token budget and is not repeated after checkpoint resume.
`request_review` creates a shared request when that action is enabled, while a
different agent uses `review_answer` with the exact problem and version hash.

Use `--resume` with the same explicit `--output` directory to resume its
checkpoint. A checkpoint is scoped to its session and system variant, so
vanilla and strategic memory cannot be reused across matched runs.
