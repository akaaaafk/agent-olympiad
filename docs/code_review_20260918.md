# Follow-up code review: budget and paginated judging

Status: **all four findings repaired**; see the
[implementation and current validation](code_repairs_20260918.md).
The findings and reproduction results below describe the original reviewed
snapshot and remain as historical evidence. This review covers the recently
changed PDF delivery, shared budget, and evaluator paths; it is not a claim of
exhaustive repository correctness. At review time, production source matched the
preceding green suite's recorded hashes. The review itself changed no production
code or historical experiment and made no paid model requests.

## P1 — Coach and private-think calls lose usage and request limits

`src/otc_artifact_pipeline.py:430-434` creates an LLM request without remaining
API/output-budget metadata and returns only `response.text`. The contest engine
therefore consumes one API call and estimates tokens from visible text instead
of charging provider-reported retries, continuation samples, and output usage.
The Coach and private-think paths share this problem; ordinary action requests
have a separate usage-aware path.

Controlled reproduction: configure two API calls and 100 output tokens. Inject
Coach and private-think responses whose usage totals six calls and 8,192 output
tokens. The saved contest budget records two calls and two tokens, and neither
request contains transport budget limits. These numbers are mock response usage,
not measurements from a paid run. They establish that the live adapter's usage
contract is discarded, allowing budget violations and biased baseline accounting.

Required repair: preserve structured usage through non-action calls, pass remaining
limits before sampling, and charge/report failures and continuations consistently.

## P2 — Page evidence bypasses existing mathematical JSON compatibility

`src/evaluation/pdf_paging.py:124` calls `json.loads` directly. Auxiliary judges
already have `evaluation.models.load_judge_json`, which conservatively repairs
only decoder-rejected backslash escapes without supplying missing structure.

Controlled reproduction: the same evidence containing an unescaped `\sqrt{2}`
is accepted by the existing auxiliary parser, but paginated judging retries twice
and aborts before final grading. This can leave otherwise readable math/science
documents without a score.

Required repair: use the common parser and retain strict evidence schema, length,
and unreadable-page checks. Do not reinterpret valid escapes or fabricate evidence.

## P2 — Final-format retries invalidate every page-evidence cache entry

`src/evaluation/pdf_paging.py:89-91` includes the whole user prompt in the cache
binding. `src/evaluation/structured_judge.py` appends validation feedback when the
final score JSON is malformed. Consequently, a final-output-only retry changes
every evidence key despite unchanged documents, rubric, and judge configuration.

Controlled reproduction: a three-page PDF needs two evidence batches. One malformed
final response followed by a valid response causes four evidence calls and two
final calls. The successful evidence was read again in its entirety.

Required repair: bind page evidence to immutable evaluation inputs and judge
configuration, while keeping final-response formatting feedback separate. Preserve
invalidation when the actual rubric, sources, page scope, or judge changes.

## P2 — A local cache failure is counted as an API call

`src/contest_reporting.py:68-92` precharges one call. Its exception adjustment
cannot subtract that charge when `PagedJudgeError.usage['api_calls']` is zero.

Controlled reproduction: alter a cached evidence checksum, then retry. The cache
is correctly rejected before invoking the model. Actual callback invocations are
zero, but reported evaluation usage is one API call with zero unmetered calls.

Required repair: account for explicit zero-call outcomes separately from failed
network attempts whose usage is unknown.

## Reproduction and scope

```sh
python results/code_review_20260918/repro.py
python -m pytest results/code_review_20260918/test_review_repros.py -q --tb=short
```

At the original reviewed snapshot, the latter command reported **four failed
invariants**. These isolated review repros are outside the normal `tests/` suite;
use the current repair regressions for post-repair validation. The first audit
mock ignores supplied budgets, so its old cap assertion is superseded by checks
of requested limits, full usage retention and stopping after an overrun. Evidence is in
`results/code_review_20260918/observations.json` and `repros.xml`.

The earlier 1,260 passing tests and 1,341 passing subtests remain a correct record
of that suite, but those tests did not exercise these cases. In particular, the
previous statement that every model call respects the shared API/token budget
was too broad. The page-count limit also does not guarantee that all future
conversation/review text fits in the model context; that remains a documented
boundary rather than an additional reproduced finding in this review.

The repair applied shared budget enforcement and mathematical evidence parsing
first, followed by cache reuse and zero-call accounting. No paid batch was
repeated to validate these mechanics.
