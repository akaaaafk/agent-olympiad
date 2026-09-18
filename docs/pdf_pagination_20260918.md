# PDF pagination and runtime rule repair

The configured `Qwen/Qwen3.6-35B-A3B` stays at its supported 65,536-token context.
The default output allowance remains 8,192 tokens (ICPC and IIOT retain their
4,096-token defaults). Input text, page images, and generated output share the
context window. Raising the output allowance cannot fix an oversized input.
The [official Tinker model table](https://tinker-docs.thinkingmachines.ai/tinker/models/)
lists this model at 64K. No model switch or paid rerun is part of this repair.

## Contestant interface

Tinker vision artifact runs now expose the existing `read_problem_pdf` interface.
Document 1 is the verified task; document 2 is the currently visible rendered
candidate. The initial request includes the first two task pages. A contestant
can select other pages, for example:

```json
{"name":"read_problem_pdf","arguments":{"problem_id":"deliverable","document":1,"pages":[61,62]}}
```

The complete authorized page list is displayed. A read delivers at most two pages
in the next action request, immediately within the same seat turn. Each seat has
at most two page-read calls before its ordinary action; each model request uses
the existing shared API and output-token budgets. This bounded navigation also
works with the existing reviewed-PDF interface for native contest tasks.

The follow-up [budget and judge repair](code_repairs_20260918.md) extends structured
accounting to Coach, private-think and leader planning. Legacy custom callbacks
that return only text still use estimates; provider-reported overruns are retained
and stop further requests, and missing failure usage remains explicitly unknown.

The action registry and baseline feature definitions are unchanged. Reads do
not enable memory actions. The control without cross-round memory sees read
results only in their originating round. The Coach stays blind to task and
candidate PDFs. Page numbers, source hashes, contestant/judge visibility, and
candidate version visibility are checked before delivery. A revised or expired
candidate invalidates its earlier page selection. Resume restores navigation
counters and selections through the ordinary contest checkpoint.

## Evaluation interface

For Tinker judges, more than two PDF pages trigger `pdf_page_evidence_v1`:

1. Read every authorized task, submission, and reference page in batches of at
   most two. Collect page-specific evidence; reject malformed or unreadable
   batches instead of silently skipping them.
2. Cache validated evidence using document hashes, ranges, roles, evaluation
   prompts, protocol version, and judge configuration. Resume reuses matching
   batches, including across final-output-only format retries. Model calls and
   usage are recorded, including failed evidence passes; known local failures
   before sampling count as zero calls.
3. Apply the original rubric to the collected evidence. Save the coverage and
   an explicit compression limitation in the result.

The evidence budget is 24,000 characters overall, capped at 1,600 per batch.
Malformed batches get one retry. This protocol requires extra judge calls and
may lose cross-page detail; its scores are not assumed identical to full-document
judging. Collaboration scoring uses the same bounded task-document path. Judge
evidence never becomes contestant input. Existing complete results are not
rewritten or rejudged by this repair.

Pagination removes the demonstrated all-pages image overflow. It does not
guarantee that arbitrary future conversation histories fit in 64K. The existing
context check and output continuation mechanism remain in force.

## Rules and budgets

Coach and contestant rule views now show the actual run's turn, API, and token
budgets instead of historical simulation defaults. The authored rule bundles
and their coordination policies are retained; short smoke budgets can still end
before the policy's usual minimum discussion interval.

IEO Business Case preparation allows online and offline research. The official
2024 task PDF, page 4, and [IEO Syllabus section 3.2](https://files.ieo-official.org/IEO_Syllabus.pdf)
support that permission and require final submission by the deadline. The
unsupported turn-21 internet/code ban and early-submission ban were removed from
both main and mini collaboration cards. The experiment covers preparation and
final artifact submission; later live presentation and oral Q&A are not simulated.
Only the corresponding mini dependency snapshot hash was refreshed.

## Verification

Evidence is saved in `results/runtime_repairs_20260918/`. The initial regression
reproduced missing artifact page access, stale displayed turn budgets, and the
unsupported IEO phase ban. Targeted regressions cover all five baselines, candidate
reading, complete-result resume without calls, hash/range rejection, full judge
page coverage, evidence cache reuse, and failed-pass usage accounting.

The complete test suite passed: **1,260 tests and 1,341 subtests**, with zero
failures or skipped tests. Source hashes did not change during the suite or mini
preflight, and the final readback matched the tested source. Byte comparisons
confirmed the action registry files were unchanged; AST comparison confirmed
the original baseline definitions were unchanged.

The mini preflight prepared all 445 combinations of 89 sessions and five
baselines across 39 competitions; all 479 asset checks passed with no parent-data
reads. This is an offline preparation check, not proof of model quality or a
completed live run of every competition. Full-suite and local Tinker encoding
results are recorded beside that preflight. With the real cached tokenizer and
Tinker adapter, Vis Moot pages 61–62 plus its full rule card used 6,782 input
tokens, including 3,922 image tokens. Reserving 8,192 output tokens and the 256
token margin fits in 65,536. First/last page windows for IJSO, PUMaC, and Jessup
also fit. Sampling was stubbed; these are encoding checks, not model solutions.
