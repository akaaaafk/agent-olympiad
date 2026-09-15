# Model Provider Profiles

`openagents.json` is loaded by `src/env_config.py` whenever `--provider openagents`
is selected. It selects the Chat Completions endpoint, dedicated environment
variable names, and default model. It does not select a baseline or start a run.

Environment overrides: `OPENAGENTS_API_KEY`, `OPENAGENTS_BASE_URL`,
`OPENAGENTS_MODEL`. Keep credentials in `.env`, never in this directory.
An explicit `--model` overrides the environment/profile model. Perplexity remains
the default provider for existing commands.

The old repository-local `OPENAI_*` block is recognized only when its base URL
is exactly the OpenAgents gateway. Dedicated `OPENAGENTS_*` values take priority;
an inherited `OPENAI_API_KEY` is never used as the gateway credential.

From the repository root, select a baseline explicitly:

```powershell
E:\agent_olympiad\.venv\Scripts\python.exe src\run_competition_batch.py --live --contest-manifest data\contest_manifests\arml_local_2009.json --system-variant vallina_otc --provider openagents --model glm-5.2 --judge-provider openagents --judge-model glm-5.2 --max-output-tokens 8192 --max-total-tokens 220000 --temperature 0.2 --action-calling native --output results\openagents_glm52_arml2009_control_new
```

Use `--system-variant otc` and a different fresh output directory for the memory
condition. Match all other settings, task manifests and judge settings. The main
contest runner otherwise defaults to a Perplexity collaboration judge even when
the solver provider differs; explicitly set `--judge-provider` as above.

The artifact entry `src/run_otc_artifact.py` also accepts `--provider openagents`
and `--judge-provider openagents`. PDF attachments are rendered into page images;
live image understanding is model-dependent and has not been validated by the
text/tool smoke checks. Batch wrappers can pin their own model, so pass both
provider and model when using them.

Verified on 2026-09-14: authenticated `glm-5.2` text and native `rest` tool calls.
`kimi-k2.6` rejected temperature 0.2 with HTTP 400 (requires temperature 1).
Changing temperature creates a different experimental setting; do not silently
pool those runs with the temperature-0.2 cohort.
