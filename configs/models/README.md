# Model profiles

All profiles use `scripts/run_model_config.py` and the existing contest engine.
Qwen is `Qwen/Qwen3.6-35B-A3B` on Tinker; Kimi, GLM and DeepSeek use OpenAgents.
Credentials stay in `.env` or the shell, never in these JSON files. Existing shell
credentials take precedence over `.env`. Gateway profiles explicitly set the
child process endpoint and credential to avoid falling back to another provider.

From the repository root, preview an ARML 2009 run without any API calls:

```powershell
..\.venv\Scripts\python.exe scripts/run_model_config.py --model-config configs/models/glm-5.2.json --variant vallina_otc --output results/glm52_arml2009_v2/vallina_otc
```

Add `--execute` to run. Switch the model config to `qwen.json`, `kimi-k2.6.json`,
or `deepseek-v4-pro.json`, and use a corresponding new output directory.
Use `--variant otc` for the memory-enabled method. Other method names supported
by the shared runner also work. Use `--resume` only with an unchanged run identity.

`--experiment-config` defaults to `configs/experiments/arml2009.json`. Copy that
file and change `contest_manifest` for another competition. Turns are derived by
the shared engine: `min(90, max(10, ceil(duration_minutes / 5)))`; ARML Local uses
10, ICPC uses 60. Five minutes is simulated time, not a wall-clock timeout.
The current experiment uses 8192 output tokens per call and a 220000 shared
output-token budget; budget exhaustion can stop a run before its turn limit.

Task and collaboration judging are enabled, CCE is disabled, and the judge uses
the contestant model/provider. For cross-model CS comparisons, account for this
judge difference; these profiles do not establish a fixed independent judge.
Preview validates local runner configuration, not remote model availability or
authentication. Existing `run_config.json` files remain runner-generated records.
