# Draft length and answer pagination

Ordinary non-programming drafts now share an **8,000-character hard limit**
across all five manifest-driven contest baselines. Prompts suggest **2,000-4,000
characters when detail is useful**; shorter complete answers are welcome. The
suggested range is neither a minimum nor a validation threshold. A 4,500-character
valid draft is accepted without a length-repair request.

The old 2,400-character ARML limit was a simulation setting, not an official
answer-length requirement. The new 8,000 value is an initial engineering choice,
not a measured optimum or a claim of improved contest scores.

## Storage, transport, and budget

- `work.content` contains a shared candidate or draft. It is not model-internal
  reasoning, a private `think` entry, or a `speak` message.
- Counts use Python string length: spaces, newlines, and formula source count.
  Character counts are separate from provider token counts.
- The same policy is supplied to action transport and checked before candidate
  writes. It also checks an inline `submit.answer`; direct submission cannot
  bypass the draft limit. A rejected write does not replace the previous answer.
- Accepted text is saved in full in answer versions, event archives, and
  checkpoints. Prompt previews never change the stored answer or its hash.
- Oversized ordinary candidates are rejected without clipping. Tinker retains
  its existing bounded rewrite recovery. A soft-target overrun needs no repair.
- Artifact runs use their own `artifact_contract.max_source_chars`, including
  60,000-character document contracts where configured. Executable and static
  source-review tasks do not inherit the ordinary-draft transport cap. Existing
  source and artifact handling remains separate.
- Larger configured native text-deliverable caps also remain in force (for
  example, HMMT Team proof packets at 60,000 characters). The same resource
  setting is resolved for every baseline without enabling OTC strategy or memory.
- `think`, communication, API-call, token, and turn budgets were not raised.
  Reading another page still consumes an ordinary `inspect_problem` action.

The main and mini rule cards with the old 2,400-character `work` limit are updated
to 8,000. A separate `precontest_brief.max_chars=2400` preserves the previous
Coach allowance in those cards; the Coach prompt, supplied-brief validation, and
generated-brief handling use this independent value. This parameter patch preserves
the other fields; separate concurrent ARML rule-description corrections are retained.
Existing larger artifact settings and
programming settings are not globally rewritten. Baseline role, review, memory,
and submission permissions are unchanged.

## Read full saved answers

`inspect_problem` retains its existing purpose and accepts three additional
optional arguments: `version_hash`, `offset`, and `limit`. Its ordinary overview
contains bounded previews and the visible version hashes. To read a saved answer:

```json
{
  "problem_id": "arml_local_2012:6",
  "version_hash": "COPY_THE_VISIBLE_VERSION_HASH",
  "offset": 0,
  "limit": 2000
}
```

Call `inspect_problem` with those arguments. Each returned version contains
`content` plus `content_page.offset`, `end`, `total_chars`, and `next_offset`.
Continue using the same problem and version hash with the returned `next_offset`;
`null` means the answer is complete. Offsets are zero-based character positions.
The page limit defaults to 2,000 and accepts values from 1 through 4,000. A
nonzero offset requires an explicit version hash so a new draft cannot silently
change the text being read.

The latest explicitly requested answer page is delivered in the reader's next
prompt even if the ordinary memory projection is full. It stays private to that
reader. Overview and shared-history previews are bounded; eligible programming
source continues to be shown in full for review. Reading does not move the
active problem, grant independent approval, expose a hidden phase's task, or
restore earlier-round answers for the memory-off OTC baseline.

The legacy environment preserves its original unpaged inspection response. When
paging arguments are supplied, it pages the currently visible inspection snapshot
and returns its hash. If that snapshot changes, a subsequent request using the
old hash is rejected and must restart from offset zero.

## Validation and experiment identity

Regression coverage exercises the actual engine request and dispatch paths for
all five baselines, exact-limit storage and checkpoint restoration, atomic
overlimit rejection, character-page reconstruction, private result visibility,
current-round isolation, and artifact/source exceptions. Captured Tinker failures
remain fixtures for testing genuinely overlimit repair under explicit smaller
limits; historical failures are not relabeled as successful runs.

Action-set version 14 records the optional pagination interface. The engine also
records the work-content policy version and resolved caps in checkpoint and run
identity settings. Use a fresh
output directory for experiments under this policy; do not rewrite old run
identities to resume with different constraints.

Validation artifacts are written under `results/work_content_limits_20260918/`.
No paid model run is required for these deterministic checks. Full live contest
completion and score improvements are separate, unmeasured outcomes.

Final verification:

- Full regression: **1,536 tests and 1,345 subtests passed**, with no failures,
  errors, or skips. No production source or rule changed during that run.
- Two concurrently updated test modules were checked again after the full run:
  **192 tests passed**. This follow-up count overlaps the full suite and is not
  added to it. The final source/test hashes are recorded in `completion.json`.
- Subsequent concurrent edits to `contest_prompts.py` and `llm.py` were covered
  by a final integrated prompt, engine, provider, transport, and budget check:
  **562 tests and 56 subtests passed**, with no source drift during that check.
  These counts also overlap earlier runs. Mini preflight was refreshed after
  those edits and concurrent ARML packet-description corrections. Final readback
  verified the current source hashes and unchanged work/think/speak/Coach caps.
- Mini preflight: **479 asset checks passed; all 445 configurations prepared**,
  with zero parent-dataset reads or asset errors. Nine mini rule dependency
  hashes were refreshed after successful preflight; original provenance hashes
  and dataset membership were preserved.
- The captured 3,564-character Qwen draft is accepted unchanged through the
  actual staged transport and dispatch path in an offline replay: three samples
  for action name, metadata, and body, with no shortening call.
- The checkout contains concurrent provider and argument-validation repairs.
  Those edits were retained and included in the combined validation. All checks
  for this change used zero paid model calls; no full contest was rerun.
