# Tinker action transport

Tinker action requests use `staged_raw_arguments_v3`. Competition actions,
permissions, roles, rules, scoring, and baseline definitions remain in their
existing registries and runtime. Native function-calling providers are unchanged.

The old route required the model to serialize an entire solution or source file
inside one JSON response. Recorded Qwen samples both exhausted their output cap
before producing an action and stopped normally with invalid JSON escapes. A
larger cap alone does not repair either failure mode.

## Generation and execution

1. Select an existing function name using an assistant prefix and quote stop
   delimiter. This stage is limited to 512 tokens.
2. The host fixes each remaining metadata key. String IDs and enum values use a
   quote stop delimiter, preventing a second payload key from being generated in
   the same field. Scalar metadata is limited to 512 tokens; arrays use the
   configured normal output cap and exact token continuation. Validate each
   parameter against the current schema. Optional parameters may be omitted.
3. Generate each existing free-text string argument as raw text. This includes
   `answer`, code, drafts, and the separate fields in a report. Only identifiers,
   enum values, and short routing fields stay in metadata JSON. The host
   serializes quotes, newlines, and backslashes. No function signature or extra
   contestant action is introduced.
4. On a length stop, append the exact generated token IDs to the original
   rendered prompt and continue. Decode the combined tokens, preserving spaces
   and token boundaries. Do not concatenate independently stripped strings.
5. Execute one action only after normal completion and schema validation. An
   existing character limit is enforced without silently clipping the candidate.

No-argument actions can finish after selection. Actions with only short arguments
can finish after metadata. The compatibility parser accepts complete single-call
JSON envelopes; it rejects malformed outer JSON and never extracts an inner call.

## Bounds, checkpoints, and trace

Selection, metadata, repair, and continuation share one controller. Its default
per-request cap is five samples (`3 + max_tool_retries`, with two retries by
default), further limited by the remaining task API and output-token budgets.
The outer action transport does not start another recovery loop. Every sample is
charged, including a sample whose action never executes. Extra input from a
continuation is reported as input usage; the existing task token budget counts
output tokens as before.

An unfinished action is saved as a private, unexecuted checkpoint buffer,
including completed fields, the current field's exact tokens, and original
prompts. On the next turn the model sees current
state and selects an action again. Exact continuation is allowed only when the
session, agent, active task, model, function, arguments, body field, current schema,
and applicable character limits match. A different action gets a fresh body.
Completed but rejected bodies do not retain a resumable token suffix.

These buffers are transport state, not shared memory, tool results, or
submissions. They do not authorize actions. The normal runtime checks still apply
at dispatch. A buffer clears after a valid action. Checkpoints save state between
actions; a hard process kill during an in-flight sample can still lose that
unreturned sample.

`action_sampling_log` records stage, actual cap, token usage, stop reason, raw
sample, and errors. `action_transport_log` continues to record actual action
execution. Raw samples themselves have `executed: false`; only the assembled
action can execute. `unexecuted_transport_drafts` preserves unfinished progress in
the final result when the total task budget runs out.

Length stops remain possible with finite budgets. The fix prevents a length stop
from automatically throwing away a complete derivation and regenerating it from
scratch. It does not guarantee that a model finishes within the total budget or
solves the task correctly. Staged generation can use more API calls for a short
action, especially one containing several report fields; all stages remain
inside the original task budget.

## Validation

Regression coverage includes recorded malformed Qwen outputs, literal source
serialization, exact within-turn and cross-turn continuation, checkpoint
round-trips, actor/task isolation, current-schema changes, rejected-body cleanup,
budget accounting, and atomic rejection. Run:

```powershell
& 'E:\agent_olympiad\.venv\Scripts\python.exe' -m pytest tests/test_tinker_action_mechanism.py tests/test_transport_draft_checkpoint.py tests/test_tinker_provider.py tests/test_action_transport.py tests/test_transport_budget_regressions.py -q
```

Fresh live validation artifacts and final evidence belong under
`results/tinker_staged_v3_smoke_20260917`; previous runs are retained as
diagnostic evidence and are not rewritten as new-code results.
