# Agent Olympiad current documentation

This directory is the maintained entry point for understanding and running the
current benchmark. The source of truth is the code under `src/`. Current engine:
`contest_session_v12`, action set 13 (`ACTION_MODULE_VERSION = 3`), 89 actions.

The [latest verified dataset status](../CURRENT_DATA_STATUS.md) is the current
source for dataset counts, readiness, and validation results.

The [remaining five-track repair](remaining_five_mini_repair_20260917.md) records
the latest scoring integration and the Mystery Hunt 2012 text selection.
The [initial LLM scoring repair](open_llm_judge_repair_20260916.md) records the earlier six-track integration. The earlier
[workspace sync entry](workspace_sync_20260916.md) now redirects to current status; its earlier snapshot is archived.

## Start here

Latest main-data expansion and local validation: [Current dataset status](../CURRENT_DATA_STATUS.md).

1. [Final pipeline overview](final-pipeline-20260914.md) — architecture,
   baselines, turn loop, memory, OTC rule-card mechanisms, judging, and
   reproducibility, with source citations.
2. [Actions appendix](final-pipeline-appendix-actions-20260914.md) —
   dated guide to the 78-action snapshot. The current registry contains 89
   actions; use the source registry and workspace sync report for current counts.

## What is current

- Runtime: contest-session engine (`src/contest_engine.py`).
- CLI: `src/run_competition_batch.py --contest-manifest ...`.
- Baselines: `single_agent`, `decentralized`, `centralized`,
  `vallina_otc` (OTC without memory actions), and `otc`.
- OTC: rule-card-enforced Open Table Coach (`--system-variant otc`). The
  matched control is `vallina_otc`: same coach/review/card, memory off and
  current-round-only context (see §7.6 of the pipeline overview).
- Action registry: `src/tool_registry.py` — common 25, memory 3,
  task-specific 61. Canonical names only on the wire.
- Run outputs: `run_config.json`, `contest_checkpoint.json`,
  `contest_session.json` (plus `calls.jsonl` / `result.json` when present).

CLI aliases still accepted: `vanilla` → `decentralized`; `strategic` /
`open_table_coach` / `open_table_coach_memory` → `otc`; `vanilla_otc` /
`otc_rule_card` → `vallina_otc`.

Do not use the legacy per-problem `--schema` path for new experiments.

When any note elsewhere conflicts with the pipeline overview, actions
appendix, or source code, the source code wins.

## Also in this folder

These are working notes, not a second architecture. Prefer the pipeline
overview when they disagree.

| File | Use |
|------|-----|
| [run_baseline_competition_year.md](run_baseline_competition_year.md) | Select a baseline, competition and year; run ARML Local 2009 with Tinker Qwen |
| [competition_experiment_commands_20260916.md](competition_experiment_commands_20260916.md) | Current PowerShell and Bash commands for decentralized / centralized runs |
| [mini_dataset_commands_20260916.md](mini_dataset_commands_20260916.md) | Mini-catalog run commands |
| [mini_dataset_remaining_20260916.md](mini_dataset_remaining_20260916.md) | All tracks included; remaining evaluator blockers and CTF readiness |
| [mini_data_audit_20260916.md](mini_data_audit_20260916.md) | Mini-data readiness check |
| [benchmark_distribution_and_completed_runs_20260916.md](benchmark_distribution_and_completed_runs_20260916.md) | Refreshed catalog and saved-run inventory (2026-09-18 UTC); retained historical snapshots and scoped mini scoring |
| [current_catalog_run_membership_20260916.csv](current_catalog_run_membership_20260916.csv) | Per-run membership against the current catalog |
| [written-track-scope-20260916.md](written-track-scope-20260916.md) | Written-only scoring scope |
| [ready-competitions-20260914.md](ready-competitions-20260914.md) | Readiness snapshot from 2026-09-14 |
| [v12-code-reaudit-20260914.md](v12-code-reaudit-20260914.md) | Runtime re-audit |
| [settings-baselines-audit-20260914.md](settings-baselines-audit-20260914.md) | Baseline-boundary audit |

The full map of `docs/` is [../README.md](../README.md).
