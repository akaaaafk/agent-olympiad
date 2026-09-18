# Documentation map

Start with the current entry point, then use the section that matches the job.
The source of truth is `src/`. When a note disagrees with the pipeline overview
or the code, the code wins.

`cleanup_audits/` is a machine inventory of deleted or repaired files. Scripts
write there. Do not treat those JSON and CSV dumps as prose documentation, and
do not move that directory.

## Start here

| Doc | Use |
|-----|-----|
| [../README.md](../README.md) | Current English installation and first-run guide |
| [from_zhongzheng/mini_pipeline_powershell.md](from_zhongzheng/mini_pipeline_powershell.md) | Current portable PowerShell guide for all five baselines |
| [from_zhongzheng/README.md](from_zhongzheng/README.md) | Maintained index for the current contest-session engine |
| [from_zhongzheng/final-pipeline-20260914.md](from_zhongzheng/final-pipeline-20260914.md) | Architecture, baselines, turn loop, judging |
| [from_zhongzheng/final-pipeline-appendix-actions-20260914.md](from_zhongzheng/final-pipeline-appendix-actions-20260914.md) | Action reference |
| [from_zhongzheng/competition_experiment_commands_20260916.md](from_zhongzheng/competition_experiment_commands_20260916.md) | Commands to launch the current Qwen / Tinker runs |
| [contest-systems.md](contest-systems.md) | Baseline and OTC contract |
| [BENCHMARK_DESIGN.md](BENCHMARK_DESIGN.md) | What the benchmark measures |

## Design and reference

These stay at the top of `docs/` because other notes and `src/` link to them
by these names.

| Doc | Use |
|-----|-----|
| [DATA_COLLECTION.md](DATA_COLLECTION.md) | Collected contests, formats, official clocks |
| [EVALUATION.md](EVALUATION.md) | Evaluators and readiness |
| [SOFTWARE_DESIGN.md](SOFTWARE_DESIGN.md) | Code layout |
| [WORKBOARD_AND_TOOLS.md](WORKBOARD_AND_TOOLS.md) | Workboard actions and metrics |
| [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md) | Tool and capability coverage |
| [TOOLING_GAPS.md](TOOLING_GAPS.md) | Missing tools |
| [HUMAN_VS_AGENT_SETTING.md](HUMAN_VS_AGENT_SETTING.md) | Human versus agent conditions |
| [VJUDGE_INTEGRATION_FEASIBILITY.md](VJUDGE_INTEGRATION_FEASIBILITY.md) | Remote programming-judge feasibility |
| [CHANGELOG.md](CHANGELOG.md) | Action, method, and metric history |
| [TESTS_AND_RESULTS.md](TESTS_AND_RESULTS.md) | Historical August results; not current validation |
| [PYTHON_ENV.md](PYTHON_ENV.md) | Python environment notes |

## How to run

| Doc | Use |
|-----|-----|
| [contest-run-reuse.md](contest-run-reuse.md) | Fingerprints, checkpoints, resume safety |
| [pipeline-runner.md](pipeline-runner.md) | Pipeline runner |
| [pipeline-repair-checklist.md](pipeline-repair-checklist.md) | Repair checklist |
| [otc-artifact-pipeline.md](otc-artifact-pipeline.md) | PDF / rubric delivery path |
| [otc-controlled-pairs.md](otc-controlled-pairs.md) | Matched OTC controls |
| [vallina-otc.md](vallina-otc.md) | Memory-off OTC control |
| [ctf.md](ctf.md) | Current CTF metadata, Docker delivery, and validation scope |
| [competition_parameter_audit_20260917.md](competition_parameter_audit_20260917.md) | Per-track parameters and outstanding completion/compliance findings |
| [problem-pdf-reader.md](problem-pdf-reader.md) | Contestant PDF reading |
| [type-pilot-fixes.md](type-pilot-fixes.md) | Typed-action pilot fixes |
| [from_zhongzheng/mini_pipeline_powershell.md](from_zhongzheng/mini_pipeline_powershell.md) | Current mini-catalog commands |

## Dated notes, 2026-09-16

One-off audits and design sketches from that day live in
[notes/20260916/](notes/20260916/). They are not the runbook.

| Doc | Use |
|-----|-----|
| [notes/20260916/required_metrics_20260916.md](notes/20260916/required_metrics_20260916.md) | Required score and collaboration metrics |
| [notes/20260916/scoring_scope_changes_20260916.md](notes/20260916/scoring_scope_changes_20260916.md) | Scoring-scope changes |
| [notes/20260916/data_audit_20260916_continuation.md](notes/20260916/data_audit_20260916_continuation.md) | Catalog audit continuation |
| [notes/20260916/data_recheck_after_exclusions_20260916.md](notes/20260916/data_recheck_after_exclusions_20260916.md) | Recheck after exclusions |
| [notes/20260916/interface_pipeline_audit_20260916.md](notes/20260916/interface_pipeline_audit_20260916.md) | Interface and pipeline contamination audit |
| [notes/20260916/interface_pipeline_repairs_20260916.md](notes/20260916/interface_pipeline_repairs_20260916.md) | Follow-up repairs |
| [notes/20260916/answer_pool_design_20260916.md](notes/20260916/answer_pool_design_20260916.md) | Answer-pool design, not yet implemented |
| [notes/20260916/ctf_docker_environments_20260916.md](notes/20260916/ctf_docker_environments_20260916.md) | CTF Docker environments |

Older snapshots and run membership tables remain in
[from_zhongzheng/](from_zhongzheng/README.md).
