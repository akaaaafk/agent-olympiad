# Appendix — The 78 Actions: Purpose and Classification (2026-09-14)

Companion to the [final pipeline overview](final-pipeline-20260914.md).
This is the dated action-set-10 snapshot. The current source registry is action
set 13 with 89 actions; see the [workspace sync report](workspace_sync_20260916.md).
Source of truth: `src/tool_registry.py` + `src/action_modules/`
(`ACTION_SET_VERSION = 10`, `ACTION_MODULE_VERSION = 3`). Every table below is
generated from the live registry; the wire accepts these canonical names only.

## How to read this appendix

Each action is classified along three independent axes:

- **Module** (ownership; the ablation switch): `common` (24) — every baseline;
  `memory` (3) — only baselines with `memory_actions=True` (i.e. `otc`, not
  `vallina_otc`); `task_specific` (51) — bound to one competition each. The
  `coach` module owns no contestant actions (the Coach only speaks at turn 0).
- **Pack** (functional grouping used for permission resolution): `common`,
  `deliberation`, `math`, `programming`, `research`, `artifacts`, `resources`,
  `contest_preparation`, `contest_flow`.
- **Tool or not**: tools are contest *instruments* (calculator, sandbox,
  search, preparation checkers, physical resources) charged against the tool
  budget and gated by the rule card's `allowed_tools`. Non-tools are the
  contestant's *desk*: talking, drafting, reviewing, submitting.

**Visibility** says who sees the action's effect: `private` (only the actor),
`team` (all teammates), `contest` (changes shared contest state, e.g. the
problem board). Arguments marked `?` are optional. All actions run on both
runtimes except the five `contest_flow` actions, which need the stateful
contest session.

Counts: common 24 + memory 3 + task-specific 51 = **78**.

---

## Plain-language guide: what every action is for

Think of the 78 actions as **buttons on a contestant's desk**. Each seat turn,
the agent usually takes **one ordinary action** — solve, talk, review, or
submit. The names below are the only buttons the wire accepts. Some are
universal; some are competition-specific tools.

### One-line summary

An action is a typed verb the model may call. Common actions are the shared
desk; memory actions are optional notes; task-specific actions are instruments
or formats owned by one contest.

### 1. Solving (the buttons you use most)

- **`work`** — write down a durable answer draft (team-visible, versioned).
- **`select_problem` / `skip_problem`** — claim a problem / put it down.
- **`inspect_problem`** — read the statement and history without changing state.
- **`triage_problem`** — set team priority, or mark a problem hopeless for now.

### 2. Talking

- **`speak`** — broadcast to the whole team.
- **`direct_message`** — private message to one teammate or a named sub-group.

### 3. Peer review and hand-in

- **`request_review`** — ask a teammate to check this draft.
- **`review_answer`** — approve or reject another agent's exact version.
- **`submit`** — hand in a final answer for grading.
- **`submit_code`** — hand in programming source to a real judge.
- **`finish_contest`** — end early once every task has a valid submission.
- **`rest`** — pass this turn and do nothing.

### 4. Rules and budget

- **`check_budget`** — how many turns, tokens, and minutes remain.
- **`query_rules`** — show the contest rules visible to this role.

### 5. Structured meeting protocol (rule-card only)

Like a short meeting agenda:

- **`propose`** — open a numbered proposal.
- **`challenge`** — object to someone else's proposal.
- **`provide_evidence`** — attach a check or counterexample.
- **`revise`** — author replaces their own open claim.
- **`decide`** — decision maker accepts, rejects, or defers.

### 6. Generic tools (calculator, sandbox, search, PDF)

- **`use_calculator`** — evaluate an expression.
- **`execute_code`** — run code in the contest sandbox.
- **`web_search`** — search permitted web resources.
- **`render_pdf`** — render a document/slide source to PDF + page previews.

### 7. Memory (`otc` only; `vallina_otc` turns these off)

- **`remember`** — store a private note.
- **`recall`** — keyword-search your own and shared notes.
- **`share_note`** — publish one private note to the team.

These three are **zero-turn auxiliaries**: they do not spend the seat's one
ordinary action, but they still cost API calls and tokens, and each seat turn
allows at most **3** memory calls. Results come back in the **same** turn
before the ordinary action.

### 8. Leader only (`centralized`)

- **`assign_problem`** — the leader replaces a teammate's enforced work list.

### 9. Competition-specific tools (most of the remaining surface)

Two families, plus a few special cases:

- **`check_*`** — check whether a supplied structure looks complete (proof
  dependencies, units, I/O cases, authority tables, …). **Never grades
  correctness** and never reveals gold answers.
- **`prepare_*`** — assemble a format-correct deliverable record (answer
  sheets, case packets, CTF flags, modeling outlines, …). The agent still
  records the candidate with `work` and hands it in through the normal submit
  path.
- **`read_lab_equipment` / `read_star_chart`** — read declared lab or astronomy
  resources.
- Science Bowl flow: **`buzz`**, **`answer_tossup`**, **`answer_bonus`**.
- HMMT Guts flow: **`collect_next_set`**, **`submit_set`**.

Each competition-bound tool is exported **only** to its owning contest.

### How to map the jargon

| Everyday meaning | Technical label |
| --- | --- |
| Buttons everyone has | module `common` (~24) |
| The note-taking kit | module `memory` (3; ablation switch) |
| Contest-owned extras | module `task_specific` (~51) |
| Real instruments | tools: calculator, code, search, PDF, `check_*`, `prepare_*` |
| Desk behavior | talk, draft, review, submit |

### The matched experiment in one sentence

`vallina_otc` and `otc` are the same system except that **`otc` adds
`remember` / `recall` / `share_note` and cross-round memory**; the control
turns that surface off so differences can be attributed to memory.

The detailed tables below list every action with arguments, visibility, and
ownership. For how memory is read and how final answers are assembled, see
§7 and §9 of the [pipeline overview](final-pipeline-20260914.md).

---

## A. Common module (24) — available in every baseline

### A.1 Solving and the problem board (pack `common`)

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `work` | `content`, `problem_id?` | team | Record durable work: a candidate answer or draft for one problem, content-hashed as a new version. `problem_id` targets (and switches to) a specific problem; short-answer tasks end with a separate `Final answer: <value>` line. |
| `select_problem` | `problem_id` | contest | Claim a problem to work on. |
| `skip_problem` | `reason?` | contest | Release the current problem. |
| `inspect_problem` | `problem_id?`, `focus?` | private | Read one problem's statement plus its full version/review/submission history without changing the active problem. Self-verification context only — never counts as an independent review. |
| `triage_problem` | `problem_id`, `priority`, `reason?` | team | Set the team's working priority for a problem or mark it hopeless (hopeless drafts are still submitted at the deadline). |

### A.2 Communication (pack `common`)

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `speak` | `content` | team | Broadcast a message to the whole team. Counted against the rule card's communication budget in `limited` mode. |
| `direct_message` | `recipients`, `content` | private | Private message to one teammate or a named sub-group. Requires the baseline's private channel and team size ≥ 2. Also budget-counted. |

### A.3 Review, submission, and lifecycle (pack `common`)

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `request_review` | `content`, `reviewer?` | team | Ask a teammate to review the current problem; does not approve anything by itself. |
| `review_answer` | `problem_id`, `version_hash?`, `decision`, `content` | team | Independently approve/reject **another agent's** answer version. `version_hash` pins the exact version read; reviews go stale when the draft changes. Under OTC, submission requires a peer approval of the exact submitted hash. |
| `submit` | `answer` | team | Submit a final answer for official evaluation. Gated by review approval and card submitter roles under OTC. |
| `finish_contest` | `reason?` | contest | End the contest early — only once every task has a valid submission and any required final review. Answer-sheet contests end through `submit` instead. |
| `rest` | `reason?` | private | Pass the turn. |

### A.4 Bookkeeping (pack `common`)

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `check_budget` | – | private | Show turns, API calls, tokens, contest clock, penalties, and which problems still have nothing recorded. |
| `query_rules` | – | private | Show the contest rules and rule card as visible to the actor's role (evaluation-only fields are stripped). |

### A.5 Leader (pack `common`; centralized baseline only)

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `assign_problem` | `agent`, `problem_ids`, `reason?` | team | Leader only: replace one teammate's enforced work list; the teammate is scheduled onto the first listed problem from the next round. Disabled under OTC (the card assigns roles, not the leader). |

### A.6 Structured deliberation (pack `deliberation`; rule-card baselines only)

Enabled only when the competition's rule card declares
`deliberation.mode = "structured"`. The engine enforces the protocol: a
minimum number of challenges before any decision, and a card-named decision
maker.

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `propose` | `content`, `problem_id?` | team | Open a numbered proposal — a candidate answer, approach, or split of work — for the team to examine. |
| `challenge` | `proposal_id`, `content` | team | Raise a concrete objection to an open proposal you did not author. |
| `provide_evidence` | `proposal_id`, `content` | team | Attach a check, derivation, or counterexample to an open proposal. |
| `revise` | `proposal_id`, `content` | team | Author only: replace the current claim of your own open proposal. |
| `decide` | `proposal_id`, `outcome`, `reason` | team | Decision maker only: accept, reject, or defer an open proposal. |

### A.7 Generic tools (four packs; gated by the rule card's `allowed_tools`)

| Action | Pack | Arguments | Visibility | What it does |
| --- | --- | --- | --- | --- |
| `use_calculator` | `math` | `expression` | private | Evaluate a mathematical expression. |
| `execute_code` | `programming` | `code`, `language?` | private | Run code in the contest sandbox. For programming tasks the same source is also run on the official sample input; only a sample AC counts as local run evidence. Guarded by the ICPC workstation lease under OTC. |
| `web_search` | `research` | `query` | private | Search permitted web resources. |
| `render_pdf` | `artifacts` | `content` | private | Render complete source to a real PDF plus page previews. In artifact contests this records the current candidate version for independent review; elsewhere it returns a preview only. Granted automatically for document/slides delivery contracts. |

---

## B. Memory module (3) — the `otc` vs `vallina_otc` switch

All three are **zero-turn auxiliaries**: they do not consume the seat's single
typed action or the simulated clock (API/token charges still apply), capped at
**3 memory calls per seat turn**; each result is fed back into the same turn's
prompt before the ordinary action. Every use leaves an event trail in the
ledger: `remember` → private `note` event, `share_note` → public `note_shared`
event (budget-counted), `recall` → private `recall_result` event recording the
query and results, plus a `memory_auxiliary_call` bookkeeping event per call —
so memory activity is fully auditable and visible to the agent's own later
turns (see §7 of the overview).

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `remember` | `content`, `problem_id?` | private | Store a private note outside the visible transcript — an intermediate result, failed approach, uncertainty, or next step, bound to a problem. Not for candidate answers (use `work`) or duplicating visible drafts. |
| `recall` | `query?`, `problem_id?` | private | Search own + team-shared notes. A nonempty query requires whole-keyword matches; an empty query browses recent notes. `problem_id` restricts to one task; omit it for cross-task methods. Ranked by keyword hits and recency, deduplicated. |
| `share_note` | `note_id` | team | Publish one of your stored notes (by its real `note_id`) to the team when its finding, pitfall, or next step is useful and not already public. Counted against the communication budget. |

`vallina_otc` removes exactly these three actions (plus cross-round history in
the strict control); everything else in the system is identical.

---

## C. Task-specific module (51) — competition-bound

### C.1 Programming submission (pack `programming`)

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `submit_code` | `code`, `language?` | team | Submit source code to the real programming evaluator (Kattis/Codeforces via the VJudge gateway). A submission action, not a tool; granted automatically wherever `execute_code` is permitted in a programming contest. Guarded by the workstation lease and duplicate-source rejection. |

### C.2 Physical resources (pack `resources`; explicit capability only)

Never inferred from a contest or task type — a benchmark must declare the
capability *and* the card must permit it.

| Action | Arguments | Visibility | What it does |
| --- | --- | --- | --- |
| `read_lab_equipment` | `resource?` | private | Read declared laboratory equipment data (science practicals). |
| `read_star_chart` | `resource?` | private | Read a declared star-chart resource (astronomy). |

### C.3 Stateful contest flow (pack `contest_flow`; session runtime only)

State-changing actions for quiz/relay formats, available only when the
manifest selects the matching `competition_flow`. Not solver tools.

| Action | Owner | Arguments | What it does |
| --- | --- | --- | --- |
| `buzz` | `science_bowl` | – | Claim the current fully displayed tossup; only the buzzer may answer it. |
| `answer_tossup` | `science_bowl` | `answer` | Give the first and final tossup answer after recognition; empty text passes. |
| `answer_bonus` | `science_bowl` | `answer` | Captain gives the first and final earned bonus answer; empty text passes. |
| `collect_next_set` | `hmmt_guts` | – | Collect the next Guts set after handing in the current one. |
| `submit_set` | `hmmt_guts` | – | Irreversibly hand in every current Guts draft (blank entries score zero). |

### C.4 Competition preparation tools (pack `contest_preparation`, 43)

One tool per competition, permitted **only** for its owning competition — a
forged capability or another contest's card can never export it. All 43 share
the same contract: they check the **structure and supplied evidence** of a
candidate deliverable (never correctness, never hidden answer keys), return
**private** preparation feedback, and the contestant still records the
candidate with `work` and hands it in through the normal submission action.

Two families:

- `check_*` (21): validate an argument/proof/test structure the contestant
  supplies — missing references, circular dependencies, duplicate or
  contradictory entries, unit problems.
- `prepare_*` (22): assemble a format-correct deliverable record — answer
  sheets, case records, flags with evidence, model papers.

| Tool | Competition | Checks / prepares |
| --- | --- | --- |
| `check_arml_power_proofs` | `arml_power` | Numbered proof packet with explicit part dependencies. |
| `check_arml_national_power_proofs` | `arml_national_power` | National Power packet; missing references and circular proof dependencies. |
| `check_bp_speech_order` | `debatebench` | BP transcript order (PM, LO, DPM, DLO, MG, MO, GW, OW); duplicate or misplaced roles. |
| `check_codeforces_io_cases` | `codeforces` | Explicit stdin/stdout edge cases; no execution, no hidden tests. |
| `check_creative_constraint_map` | `odyssey_of_the_mind` | Maps each long-term/spontaneous constraint to a solution element and evidence. |
| `check_eoes_measurements` | `eoes` | Experimental report: quantities, units, uncertainty, data provenance. |
| `check_icpc_io_cases` | `icpc` | Stdin/stdout cases for the shared-workstation workflow; flags contradictory duplicates. Contestant tests, not judge evidence. |
| `check_iiot_io_cases` | `iiot` | Deterministic test cases for the selected language; acquires no workstation. |
| `check_ijso_measurements` | `ijso_practical` | Practical-report measurements with units, uncertainties, sources; no invented readings. |
| `check_ioaa_observations` | `ioaa_group` | Observation table: object, observation, frame/units, material reference. |
| `check_ioai_artifact_manifest` | `ioai_team` | Artifact names, media types, provenance against the year's output contract. |
| `check_jessup_authority_table` | `jessup` | Applicant/Respondent argument map linking propositions to authority and packet facts. |
| `check_linguistic_rule_table` | `iol_team` | Proposed linguistic rules aligned with numbered examples and counterexamples. |
| `check_math_research_dependencies` | `itym` | Research-paper claims, proofs, dependency graph; computational claims need reproducible evidence. |
| `check_physics_answer_units` | `fyziklani` | Numeric answers: values, units, caller's unit requirements; finite numbers. |
| `check_portfolio_weights` | `wharton_investment` | Portfolio weights vs. client constraints; total allocation and duplicate holdings. |
| `check_pumac_proof_packet` | `pumac_power` | Power proofs with earlier-part dependencies. |
| `check_puzzle_extraction` | `mystery_hunt` | Ordered letter extraction from supplied feeder answers and 1-based indices; never queries answer keys. |
| `check_robot_mission_sequence` | `wro` | Mission plan: steps, expected observations, durations vs. a supplied run limit. Hypothetical — no robot runs. |
| `check_vis_authority_table` | `vis_moot` | Claimant/Respondent arbitration argument map with authorities and record references. |
| `check_writing_prompt_allocation` | `wsc_writing` | Exactly three responses, three distinct authors, three distinct prompts. |
| `prepare_appe_case_response` | `ethics_bowl_appe` | Case response, opposing commentary, reply, and answers to judges as separate parts. |
| `prepare_arml_local_sheet` | `arml_local` | Team Round numbered short answers matching the packet's problem IDs. |
| `prepare_arml_team_sheet` | `arml_national_team` | National Team Round answer sheet for the selected packet. |
| `prepare_chemistry_fight_record` | `ichto` | Report, opposition, response, review, experimental evidence as distinct contributions. |
| `prepare_cybench_flag` | `cybench` | Exact recovered flag plus challenge-environment evidence; a formatted candidate is not proof of recovery. |
| `prepare_defense_inject_response` | `ccdc` | Inject response: business request, affected services, actions, verification evidence, rollback. |
| `prepare_equity_research_record` | `cfa_research_challenge` | Investment thesis, valuation assumptions, catalysts, risks, public-source citations. |
| `prepare_event_answer_sheet` | `science_olympiad` | Event answer sheet bound to season, division and event. |
| `prepare_guts_set` | `hmmt_guts` | One November 3-question or February 4-question set; does not unlock later sets. |
| `prepare_history_bowl_answer` | `history_olympiad` | One history answer; no buzzer, opponent, or quarter simulation. |
| `prepare_hmmt_team_packet` | `hmmt_team` | November short answers vs. February proofs, per the task's season. |
| `prepare_icm_model_record` | `icm` | Interdisciplinary model record: objectives, model, validation, tradeoffs, disclosures. |
| `prepare_ieo_case_recommendation` | `ieo_business_case` | Business case: alternatives, recommendation, economic evidence, implementation, risks. |
| `prepare_ma_case_record` | `gcch_harvard` | M&A pitch book: target fit, valuation, financing, synergies, integration risks. |
| `prepare_mcm_model_record` | `mcm` | Modeling paper outline: assumptions, variables, model, validation, sensitivity. |
| `prepare_nhseb_case_response` | `ethics_bowl_nhseb` | Presentation, commentary, response, and answers to judges for the selected scope. |
| `prepare_nyu_ctf_flag` | `nyu_ctf_bench` | Flag candidate bound to contestant-provided recovery evidence; reads no host files or writeups. |
| `prepare_physics_research_outline` | `iypt` | Deck outline: theory, evidence, uncertainty, conclusions, citations. |
| `prepare_purple_comet_answers` | `purple_comet` | Non-negative integer answers with exact numbering; MS and HS are distinct packets. |
| `prepare_quizbowl_answer` | `qanta` | Concise answerline preserving the contestant's disambiguation. |
| `prepare_science_bowl_answer` | `science_bowl` | Multiple-choice letter + option text, or a concise short answer; formatting only, no buzzing. |
| `prepare_wmtc_team_sheet` | `wmtc` | Team Round answers preserving the packet's level and numbering. |

---

## D. Which baseline sees what

| Surface | single_agent / decentralized | centralized | vallina_otc | otc |
| --- | --- | --- | --- | --- |
| Solving, communication, review, submit (A.1–A.4) | yes (review actions only when a workflow requires them) | yes | yes | yes |
| `assign_problem` (A.5) | – | leader only | – | – |
| Deliberation (A.6) | – | – | card-gated | card-gated |
| Generic tools (A.7) | card/rules allowlist | card/rules allowlist | card allowlist | card allowlist |
| Memory actions (B) | – | – | **–** | **yes** |
| `submit_code`, competition tools (C) | owning competition only | owning competition only | owning competition only | owning competition only |
| `contest_flow` (C.3) | manifest-selected, session runtime only | same | same | same |

Resolution order (`resolve_actions` in `src/tool_registry.py`): always-on
common core → packs implied by competition/task type → rule-card allowlist
(authoritative when present, even if empty) → module switches
(`memory_actions`, deliberation, review workflow) → per-competition tool
ownership → runtime filter. `system_variant` is deliberately ignored by the
resolver, so a baseline's *name* can never fork the action surface — only its
declared feature switches can.
