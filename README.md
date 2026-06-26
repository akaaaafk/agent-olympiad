# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks** (not solo paper tests). Part of the **Agent Olympiad** research project at DAPLab.

Pipeline: problem text → N agents × R discussion rounds → synthesized answer → external judge vs gold solution.

## Quick start

```bash
pip install -r requirements.txt
export PERPLEXITY_API_KEY="pplx-..."

# Smoke test (2 agents, 2 rounds)
python3 src/run.py agent:openai/gpt-5.4-mini slides --smoke

# IEO Business Case — 20 rounds, slides
python3 src/run.py agent:openai/gpt-5.5 slides --rounds 20

# Score teamwork on saved discussion logs
python3 src/score_teamwork.py
```

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/STATUS.md`](docs/STATUS.md) | Dataset counts, experiment scores, human baselines |
| [`docs/FORMAT.md`](docs/FORMAT.md) | Per-olympiad format reference and scoring scales |
| [`data/benchmarks/index.json`](data/benchmarks/index.json) | Olympiad catalog and collection status |
| [`results/`](results/) | Experiment outputs grouped by run |

## Repository structure

```
├── src/
│   ├── run.py                 # Main multi-agent pipeline
│   ├── score_teamwork.py      # Teamwork scorer on saved JSON logs
│   └── collectors/              # PDF download + benchmark.json builders
├── data/
│   ├── benchmarks/            # Curated problem JSON (5 olympiads)
│   └── raw/                   # Source PDFs (gitignored; run collectors)
├── results/                   # Experiment outputs
├── docs/                      # STATUS.md, FORMAT.md
└── archive/                   # Legacy single-agent IEO track
```

## Olympiads

| ID | Type | Team size |
|----|------|-----------|
| `iol_team` | test | 4 |
| `ioaa_group` | test | 5 |
| `arml_power` | test | variable |
| `ijso_practical` | test | 3 |
| `ieo_business_case` | rubric | 5 |

Collect or refresh problems: `python3 src/collectors/iol_team.py` (and siblings in `src/collectors/`).
