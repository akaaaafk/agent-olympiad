# Multi-Agent Olympiad Benchmarks

Five **test-based** team olympiads (OlympiadMAS) + **IEO Business Case** rubric pilot.

**Target:** up to 30 **full** team tasks per olympiad. Each slot is one complete published problem (internal sub-parts stay together). Collect across years/contests; some olympiads have fewer than 30 in the archive (e.g. IOL Team has 24, IOAA Group ~18).

## Olympiads

| ID | Type | Team | Source | Status |
|---|---|---|---|---|
| `iol_team` | test | 4 | [ioling.org/problems](https://ioling.org/problems/by_year/) | scaffolded |
| `ioaa_group` | test | 5 | [ioaastrophysics.org](https://ioaastrophysics.org/resources/problems-from-past-ioaa) | scaffolded |
| `arml_power` | test | variable | [arml.com power archive](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=samples) | scaffolded |
| `euso` | test | 3 | [euso.eu](http://euso.eu/) | scaffolded |
| `ijso_practical` | test | 3 | [ijsoweb.org](https://ijsoweb.org/downloads) | scaffolded |
| `ieo_business_case` | rubric | 5 | IEO PDFs in `data/raw/business_case/` | **1 problem, pipeline working** |

See `index.json` for collection strategy and gold-score notes per olympiad.

**Format reference (all 6 olympiads + human gold scores):** [`FORMAT.md`](FORMAT.md)

## Problem JSON schema (test-based)

```json
{
  "problem_id": "iol_team_2023_murrinh_patha",
  "competition": "International Linguistics Olympiad",
  "year": 2023,
  "topic": "Team Contest — Murrinh-patha",
  "task_type": "team_contest",
  "team_size": 4,
  "source_url": "https://ioling.org/problems/2023/",
  "source_file": "data/raw/iol/2023_team.pdf",
  "total_points": 20,
  "problem_description": "Full problem text as published (all sub-parts included)",
  "gold_label": {
    "expected_answer": "Official solution or marking scheme for the whole task",
    "grading_rubric": "Official points breakdown for the full problem",
    "human_baseline": "Top team score if published, or null"
  }
}
```

## Gold scores

| Olympiad | Human out of | AI judge out of | Gold source | Human baseline (example) |
|---|---|---|---|---|
| IOL Team | Varies (e.g. /200) | /100 | Solutions PDF per year | 200.0/200 Taiwan 2025 |
| IOAA Group | Time-ranked | /100 | Marking schemes in solution PDFs | Fastest team wins |
| ARML Power | /40 | /40 | Solution PDFs | 36–40/40 top teams |
| EUSO | /100 (%) | /100 | Model answers on euso.eu | 97.5/100 Germany 2004 |
| IJSO Practical | /40 | /40 | Marking PDFs on ijsoweb.org | Gold team top /40 |
| IEO Business Case | /50 BC; /100 overall | /50 | Grading rubric | Canada 92.5/100 overall 2025 |

See [`FORMAT.md`](FORMAT.md) for full competition rules and pipeline mapping.

## Run

```bash
export PERPLEXITY_API_KEY="pplx-..."

# IEO Business Case — 20 rounds, slides (default)
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 agent:openai/gpt-5.5 slides --rounds 20

# Smoke test (2 agents, 2 rounds, gpt-4o-mini)
python3 run_multiagent_experiment.py agent:openai/gpt-5.4-mini slides --smoke

# IOL Team (15 years collected; image-only PDFs need OCR for the rest)
python3 scripts/collect_iol_team.py
python3 run_multiagent_experiment.py agent:openai/gpt-5.4-mini --olympiad iol_team --smoke --limit 1
```

Generate 30 placeholder slots per test olympiad:

```bash
python3 scripts/scaffold_olympiad_slots.py
```
