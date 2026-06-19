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
| IOL Team Contest | 21 | 19 | 15 | **14** | 0 | 21 |
| IOAA Group | 9 | 9 | 4 | **4** | 0 | 18 |
| ARML Power | 15 | 15 | 11 | **11** | 0 | 30 |
| IJSO Practical | 22 | 14 | 12 | **12** | 0 | 22 |
| IEO Business Case | 5 | 5 | rubric only | 5 (rubric) | 1 | 30 |
| **4 test olympiads** | **67** | **57** | **42** | **41** | 0 | ~91 max |

**Runnable** = `--with-gold` can run it (problem text + `gold_label.expected_answer` extracted from solution PDF).

**Human baseline:** almost all per-problem fields are `null`. Competition-level human gold examples are in Table 2.

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
| IOL | Taiwan 2025: 200.0/200 |
| ARML Power | Top teams: 36–40/40 |
| IEO | Canada 2025: 92.5/100 overall |

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
| IOAA Group | 4 | 4 | 2014: 43/100, 2015: 15/100, 2021: 15/115, 2025: 8/150 |
| ARML Power | 11 | 11 | 19–35/40 (top: Fall 2025 35/40, Fall 2024 33/40) |
| IJSO Practical | 12 | 12 | 0–85/100 (best: 2011 85/100; many low) |

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
