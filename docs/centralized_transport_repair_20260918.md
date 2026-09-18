# Centralized task focus and OTC body-repair failures

The stopped Qwen ARML runs exposed two additional paths beyond the earlier
[accounting and checkpoint repairs](call_contract_repairs_20260918.md). The same
transport circuit stopped both runs, but their underlying failures differ.
The earlier offline regression did not cover these live request sequences.

## Centralized workers inherited another worker's active task

The final centralized checkpoint records turn 7/10, 142 API calls, 25,474 output
tokens, 14 drafts across ten questions, and no submissions. Its 141 staged samples
include 45 `unavailable function name: 'work'` errors and one unavailable `submit`.

Once a worker had authored drafts for every assigned non-programming task, the
scheduler returned no next task. The shared active cursor remained on Agent_2's
question. Agents 3, 4 and 5 were therefore shown that question while `work` was
correctly withheld by their assignment permissions. The user prompt compounded
the mismatch by telling them to act directly on that selected task without
selecting another question. Each worker repeated the rejected selection five
times, and three consecutive failed logical requests opened the circuit.

The scheduler now falls back to an eligible, unsubmitted draft within the current
worker's assignment, after existing initial-draft, review and programming
priorities. It excludes locked, temporarily blocked and already-submitted drafts.
The prompt also explicitly identifies a foreign active task when no eligible
assigned target can be scheduled. Actions remain filtered by role, assignment,
phase and runtime state; `work` is not granted on another worker's task.

The original checkpoint replay now schedules Agents 3, 4 and 5 onto questions
3, 4 and 5 respectively and offers their permitted `work` action. A six-worker,
ten-round regression reproduces the original circuit failure before the fix and
reaches deadline submission after it. This is a deterministic model fixture,
not a rerun of the paid experiment.

## OTC ran out of recovery calls before rewriting a rejected body

The original OTC checkpoint stopped at turn 2 after 39 API calls. Three complete
`work.content` generations exceeded the existing 2,400-character limit. These
responses stopped normally; this failure was a character-limit rejection rather
than token truncation. The captured final rejected body has 3,119 characters.

The adapter had already validated the function name and problem ID, then spent
its remaining two attempts reselecting the same function and regenerating the
same problem ID. No attempt remained to produce a shorter body.

A rejected raw argument now uses the remaining sampling allowance to rewrite
that field directly. The prompt supplies the validation error and rejected text,
requests a complete replacement, and preserves the current action and metadata.
The rejected text is retained privately. Completed fields are preserved, while
tokens from a rejected complete body are not continued. Repeated failures still
exhaust the same budget and execute nothing. No work-argument character limit, action schema,
baseline definition or circuit threshold was relaxed; no final answer is clipped
or selected using a gold label.

## Original-input replay and bounded live validation

Artifacts are in `results/centralized_transport_repair_20260918/`. The original
centralized and OTC run directories are preserved. The stopped checkpoints are
not silently resumed under a changed source identity, and no historical score
or submission is rewritten.

Using the same `Qwen/Qwen3.6-35B-A3B` model:

| Probe | Real sampling calls | Real output tokens | Result |
|---|---:|---:|---|
| Agent_3 with its corrected active question | 3 | 559 | Valid `work` for `arml_local_2012:3` |
| Rewrite the captured rejected OTC body | 1 | 925 | 2,001 characters, within the unchanged 2,400 limit |

The OTC probe replayed three recorded selection/metadata/body samples before
making its single real rewrite request. Those replayed samples are not counted
as paid calls. The rewrite retained the proposed final expression
`40\pi/3 + 36\sqrt{3}`. This tests transport and preservation, not independent
verification of the mathematical answer. The centralized result also passed
local work dispatch in an isolated in-memory copy of the checkpoint.

The probes used four real sampling calls and 1,484 generated tokens in total,
below their six-call / 6,144-output-token caps. No external competition tool or
formal submission was executed by the probes. A successful bounded action probe
does not establish that a complete live competition will always finish.

Run the offline regression from the repository root:

```sh
python results/centralized_transport_repair_20260918/replay.py
python -m pytest tests/test_assignment_cursor_recovery.py tests/test_tinker_body_repair.py -q
python -m pytest tests -q
```

`live_probe.py` makes authenticated model requests and incurs provider usage;
the saved `live_probe.json` can be inspected without rerunning it.

## Final verification

Final verification also includes a concurrent judge-page evidence-limit change
and its tests. That separate change does not alter OTC's 2,400-character work
limit. Its 44 targeted pagination tests passed before the final full regression.

The frozen-source full regression passed **1,468 tests and 1,345 subtests**, with
zero failures, errors or skips. Mini preflight passed all **479 asset checks**
and prepared **all 445 configurations** across 39 tracks and 89 sessions.
`all_jobs_environment_ready` is true for this check; no paid competition run
is implied by the preparation result.

Final readback verifies matching source hashes across the full suite, mini
preflight and current files; exact preservation of action/baseline/provider
default contracts; unchanged historical centralized and OTC output files; and
valid local documentation links. The record is
`results/centralized_transport_repair_20260918/completion.json`.
