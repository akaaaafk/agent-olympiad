# Newcomer inspection: repairs and verification

This closes the seven findings in the [inspection](newcomer_inspection_20260917.md).
The subsequent [parameter audit](competition_parameter_audit_20260917.md) found
additional context and phase-enforcement gaps; this report is not an all-track
acceptance certificate.
Changes were applied one at a time, with failing reproductions before the code
fixes. Existing competition actions, baseline definitions, permission rules, and
the Tinker staged continuation implementation were preserved.

## Completed changes

| Finding | Repair | Evidence |
|---|---|---|
| Gemini thought-only usage | Normalize thought tokens even without a candidate count; preserve explicit zero usage; use one action-usage helper in retries and the engine | Real engine fixture now charges 500 rather than 1; zero remains zero |
| Malformed native arguments | Return a failed response with the original usage and no calls; reject valid-plus-invalid batches atomically | DeepSeek, compatible, Anthropic, and Gemini fixtures complete the engine run without executing partial actions |
| Inconsistent truncation recovery | Normalize token-limit reasons to `length`, retaining `provider_finish_reason`; keep refusal/filter reasons separate | All four public adapters recover within one bounded retry; API/output exhaustion prevents a second call |
| Dataset selection polluted by imports | Scope the repair script's mini selection to its CLI execution; preserve the importing process's environment | Fresh-process import tests cover unset and explicitly selected data roots |
| Broken/stale onboarding | Rewrite README and the PowerShell guide in English; remove machine-specific paths; route generated selection pages to one guide; label old results historical; correct rules-mode documentation | Local links resolve; nine PowerShell blocks parse; registration/report/help commands succeed |
| Installation drift | Pin Tinker 0.29.0; add explicit development requirements; install into a separate clean Python 3.12 environment | All runtime requirements satisfied, including imageio-ffmpeg; pip check passes; full suite passes there |
| Stale CTF readiness | Remove obsolete readiness copies from 82 active main records; sync the 15 existing mini records to verified current evaluation metadata; bind local evidence copies; rebuild mini scorecards for selected IDs only | Runtime report hashes and passed entries verified, task membership/content preserved, dependency audit passes |

The two stale test fixtures now reflect the current contract: removed Odyssey
practice records remain absent, and the pending-evaluation fixture declares
`evaluation_pending=True`. The existing engine size limit was retained; desk
diagnostics were extracted into a helper, with replay output unchanged.

## Validation

All artifacts are under `results/newcomer_repairs_20260917/`, except the main
catalog audit noted below.

| Check | Result | Artifact |
|---|---|---|
| Full suite in the clean environment | **1192 passed, 1341 subtests passed**, 164.17 seconds; no excluded module | `07_clean_full_tests.log`, `07_clean_full_tests.xml` |
| Provider, retry, and Tinker-focused regressions | 51 passed, 22 subtests passed | `03_recovery_green.log` |
| Import, CTF, flow, and evaluation regressions | 34 passed, 94 subtests passed | `04_isolation_green.log` |
| Engine replay and size constraint | 1 passed, 25 subtests passed | `04_engine_refactor.log` |
| CTF current metadata and controller checks | 13 passed, 194 subtests passed | `06_ctf_green.log` |
| Mini preparation in the clean environment | 445/445 prepared; 479 asset checks; no asset errors or parent-data reads | `07_mini_preflight.json` |
| Clean installation | All declared runtime requirements satisfied; pip check passes | `08_clean_requirements.json`, `08_clean_freeze.txt`, `08_clean_pip_check.txt` |
| README entry points | Registration, reporting, provider help all exit 0 | `08_register.log`, `08_report.log`, `08_provider_help.txt` |
| Documentation | No missing local links, replacement characters, or Chinese text in the checked English guides | `08_documentation_check.json` |
| Main catalog and derived package integrity | 39 tracks / 977 records; 0 structural issues | `output/newcomer_repairs_20260917/catalog/after.json` |

The refreshed main snapshot has 441 `ready`, 288 `ready_with_limitations`, 158
`remote_judge_ready`, and 90 `not_ready` records. The previous inspection's 984
records describe an older snapshot; the membership difference is in Mystery Hunt.
This CTF refresh preserved all 82 main and 15 mini task IDs. Other updates to the
shared workspace's current-data reports were left intact.

The main audit checked 10,769 unique file hashes, 1,251 declared PDF headers, and
the main/derived package projections. Removing the duplicate CTF source-review
text did not change the derived task inputs; the current projections pass the
audit. Mini scorecards and dependency bindings were regenerated where changed.

## CTF scope and preservation

"Latest CTF" is applied to the current effective records and validation evidence,
not interpreted as deleting every historical competition year. Old contradictory
readiness statements are removed from active rows and scorecards. The current
guide is [CTF delivery](ctf.md). Historical source material and experiment outputs
were not deleted.

`scripts/refresh_ctf_metadata.py` verifies evidence before writing. Its change
manifest and rollback archive are under `ctf/` in the repair artifact directory.
It preserves statements, flags, assets, roster, permissions, scoring semantics,
and selected task IDs. Evidence copied into mini is byte-identical to its verified
source report and remains outside contestant-visible assets.

Before/after hashes also confirm that the checked action-module files,
`contest_config.py`, `tool_registry.py`, `competition_flow.py`, `contest_actions.py`,
and `tinker_action.py` did not change. Runtime edits are limited to public provider
response handling, shared action usage, and the engine's reporting helper.

## Remaining validation boundaries

No paid model experiment was launched for these repairs. Provider error cases use
mocked responses at the actual adapter/engine boundary. A successful offline test
does not establish live account access or the frequency of a provider response
shape. Provider usage that is not reported still requires a visible-output
estimate; budget output counts are not a replacement for a provider bill.

CTF runtime evidence verifies preparation and exact-flag grading, not independent
exploit solving. The broader data audit still has 12 mixed gold/rubric weight
review candidates and 9 shared public/judge-byte candidates; they are not new
structural failures or automatically proven leaks. This repair does not certify
every PDF formula, every task's solvability, or official score equivalence.

Use a fresh output directory for subsequent experiments: source or data changes
alter run identity. Old run identities were not rewritten and old experiments
were not restarted.
