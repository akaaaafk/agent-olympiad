# Tinker contest queue

Configure `TINKER_API_KEY`, `TINKER_API_KEY2`, and `TINKER_MODEL` in the repo
`.env`. The two keys must be distinct. Existing shell variables take precedence.
No key values appear in command arguments or launch summaries.

Run from the repository root:

```powershell
E:\agent_olympiad\.venv\Scripts\python.exe scripts/run_tinker_parallel.py --manifest data/contest_manifests/generated/arml_local_2009.json --variants vallina_otc otc --key-env TINKER_API_KEY TINKER_API_KEY2
```

Repeat `--manifest PATH` to queue additional competitions. Each manifest is
combined with every selected variant. Each key runs at most one child process
at a time, then takes another job. The child receives its assigned credential
as `TINKER_API_KEY`; the launcher never swaps credentials in a running process.
Two jobs can execute concurrently with two configured slots. Independent
service quotas or a twofold speedup are not established by this implementation.

The runner uses baseline-defined rule modes, temperature 0.2, an 8192 output
limit, 10 turns by default, deadline submission, and deterministic grading.
Auxiliary judges are disabled. `--max-turns` changes the turn cap and uses five
simulated minutes per turn. `--env-file` selects another environment file.

Outputs are under a fresh `results/tinker_parallel_TIMESTAMP` directory:
`summary.json`, and per-job `runner.log`, `launch_summary.json`,
`contest_session.json`, `chat.json`, and `chat.md`. Failed jobs are retained;
other queued jobs continue. A nonzero final exit status indicates an invalid
or unsuccessful result. Each summary records the key variable name, not its value.

Validation: credential-isolation and UTF-8 BOM loading tests passed. A real
single-slot OTC job completed. Two-key live concurrency remains unverified
until the second credential is available in the saved environment file.
