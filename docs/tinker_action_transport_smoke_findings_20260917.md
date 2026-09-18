# Live smoke: remaining Tinker action transport failures

Historical diagnosis of the earlier smoke. The later transport implementation
is described in [tinker_action_transport.md](tinker_action_transport.md); its
separate live evidence is under `results/tinker_staged_v3_smoke_20260917`.

This supersedes any interpretation that the 2026-09-17 retry-limit fix made
Tinker actions reliable. It fixed a constant-limit retry, not the entire
generation/serialization failure mode.

Evidence root: `results/mini_live_smoke_20260917_1q_v2`.
Model: `Qwen/Qwen3.6-35B-A3B`; provider and judge: Tinker; baseline: single_agent.
Generation limits: 10 turns, 24 API calls, 65536 output-token budget per task.
The full per-competition results are in that directory's `smoke_results.json`,
`smoke_results.tsv`, and `smoke_results.md`. Scores from source review and rubric
review are proxies, not claims of passing official tests or winning events.

## Confirmed observations

- ARML Local 2013 Q9: `-32/3`, 4/4, no action errors. The source-reviewed
  fraction-chain repair reaches live model input and exact-answer evaluation.
- CCDC: 80/100 proxy rubric score; CFA: 65.5/100 proxy score. Both completed
  evaluation without pending stages in these new runs.
- ICPC Uncrossed Knight's Tour: 3 truncation errors, 1 missing `work.content`,
  1 exhausted output-budget error; 22 API calls; 65536 output tokens consumed;
  score 0/1. Increased retry capacity did not eliminate failures.
- IIOT Selection: 2 truncation action errors before a complete C++ submission;
  7 turns, 12 API calls, 42623 tokens; static source-review score 100/100.
  This is evidence of eventual completion, not reliable transport or official
  execution correctness.
- ARML National Power document route: no rendered candidate at deadline,
  hence `unsubmitted`. Do not mislabel this as a judge-only failure or zero score.

## Why OTC can be more expensive

Each emulated action still requires a complete schema-valid JSON object.
Long reasoning or long content can exceed even the doubled cap. The recovery
request currently starts from the task again rather than supplying the previous
unexecuted draft, so it can repeat expensive generation. Ordinary malformed-JSON
retries also consume budget. OTC schedules more model calls across agents;
there are therefore more opportunities for failures and repeated token spending.
This does not prove a higher per-call failure probability, and this smoke is not
a matched single_agent-versus-OTC comparison.

The earlier OTC ARML 2013 session provides an additional independent failure
mode: 22 truncation action errors, 7 rejections because `work` exceeded its
2400-character limit, and 3 missing-argument `review_answer` errors. Raising the
generation token limit does not change the action's character limit. A complete
but oversized argument can still be rejected. These counts come from unique
`memory.events` action-error entries, not text occurrences across nested traces.

## Next repair must address the mechanism

Evaluate a separate bounded draft/serialization stage or draft-aware action
repair, plus incremental artifact writing for long content. Charge all stages
to the same API/token budget, retain role/tool permissions and atomic validation,
and never execute truncated JSON. Do not merely keep increasing token limits or
claim that enabling thinking creates a separate free reasoning budget.

Validate the eventual change against the failed ICPC/IIOT/document paths and a
small OTC run before any claim of readiness for an OTC full batch. No such new
mechanism has been implemented or validated in this smoke.
