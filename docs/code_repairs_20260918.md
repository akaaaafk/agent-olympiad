# Budget and paginated judge repairs

The four findings in the [follow-up review](code_review_20260918.md) are repaired.
The subsequent [fresh review](fresh_review_20260918.md) found additional
ordinary-action and native-provider error paths, now addressed in the
[action, provider and checkpoint repairs](call_contract_repairs_20260918.md).
Neither repair is an all-code correctness certification.
Existing actions, baseline definitions, model selection and configured context /
output defaults are preserved. Historical experiments are unchanged. All new
validation in `results/code_repairs_20260918/` uses offline model fixtures.

## 1. Non-action budgets and usage

Coach, private-think and centralized leader planning now use a structured request
behind the existing two-string query interface. The native contest runner and
artifact runner pass remaining API attempts and generated-output allowances
before sampling. Retries and continuation samples share those allowances.
Provider-reported usage is retained, including failures, and recorded in private
`model_usage` runtime events. Incomplete thoughts are charged and stop the run.

Perplexity's structured adapter now bounds its internal retries and preserves
attempt counts; OpenAI Responses disables hidden SDK retries. Tinker distinguishes
local prompt preparation from actual sampling and retains failed continuation
attempts and previously generated tokens. Unknown failed-request token usage is
marked as unknown rather than presented as measured zero usage.

The enforceable client contract has a limit: an injected adapter can ignore its
requested cap. If it reports an overrun, the engine records the full actual usage
and stops subsequent contestant calls. It cannot undo a completed request. The
audit's deliberately noncompliant fixture now receives limits of two calls and
100 output tokens, reports three calls and 4,096 tokens, and is stopped after
that one adapter invocation. The saved budget truthfully records three / 4,096.
A compliant fixture completes within two / 100. The original audit test that
demanded an ignoring mock spend less than its own fixed response was not a valid
post-repair oracle; current tests check both request limits and honest accounting.

Custom legacy callbacks returning only text keep their existing estimated
visible-text accounting. Accurate accounting requires the structured interface;
see [the Python adapter contract](public_model_interfaces.md#non-action-query-adapters).
The output-token budget remains separate from input tokens and billing totals.

## 2. Mathematical evidence JSON

Page evidence now uses the existing `load_judge_json` parser. It repairs only
backslash escapes rejected by the JSON decoder, such as an unescaped `\sqrt`.
Valid JSON escapes are unchanged. Missing structure, empty or oversized evidence,
and unreadable pages still fail validation; no score is fabricated.

## 3. Final-format retry cache

Structured judge retries identify the exact host-generated formatting-feedback
span. Page-evidence collection and cache keys omit only that verified span,
retaining the original rubric and appended rule/reference context. The final
judge still receives the feedback. A wrapper that changes the span's location
causes ordinary cache invalidation instead of stripping unverified text.

The three-page reproduction now makes two evidence calls and two final calls,
instead of four evidence calls and two final calls. Document bytes, page scope,
rubric, rules, system instructions and judge namespace changes still invalidate
evidence. The evidence protocol and its compression limitation are unchanged.

## 4. Zero-call and failed-call accounting

The outer evaluation meter and inner pagination meter use the same usage
normalizer. An explicit zero-call result or failure stays zero. Local PDF range
and cache-checksum failures before sampling record zero API calls. A failed
network request with no usage records one attempt with unknown token usage.
Reported multi-attempt failure usage survives both wrappers without duplication.

## Verification

Run from the repository root:

```sh
python -m pytest tests -q
python results/code_repairs_20260918/recheck.py
python scripts/verify_mini_dataset.py --output results/mini_preflight.json
```

Current regressions cover native Tinker continuation and failure accounting,
artifact Coach/private-think/leader budgets, overrun rejection, mathematical
escapes, format retries, real-input invalidation, and nested zero-call / failed-call
meters. The four original probes pass their corrected current invariants. The
original review outputs are preserved separately.

The mini data check passed all 479 assets without parent-data reads. It checked
445 configurations across 89 sessions, five baselines and 39 tracks: 440 prepared,
with the five ICPC configurations marked `environment_pending` because a separate
GLM-5.3 ARML 2012 contest runner was active. Accordingly,
`all_jobs_environment_ready` is false; no running experiment was stopped.

The full suite passed **1,297 tests and 1,342 subtests**, with zero failures,
errors or skips. Source hashes stayed unchanged during the suite and preflight,
and the final readback matched both. Byte comparisons verified that the action
registry, baseline configuration, artifact contract and Tinker model policy were
unchanged. The mini dependency hash audit found no issues.

Full-suite output and source readback are recorded in
`results/code_repairs_20260918/suite_run.json` and `completion.json`.
Offline tests and preparation do not prove model quality, official
score equivalence, or successful live completion of every competition. Runs
started before this repair are not validation of the new code.
