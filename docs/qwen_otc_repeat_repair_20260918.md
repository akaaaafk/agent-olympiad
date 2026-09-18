# Qwen OTC repeated overlong-body failure, 2026-09-18

## Exact incident

The inspected run is `results/tinker_qwen_arml_local_2012_otc_20260918`,
job `arml_local_ce2a2745f7f6f21d`, model `Qwen/Qwen3.6-35B-A3B`.
Its checkpoint stopped at turn 2/10, with eight executed `work` actions and
no final summary. The session budget records 52 API calls and 39,815 output
tokens; 40 calls were staged action samples.

Agents 3, 4 and 5 then attempted question 9. Their first complete bodies were
3,564, 3,335 and 2,737 characters, above the existing 2,400-character `work.content`
limit. The two retries remained overlong: 3,564/3,564; 3,335/3,335; 2,722/2,722.
These were stopped responses, not token-limit truncation or invalid JSON.
The selected `work` name and problem identifier had already been accepted.
The three exhausted logical requests triggered the provider/model circuit.

This is a different failure from the earlier OTC sample described in
`centralized_transport_repair_20260918.md`. In the currently inspected run,
the direct-body-rewrite repair was already present, and retries did occur.
The previous small probe did not establish reliability in full OTC context.
The separate PDF judge limit of 3,200 characters is unrelated.

## Reproduction and diagnosis

`tests/fixtures/qwen_otc_body_repeat_20260918.json` preserves Agent 3's five
recorded outputs. The original transport repeats the same solve/coordination
prompt for editing, appending a generic instruction to shorten the body.
It does not supply the measured length or adapt the target after another failure.
Inspection ruled out accidental token continuation: rejected complete bodies
were retried with an empty continuation prefix.

The offline regression initially failed with an empty `tool_calls` tuple and
`work.content exceeds the existing 2400-character limit`. Its responsive model
stand-in tests the editing protocol, not live model obedience. A separate
unresponsive replay deliberately keeps returning the captured replies and
must still fail safely; arbitrary invalid replies are not accepted by the fix.

## Fix

`src/tinker_action.py` now uses `staged_raw_arguments_v5_focused_rewrite`:

- Initial action selection and generation retain their normal instructions.
- A rejected raw argument receives a narrow editing-only system instruction,
  fixed selected action/arguments, measured length and the rejected text.
  The full contestant role and original solving observation are not repeated.
- Rewrites can only edit the supplied material: preserve the proposed final
  answer, essential evidence and uncertainty; do not solve again, use tools,
  introduce sources or alter other arguments.
- The first target is 75% of the existing character limit; each failed rewrite
  halves that target. The validator still uses the unchanged hard limit.
- Rewrite attempts/targets and decoded character counts are audited. Truncated
  rewrites preserve exact continuation tokens, prompts and retry state.

The original sampling/token allowance, role/phase/schema permissions, shared
action registry, baseline definitions, 2,400-character limit and three-failure
circuit threshold are unchanged. No final answer is clipped or selected from
an answer key. A transport-version bump prevents silent continuation of an old
runtime checkpoint under this changed protocol.

## Bounded live validation (not a competition rerun)

`tmp/probe_qwen_otc_rewrite_20260918.py` builds an in-memory diagnostic view of
the archived tasks/memory and replays selection, metadata and the rejected body.
It then samples only the rewrite using the same Qwen model. It does not call
`engine.run()`, execute competition tools or mutate the original checkpoint.
The reconstructed observation is not claimed to be a byte-identical historical
request. All paid/replayed usage is recorded separately.

The first candidate removed the original user observation but kept the full
29,116-character contestant system prompt. That live probe passed only 2/3:
Agent 3 repeated its complete 3,564-character body twice. It used six actual
calls and 7,711 output tokens; its failed evidence is preserved in
`results/qwen_otc_repeat_repair_20260918/probe.json`.

The final candidate uses the editing-only system prompt. Its live results are
in `results/qwen_otc_repeat_repair_20260918_focused/probe.json`:

| Captured body | Final replacement | Actual rewrite calls | Result |
|---|---|---|---|
| Agent 3: 3,564 characters | 2,237 characters | 1 | Valid `work` |
| Agent 4: 3,335 characters | 1,257 characters | 2 | Valid `work` |
| Agent 5: 2,737 characters | 2,259 characters | 1 | Valid `work` |

The final probe used four actual calls and 4,414 output tokens. Across both
candidate probes: ten actual calls and 12,125 output tokens. Every final
replacement retains its original `Final answer:` text exactly; this verifies
preservation, not mathematical correctness. No full competition score exists.

The archived checkpoint hash is unchanged. The final probe's transport source
hash matches the tested source. Offline regressions also cover repeated refusal,
exact-token continuation after checkpointing, and actual OTC request/dispatch.

## Verification commands

```powershell
E:\agent_olympiad\.venv\Scripts\python.exe -m pytest tests\test_qwen_otc_repeat_recovery.py tests\test_tinker_body_repair.py -q
E:\agent_olympiad\.venv\Scripts\python.exe -m pytest tests -q
```

The focused suite passed six tests. The full suite passed **1,472 tests and
1,345 subtests in 242.25 seconds**, with no failures. Live probe success does not guarantee every future model
response will obey the character limit or that a full OTC competition finishes.
The failed competition remains unfinalized; do not clear its circuit marker or
overwrite its identity to make a changed-code continuation look like the same run.

During final verification a separately started
`results/tinker_qwen_arml_local_2012_otc_20260918_2` process was observed. Its
recorded transport source hash matched this repair, and its checkpoint identified
`staged_raw_arguments_v5_focused_rewrite`. At the readback it was at turn 1 with
three executed actions and no circuit abort. This diagnostic did not launch or
intervene in that run; that partial status is not an end-to-end completion claim.
