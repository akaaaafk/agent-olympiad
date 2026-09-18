# Model Provider Profiles

For the additional public interfaces (`anthropic`, `gemini`, `deepseek`, and
`openai_compatible`), see [the interface guide](../../docs/public_model_interfaces.md).
Existing profiles and defaults below are unchanged.

VectorEngine: use `--provider vectorengine --judge-provider vectorengine` with
`VECTORENGINE_API_KEY`, `VECTORENGINE_BASE_URL`, and `VECTORENGINE_MODEL`.
The configured `claude-sonnet-5` identifier is a gateway model alias, not a
verified upstream identity. Text/native tools use Chat Completions. Attachments
and the PDF-reader action are disabled pending a successful image preflight.
No other provider's key is borrowed.
Pilot: `python scripts/run_vectorengine_arml2009.py --model claude-sonnet-5`
(one fresh single-agent run; explicit model prevents accidental substitutions).

Provider profiles are loaded by `src/env_config.py`. `openagents.json` selects
the Chat Completions endpoint, dedicated environment variable names, default
model, and the gateway model catalog. `tinker.json` selects the Tinker sampling
API, its credential variable, and its default model. Profiles do not select a
baseline or start a run.

Environment overrides: `OPENAGENTS_API_KEY`, `OPENAGENTS_BASE_URL`,
`OPENAGENTS_MODEL`. Keep credentials in `.env`, never in this directory.
An explicit `--model` overrides the environment/profile model. The `models`
array is an inventory, not an allowlist, so newly released models can still be
selected explicitly before the catalog is refreshed. Perplexity remains the
default provider for existing commands.

OpenAgents reads only `OPENAGENTS_API_KEY`, `OPENAGENTS_BASE_URL`, and
`OPENAGENTS_MODEL`. There is no fallback to `OPENAI_*`, including repository
`.env` values. Reserve `OPENAI_API_KEY` for the real OpenAI provider.
`OPENAGENTS_API_KEY_LEGACY` is an optional backup only; it is never selected
automatically. To switch keys, explicitly update `OPENAGENTS_API_KEY`.

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

The OpenAgents model inventory was refreshed from the gateway `/models` endpoint
on 2026-09-15. Availability is not the same as compatibility: each model still
needs a text/tool smoke test with its required temperature and token settings.
