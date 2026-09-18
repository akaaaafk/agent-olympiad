# Runtime settings audit - 2026-09-17

Update: the runtime budget, pipeline forwarding, sampling identity and three stale fixture findings below have now been addressed. Explicit turn overrides also clamp to 10-90, per the user's latest instruction. The affected and expanded offline suite passes 157 tests. Current behavior: [Unified runtime settings](unified_runtime_settings.md). The findings below preserve the pre-repair audit.

Scope: current source, 39 active competitions, main/mini rules, five baselines, native/artifact entrypoints, identities, providers, budgets and offline regressions. No paid models or remote submissions were run. This audit changes documentation only.

## Findings

1. Priority: artifact timing still uses the old rule-card simulation rounds and minutes_per_turn=0, without a simulated-time limit. Native uses resolve_contest_budget (5 minutes per turn, default 10-90 turns). MCM/ICM cards use 24 turns versus native 90. Static comparison finds 36 of 39 old card budgets differ; this does not mean all 36 actually run through the artifact route. Explicit artifact max_turns also lacks the native 90-turn clamp. Location: src/otc_artifact_pipeline.py::prepare_artifact_run.

2. Cross-route budget defaults differ. Artifact has a 220000 total-token cap and 8192 per-call output cap. Native has no default total-token cap and uses competition/provider output defaults. scripts/run_pipeline.py does not expose/forward unified turn, total-token or temperature overrides. Matching baseline/model/roster alone does not establish matched settings across routes.

3. Artifact sampling is not explicitly recorded. run_otc_artifact.py passes no temperature to solver/judge resolve_request_fn, which defaults to 0.2. Its CLI offers no temperature option and its execution identity does not explicitly record that value. Native solver also defaults to 0.2: the issue is configuration/recording, not a demonstrated solver temperature mismatch. Source hashes still protect against directly reusing results after code changes.

4. Three CLI identity regression fixtures are stale after fixed-roster enforcement. tests/test_contest_run_identity.py::CliIdentityTests supplies competition=custom, vanilla, team-size=1 without custom/competition.json. They fail roster validation before reaching their intended resume checks. Supply valid temporary competition rules/rosters while preserving the original assertions; do not restore a silent roster fallback. Official catalog roster tests pass.

## Confirmed checks

- All 39 active competitions have matching main/mini active_default. Single-agent uses 1; the other four use the competition roster. Conflicting overrides are rejected.
- All main/mini competition.json fields except provenance match. Packaging provenance path differences are not treated as runtime defects.
- Shared public rules reach all five baselines. Plain baselines do not attach OTC cards. OTC/vallina_otc presets differ only in memory.
- Selected provider policy, JSON escape repair, pipeline process recovery/timeout, budget accounting, baseline boundaries and other identity checks pass.
- 20 active competitions have no registered numeric duration and native defaults to 90 turns. This fallback is not evidence of a 450-minute official contest clock.

## Validation

18 selected modules: 134 tests, 131 passed, 3 errors, all the custom-roster fixtures described above. Logs: tmp/settings_audit_current.log and tmp/settings_audit_current.stdout.log. This is not a full-repository or live-service certification.

Suggested repair order: unify artifact/native budget resolution; expose pipeline overrides and record sampling; update the three fixtures and rerun affected tests.

## Active competition inventory

Single-agent always uses 1. Agents below apply to the other four baselines. Old card rounds are a static comparison, not a claim that every competition uses artifact delivery.

| Competition | Agents | Native default turns | Old card simulation turns |
|---|---:|---:|---:|
| arml_local | 6 | 10 | 9 |
| arml_national_power | 15 | 12 | 30 |
| arml_national_team | 15 | 10 | 4 |
| arml_power | 15 | 12 | 30 |
| ccdc | 8 | 90 | 30 |
| cfa_research_challenge | 4 | 90 | 12 |
| cybench | 5 | 90 | 30 |
| debatebench | 2 | 90 | 30 |
| eoes | 3 | 90 | 30 |
| ethics_bowl_appe | 5 | 90 | 30 |
| ethics_bowl_nhseb | 5 | 90 | 30 |
| fyziklani | 5 | 36 | 30 |
| gcch_harvard | 4 | 90 | 30 |
| hmmt_team | 8 | 12 | 12 |
| ichto | 4 | 90 | 30 |
| icm | 3 | 90 | 24 |
| icpc | 3 | 60 | 60 |
| ieo_business_case | 5 | 90 | 30 |
| iiot | 4 | 36 | 30 |
| ijso_practical | 3 | 36 | 30 |
| ioaa_group | 5 | 18 | 30 |
| ioai_team | 4 | 90 | 30 |
| iol_team | 4 | 48 | 30 |
| itym | 6 | 90 | 24 |
| iypt | 5 | 90 | 24 |
| jessup | 5 | 90 | 30 |
| mcm | 3 | 90 | 24 |
| mystery_hunt | 12 | 90 | 12 |
| nyu_ctf_bench | 5 | 90 | 12 |
| odyssey_of_the_mind | 7 | 90 | 30 |
| pumac_power | 8 | 90 | 30 |
| purple_comet | 6 | 18 | 18 |
| qanta | 4 | 90 | 12 |
| science_bowl | 4 | 90 | 12 |
| science_olympiad | 15 | 90 | 30 |
| vis_moot | 5 | 90 | 30 |
| wharton_investment | 5 | 90 | 30 |
| wmtc | 6 | 90 | 12 |
| wsc_writing | 3 | 15 | 30 |
