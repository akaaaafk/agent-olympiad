# Meeting Brief for Yusen (Jun 2025)

## One-sentence pitch

We built a **multi-agent olympiad benchmark pipeline**: teams of LLM agents collaborate on real team-competition tasks, submit answers, and get scored by an external judge against official solutions or rubrics.

---

## What you asked for vs where we are

| Goal | Status |
|------|--------|
| **5 test-based olympiad datasets** | ✅ Structure + collection scripts for all 5 |
| **≥30 problems each** | ❌ **Not there yet** — limited by what's published online |
| **Smoke tests (GPT mini)** | ✅ Pipeline works; running 1 problem × 5 olympiads now |
| **External judge (Claude)** | ✅ Supported; smoke runs use Claude as judge |
| **IEO Business Case (bonus)** | ✅ 5 years collected; full GPT-5.5 20-round run on 2025 |

### Dataset counts (honest)

| Olympiad | Collected | Target | Gold solutions | Blocker |
|----------|-----------|--------|----------------|---------|
| IOL Team | **19** | 30 (~24 exist) | 16 | Image PDFs, dead links |
| IOAA Group | **9** | ~18 max | 4 | Few years publish group PDFs |
| ARML Power | **15** | 30 | 11 | Need older archive seasons |
| EUSO | **14** | 30 | 0 | Dead URLs 2005–2014; no marking PDFs scraped |
| IJSO Practical | **14** | ~22 max | 12 | 2004–2006, 2015 URLs dead |

**We cannot honestly claim 30×5 yet.** Some olympiads don't have 30 team tasks in public archives. Next step is manual PDF collection + OCR for gaps.

---

## What the pipeline does

```
Problem text → N agents × R discussion rounds → final answer/slides
                                              → external judge scores vs gold
```

- **Test olympiads** (IOL, IOAA, ARML, EUSO, IJSO): format `answer`, judge vs official solution (/40 or /100)
- **IEO Business Case**: format `slides`/`report`, judge vs rubric (/50)
- **No web search** in test runs (matches IOL rules); IEO BC should allow internet (not enabled yet)
- See `data/olympiads/FORMAT.md` for rules per competition

---

## Completed experiment runs

| Run | Agents | Judge | Result |
|-----|--------|-------|--------|
| IEO 2025 Business Case, 20 rounds, slides | GPT-5.5 × 5 | GPT-5.5 | **45/50** |
| IEO 2025 Business Case, 3 rounds, report | GPT-5.5 × 5 | GPT-5.5 | **46/50** |
| IOL Team, 9 gold years, 3 rounds | GPT-5.5 × 4 | GPT-5.5 | avg ~51/100 (3 zeros from API truncation) |
| IOL smoke, 2023 | GPT-5.4-mini × 2 | GPT-5.4-mini | **99/100** |

Files: `data/processed/multiagent_*.json` and `.md`

---

## Smoke test results (completed)

**Config:** GPT-5.4-mini agents (2×2 rounds), **Claude Sonnet 4.6** judge, 1 problem each.

| Olympiad | Problem | Score |
|----------|---------|-------|
| IOL Team | 2008 Fanqie | **29/100** |
| IOAA Group | 2025 | **9/150** |
| ARML Power | Fall 2018 | **19/40** |
| IJSO Practical | 2009 | **46/100** |
| EUSO | 2003 exp 1 | **81/100** |

Results: `data/processed/multiagent_*_2r_openai_gpt-5_4-mini_judgedby_anthropic_claude-sonnet-4-6.{json,md}`  
Log: `data/processed/smoke_all_olympiads.log`

---

## Smoke tests in progress (for this meeting)

**Config:** `gpt-5.4-mini` agents, **Claude Sonnet 4.6** judge, 2 agents × 2 rounds, 1 problem per olympiad.

Log: `data/processed/smoke_all_olympiads.log`

---

## Repo

https://github.com/selinkaracaa/agent-olympiad

Key paths:
- `data/olympiads/*/benchmark.json` — datasets
- `run_multiagent_experiment.py` — main runner
- `scripts/collect_*.py` — PDF download + extract

---

## What to tell Yusen we need

1. **Time to collect** remaining PDFs (or help sourcing EUSO/IOL image scans)
2. **Confirm target:** 30 per olympiad vs "as many as exist" (IOL max ~24, IOAA ~18)
3. **Web search for IEO BC** — match real competition rules
4. **Human baseline scores** — extract from results booklets per year

---

## Commands to demo live

```bash
export PERPLEXITY_API_KEY="..."

# Smoke test one olympiad
python3 run_multiagent_experiment.py agent:openai/gpt-5.4-mini agent:anthropic/claude-sonnet-4-6 \
  --olympiad iol_team --smoke --limit 1 --with-gold

# Full IEO business case
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 agent:openai/gpt-5.5 slides --rounds 20
```
