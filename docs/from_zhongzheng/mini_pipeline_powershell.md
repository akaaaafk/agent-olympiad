# Mini pipeline: PowerShell guide

Run from the repository root with Python 3.12. The independent catalog is
`data/mini_data` inside this checkout. No machine-specific path is required.

## Install and configure

```powershell
python -m venv .venv
$py = Join-Path (Get-Location) '.venv/Scripts/python.exe'
& $py -m pip install -r requirements.txt
& $py -m pip check
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
```

Edit `.env` with your chosen provider key. Replace the model placeholder with an
exact model available to your account. To use an existing environment, set `$py`
to its Python executable instead.

```powershell
$provider = 'tinker'
$model = 'YOUR_MODEL_ID'
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
$common = @('--provider', $provider, '--model', $model)
```

See [model interfaces](../public_model_interfaces.md) for other providers and
custom endpoints. This probe makes two small paid calls without a competition:

```powershell
& $py scripts/check_provider.py @common
```

## Register and run one bounded smoke session

```powershell
& $py scripts/verify_mini_dataset.py --output "results/mini_preflight_$runTag.json"
$out = "results/mini_single_agent_$runTag"
& $py scripts/run_mini_dataset.py register --output $out
$smoke = @('--competitions', 'arml_local', '--system-variant', 'single_agent',
           '--limit', '1', '--max-turns', '10', '--max-api-calls', '24',
           '--max-total-tokens', '20000')
& $py -u scripts/run_mini_dataset.py run @common @smoke --output $out
```

Verification and registration make no model calls. Read both `passed` and
`all_jobs_environment_ready`: valid data may still need external services.
Execution is paid. A mini session can include multiple questions. Production
turn limits are clamped to 10-90. Use matched budgets for baseline comparisons.

## All five baselines, sequentially

These commands launch every mini track. API and total token caps are unset unless
you supply them; choose suitable budgets before a full run.

```powershell
foreach ($variant in @('single_agent', 'decentralized', 'centralized', 'vallina_otc', 'otc')) {
    & $py -u scripts/run_mini_dataset.py all @common --system-variant $variant `
        --output "results/mini_all_${variant}_$runTag"
    if ($LASTEXITCODE -ne 0) { break }
}
```

`vallina_otc` is the existing CLI spelling. Team sizes, actions, and permissions
come from the existing competition definitions.

## Select a track, year, or session

Use IDs in `data/mini_data/selection_manifest.json` and the registered
`registry.json`. Unmatched filters are errors.

```powershell
& $py -u scripts/run_mini_dataset.py all @common --competitions cybench `
    --system-variant single_agent --output "results/mini_cybench_$runTag"
& $py -u scripts/run_mini_dataset.py all @common --competitions arml_local --years 2013 `
    --system-variant otc --output "results/mini_arml_2013_otc_$runTag"
```

`--competitions`, `--years`, and `--sessions` accept comma-separated values.
Use `scripts/run_pipeline.py` for editions in the main catalog. Do not mix main
and mini into the same output directory.

## External services

Start Docker and prepare images for the selected runner. LaTeX setup:

```powershell
docker info
docker build -t agent-olympiad-latex:v1 docker/latex
```

ICPC requires a configured VJudge gateway. In another terminal using the same
repository/environment:

```powershell
& $py -u src/vjudge_gateway.py serve --host 127.0.0.1 --port 8787
```

Configure `VJUDGE_GATEWAY_URL` and judge credentials using the
[gateway guide](../VJUDGE_INTEGRATION_FEASIBILITY.md). A listening port does not
prove authenticated judging. See [CTF delivery](../ctf.md)
for CTF images, reviewed mappings, and exact-flag grading limitations.

## Resume and inspect

Keep the same output directory and all original settings:

```powershell
& $py -u scripts/run_mini_dataset.py run @common @smoke --output $out
& $py scripts/run_mini_dataset.py report --output $out
Import-Csv (Join-Path $out 'summary.tsv') -Delimiter "`t" | Format-Table
```

In a new terminal, restore `$out` to the existing path and recreate the same
arguments. Use `run`, not `all` or `register`, to preserve a prepared smoke
registry. Verified completed work is skipped; checkpoints and missing evaluation
are continued where possible. Source/configuration changes need a fresh output.

Read `batch_status.json`, `summary.tsv`, and `logs/<job>.log` together.
`evaluation_pending` does not mean contestants must start again. Check the lock
owner and child processes before treating a lock as stale. The per-job timeout
defaults to 21,600 seconds; configure it with `--job-timeout-seconds`.
