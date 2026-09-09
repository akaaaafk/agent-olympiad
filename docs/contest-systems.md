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

`vanilla_team` has no Coach, private deliberation, review workflow, review gate,
or cross-problem strategic summary. It makes one model call and executes at most
one public action per scheduled agent. `request_review` and `review_answer` are
hidden from this baseline. After a new answer-sheet draft is recorded, contest
control advances the shared cursor to the first unseen task. The common stall
guard also moves either variant away from an unchanged task; vanilla's automatic
moves are reported separately as `baseline_mechanical_switches`.

Both variants receive the same contest rules and competition-specific base tool
packs. Actions invalid under the contest's submission contract are hidden for
both variants, including incomplete answer-sheet submissions.

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
mid-contest. Strategic `submit` remains gated on review completion. At session
end, the environment collects pending non-programming drafts for
**both** variants, leaving missing tasks blank. The last model action remains
available for solving or revising a draft; deadline collection consumes no extra
model call. Programming contests retain per-problem `submit_code` semantics.

Results record `protocol_version=contest_session_v3` and
`deadline_policy=collect_pending_non_programming_drafts`. Re-run old experiments
from fresh output directories when comparing this protocol; do not mix old
checkpoints or scores with the new submission policy.

### OTC programming workflow v2 (2026-09-08)

Reviewed strategic programming sessions additionally record
`programming_workflow_version=programming_workflow_v2`. Math, short-answer,
Vanilla, and explicitly review-disabled sessions retain their existing answer
semantics. Use fresh output directories for v2 comparisons; old ICPC runs
without this marker used the prior programming workflow.

In this programming workflow, `work` records discussion/analysis in memory and
never replaces candidate source. `execute_code` records complete source and
its sample evidence. After sample AC, the scheduler prioritizes the author
until the exact version is reported with `speak`, then routes independent
review and frozen-source submission. A review rejection still permits an
official submission; reviewers do not decide the official verdict.

`src/programming_workflow.py` tracks unproductive work actions per agent/task.
After `stall_turns` such actions (default 3), the task moves behind the worker's
other assigned tasks and remains eligible for later revisiting. Fresh failing
code versions and ordinary active-cursor changes do not reset this budget.
A newly sample-passing candidate, a local-run report, or a valid formal
submission resets it. Report/review/submission-ready code retains pipeline
priority. Infrastructure errors such as `JUDGE_ERROR` are not sample failures.
The counter and rotation order are persisted in memory and restored on resume.

`diagnostics.programming_repair_yields` counts these repair-budget yields
separately from the legacy round-based `stalled_turns` metric. Local sample
failures never increment the official non-AC submission counter or add penalty
minutes. Ordinary progress-accounting events are excluded from the limited
working-memory projection so they do not crowd out source and judge feedback.

An explicit `split_parts` request now fails if numbered prompts cannot be
matched to the requested part IDs. Appended numbered answer sections are
removed before either packet or split prompts are delivered. Deterministic
grading reports unavailable tasks separately, excludes them from score and
utility denominators, and records `evaluation_coverage`. A completely ungradable
session has `task_utility=null`, not an accuracy of zero.

Agent Python, local Python judging, and sample-output diagnostics use Docker
isolation. Only the submitted source is mounted; test input is streamed on stdin
and expected answers remain in the host evaluator. Containers have no network,
host environment, repository mount, or write access to the image. Time, memory,
process, and output limits apply. There is no automatic host fallback when
Docker is unavailable. Install the pinned `PYTHON_IMAGE` from
`src/isolated_python.py` before running code-enabled contests. The judge's
`trusted_python=True` option is exclusively for explicitly trusted fixtures;
benchmark adapters do not use it.

`--max-total-tokens` continues to mean a shared **output-token** budget, as its
CLI help states. It does not match total input-plus-output cost across systems.

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

### Optional programming deadline submission

`--programming-deadline-submit` (default: off) enables controller-side code
collection after the last normal turn, or earlier budget exhaustion. It uses
no additional model calls or turns. For each unsolved programming task, it
selects one recorded nonempty source not previously attempted officially:
sample-AC candidates first, independently approved candidates as a tiebreaker,
then recency. This preserves a sample-AC candidate over a later sample failure.
An earlier WA/TLE does not exclude a genuinely new candidate. Analysis notes
are not code; blank tasks, accepted tasks, and active cooldowns are skipped.
Code identity ignores version-parent hashes, fences and outer whitespace, so
recreating an old failed source does not authorize another submission. Pending
or otherwise uncertain normal attempts also exclude their source; explicitly
local-only `SAMPLE_*` rejections do not. Sample AC is not proof of correctness.
Normal actions retain their sample and independent-review gates. Only this
controller-only deadline path waives those gates; official WA still incurs the
normal penalty. Pending, human-verification, sample-only, and failed responses
are not official acceptance.

This option does not alter mathematics or short-answer collection, and is
available to either variant as an explicit environment policy. Use the same
setting in matched comparisons. Results record
`deadline_policy=collect_pending_non_programming_drafts_and_unsubmitted_candidates_v2`,
`programming_deadline` before/after task lists, source hashes and judge results
in `programming_deadline_*` memory events, and separate deadline attempt/AC
counts. Write fresh experiment outputs: finalized checkpoints cannot be used
to retroactively enable submissions. Intent is checkpointed before each remote
call; interrupted or uncertain attempts are not automatically retried on resume
because the judge may already have received the code.

Regression coverage: `tests/test_programming_deadline.py`. This is a submission
safety net, not a remedy for agents failing to generate or repair source.

### OTC programming workflow v3 (2026-09-08)

Reviewed strategic programming runs now record
`programming_workflow_version=programming_workflow_v3`. Use fresh experiment
outputs instead of appending to v2 runs. Mathematics, short-answer, Vanilla,
and explicitly review-disabled flows retain their action rules.

- Ordinary sample/official-WA repair candidates and uncoded tasks follow the
  same worker rotation order. Uncoded tasks no longer override that order and
  indefinitely starve repairs. Ready sample-AC reporting, review, and submission
  retain their existing priority. The three-unproductive-action rotation still
  provides time for other assigned tasks.
- The active programming source is pinned in full, with its exact hash,
  matching sample report, reviews, and latest valid official submission.
  This block is outside the eight-event / 6,000-character general-memory
  projection. Shared history previews remain bounded.
- During implementation or failed-source repair, two own-task actions without
  a code execution/progress exhaust the analysis allowance. The next action on
  that task exposes only `execute_code` and explicitly asks for a complete
  stdin/stdout solver. Notes, rest, messages, verification, and manual switches
  cannot indefinitely replace source production. Counters are worker/task-local,
  persist across automatic rotation and checkpoint resume, and reset on a
  non-infrastructure code attempt (even sample WA) or real workflow progress.
  Empty source is rejected before execution. Sample-AC reporting, independent
  review, and submission are not subject to this source-production gate.
- `diagnostics.programming_source_required_actions` counts forced-source
  prompts; their controller events do not consume general working-memory slots.

These are execution-policy guarantees, not correctness guarantees. Nonempty
placeholder programs, hardcoded sample harnesses, and algorithmic mistakes can
still pass syntax checks or fail hidden tests. The independent-review override
and optional deadline submission policy have not been changed in v3.

Regression coverage: `tests/test_programming_productivity.py`, plus the existing
programming pipeline, family separation, and deadline-submission tests.

### Programming gap repairs v4 (2026-09-08)

Reviewed strategic programming runs now record `programming_workflow_v4`.
Use fresh outputs instead of resuming old experiments across this policy change.
Only the requested checker, duplicate-execution and deadline-selection gaps
are changed; task-wide budget limits and counterexample tools are not added.

- The ICPC 2012 Infiltration legacy sample adapter uses a semantic checker:
  optimal cardinality from the trusted answer, unique in-range cells, correct
  case labels, and direct domination of every input vertex. It accepts different
  valid optimal sets and arbitrary identifier order, not merely reordered text.
  Other legacy problems retain token checking; configured official packages
  keep their own checkers. This public judging correction applies equally to
  both variants, not to mathematics or short-answer grading.
- Reviewed OTC programming reuses a known failed result when source, language,
  task metadata, local samples and judge-code identity match. The saved public
  sample results support reuse across agents and checkpoint restoration without
  re-executing code or creating a version. It does not overwrite the active
  source, grant evidence, or reset source/progress counters. Failures of the
  infrastructure, unknown results and successful runs are not cached. Bundled
  judges with untracked dependencies opt out; source/test changes cause real
  execution. Vanilla, non-programming and review-disabled flows do not receive
  this strategic deduplication policy. Injected custom executors should expose
  `execution_context_key(task)` (return `None` to opt out); otherwise their
  benchmark metadata is assumed stable for the run.
- Results separately count `programming_duplicate_executions_avoided`; cached
  execute attempts still use their ordinary agent turn and model budget. They
  save sandbox work and make the required repair explicit, not refund tokens.
- The explicit deadline policy above records both the selected historical hash
  and the final submitted hash, source identity and selection reason. It keeps
  one checkpointed deadline intent per task and never retries an interrupted
  deadline call. Both variants receive this policy only when explicitly enabled.

Regression coverage: `tests/test_programming_gap_repairs.py` and the existing
deadline, productivity, contest-family and variant suites.
