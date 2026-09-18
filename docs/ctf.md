# Current CTF delivery

The active verified catalog contains 38 Cybench tasks and 44 NYU CTF tasks.
The independent mini catalog retains its selected 8 Cybench and 7 NYU tasks.
These are the current verified subsets, not a claim to implement every upstream
challenge or to select only the newest competition year.

Each record's `evaluation` contains its current status, limitations, exact-flag
score basis, and `runtime_validation` evidence binding. Superseded readiness
copies have been removed from active records. Main-catalog evidence is referenced
by its path and SHA-256; mini has its own identical, hash-bound report copies in
`data/mini_data/validation/ctf/`. Mini scorecards contain only selected records.

The existing checks cover isolated Docker startup, required dependencies,
delivered input hashes, service TCP reachability where applicable, and reference
acceptance plus wrong/empty flag rejection. They do not establish independent
model solving, end-to-end exploit success, guided subtask credit, or official
dynamic scoring. The records therefore remain `ready_with_limitations`.

## Run

Use the [English PowerShell guide](from_zhongzheng/mini_pipeline_powershell.md)
for installation and provider configuration. Docker must be running with Linux
containers. Build the contestant image from the repository root:

```sh
docker build -t agent-olympiad-ctf:v1 docker/ctf
python scripts/run_mini_dataset.py all --provider YOUR_PROVIDER --model YOUR_MODEL_ID --competitions cybench --system-variant single_agent --output results/mini_cybench_new
```

Use `--competitions nyu_ctf_bench` for NYU, or a comma-separated list for both.
These commands launch model experiments. Use `scripts/run_pipeline.py` for the
main catalog. The existing controller only exposes reviewed task mappings and
contestant assets; source trees and judge references are not contestant input.

## Refresh and verify metadata

After new main-catalog runtime validation, update the existing mini selection:

```sh
python scripts/refresh_ctf_metadata.py --audit-dir results/ctf_metadata_refresh_new
python scripts/verify_mini_dataset.py --output results/ctf_mini_preflight_new.json
python scripts/audit_mini_dependency_hashes.py
python scripts/write_mini_dataset_docs.py
```

The refresh verifies recorded report hashes and per-task passed status, saves a
change manifest and rollback archive, replaces old readiness text, and rebuilds
mini scorecards. It does not rerun Docker or models, change task membership,
alter scoring rules, or delete source material. Refreshing metadata changes run
identity; use a fresh output directory for subsequent experiments.
