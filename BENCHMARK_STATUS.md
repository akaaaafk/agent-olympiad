# Olympiad Benchmark — Status & Results

Last updated: 2026-06-19

**Use this file instead of `README.md` + `FORMAT.md` for a quick overview.**

---

## Recently completed

| Process | Finished | Result |
|---------|----------|--------|
| **Gold batch** | Fri Jun 19, 1:19 PM EDT (~59 min) | IOAA 4/4, ARML 11/11, IJSO 12/12 ✓. IOL **4/14** then judge crash on 2014. Log: `data/processed/gold_batch_full_teams.log` |
| IOL rerun (2018/2021/2023) | 12:41 PM EDT | 2021 → 76/100; 2018 & 2023 still 0 (truncation) |

---

## Quick comparison — what each olympiad requires

| | **IOL** | **IOAA** | **ARML** | **IJSO** |
|---|:---:|:---:|:---:|:---:|
| **Full name** | International Linguistics Olympiad — Team Contest | International Olympiad on Astronomy and Astrophysics — Group Competition | American Regions Mathematics League — Power Contest | International Junior Science Olympiad — Team Practical |
| **Team size** | 4 | 5 | 10–15 | 3 |
| **Time** | 4 h | 90 min | 45 min | 3–4 h |
| **Internet** | No | No | No | No |
| **Deliverable** | Answer sheet | Boxed answers | Proofs / computations | Lab report |
| **Human score** | Points (varies) | Time-ranked | /40 | /40 |
| **Nature** | Linguistics puzzles | Astro physics Q&A | Team math power round | Lab experiment |
| **Fits our pipeline?** | ★★★★★ | ★★★★ | ★★★★★ | ★★ |

IJSO is ★★ because we only have the protocol text — no lab equipment or real measurements. IOAA is ★★★★ because humans are scored by time, not points (we still judge AI /100 for comparability).

---

## Table 1 — Dataset inventory

| Olympiad | Collected | Problem text | Gold solution text | **Q + solution pairs** (runnable) | Human score in JSON | Target |
|----------|----------:|-------------:|-------------------:|----------------------------------:|--------------------:|-------:|
| IOL Team Contest | 21 | 19 | 15 | **14** | **13** | 21 |
| IOAA Group | 9 | 9 | 4 | **4** | 0 | 18 |
| ARML Power | 15 | 15 | 11 | **11** | **9** | 30 |
| IJSO Practical | 22 | 14 | 12 | **12** | **1** | 22 |
| IEO Business Case | 5 | 5 | rubric only | 5 (rubric) | 1 | 30 |
| **4 test olympiads** | **67** | **57** | **42** | **41** | **23** | ~91 max |

**Runnable** = `--with-gold` can run it (problem text + `gold_label.expected_answer` extracted from solution PDF).

**Human baseline:** published top-team scores in `gold_label.human_baseline` where available (see [Human baselines](#human-baselines-published)). IOAA has no point-based human score (time-ranked only).

### Gold-runnable problems (by olympiad)

| Olympiad | Count | Years / IDs |
|----------|------:|-------------|
| IOL Team | 14 | 2008, 2009, 2010, 2011, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2025 |
| IOAA Group | 4 | 2014, 2015, 2021, 2025 |
| ARML Power | 11 | Fall 2018–2025 (11 seasons with solution text) |
| IJSO Practical | 12 | 2009–2011, 2013–2014, 2016–2019, 2021–2023 |

---

## Table 2 — Competition format

| Olympiad | Type | Team size | Time | Tools | Deliverable | Human score | AI judge |
|----------|------|----------:|------|-------|-------------|-------------|----------|
| **IOL** — International Linguistics Olympiad, Team Contest | Test | **4** | 4 h | No internet | Answer sheet | Varies (e.g. 200/200 in 2025) | /100 |
| **IOAA** — International Olympiad on Astronomy and Astrophysics, Group Competition | Test | **5** | 90 min | No internet | Answer sheet | Time-ranked (no points) | /100 |
| **ARML** — American Regions Mathematics League, Power Contest | Test | **12** (real: 10–15) | 45 min | No internet | Proofs / computations | /40 | /40 |
| **IJSO** — International Junior Science Olympiad, Team Practical | Test | **3** | 3–4 h | No internet | Lab write-up | /40 | /40 |
| **IEO** — International Economics Olympiad, Business Case | Rubric | **5** | ~24 h | **Yes** (not in pipeline) | Slides / report | /50 BC; /100 overall | /50 |

**Pipeline:** problem → N agents × R discussion rounds → final answer → external judge vs gold solution.

**Published human gold (competition level):**

| Olympiad | Example |
|----------|---------|
| IOL | Taiwan 2025: 200.0/200 (see human baselines below) |
| ARML Power | Top teams: 36–40/40 (see human baselines below) |
| IJSO | Russia 2007: 39.4/40 practical gold |
| IEO | Canada 2025: 92.5/100 overall |
| IOAA | **Time-ranked only** — no /100 human baseline |

---

## IOAA Group — agent results vs real olympiad

### How agents are doing

| Run | Config | Scores |
|-----|--------|--------|
| Smoke | 2 agents, 2 rounds | 2025: **9/150** |
| Gold batch | 5 agents, 2 rounds | 2014: **43/100**, 2015: **15/100**, 2021: **15/115**, 2025: **8/150** |

Agents are scoring **~5–15%** of available marks (judge scale varies by year). That is expected: IOAA group tasks often require hands-on work, plots, and timed submission — none of which the text-only pipeline provides.

### Real IOAA Group vs our pipeline

| | **Real IOAA Group** | **Our benchmark** |
|---|---------------------|-------------------|
| **Team** | 5 students from **5 different countries** (random mix at venue) | 5 LLM agents (same model family) |
| **Time** | **90 min** hard cap; **winner = fastest finish** after time penalties for wrong/missing answers | No time limit; async API calls over many minutes |
| **Scoring** | Wall-clock time + penalties (e.g. +15 min for wrong Arecibo decode); **not points** | External LLM judge vs official marking scheme → **/100** (or problem max) |
| **Materials** | Calculator, paper, constants table, geometry tools **provided on table** | Text problem only; no attachments (CSV, star charts, graph paper) |
| **Equipment / media** | Often requires **radio telescope software**, **video on room screens** (e.g. 2023 Arecibo reply), plotting on **graph paper** | No telescope, no video, no plotting — agents answer from PDF text |
| **Interaction** | One table, sealed envelope, proctor; no other teams | Multi-round written discussion → single synthesized answer |
| **Internet** | Not allowed | Not used in pipeline (but agents lack physical kit anyway) |

**Pipeline fit ★★★★** (not ★★★★★): problem text transfers well, but **time-based human scoring cannot be compared** to our point-based judge, and **lab/observation-heavy years (2025 radio telescope, 2021 HI CSV spectra)** are a poor match for a text-only agent.

---

## Human baselines (published)

Populated in `gold_label.human_baseline` via `scripts/populate_human_baselines.py`. Sources: [ioling.org/results](https://ioling.org/results/), [arml.com power results](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=power_results), [ijsoweb.org/past-results](http://www.ijsoweb.org/past-results).

**IOL Team** (gold trophy score; max varies by year — compare cautiously to AI /100):

| Year | Human gold |
|------|------------|
| 2008 | 85 (USA 2) |
| 2009 | 2261 (USA Red; different scale) |
| 2010 | 96 (Latvia) |
| 2011 | 85 (USA Red) |
| 2014 | 29 (USA Red) |
| 2016 | 57 (Sweden) |
| 2018 | 84.83 (USA Blue) |
| 2019 | 113 (Slovenia) |
| 2021 | 56.8 (Ukraine) |
| 2022 | 68.1 (Korea Mal) |
| 2023 | 256 (UK) |
| 2024 | 85.5 (Czechia) |
| 2025 | **200.0/200** (Taiwan Blue Magpie) |

**ARML Power** (top team /40 per round):

| Season | Human gold |
|--------|------------|
| Fall 2018 | 40/40 |
| Fall 2019 | 40/40 |
| Spring 2019 | 39/40 |
| Fall 2020 | 40/40 |
| Spring 2020 | 38/40 |
| Fall 2021 | 40/40 |
| Spring 2021 | 38/40 |
| Fall 2024 | 37/40 |
| Fall 2025 | 40/40 |

Fall 2022–2023 and several spring seasons: results pages not yet parsed → still `null`.

**IJSO Practical:** 2007 only so far — **39.4/40** (Russia, experimental gold). Most years need manual extraction from result booklets.

**IOAA / IEO:** IOAA is time-ranked (no point baseline). IEO 2025: Canada **92.5/100** overall (already in JSON).

---

## Table 3 — Experiment results

### Smoke tests (2 agents, 2 rounds) — Claude judge

| Olympiad | Problem | Score |
|----------|---------|------:|
| IOL Team | 2008 Fanqie | **29/100** |
| IOAA Group | 2025 | **9/150** |
| ARML Power | Fall 2018 | **19/40** |
| IJSO Practical | 2009 | **46/100** |

Config: GPT-5.4-mini agents, Claude Sonnet 4.6 judge.

### IOL Team — full team (4 agents, 3 rounds) — GPT-5.5 self-judged

| Year | Score | Notes |
|------|------:|-------|
| 2008 | 93/100 | |
| 2010 | 93/100 | |
| 2017 | 81/100 | |
| 2018 | 0/100 | API truncation |
| 2019 | 44.8/100 | |
| 2021 | 76/100 | Rerun fixed (was 0) |
| 2022 | 96/100 | |
| 2023 | 0/100 | API truncation |
| 2025 | 48/100 | |

### IEO Business Case 2025 — GPT-5.5 self-judged

| Format | Rounds | Score |
|--------|-------:|------:|
| Slides | 20 | 45/50 |
| Slides | 3 | 44/50 |
| Report | 3 | 46/50 |

### Gold batch (full team, 2 rounds) — **done**

GPT-5.4-mini agents, Claude Sonnet 4.6 judge, real team sizes, `--with-gold`. Finished **Fri Jun 19, 1:19 PM EDT**.

| Olympiad | Done | Total | Scores (Claude judge) |
|----------|-----:|------:|-----------------------|
| IOL Team | 4 | 14 | 2008: 27/100, 2009: 19/100, 2010: 86/100, 2011: 37/100 — **crashed on 2014** |
| IOAA Group | 4 | 4 | see [IOAA section](#ioaa-group--agent-results-vs-real-olympiad) |
| ARML Power | 11 | 11 | see table below |
| IJSO Practical | 12 | 12 | see table below |

**IOAA Group** (5 agents, Claude judge):

| Year | Score | Human baseline |
|------|------:|----------------|
| 2014 | 43/100 | time-ranked (no /100) |
| 2015 | 15/100 | time-ranked (no /100) |
| 2021 | 15/115 | time-ranked (no /100) |
| 2025 | 8/150 | time-ranked (no /100) |

**ARML Power** (12 agents, Claude judge /40):

| Season | Score |
|--------|------:|
| Fall 2018 | 19/40 |
| Fall 2019 | 27/40 |
| Spring 2019 | 22/40 |
| Fall 2020 | 20/40 |
| Spring 2020 | 27/40 |
| Fall 2021 | 31/40 |
| Spring 2021 | 24/40 |
| Fall 2022 | 21/40 |
| Fall 2023 | 22/40 |
| Fall 2024 | 33/40 |
| Fall 2025 | 35/40 |

**IJSO Practical** (3 agents, Claude judge — scale varies by year):

| Year | Score |
|------|------:|
| 2009 | 15/40 |
| 2010 | 43/100 |
| 2011 | 85/100 |
| 2013 | 8.5/40 |
| 2014 | 6.5/40 |
| 2016 | 21/40 (52/100 normalized) |
| 2017 | 15/100 |
| 2018 | 31/100 |
| 2019 | 13/100 |
| 2021 | 5/100 |
| 2022 | 35/100 |
| 2023 | 0/100 |

IOL still needs **10 remaining gold problems** rerun (2014+ crashed mid-judge).

Output: `data/processed/multiagent_*_2r_openai_gpt-5_4-mini_judgedby_anthropic_claude-sonnet-4-6.{json,md}`

---

## Commands

```bash
export PERPLEXITY_API_KEY="..."

# One olympiad, all gold problems, real team size, 2 rounds
python3 run_multiagent_experiment.py agent:openai/gpt-5.4-mini agent:anthropic/claude-sonnet-4-6 answer \
  --olympiad iol_team --with-gold --rounds 2

# ARML needs explicit team size (10–15 recommended)
python3 run_multiagent_experiment.py agent:openai/gpt-5.4-mini agent:anthropic/claude-sonnet-4-6 answer \
  --olympiad arml_power --with-gold --rounds 2 --agents 12
```

Repo: https://github.com/selinkaracaa/agent-olympiad
