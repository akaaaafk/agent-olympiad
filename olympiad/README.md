# Data collected — `olympiad/`

Last updated: 2026-07-07

> **Data files are not in git.** They are hosted on the private HF dataset [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) — run `python download_data.py` at the repo root to fetch them.

**Current focus:** academic olympiad and math-modeling benchmark data for multi-agent team competitions in STEM disciplines, complementing the humanities/arts/business collection in `art/`. Both datasets below are structured (JSON / Parquet) and machine-readable, unlike the mostly-PDF raw material in `art/`.

**Competition** = one contest type (one row in the tracker).
**Year/session** = one published problem release (one split or one contest year).
**Question** = one scored problem (e.g. one olympiad problem, one modeling task).

---

## Summary

### Collected

| Competitions | Years/sessions | Questions |
|-------------:|---------------:|----------:|
| **2 datasets (12 source contests)** | **19** | **10,683** |

| ID | Dataset | Domain | Years/sessions | Questions |
|----|---------|--------|---------------:|----------:|
| `OlympicArena` | OlympicArena (GAIR, NeurIPS 2024) | STEM olympiads — 7 disciplines | 14 (7 disciplines × val/test) | 10,615 |
| `modeling_agent` | Math modeling contests (HiMCM / MCM / ICM / IM2C / MidMCM) | Applied math modeling | 2001–2025 (5 contest series) | 68 |
| **Total** | | | **19** | **10,683** |

---

## Simulator Matrix

| ID | Full Name | Input Modality | Team Setup | Computers | Allowed Tools & Resources | Materials Provided | Final Deliverable | Sources |
|----|-----------|----------------|------------|-----------|--------------------------|-------------------|-------------------|---------|
| `OlympicArena` | OlympicArena benchmark | Problem text + figures (EN/ZH, text-only & multimodal) | Individual in origin contests; adaptable to per-discipline specialist agents | None in origin olympiads | Closed-book olympiad conditions · fine-grained answer types (single/multi-value, expression, code with test cases) enable auto-grading | Parquet splits per discipline; `val` includes answers, `test` answers withheld (submit to official platform) | Short answers / expressions / code, auto-judged | [HF dataset](https://huggingface.co/datasets/GAIR/OlympicArena) · [GitHub](https://github.com/GAIR-NLP/OlympicArena) · [arXiv:2406.12753](https://arxiv.org/abs/2406.12753) |
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM math modeling | Open-ended problem statement (text + described images) | 3–4 students per team (origin rules) | Unrestricted | Multi-day open-book contest · full internet & software · judged on modeling quality, not single answers | JSON with problem text, grading requirements, suggested evaluator roles, decomposition | Modeling paper (analysis + model + recommendations), rubric-judged | [COMAP](https://www.comap.com/contests) |

---

## OlympicArena · `OlympicArena/`

| | |
|---|---|
| **Domain** | STEM olympiads — Math, Physics, Chemistry, Biology, Geography, Astronomy, CS |
| **Years/sessions** | 14 (7 disciplines × val/test splits) |
| **Questions** | 10,615 (test 9,977 with withheld answers · val 638 with public answers) |
| **Team size** | Individual in origin contests; per-discipline specialist agents possible |
| **Time** | Origin: timed closed-book olympiad rounds |
| **Answer type** | Fine-grained: single/multiple values, expressions, intervals, code (CS problems ship with test cases) |
| **Grading** | Auto-gradable via answer-type-aware rules; `test` split answers withheld — submit to official platform |
| **Source** | Closed-book; EN + ZH; text-only and image-containing problems (`language` / `modality` fields per row) |
| **Link** | [HF: GAIR/OlympicArena](https://huggingface.co/datasets/GAIR/OlympicArena) · [GitHub](https://github.com/GAIR-NLP/OlympicArena) · [arXiv:2406.12753](https://arxiv.org/abs/2406.12753) |
| **Data** | `OlympicArena/` — 7 discipline folders, each with `val-*.parquet` + `test-*.parquet` (14 parquet files, ~254 MB; `CS/val` is 244 MB alone because it embeds full test-case I/O for code problems) |
| **Notes** | License CC-BY-NC-SA-4.0. Per-question counts: Math 3,221 · Geography 1,590 · Biology 1,558 · Chemistry 1,419 · Physics 1,393 · Astronomy 1,200 · CS 234. Load with `datasets`: `load_dataset(path, "Math", split="val")`. Val split enables fully-local closed-loop evaluation. |

---

## Math modeling contests · `modeling_agent/`

| | |
|---|---|
| **Domain** | Applied math modeling — statistics, optimization, simulation, data analysis |
| **Years/sessions** | 2001–2025 across 5 contest series: MCM (24), ICM (20), HiMCM (19), MidMCM (3), IM2C (2) |
| **Questions** | 68 full modeling problems (Middle School 3 · High School 21 · Undergraduate 44) |
| **Team size** | 3–4 students per team (COMAP rules) |
| **Time** | Multi-day contest window (typically 4 days / 14 days depending on series) |
| **Answer type** | Open-ended modeling paper: assumptions, model, analysis, recommendations |
| **Grading** | Rubric-based; each problem annotated with per-category `requirements` (grading points) for LLM-judge scoring |
| **Source** | Open-book: unrestricted internet, software, and references during contest |
| **Link** | [COMAP contests](https://www.comap.com/contests) |
| **Data** | `modeling_agent/modeling_data_final.json` — 68 entries keyed by `year_title`; fields: `year`, `title`, `level`, `source`, `link`, `question` (with inline image descriptions), `requirements`, `eval_roles`, `decomposition` |
| **Notes** | Each problem ships with **suggested evaluator roles** (e.g. Mathematician / Data Scientist / domain expert) and a **decomposition into grading points** — directly usable to build a multi-agent solver plus an LLM-judge panel. Natural fit for 3–4 agent team simulation with role split. |

---

## Collection backlog

| ID | Action |
|----|--------|
| `OlympicArena` | Fetch figure images referenced by `figure_urls` for offline multimodal runs; register on the official platform to score `test`-split submissions |
| `modeling_agent` | Collect Outstanding-winner papers (COMAP publishes abstracts; full papers via UMAP Journal) as gold-standard references |
