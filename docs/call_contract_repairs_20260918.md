# Action, provider and checkpoint repairs

The four findings in the [fresh review](fresh_review_20260918.md) are repaired.
Subsequent live Qwen runs exposed two additional task-focus and body-repair
failures, documented with their fixes and live probes in the
[centralized and OTC follow-up](centralized_transport_repair_20260918.md).
The changes also cover the corresponding non-action and judge paths. Existing
action definitions, baseline behavior, model selection and configured output
defaults are preserved. Historical experiments are unchanged.

The validated workspace also includes concurrent Tinker template/final-channel
checks and finalized-result identity handling. These changes were retained and
included in the final source-hash verification; the Tinker model-policy file is
not claimed to be byte-identical to the initial snapshot. Reading a fully
completed result can tolerate source-only drift, while execution and pending
evaluation resume still require a matching source identity. Action definitions,
baseline configuration and provider defaults are checked separately for exact
preservation.

## Shared accounting and remaining budgets

Ordinary actions, Coach and private thinking use the same usage normalization
and charging helpers. The engine records already-spent API calls and generated
output in full, including retries. A local zero-call failure refunds the reserved
call. An exhausted output budget does not create phantom API calls. A reported
overrun stops subsequent contestant requests without clipping the recorded cost.

For the original two-call / 100-token overrun fixture, the saved budget now
records the reported three calls and 4,096 tokens. A compliant call consuming
all 100 tokens remains one recorded call when later turns have no output budget.
This cannot undo provider spend or measure tokens a failed request never reports.
Unreported usage stays explicitly unknown; legacy text-only callbacks retain
their visible-text estimates.

`max_transport_output_tokens` is the total remaining allowance across attempts.
It must not become the per-call generation limit. Built-in adapters cap each
request using the configured output limit and the remaining total. Explicit
caller overrides supported by an existing adapter retain their prior behavior.
The output allowance includes reported thinking tokens and excludes input tokens.

## Failure checkpoints and resume

The action transport carries earlier attempts' known usage through a later
exception. The engine charges it before saving the pending seat and propagating
the error. The original three-attempt fixture now saves three calls and twelve
known output tokens, including the seven-token generation before the failed retry.
Resuming uses only the remaining allowance; an exhausted allowance starts no call.

Coach, centralized leader planning and private thinking save failure checkpoints
too. A resumed private thought does not rerun the completed Coach plan. Legacy
text callbacks use this failure boundary as well. Returned incomplete thoughts
remain rejected; network failures are distinguished from completed responses so
they remain resumable. OpenAgents gateway failures retain every bounded 504
attempt, including when all attempts fail.

Tinker's internal staged sampler follows the same zero-call and unknown-usage
rules. A failed sample preserves accumulated usage and the private, unexecuted
draft before the engine saves its checkpoint. Selection tokens are continued
only for an identical observation and tool schema; a changed observation must
revalidate selection, with the old draft still explicitly unexecuted.

Use the normal resume command with the same identity, output directory and
budgets. These checks concern interruptions under the repaired source. They do
not authorize mixing an older source identity into a new experiment.

## Completion and function-call validation

OpenAI Responses and Perplexity preserve overall response status. An incomplete
response with `max_output_tokens` becomes a length failure even if a valid
function-call item or valid JSON appears in its output. Rejected or incomplete
responses cannot supply an executed action, a completed private thought, page
evidence, or a final score.

Malformed native function arguments become failed responses with their returned
usage intact. No partial call executes. The existing bounded action and judge
recovery policies remain in control. Local attachment preparation errors report
zero model calls; network failures report known attempts and unknown token usage.

## Verification

New offline tests exercise the real adapters with deterministic wire responses:
OpenAI Responses, Perplexity, GLM Chat Completions, OpenAgents, VectorEngine,
generic Chat Completions, DeepSeek, Anthropic and Gemini. They cross successful,
length-limited, refused and malformed responses with action, non-action and
structured-judge consumers. Existing Tinker tests cover staged actions, exact
continuation, failed sampling and checkpointed drafts.

Additional engine tests exercise full-cost overruns, zero calls, failed action
retries, exhausted-budget resume, Coach/leader/private-thought resume, local
attachment errors, gateway attempt counts, and truncated page evidence. The
original seven fresh-review invariants are replayed without replacing the
historical failure artifacts.

The first full regression exposed two old tokenizer fixtures that treated
decoding as a queue with one item per API call. Continuation can decode both
the new sample and accumulated tokens. The fixture now decodes deterministically;
the assertions still require correct call/token totals and rejection of a
length-stopped action. Its original failed run is retained as `suite_first.*`.
Six additional Tinker failure-accounting probes were recorded red before the
internal sampler repair and incorporated into the normal regression suite.

Run from the repository root:

```sh
python -m pytest tests -q
python results/call_contract_repairs_20260918/recheck.py
python scripts/verify_mini_dataset.py --output results/mini_preflight.json
```

Validation artifacts are stored in `results/call_contract_repairs_20260918/`.
The final frozen-source regression passed **1,452 tests and 1,345 subtests**, with
zero failures, errors or skips. All seven original review invariants pass.
Source hashes remained unchanged during both the full suite and mini preflight,
and their recorded source hashes match the final files.

Mini preflight passed all **479 asset checks** with no parent-data reads or
dependency hash issues. Across 39 tracks and 89 sessions, **440 of 445** baseline
configurations prepared. The five ICPC configurations remain
`environment_pending` because another contest runner is active;
`all_jobs_environment_ready` is false. No new paid model experiment was started.

Exact comparisons preserve 14 action, baseline, provider-default and artifact
contract files. The English README and updated documents have no broken local
links across 24 checked links. `pip check` reports no broken requirements.
The final record is `results/call_contract_repairs_20260918/completion.json`;
the first failed and intermediate suite logs remain available separately.

Offline regression and data preparation do not establish successful live
completion of every competition, live provider access, model quality, or official
score equivalence. Runs started before these changes do not validate this source.
