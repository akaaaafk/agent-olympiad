# from_zhongzheng — Domain Catalog

Last updated: 2026-07-21

English index of **domains** covered by the datasets documented under [`olympiad/`](olympiad/README.md) and [`art/`](art/README.md). Per-contest deep dives, simulator rules, and download notes stay in those trackers.

**Grading**
- **RULE** — closed-form / tests / flags / exact match (auto-gradable)
- **RUBRIC** — open-ended deliverable scored by rubric, jury, or calibrated LLM judges
- **RULE + RUBRIC** — hybrid (e.g. portfolio replay + strategy report)

**Questions** — size of the usable problem set for simulation / eval. Exact integers where the source is itemized; `~` for archive-level counts (PDF packs, yearly sets, or answer-index rows). Details live in each tracker's deep-dive card.

Overlaps: several `art/` contests are also listed in `olympiad/` (linked back to `art/`). They are counted once below.

---

## Summary

| Domains | Unique competitions | Sources |
|:-------:|--------------------:|---------|
| **23** | **36** | `olympiad/` · `art/` |

| # | Domain | Competitions | RULE | RUBRIC | Hybrid |
|---|--------|-------------:|-----:|-------:|-------:|
| 1 | [STEM olympiad & competition math](#1-stem-olympiad--competition-math) | 4 | 3 | 1 | 0 |
| 2 | [Competitive programming](#2-competitive-programming) | 3 | 3 | 0 | 0 |
| 3 | [Software engineering](#3-software-engineering) | 1 | 1 | 0 | 0 |
| 4 | [ML engineering](#4-ml-engineering) | 1 | 1 | 0 | 0 |
| 5 | [AI / ML research & AI olympiad](#5-ai--ml-research--ai-olympiad) | 3 | 0 | 2 | 1 |
| 6 | [Applied math modeling](#6-applied-math-modeling) | 1 | 0 | 1 | 0 |
| 7 | [Experimental science](#7-experimental-science) | 1 | 0 | 1 | 0 |
| 8 | [Chemistry tournament](#8-chemistry-tournament) | 1 | 0 | 1 | 0 |
| 9 | [Astronomy & astrophysics](#9-astronomy--astrophysics) | 1 | 1 | 0 | 0 |
| 10 | [Earth science](#10-earth-science) | 1 | 1 | 0 | 0 |
| 11 | [Geography](#11-geography) | 1 | 0 | 0 | 1 |
| 12 | [Linguistics](#12-linguistics) | 1 | 1 | 0 | 0 |
| 13 | [Cybersecurity](#13-cybersecurity) | 2 | 2 | 0 | 0 |
| 14 | [Medicine](#14-medicine) | 1 | 0 | 1 | 0 |
| 15 | [Business, finance & economics](#15-business-finance--economics) | 4 | 0 | 2 | 2 |
| 16 | [Law](#16-law) | 1 | 0 | 1 | 0 |
| 17 | [Ethics](#17-ethics) | 2 | 0 | 2 | 0 |
| 18 | [Philosophy](#18-philosophy) | 1 | 0 | 1 | 0 |
| 19 | [History](#19-history) | 1 | 0 | 0 | 1 |
| 20 | [Debate](#20-debate) | 1 | 0 | 1 | 0 |
| 21 | [Collaborative writing](#21-collaborative-writing) | 1 | 0 | 1 | 0 |
| 22 | [Science & general-knowledge quiz](#22-science--general-knowledge-quiz) | 2 | 2 | 0 | 0 |
| 23 | [Collaborative puzzle hunt](#23-collaborative-puzzle-hunt) | 1 | 1 | 0 | 0 |
| | **Total** | **36** | **16** | **15** | **5** |

---

## 1. STEM olympiad & competition math

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `OlympicArena` | OlympicArena (7 STEM disciplines) | 10,615 | RULE | [olympiad](olympiad/README.md) |
| `OlympiadBench` | Olympiad math + physics (EN/ZH, multimodal) | 8,476 | RULE | [olympiad](olympiad/README.md) |
| `AIME` | AIME 2024 + 2025 | 60 | RULE | [olympiad](olympiad/README.md) |
| `pumac_power` | PUMaC Power Round (8-agent proofs) | ~19 packets (2007–2025) | RUBRIC | [olympiad](olympiad/README.md) |

---

## 2. Competitive programming

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `USACO` | USA Computing Olympiad | 307 | RULE | [olympiad](olympiad/README.md) |
| `LiveCodeBench` | LeetCode / AtCoder / Codeforces | ~1,055 | RULE | [olympiad](olympiad/README.md) |
| `CodeContests` | Codeforces / ICPC-style (AlphaCode) | ~13,600 | RULE | [olympiad](olympiad/README.md) |

---

## 3. Software engineering

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `SWE-bench_Verified` | SWE-bench Verified | 500 | RULE | [olympiad](olympiad/README.md) |

---

## 4. ML engineering

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `MLAgentBench` | MLAgentBench | 15 tasks | RULE | [olympiad](olympiad/README.md) |

---

## 5. AI / ML research & AI olympiad

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `MLR-Bench` | ML research tasks | 201 | RUBRIC | [olympiad](olympiad/README.md) |
| `PaperBench` | Replicate ICML 2024 papers | 20 papers | RUBRIC | [olympiad](olympiad/README.md) |
| `ioai` | International Olympiad in AI | ~6 Individual tasks (2025) + Team Challenge ×3 yrs | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 6. Applied math modeling

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | 68 | RUBRIC | [olympiad](olympiad/README.md) |

---

## 7. Experimental science

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `eoes` | EOES / EUSO | 2 experiments/year · local EUSO + EOES packs | RUBRIC | [olympiad](olympiad/README.md) |

---

## 8. Chemistry tournament

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `ichto` | International Chemistry Tournament | 9 sets · ~10–15 problems/set | RUBRIC | [olympiad](olympiad/README.md) |

---

## 9. Astronomy & astrophysics

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `ioaa` | Intl. Olympiad on Astronomy & Astrophysics (incl. Group) | ~20 years · 174 PDFs (16 Group/Team) | RULE | [olympiad](olympiad/README.md) |

---

## 10. Earth science

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `ieso` | International Earth Science Olympiad | ~125 theory/practical PDFs | RULE | [olympiad](olympiad/README.md) |

---

## 11. Geography

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `igeo` | International Geography Olympiad (iGeo) | ~17 WRT editions (1996–2025) + fieldwork | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 12. Linguistics

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `iol` | International Linguistics Olympiad | 130 source · 555 HF records | RULE | [olympiad](olympiad/README.md) |

---

## 13. Cybersecurity

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `NYU_CTF_Bench` | CSAW CTF (NYU CTF Bench) | 200 | RULE | [olympiad](olympiad/README.md) |
| `Cybench` | Professional CTF | 40 | RULE | [olympiad](olympiad/README.md) |

---

## 14. Medicine

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `HealthBench` | OpenAI HealthBench | 5,000 | RUBRIC | [olympiad](olympiad/README.md) |

---

## 15. Business, finance & economics

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `gcch_harvard` | Global Case Competition at Harvard | 7 | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `cfa_research_challenge` | CFA Institute Research Challenge | 19 champion reports | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `wharton_investment` | Wharton Global HS Investment Competition | 4 | RULE + RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `ieo` | International Economics Olympiad | ~1 open set + ~10+ case/task PDFs | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 16. Law

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `vis_moot` | Willem C. Vis Commercial Arbitration Moot | 7 | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |

---

## 17. Ethics

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | ~140 cases | RUBRIC | [art](art/README.md) |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | 15 cases | RUBRIC | [art](art/README.md) |

---

## 18. Philosophy

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `ipo` | International Philosophy Olympiad | ~25 topic PDFs | RUBRIC | [olympiad](olympiad/README.md) |

---

## 19. History

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `history_olympiad` | International History Olympiad | ~90 exam/key PDFs (6 editions) | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 20. Debate

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `debatebench` | WUDC / BP Debate (DebateBench) | 256 transcripts | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |

---

## 21. Collaborative writing

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | ~42 guiding Qs + 3–4 prompts/session | RUBRIC | [olympiad](olympiad/README.md) |

---

## 22. Science & general-knowledge quiz

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `science_bowl` | DOE National Science Bowl | ~14,000+ | RULE | [art](art/README.md) |
| `qanta` | QANTA Quiz Bowl | ~100,000 | RULE | [art](art/README.md) |

---

## 23. Collaborative puzzle hunt

| ID | Competition | Questions | Grading | Tracker |
|----|-------------|-----------|---------|---------|
| `mystery_hunt` | MIT Mystery Hunt | ~2,300 keyed answers · ~4,000+ indexed | RULE | [olympiad](olympiad/README.md) |

---

## Cross-reference by tracker

| Tracker | Role | Competitions (unique) |
|---------|------|----------------------:|
| [`olympiad/README.md`](olympiad/README.md) | Broad olympiad suite + links to art | 34 rows (6 shared with `art/`) |
| [`art/README.md`](art/README.md) | Humanities, quiz, business, law, debate | 9 |
| **Union** | | **36** |

---

## Data location

Raw files are **not** stored in this git folder. See download sections in each tracker; local mirrors live under the workspace [`benchmark/`](../../../benchmark/) directory (and HF [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) for the original private bundle).
