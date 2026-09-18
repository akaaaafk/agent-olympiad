# PowerShell experiment commands by competition

Date: 2026-09-16. Current checkout; Tinker; Qwen/Qwen3.6-35B-A3B.

## Usage

Choose ONE competition at a time. Run decentralized first, then centralized in the same PowerShell window. Do not execute this entire document at once. Each command visits all registered sessions for the selected competition without a pilot limit.

PowerShell commands use argument arrays (`$runArgs` / `@runArgs`), one argument per line, with no backtick continuations. Copy the entire code block without terminal prompts such as `PS ...>` or `>>`. Press Ctrl+C first if the terminal is waiting for unfinished input.

One provider per run: `--provider` controls contestants, leader planning/Coach, task scoring, and collaboration judges. Omit `--judge-provider`; it inherits the selected provider. Explicit mismatches now fail before any API call. `--judge-model` may select another model only within the same provider; omitted judges inherit `--model`. To use Perplexity instead of Tinker, change `--provider` to `perplexity` and `--model` to a supported Perplexity model (for example, `openai/gpt-5.4-mini`). Start a fresh output directory when changing providers; do not relabel or resume a run created with another provider.

Run this setup once:

```powershell
Set-Location E:\agent_olympiad\agent-olympiad
$py = 'E:\agent_olympiad\.venv\Scripts\python.exe'
```

API keys are loaded from the project .env. These commands launch new paid solver runs with fresh output directories. They do not convert existing single_agent or OTC results and do not overwrite results/tinker_mcm_pdftext_20260916.

Registration includes the whole catalog, but --competitions restricts execution to the selected track. Unready data, missing inputs, unavailable judges, and unsupported environments remain blocked. Valid results for every record are not guaranteed. ICPC requires Docker and a healthy local gateway.

Variant propagation and mandatory collaboration evaluation are tested for native and artifact routes. Full paid execution has not been verified. Unrelated historical catalog/test fixtures still need alignment.

## macOS / Linux (Bash / Zsh)

Use the commands below in a macOS or Linux terminal. First enter the local latest checkout and replace the path with your actual path. You need a Unix Python environment with the project dependencies installed and the project `.env`. Windows `.venv/Scripts/python.exe` cannot be used here.

```bash
cd /path/to/agent-olympiad
# Use the local Python that already has the project dependencies installed, for example the Unix venv inside the project:
py="$PWD/.venv/bin/python"
# If the venv is one level above the checkout, use:
# py="$PWD/../.venv/bin/python"
"$py" --version
```

Choose one competition at a time. Set `competition` to a track ID listed in the sections below. Run decentralized first, then centralized after it succeeds. Do not set a pilot limit. Each pair uses its own new output directory. Both baselines default to rules off.

```bash
competition='arml_local'
runTag="$(date '+%Y%m%d_%H%M%S')_$$"

for variant in decentralized centralized; do
  output="results/${competition}_${variant}_${runTag}"
  if [ -e "$output" ]; then
    printf 'Output already exists: %s\n' "$output" >&2
    break
  fi
  "$py" -u scripts/run_pipeline.py all \
    --competitions "$competition" \
    --system-variant "$variant" \
    --provider tinker \
    --model 'Qwen/Qwen3.6-35B-A3B' \
    --judge-provider tinker \
    --judge-model 'Qwen/Qwen3.6-35B-A3B' \
    --output "$output" || break
done
```

Use the latest pipeline. For native contests, the pipeline generates and passes each session's `--contest-manifest`. Document and slide contests follow the matching artifact path. Do not add the legacy `--schema` flag. Records whose data is not ready or whose evaluator is unavailable still block. If the process exits with a failure, check `batch_status.json` in that output directory first.

To resume, pass the original output directory, competition, and variant, and use `run`. Do not generate a new timestamp:

```bash
"$py" -u scripts/run_pipeline.py run \
  --competitions arml_local \
  --system-variant decentralized \
  --provider tinker \
  --model 'Qwen/Qwen3.6-35B-A3B' \
  --judge-provider tinker \
  --judge-model 'Qwen/Qwen3.6-35B-A3B' \
  --output 'results/YOUR_EXISTING_OUTPUT_DIRECTORY'
```

Refresh the pipeline report only, without calling the solver:

```bash
"$py" scripts/run_pipeline.py report \
  --output 'results/YOUR_EXISTING_OUTPUT_DIRECTORY'
```

Re-evaluate existing results (this spends evaluation API quota), or export existing metrics only:

```bash
"$py" -u src/evaluate_saved_metrics.py \
  --output 'results/YOUR_EXISTING_OUTPUT_DIRECTORY' \
  --judge-provider tinker \
  --judge-model 'Qwen/Qwen3.6-35B-A3B'

"$py" src/evaluate_saved_metrics.py \
  --output 'results/YOUR_EXISTING_OUTPUT_DIRECTORY' \
  --report-only
```

## 1. arml_local

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_local'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_local_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_local'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_local_centralized_$runTag"
)
& $py @runArgs
```

### Single-session ARML Local 2009: centralized + Tinker

This self-contained command runs only the 2009 session: 6 agents, 10 questions, and 10 default turns. It creates a fresh timestamped output directory and uses Tinker for solving and collaboration evaluation. Local uses gold-answer task scoring, which differs from the ARML Power document-rubric evaluation path.

```powershell
Set-Location 'E:\agent_olympiad\agent-olympiad'
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
$runArgs = @(
    '-u'
    'src\run_competition_batch.py'
    '--live'
    '--contest-manifest'
    'data\contest_manifests\arml_local_2009.json'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--judge-collab'
    '--max-total-tokens'
    '220000'
    '--max-output-tokens'
    '8192'
    '--output'
    "results\arml_local_2009_centralized_tinker_$runTag"
)
& 'E:\agent_olympiad\.venv\Scripts\python.exe' @runArgs
```

To resume after this process exits, use the following in the same PowerShell window only while `$runArgs` still contains the original arguments. This reuses the original output directory; do not regenerate `$runTag`. The run configuration and source identity must match.

```powershell
$resumeArgs = @($runArgs) + @('--resume')
& 'E:\agent_olympiad\.venv\Scripts\python.exe' @resumeArgs
```

## 2. mcm

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'mcm'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\mcm_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'mcm'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\mcm_centralized_$runTag"
)
& $py @runArgs
```

## 3. ijso_practical

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ijso_practical'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ijso_practical_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ijso_practical'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ijso_practical_centralized_$runTag"
)
& $py @runArgs
```

## 4. ieo_business_case

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ieo_business_case'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ieo_business_case_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ieo_business_case'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ieo_business_case_centralized_$runTag"
)
& $py @runArgs
```

## 5. iol_team

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'iol_team'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\iol_team_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'iol_team'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\iol_team_centralized_$runTag"
)
& $py @runArgs
```

## 6. ioaa_group

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ioaa_group'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ioaa_group_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ioaa_group'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ioaa_group_centralized_$runTag"
)
& $py @runArgs
```

## 7. arml_power

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_power'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_power_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_power'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_power_centralized_$runTag"
)
& $py @runArgs
```

## 8. arml_national_team

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_national_team'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_national_team_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_national_team'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_national_team_centralized_$runTag"
)
& $py @runArgs
```

## 9. arml_national_power

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_national_power'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_national_power_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'arml_national_power'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\arml_national_power_centralized_$runTag"
)
& $py @runArgs
```

## 10. wsc_writing

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'wsc_writing'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\wsc_writing_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'wsc_writing'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\wsc_writing_centralized_$runTag"
)
& $py @runArgs
```

## 11. jessup

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'jessup'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\jessup_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'jessup'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\jessup_centralized_$runTag"
)
& $py @runArgs
```

## 12. iiot

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'iiot'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\iiot_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'iiot'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\iiot_centralized_$runTag"
)
& $py @runArgs
```

## 13. icpc

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'icpc'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\icpc_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'icpc'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\icpc_centralized_$runTag"
)
& $py @runArgs
```

## 14. iypt

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'iypt'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\iypt_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'iypt'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\iypt_centralized_$runTag"
)
& $py @runArgs
```

## 15. hmmt_team

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'hmmt_team'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\hmmt_team_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'hmmt_team'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\hmmt_team_centralized_$runTag"
)
& $py @runArgs
```

## 16. icm

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'icm'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\icm_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'icm'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\icm_centralized_$runTag"
)
& $py @runArgs
```

## 17. fyziklani

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'fyziklani'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\fyziklani_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'fyziklani'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\fyziklani_centralized_$runTag"
)
& $py @runArgs
```

## 18. purple_comet

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'purple_comet'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\purple_comet_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'purple_comet'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\purple_comet_centralized_$runTag"
)
& $py @runArgs
```

## 19. itym

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'itym'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\itym_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'itym'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\itym_centralized_$runTag"
)
& $py @runArgs
```

## 20. ccdc

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ccdc'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ccdc_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ccdc'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ccdc_centralized_$runTag"
)
& $py @runArgs
```

## 21. cfa_research_challenge

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'cfa_research_challenge'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\cfa_research_challenge_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'cfa_research_challenge'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\cfa_research_challenge_centralized_$runTag"
)
& $py @runArgs
```

## 22. cybench

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'cybench'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\cybench_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'cybench'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\cybench_centralized_$runTag"
)
& $py @runArgs
```

## 23. debatebench

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'debatebench'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\debatebench_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'debatebench'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\debatebench_centralized_$runTag"
)
& $py @runArgs
```

## 24. eoes

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'eoes'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\eoes_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'eoes'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\eoes_centralized_$runTag"
)
& $py @runArgs
```

## 25. ethics_bowl_appe

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ethics_bowl_appe'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ethics_bowl_appe_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ethics_bowl_appe'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ethics_bowl_appe_centralized_$runTag"
)
& $py @runArgs
```

## 26. ethics_bowl_nhseb

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ethics_bowl_nhseb'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ethics_bowl_nhseb_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ethics_bowl_nhseb'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ethics_bowl_nhseb_centralized_$runTag"
)
& $py @runArgs
```

## 27. gcch_harvard

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'gcch_harvard'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\gcch_harvard_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'gcch_harvard'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\gcch_harvard_centralized_$runTag"
)
& $py @runArgs
```

## 28. ichto

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ichto'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ichto_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ichto'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ichto_centralized_$runTag"
)
& $py @runArgs
```

## 29. ioai_team

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ioai_team'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ioai_team_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'ioai_team'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\ioai_team_centralized_$runTag"
)
& $py @runArgs
```

## 30. mystery_hunt

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'mystery_hunt'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\mystery_hunt_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'mystery_hunt'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\mystery_hunt_centralized_$runTag"
)
& $py @runArgs
```

## 31. nyu_ctf_bench

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'nyu_ctf_bench'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\nyu_ctf_bench_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'nyu_ctf_bench'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\nyu_ctf_bench_centralized_$runTag"
)
& $py @runArgs
```

## 32. odyssey_of_the_mind

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'odyssey_of_the_mind'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\odyssey_of_the_mind_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'odyssey_of_the_mind'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\odyssey_of_the_mind_centralized_$runTag"
)
& $py @runArgs
```

## 33. pumac_power

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'pumac_power'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\pumac_power_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'pumac_power'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\pumac_power_centralized_$runTag"
)
& $py @runArgs
```

## 34. qanta

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'qanta'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\qanta_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'qanta'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\qanta_centralized_$runTag"
)
& $py @runArgs
```

## 35. science_bowl

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'science_bowl'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\science_bowl_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'science_bowl'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\science_bowl_centralized_$runTag"
)
& $py @runArgs
```

## 36. science_olympiad

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'science_olympiad'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\science_olympiad_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'science_olympiad'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\science_olympiad_centralized_$runTag"
)
& $py @runArgs
```

## 37. vis_moot

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'vis_moot'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\vis_moot_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'vis_moot'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\vis_moot_centralized_$runTag"
)
& $py @runArgs
```

## 38. wharton_investment

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'wharton_investment'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\wharton_investment_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'wharton_investment'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\wharton_investment_centralized_$runTag"
)
& $py @runArgs
```

## 39. wmtc

Set the timestamp for this competition batch:

```powershell
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss'
```

### decentralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'wmtc'
    '--system-variant'
    'decentralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\wmtc_decentralized_$runTag"
)
& $py @runArgs
```

### centralized

```powershell
$runArgs = @(
    '-u'
    'scripts\run_pipeline.py'
    'all'
    '--competitions'
    'wmtc'
    '--system-variant'
    'centralized'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--output'
    "results\wmtc_centralized_$runTag"
)
& $py @runArgs
```

## Results and resume

Each output directory contains summary.tsv, batch_status.json, runs/, and logs/. Inspect states and logs for failed or blocked jobs. A nonzero exit code does not mean saved outputs were lost.

To resume, copy the original command, replace all with run, and use the exact existing output directory. Keep the same competition, variant, model, and judging options. Do not create a new timestamp for resume. Changed code or input identities require a fresh output directory.

Refresh reports only, without solver calls:

```powershell
$runArgs = @(
    'scripts\run_pipeline.py'
    'report'
    '--output'
    "results\YOUR_EXISTING_OUTPUT_DIRECTORY"
)
& $py @runArgs
```

## Automatic evaluation and required metrics

Newly started experiments automatically evaluate the task score, Communication, Planning, and CS, and they write accuracy, turns, api_calls, tokens, and sec. CS = (Communication + Planning) / 2. This also applies to paper and slide tasks. Solver usage and evaluator usage are counted separately. The Tinker token estimate basis is stored in tokens_basis.

A multi-agent experiment missing a valid collaboration score is marked evaluation_pending and must not be treated as complete. A resume fills in only the missing evaluations. It does not re-solve or re-score a completed paper task. single_agent records only the task score and run usage. It does not call Communication, Planning, CS, or interaction collaboration evaluation. Collaboration fields in the shared table are N/A (not applicable), not 0. Unsubmitted artifacts or tasks missing an evaluator cannot automatically become a valid score.

Each run directory automatically writes required_metrics.json and required_metrics.csv. Native paths also keep contest_summary.csv. The pipeline summary.tsv includes every required metric and separate evaluation-usage fields.

### Existing MCM results: evaluation only

The command below calls the evaluation model and spends evaluation API quota. It does not call the solver, and it does not change task scores in historical contest_session.json or result.json. Evaluations that are already complete and whose evidence still matches are reused.

```powershell
$runArgs = @(
    '-u'
    'src\evaluate_saved_metrics.py'
    '--output'
    'results\tinker_mcm_pdftext_20260916'
    '--judge-provider'
    'tinker'
    '--judge-model'
    'Qwen/Qwen3.6-35B-A3B'
)
& $py @runArgs
```

A batch directory is scanned for existing contest_session.json files. Tasks whose solve did not finish, or whose original task input cannot be recovered, stay explicitly evaluation_pending. The aggregate outputs are required_metrics_summary.csv and required_metrics_status.json. Tasks that never started solving do not get invented results.

### ARML Power: resume after a judge JSON failure (--resume)

If `run_otc_artifact.py` fails during judging with `Malformed evaluator JSON`, use the full command below. Keep the original output directory and every run argument, and add `--resume`. When `contest_session.json` already exists, the contestant answers and submission are reused, the unfinished judge call is made again, and the required metrics are then filled in. Judging spends API quota. Do not change the output directory or generate a new timestamp.

```powershell
Set-Location E:\agent_olympiad\agent-olympiad
$runArgs = @(
    '-u'
    'src\run_otc_artifact.py'
    '--competition'
    'arml_power'
    '--system-variant'
    'centralized'
    '--task-pdf'
    'data\raw\arml\Fall_2018\ARMLPower_Fall_2018.pdf'
    '--task-pages'
    '1-4'
    '--rubric'
    'E:\agent_olympiad\dataset_backups\integrity_repair_20260916T213429Z\data\rubrics\arml_power_fall_2018_v1.json'
    '--provider'
    'tinker'
    '--model'
    'Qwen/Qwen3.6-35B-A3B'
    '--max-tokens'
    '220000'
    '--max-output-tokens'
    '8192'
    '--output'
    'results\arml_power_fall_2018_centralized_new'
    '--resume'
    '--evaluation-only'
)
& 'E:\agent_olympiad\.venv\Scripts\python.exe' @runArgs
```

This fix and other local updates changed the source and action-set versions, so also pass `--evaluation-only`. It allows evaluation-only resume for runs whose contestant phase has already finished, and it allows code and protocol version updates. It still strictly checks the task, rubric contents, model, and run configuration. The original run identity is preserved, and the current evaluation-code identity is appended to `evaluation_resume_identity.jsonl`. A plain `--resume` still requires the source identity to match.

The rubric used by this older run was also updated by a later data repair. The `--rubric` above points at the original copy in the backup. Its SHA256 is `c0c0bd4d07a6755c8a0f48cf588fb5fc94dc5caa8d9f7bf1b1298be5907d2e96`, which matches the old run exactly. Do not switch to the new rubric when continuing an old experiment.

A newly started process recovers judge format errors by default; no extra flag is required. It first locally repairs clearly illegal JSON backslash escapes. If parsing still fails or the payload does not match the rubric, it automatically retries judging at most twice (three attempts in total) and does not re-run the contestants. It accepts the first valid score, including zero, and does not pick the highest score. Retries spend judge API quota and record usage. The process exits only after all three attempts fail, and the contestant result is kept. Every artifact-judge response is appended to `judge_responses.jsonl`. Repairs and retries are recorded in the scoring warnings. If a resume reports an identity mismatch, do not delete or hand-edit the historical identity.

### ARML Power: fill required metrics only after task scoring is done

A process that is already running does not pick up code updates automatically. After the current experiment finishes, run:

```powershell
$runArgs = @(
    '-u'
    'src\evaluate_saved_metrics.py'
    '--output'
    'results\arml_power_fall_2018_centralized_new'
    '--judge-provider'
    'tinker'
    '--judge-model'
    'Qwen/Qwen3.6-35B-A3B'
)
& $py @runArgs
```

### Export existing metrics only, without calling the evaluation model

```powershell
$runArgs = @(
    'src\evaluate_saved_metrics.py'
    '--output'
    'results\tinker_mcm_pdftext_20260916'
    '--report-only'
)
& $py @runArgs
```

Missing or invalid collaboration evaluations stay marked pending. They are not filled with invented scores.
