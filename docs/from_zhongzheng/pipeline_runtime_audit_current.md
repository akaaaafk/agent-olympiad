# Current pipeline runtime audit

## Repair follow-up

The four findings below have now been addressed in local code: auxiliary judges share conservative JSON escape repair; gateway preflight uses VJUDGE_GATEWAY_URL; new lock records track host/owner/child and permit only proven-dead recovery; children have a configurable wall-clock timeout (default 21600 seconds) and process-tree cleanup. Legacy/unknown locks, different-host locks and interrupted launch windows remain manual-review cases.

Validation: 120 targeted tests passed in `tmp/pipeline_runtime_repairs_tests.log`; after adding public coordination/IHS response coverage and stricter lock metadata, 62 affected tests passed in `tmp/pipeline_runtime_repairs_final.log`. A real local sleeping child was terminated by timeout without changing its checkpoint. All 48 PowerShell blocks parsed without syntax errors. No paid experiments or remote submissions were run.

Commands: [Mini pipeline PowerShell](mini_pipeline_powershell.md).

The sections below preserve the original audit findings, before the repair.

Scope: current local code; no paid model calls, remote judge submissions, or historical result edits.

## Regression verification

16 selected modules, 108 tests, zero failures/errors/skips. Log: `tmp/pipeline_runtime_audit_current.log`.
Coverage: task-judge JSON escaping and invalid structures; ARML cross-task binding and final-answer extraction; auxiliary-judge-only resume; run identities and artifact identity; pipeline completion/metrics/locking; transport budgets and gateway/Kattis retry rules.

## Outstanding findings

1. JSON repair is not shared by all judge parsers. `src/evaluation/models.py:_load_evaluator_json` accepts and records a repair for a JSON string containing a bare LaTeX backslash. The same payload passed to `src/evaluation/cce.py:_parse_json_object` raises `JSONDecodeError: Invalid \escape`. IHS parsing in `src/evaluation/collaboration_score.py` also directly uses `json.loads`; that route was inspected but not separately replayed here. This can leave auxiliary evaluation pending even when task grading succeeds.
2. `scripts/run_pipeline.py` probes a literal `http://127.0.0.1:8787/v1/health`, while the submission client uses `VJUDGE_GATEWAY_URL`. A configured different port/host can therefore fail preflight despite correct submission configuration. The current configured default address is unaffected.
3. The pipeline exclusively creates `pipeline.lock` and removes it in `finally`, but does not recover locks left by forced termination/reboot. Ordinary exceptions release the lock (tested); a stale lock blocks restart. Any future recovery must verify ownership/liveness before removal.
4. The parent `subprocess.run(cmd, ...)` has no timeout. Individual clients can have timeouts, but these do not establish an outer bound on a stalled child process. This is a code-level gap, not a newly observed hung run.

These findings were audited, not changed in this pass. Passing targeted mock/offline tests does not establish full live-model reliability or all-test-suite success.
