# Run a specific baseline, competition, and year

## Ready-to-run: ARML Local 2009, decentralized, Tinker Qwen

The repository `.env` currently specifies `TINKER_MODEL=Qwen/Qwen3.6-35B-A3B` and contains `TINKER_API_KEY`. The launcher explicitly selects that model. The Python entrypoint loads the key from `.env`; no key is copied into this document or the launcher.

```powershell
Set-Location E:\agent_olympiad\agent-olympiad
.\scripts\run_arml2009_decentralized_tinker_qwen.ps1
```

This selects:

| Setting | Value |
|---|---|
| Provider | tinker |
| Model | Qwen/Qwen3.6-35B-A3B |
| Baseline | decentralized |
| Competition | arml_local |
| Year | 2009 |
| Session | arml_local_2009 |
| Dataset | Full data catalog |
| Questions | 10 |
| Agents | 6 |
| Turn budget | 10 |

A new timestamped output directory is created automatically. To resume a previous run, specify its existing directory and keep its model and run identity unchanged:

```powershell
.\scripts\run_arml2009_decentralized_tinker_qwen.ps1 `
  -Output 'results/YOUR_EXISTING_RUN_DIRECTORY'
```

The model is explicit in this task-specific launcher, not a global default. If you change the intended model later, use the generic launcher with an explicit model argument.

## Equivalent pipeline command

```powershell
Set-Location E:\agent_olympiad\agent-olympiad
$env:AGENT_OLYMPIAD_DATA_ROOT = Join-Path (Get-Location) 'data'
$Output = "results/arml_local_2009_decentralized_$(Get-Date -Format yyyyMMdd_HHmmss)"

python scripts/run_pipeline.py all `
  --provider tinker `
  --model 'Qwen/Qwen3.6-35B-A3B' `
  --system-variant decentralized `
  --competitions arml_local `
  --years 2009 `
  --sessions arml_local_2009 `
  --output $Output
```

## Select other baselines or years

- `--system-variant`: single_agent, centralized, decentralized, otc, or vallina_otc.
- `--competitions`: competition IDs, optionally comma-separated.
- `--years`: benchmark year values, optionally comma-separated. Years are read from metadata, not guessed from filenames.
- `--sessions`: optional exact session IDs to distinguish multiple packets in the same year.

All filters apply together. A year filter selects every matching session unless narrowed by `--sessions`. No matches produce an error. Refresh old registries without year metadata using `all` or `register`. The `all` stage registers the catalog but executes only the selected jobs.

## Generic PowerShell launcher

```powershell
.\scripts\run_arml2009_decentralized.ps1 `
  -Provider tinker `
  -Model 'Qwen/Qwen3.6-35B-A3B'
```

Without `-ApiKeyEnv`, the Python entrypoint uses the provider key from the environment or repository `.env`. To explicitly select an existing shell variable, add `-ApiKeyEnv YOUR_KEY_VARIABLE`. Existing process environment variables take precedence over `.env` under the repository loader.

## Validation

Offline preflight selected one ready native session with 10 questions, 6 agents, and 10 turns. The 29 selection, pipeline, locking, and recovery tests passed. PowerShell syntax and argument forwarding were checked with a fake executor. No paid experiment was started.
