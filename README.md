# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks** (not solo paper tests). Part of the **Agent Olympiad** research project at DAPLab.

## Current focus

1. **IEO Business Case** (rubric-based pilot) — pipeline working, 5 agents, configurable rounds
2. **5 test-based team olympiads** — IOL Team, IOAA Group, ARML Power, EUSO, IJSO Practical (up to 30 full problems each from multiple years, in progress)

See [`data/olympiads/README.md`](data/olympiads/README.md) for schemas, gold-score sources, and collection status.

## Quick start

```bash
export PERPLEXITY_API_KEY="pplx-..."

# IEO Business Case — 20 rounds, slides
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 slides --rounds 20

# Smoke test (2 agents, 2 rounds)
python3 run_multiagent_experiment.py agent:openai/gpt-5.4-mini slides --smoke

# Score teamwork on saved discussion logs
python3 score_teamwork.py
```

## Repository structure

```
agent_olympiad_econ/
├── run_multiagent_experiment.py   # Main multi-agent pipeline
├── score_teamwork.py              # Teamwork scorer (retroactive on JSON logs)
├── run_experiment.py              # Legacy single-agent IEO open questions
├── scripts/scaffold_olympiad_slots.py
├── data/
│   ├── olympiads/                 # 5 test olympiads + IEO business case
│   ├── raw/business_case/         # IEO PDFs 2021–2025
│   └── processed/                 # Results JSON/MD
```

## Results so far (IEO 2025 Caspian Connector)

| Run | Score | Teamwork |
|---|---|---|
| GPT-5.5 report | 46/50 | 10/10 |
| GPT-5.5 slides | 44/50 | 9.9/10 |

Human baseline (2025 winner Canada): **92.5/100** raw — not directly comparable to LLM judge /50.

## Legacy

Single-agent IEO open-ended questions remain in `data/processed/ieo_benchmark.json` and `run_experiment.py` but are no longer the primary track.
