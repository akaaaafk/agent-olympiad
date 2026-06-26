# Experiment results

Outputs from `src/run.py`. New runs default to `results/multiagent_*.json` at this level.

## Grouped runs

| Folder | Agents | Rounds | Judge | Olympiads |
|--------|--------|--------|-------|-----------|
| `gold-batch-2025-06-19/` | GPT-5.4-mini | 2 | Claude Sonnet 4.6 | IOL, IOAA, ARML, IJSO |
| `iol-gpt55/` | GPT-5.5 | 3 | GPT-5.5 | IOL Team |
| `iol-gpt54-mini-2r/` | GPT-5.4-mini | 2 | GPT-5.4-mini | IOL Team (smoke) |
| `ieo-2025-gpt55/` | GPT-5.5 | 3 or 20 | GPT-5.5 | IEO Business Case 2025 |

Each olympiad subfolder contains `answer.json` (full logs) and `answer.md` (readable summary).

## Other

- `summaries/` — cross-run score tables
- `legacy/` — deprecated single-agent IEO open questions and early experiments
- `logs/` — run logs (gitignored)
