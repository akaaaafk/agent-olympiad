# Competition parameter and completion audit

Follow-up, 2026-09-18: [pagination and runtime repairs](pdf_pagination_20260918.md)
address the PDF delivery, IEO phase, and displayed-budget findings below. The two
previous focused test failures also pass on the current code. This audit is
retained as the original evidence; dataset readiness and live-run acceptance
remain separate questions.

**Acceptance status: not cleared for an all-competition run.** The seven findings
in the earlier newcomer inspection were repaired. That result is narrower than
certifying the current code, all rule semantics, or every complete live run.

This audit uses the current mini selection and the configured Tinker model
`Qwen/Qwen3.6-35B-A3B`, across all five baselines. It makes no paid model calls.
Evidence is under `results/competition_parameter_audit_20260917/`.

## Confirmed outstanding findings

1. **The new image delivery cannot fit the complete mini Vis Moot packet.**
   Its 62-page PDF is attached in full by the artifact runner. Actual local Tinker
   rendering assigns 1,961 image tokens per page: the first 34 pages already use
   **66,674 image tokens**, exceeding the adapter's **65,536-token context limit**
   before any instructions, conversation, draft, or output allowance. Preparation
   currently accepts this job because it does not measure the resulting image
   context. This is an input-context failure, not an output-truncation failure.
   Evidence: `check_context.py`, `image_context.json`; relevant code:
   `src/otc_artifact_pipeline.py`, `src/tinker_vision.py`, `src/llm.py`.
   Required repair: provide bounded page access for long task packets, retain the
   complete accessible source, and verify solver and judge request sizes. Raising
   `max_output_tokens` or silently dropping pages is not a repair.

2. **The current contest engine and the declared IEO benchmark phase disagree.**
   At turn 25, the card's `deck_lock` phase bans `web_search`. A reproduction using
   the actual action resolver and mutation dispatcher exposes that tool and calls
   the supplied backend successfully. The backend was mocked, so this check made
   no web request. `PhaseSchedule` is connected to the legacy environment, while
   the current executor creates that environment with `rules_mode="off"` and the
   contest engine does not apply that schedule. The card only defines phases
   through turn 30, although the production budget is 90 turns. Evidence:
   `phase_reproduction.json`; `src/rules/phases.py`, `src/contest_adapters.py`,
   `src/contest_policy.py`, `src/contest_actions.py`.
   **Official-rule clarification, 2026-09-18:** this reproduction proves a
   code/card mismatch, not an official ban on web research. Page 4 of the actual
   mini task, `data/mini_data/raw/business_case/2024.pdf`, explicitly permits
   online/offline materials while solving the case, prohibits outside assistance,
   and freezes slides at the submission deadline. The current
   [official syllabus, section 3.2](https://files.ieo-official.org/IEO_Syllabus.pdf)
   also permits online/offline preparation materials and prohibits changing
   slides after the deadline. Neither cited text establishes the card's blanket
   `web_search`/`execute_code` ban starting at an arbitrary turn number.
   Do not remove preparation-stage web search on that basis. The follow-up must
   reconcile the benchmark phase model with source-backed preparation and
   submission-lock semantics, and label any additional experimental restriction
   explicitly. Runtime permissions were not changed by this verification.

3. **Rule-card budget text still disagrees with resolved runtime settings.**
   **36 of 39** mini tracks have a different `simulation.max_turns` value from the
   production default. The runtime settings guide explicitly says these old
   fields no longer select the budget. However, full card views still carry them
   into Coach and OTC contestant prompts. For example, ARML Local says 9 versus
   runtime 10; IEO says 30 versus runtime 90. Required repair: render one effective
   budget in runtime prompts, retaining historical source information separately.
   This finding does not imply that the runtime itself uses the old turn count.

4. **The main catalog deliberately retains unresolved tasks.** The final captured
   snapshot has 39 tracks and 969 records. All **70 `not_ready` records are Mystery
   Hunt puzzles**, grouped into four blocked sessions; the other 629 registered sessions have no
   registration blocker. Registration is not execution or judge verification.
   The mini selection has 109 records and 89 sessions, with no such blockers.
   Missing or unverified puzzle context must be repaired from source evidence or
   remain excluded from runnable selections; changing readiness labels is not a
   repair. Evidence: `main.json`, `main/registration/registry.json`.
   The shared workspace changed during this audit: the initial snapshot had 977
   records and 90 unresolved puzzles. These counts describe captured versions,
   not an assertion that concurrent data repair has stopped.

5. **The current suite has two failures requiring different follow-up.**
   `test_real_tinker_adapter_budgets_output_from_encoded_input` observes a real
   reporting mismatch: the SDK output cap is correctly reduced to 3,214 tokens,
   but the completion response still reports 8,192. This does not establish an
   actual SDK budget overrun. `test_real_tinker_sampler_caps_tokens_and_preserves_stop_reason`
   still expects JSON assistant-prefix tokens for the unknown model `mock`; the
   new model policy intentionally stops assuming Qwen prefix support for unknown
   models. That fixture needs to distinguish known prefix-capable models from
   unknown models, preserving its cap and stop-reason checks. Neither failure is
   treated as evidence that all new model policies are incorrect.

## What the parameter checks establish

The mini preflight resolves the actual native/artifact entrypoints and records
their run identities. All 445 combinations match the configured roster, turn
budget, deadline turn, collaboration-evaluation flag, OTC review requirement,
memory switch, solver temperature and per-call output limit. This does **not**
exercise all possible requests, phase transitions, model answers, or final judges.
The two reproductions above demonstrate gaps outside those preparation checks.

All multi-agent rosters fall within their rule-card ranges; single-agent runs use
one contestant. Default turns are bounded to 10–90, with 20 tracks using the
90-turn fallback rather than a registered duration. Solver temperature is 0.2.
Output limits default to 8,192 tokens, except ICPC and IIOT at 4,096. No total API
or output-token budget is set by default. The pipeline has a six-hour child-job
timeout, which preserves checkpoints but does not guarantee a completed result.

These are benchmark parameters. The adaptation text explicitly distinguishes
simulated minutes, selected task counts, agent rosters, and scoring limits from
historical human-contest rules. Rubric/proxy tracks such as IIOT, CCDC and CFA must
not be described as reproducing every official execution environment or score.

Actual image-token counts for three other long mini packets were 47,064 for IJSO
(24 pages), 41,800 for PUMaC (22), and 39,900 for Jessup (21). These are image-only
counts, so they do not certify sufficient context after conversation and artifacts
are added.

## Current-source validation

Since the previous repair suite, the shared workspace changed `llm.py`,
`otc_artifact_pipeline.py`, `saved_run_metrics.py`, and `tinker_action.py`, and added
Tinker model-policy, vision, and completion modules. The isolated validation
environment was updated from the current `requirements-dev.txt`, including
`tinker-cookbook==0.5.7`. This audit does not revert those changes or reuse the old
test result as evidence for them.

The current suite command is `python -m pytest tests -q`. Its log, JUnit output,
exit status and source hashes are saved as `suite.log`, `suite.xml`,
`suite_run.json`, and `suite_source_before.json`. Result: **1,211 passed, 2 failed,
1,341 subtests passed**, in 306.51 seconds. No production source changed during
the suite, but `tests/test_mystery_2015_delivery.py` changed concurrently; this is
not a frozen-checkout certification. `pip check` passes after updating the isolated
environment. The refreshed mini parameter preparation is **445/445 prepared**,
with no source changes during that check.

An initial unscoped pytest
invocation accidentally traversed the local validation environment; that
collection failure is preserved in `full_tests.log` and is not counted as a
product test result.

No production code, action definitions, baseline definitions or historical
experiment outputs were changed by this audit. Passing tests do not override the
confirmed context and phase-gating findings above.

## Effective parameters by track

The table below is generated from `mini.json`. Team size is for the four
multi-agent baselines; the single-agent baseline always uses one contestant.
"Fallback" means no duration is registered in `contest_budget.py`.

| Track | Route | Team | Turns | Output/call | Budget basis |
|---|---|---:|---:|---:|---|
| ijso_practical | document | 3 | 36 | 8192 | 180 min registry |
| ieo_business_case | slides | 5 | 90 | 8192 | 1440 min registry |
| iol_team | document | 4 | 48 | 8192 | 240 min registry |
| ioaa_group | document | 5 | 18 | 8192 | 90 min registry |
| arml_power | document | 15 | 12 | 8192 | 60 min registry |
| arml_national_team | native | 15 | 10 | 8192 | 20 min registry |
| arml_national_power | document | 15 | 12 | 8192 | 60 min registry |
| arml_local | native | 6 | 10 | 8192 | 45 min registry |
| wsc_writing | native | 3 | 15 | 8192 | 75 min registry |
| jessup | document | 5 | 90 | 8192 | 43200 min registry |
| iypt | document | 5 | 90 | 8192 | 720 min registry |
| hmmt_team | native | 8 | 12 | 8192 | 60 min registry |
| fyziklani | native | 5 | 36 | 8192 | 180 min registry |
| purple_comet | native | 6 | 18 | 8192 | 90 min registry |
| itym | document | 6 | 90 | 8192 | 720 min registry |
| ethics_bowl_appe | native | 5 | 90 | 8192 | Fallback |
| ethics_bowl_nhseb | native | 5 | 90 | 8192 | Fallback |
| ichto | native | 4 | 90 | 8192 | Fallback |
| pumac_power | document | 8 | 90 | 8192 | Fallback |
| qanta | native | 4 | 90 | 8192 | Fallback |
| science_bowl | native | 4 | 90 | 8192 | Fallback |
| vis_moot | document | 5 | 90 | 8192 | Fallback |
| wmtc | native | 6 | 90 | 8192 | Fallback |
| mcm | document | 3 | 90 | 8192 | 5940 min registry |
| icm | document | 3 | 90 | 8192 | 5940 min registry |
| icpc | native | 3 | 60 | 4096 | 300 min registry |
| iiot | native | 4 | 36 | 4096 | 180 min registry |
| ccdc | native | 8 | 90 | 8192 | Fallback |
| cfa_research_challenge | native | 4 | 90 | 8192 | Fallback |
| cybench | native | 5 | 90 | 8192 | Fallback |
| debatebench | native | 2 | 90 | 8192 | Fallback |
| eoes | native | 3 | 90 | 8192 | Fallback |
| gcch_harvard | slides | 4 | 90 | 8192 | Fallback |
| ioai_team | native | 4 | 90 | 8192 | Fallback |
| mystery_hunt | native | 12 | 90 | 8192 | Fallback |
| nyu_ctf_bench | native | 5 | 90 | 8192 | Fallback |
| odyssey_of_the_mind | native | 7 | 90 | 8192 | Fallback |
| science_olympiad | native | 15 | 90 | 8192 | Fallback |
| wharton_investment | native | 5 | 90 | 8192 | Fallback |
