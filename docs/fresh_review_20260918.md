# Fresh review: provider failures, ordinary actions and resume accounting

Status: **all four findings below are repaired** by the subsequent
[action, provider and checkpoint repairs](call_contract_repairs_20260918.md).
The findings and numbers below describe the source at review time. The original
failure artifacts remain unchanged; follow-up verification is stored separately
in `results/call_contract_repairs_20260918/`.

At review time, the preceding repair had fixed its four reproduced paths but
had not established complete correctness of every provider and ordinary-action
path. No production source or historical run was changed during the review.
Source and normal-test hashes then matched
`results/code_repairs_20260918/completion.json`.

## P1 — Ordinary-action usage still differs from non-action usage

`src/contest_engine.py:1258-1277` forces reported API usage to at least one and
tries to charge extra calls through `consume_budget`. When actual reported usage
already exceeds the configured limit, that charge raises before recording any
extra calls or generated tokens. `src/contest_engine.py:1306-1314` separately
clamps generated tokens to the remaining allowance. Those paths do not use the
new non-action accounting behavior.

Verified production-engine probes:

| Trigger | Actual / reported usage | Saved contest budget |
|---|---|---|
| Adapter ignores two-call / 100-token cap | 3 calls, 4,096 output tokens | 1 call, 0 tokens |
| Output-only overrun | 1 call, 4,096 output tokens | 1 call, 100 tokens |
| Explicit local zero-call failure | 0 calls, 0 tokens | 1 call, 0 tokens |
| Compliant call exhausts output budget; two turns follow | 1 model call total | 3 API calls |

The last case needs no noncompliant adapter: `request_single_action` correctly
skips requests after the output allowance reaches zero, but the engine keeps its
one-call reservation for each skipped action. The overrun fixtures establish
honest-accounting failures, not a claim that client code can undo provider spend.
These errors affect both budget enforcement and comparisons of baseline cost.

## P1 — An interrupted ordinary-action retry loses usage and checkpoint progress

`src/action_transport.py:49` invokes the provider without preserving prior retry
usage if a later request raises. The exception reaches
`src/contest_engine.py:1247` before its accounting and checkpoint update.

The minimized two-turn engine probe makes one successful call (5 output tokens),
then a length-stopped call (7 tokens), then a failing retry. Actual attempts are
three and known generated tokens are twelve. In-memory budget is two calls / five
tokens; the latest checkpoint remains one call / five tokens. The propagated
exception carries only the final failed attempt's usage. Resuming from that
checkpoint therefore cannot retain the spent retry allowance.

Unknown tokens from the failed network request must remain unknown. That does
not justify losing the preceding successful generation's seven known tokens.

## P1 — OpenAI Responses discards incomplete status

`src/llm.py:256-269` copies token usage and tool calls but does not preserve or
normalize `status` / `incomplete_details`. The installed OpenAI SDK explicitly
defines `status="incomplete"` and `incomplete_details.reason="max_output_tokens"`.
The non-action and action controllers inspect normalized finish/error metadata,
which is absent from this adapter response.

An SDK-shaped offline response with those fields and unfinished text is accepted
as a completed private thought. A separate fixture with a valid function-call
item in an overall incomplete response is returned by the single-action
validator instead of being rejected for truncation. This is a reproduced missing
guard, not a measurement of how often a live account emits either response.
It does not demonstrate a regression in Tinker's separate continuation adapter.

## P2 — Malformed native tool arguments abort the run and drop returned usage

`src/llm.py:205-207` raises while parsing invalid argument JSON. The OpenAI
Responses adapter calls that parser before constructing `LLMResponse`, with no
usage-preserving error conversion at `src/llm.py:268`.

One completed mock response reports twenty output tokens and invalid function
arguments. The actual contest engine raises `ValueError: Function-call arguments
are not valid JSON.`; no completed run result is returned, its token budget stays
zero, and the exception has no usage. The invalid action is not executed, but
the exception boundary is inconsistent with the already repaired public REST
adapters' recorded failed-response behavior.

## Data, installation and entrypoint checks

The clean validation environment satisfies every declared runtime requirement;
`pip check` reports no broken requirements. README local links all resolve and
the README remains English. These checks cover the existing installed environment,
not a new installation on an arbitrary machine.

The current main catalog contains 39 tracks / 899 records; mini contains 39 tracks /
109 records / 89 execution sessions. Main status counts are 441 `ready`, 300
`ready_with_limitations`, and 158 `remote_judge_ready`. Mini has 54, 44, and 11
respectively. IIOT, CCDC and CFA are among the rubric-evaluated tracks with explicit
limitations; a readiness label is not proof of official execution or score equivalence.

Fresh mini preflight passes all 479 asset checks and the dependency hash audit,
with no parent-data reads. Of 445 configurations, 440 prepare and five ICPC
configurations remain `environment_pending` because another contest runner is
active. `all_jobs_environment_ready` is false. No new data-integrity failure was
reproduced in these checks. This is not a page-by-page revalidation of all original
formulas, diagrams, official rules or evaluator assumptions.

## Historical reproduction and repair guidance

```sh
python results/call_contract_repairs_20260918/recheck.py
python -m pytest results/fresh_review_20260918/test_invariants.py -q --tb=short
```

At review time, the invariant command produced **seven expected failures**,
covering the four findings above. It now passes on the repaired source. These
review tests are kept outside the normal `tests/` suite; their original failed
output remains in `results/fresh_review_20260918/repros.xml`.
Detailed usage, checkpoints, current inventory and mini preflight are saved in
the same directory. All provider responses are local fixtures; paid model calls
and remote submissions are zero.

The review recommended repairing ordinary-action accounting and failed-retry
checkpoints together first, then normalizing native response status and preserving
malformed-response usage. It called for an end-to-end matrix over successful,
incomplete, malformed, failed, zero-call
and over-budget responses across action, non-action and judge paths. Separate
accounting implementations had allowed the same class of bug to survive at
another entrypoint even after one path has passed its regression tests.

The earlier **1,297 tests and 1,342 subtests passed** on the same production source.
Those results are valid evidence for their covered cases; these new red probes
show why they cannot support a claim that the entire repository is fixed.
