# from_zhongzheng — Domain Catalog

Last updated: 2026-07-22

English index of **domains** covered by the datasets documented under [`olympiad/`](olympiad/README.md), [`art/`](art/README.md), and the workspace [`benchmark/README.md`](../../../benchmark/README.md). Per-contest deep dives, simulator rules, and download notes stay in those trackers.

**Grading**
- **RULE** — closed-form / tests / flags / exact match (auto-gradable)
- **RUBRIC** — open-ended deliverable scored by rubric, jury, or calibrated LLM judges
- **RULE + RUBRIC** — hybrid (e.g. portfolio replay + strategy report)

**Questions** — size of the usable problem set for simulation / eval. Exact integers where the source is itemized; `~` for archive-level counts (PDF packs, yearly sets, or answer-index rows). Details live in each tracker's deep-dive card.

**Format** — what kind of contest this is (exam style, team event, pitch, CTF, etc.) — the human competition form we are simulating.

Overlaps: several `art/` contests are also listed in `olympiad/` (linked back to `art/`). They are counted once below. Local `benchmark/` folders = **46** (same union).

---

## Summary

| Domains | Unique competitions | Sources |
|:-------:|--------------------:|---------|
| **25** | **46** | `olympiad/` · `art/` · `benchmark/` |

| # | Domain | Competitions | RULE | RUBRIC | Hybrid |
|---|--------|-------------:|-----:|-------:|-------:|
| 1 | [STEM olympiad & competition math](#1-stem-olympiad--competition-math) | 4 | 3 | 1 | 0 |
| 2 | [Competitive programming](#2-competitive-programming) | 3 | 3 | 0 | 0 |
| 3 | [Software engineering](#3-software-engineering) | 1 | 1 | 0 | 0 |
| 4 | [ML engineering](#4-ml-engineering) | 2 | 2 | 0 | 0 |
| 5 | [AI / ML research & AI olympiad](#5-ai--ml-research--ai-olympiad) | 3 | 0 | 2 | 1 |
| 6 | [Applied math modeling](#6-applied-math-modeling) | 1 | 0 | 1 | 0 |
| 7 | [Experimental science](#7-experimental-science) | 1 | 0 | 1 | 0 |
| 8 | [Chemistry tournament](#8-chemistry-tournament) | 1 | 0 | 1 | 0 |
| 9 | [Astronomy & astrophysics](#9-astronomy--astrophysics) | 1 | 1 | 0 | 0 |
| 10 | [Earth science](#10-earth-science) | 1 | 1 | 0 | 0 |
| 11 | [Geography](#11-geography) | 1 | 0 | 0 | 1 |
| 12 | [Linguistics](#12-linguistics) | 1 | 1 | 0 | 0 |
| 13 | [Cybersecurity](#13-cybersecurity) | 2 | 2 | 0 | 0 |
| 14 | [Medicine](#14-medicine) | 2 | 0 | 2 | 0 |
| 15 | [Business, finance & economics](#15-business-finance--economics) | 4 | 0 | 2 | 2 |
| 16 | [Law](#16-law) | 1 | 0 | 1 | 0 |
| 17 | [Ethics](#17-ethics) | 2 | 0 | 2 | 0 |
| 18 | [Philosophy](#18-philosophy) | 1 | 0 | 1 | 0 |
| 19 | [History](#19-history) | 1 | 0 | 0 | 1 |
| 20 | [Debate](#20-debate) | 1 | 0 | 1 | 0 |
| 21 | [Collaborative writing](#21-collaborative-writing) | 1 | 0 | 1 | 0 |
| 22 | [Science & general-knowledge quiz](#22-science--general-knowledge-quiz) | 2 | 2 | 0 | 0 |
| 23 | [Collaborative puzzle hunt](#23-collaborative-puzzle-hunt) | 1 | 1 | 0 | 0 |
| 24 | [Frontier exams, reasoning & agents](#24-frontier-exams-reasoning--agents) | 4 | 4 | 0 | 0 |
| 25 | [Writing & professional deliverables](#25-writing--professional-deliverables) | 4 | 0 | 4 | 0 |
| | **Total** | **46** | **21** | **20** | **5** |

---

## 1. STEM olympiad & competition math

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `OlympicArena` | OlympicArena (7 STEM disciplines) | Timed written olympiad exam (multi-subject) | 10,615 | RULE | [olympiad](olympiad/README.md) |
| `OlympiadBench` | Olympiad math + physics (EN/ZH, multimodal) | Timed written olympiad exam (math/physics) | 8,476 | RULE | [olympiad](olympiad/README.md) |
| `AIME` | AIME 2024 + 2025 + 2026 | Timed individual math contest (integer answers) | 90 | RULE | [olympiad](olympiad/README.md) |
| `pumac_power` | PUMaC Power Round (8-agent proofs) | Week-long team proof packet | ~19 packets (2007–2025) | RUBRIC | [olympiad](olympiad/README.md) |

---

## 2. Competitive programming

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `USACO` | USA Computing Olympiad | Individual programming contest (submit code) | 520 | RULE | [olympiad](olympiad/README.md) |
| `LiveCodeBench` | LeetCode / AtCoder / Codeforces | Online judge programming contest | ~1,055 | RULE | [olympiad](olympiad/README.md) |
| `CodeContests` | Codeforces / ICPC-style (AlphaCode) | ICPC-style team programming (shared machine) | **13,610** | RULE | [olympiad](olympiad/README.md) |

---

## 3. Software engineering

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `SWE-bench_Verified` | SWE-bench Verified | Issue → patch engineering challenge | 500 | RULE | [olympiad](olympiad/README.md) |

---

## 4. ML engineering

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `MLAgentBench` | MLAgentBench | Kaggle-style ML engineering tasks | 15 tasks · 15 problems total | RULE | [olympiad](olympiad/README.md) |
| `MLE-bench` | MLE-bench (OpenAI) | Real Kaggle competitions end-to-end | 75 official (Lite 22); local 82 folders | RULE | [benchmark](../../../benchmark/README.md) |

---

## 5. AI / ML research & AI olympiad

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `MLR-Bench` | ML research tasks | Open-ended research pipeline contest | 201 | RUBRIC | [olympiad](olympiad/README.md) |
| `PaperBench` | Replicate ICML 2024 papers | Paper-replication research contest | 20 papers | RUBRIC | [olympiad](olympiad/README.md) |
| `ioai` | International Olympiad in AI | AI olympiad: Individual ML tasks + Team Challenge | **17** tasks | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 6. Applied math modeling

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | Multi-day team math modeling contest | 68 | RUBRIC | [olympiad](olympiad/README.md) |

---

## 7. Experimental science

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `eoes` | EOES / EUSO | 3-person integrated lab practical olympiad | **2 exp/year** · local **~90 PDFs / ~172 MB** (EOES 2021/23–25 + EUSO archive; 2022 tasks unpublished) | RUBRIC | [olympiad](olympiad/README.md) |

---

## 8. Chemistry tournament

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ichto` | International Chemistry Tournament | IYPT-style oral science fights (report / oppose / review) | **106** problems · 9 sets (12×8 + 10 in 2025) | RUBRIC | [olympiad](olympiad/README.md) |

---

## 9. Astronomy & astrophysics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ioaa` | Intl. Olympiad on Astronomy & Astrophysics (incl. Group) | Written + observation olympiad; 5-person Group round | ~20 years · 174 PDFs (16 Group/Team) | RULE | [olympiad](olympiad/README.md) |

---

## 10. Earth science

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ieso` | International Earth Science Olympiad | Theory + practical earth-science olympiad | ~125 theory/practical PDFs | RULE | [olympiad](olympiad/README.md) |

---

## 11. Geography

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `igeo` | International Geography Olympiad (iGeo) | WRT written + FWE fieldwork + MMT sample | **600** (WRT 505 · FWE 55 · MMT 40) · structured `igeo_questions.json` | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 12. Linguistics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `iol` | International Linguistics Olympiad | Written linguistics olympiad (+ 4-person Team Contest) | **130** source problems · 555 HF records | RULE | [olympiad](olympiad/README.md) |

---

## 13. Cybersecurity

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `NYU_CTF_Bench` | CSAW CTF (NYU CTF Bench) | Team CTF (capture-the-flag) | 200 | RULE | [olympiad](olympiad/README.md) |
| `Cybench` | Professional CTF | Harder professional CTF (HackTheBox / Sekai / HKCERT packs) | **40** local challenge packs | RULE | [olympiad](olympiad/README.md) |

---

## 14. Medicine

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `HealthBench` | OpenAI HealthBench | Multi-turn clinical Q&A / advice (consumer) | 5,000 | RUBRIC | [olympiad](olympiad/README.md) |
| `HealthBench-Professional` | OpenAI HealthBench Professional | Physician workflow (consult / writing / research) | **525** | RUBRIC | [olympiad](olympiad/README.md) |

---

## 15. Business, finance & economics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `gcch_harvard` | Global Case Competition at Harvard | Business case → slide deck + pitch | 7 | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `cfa_research_challenge` | CFA Institute Research Challenge | Equity research report + oral defense | **19** inferred company tasks (`tasks.json`) + champion reports | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `wharton_investment` | Wharton Global HS Investment Competition | Long-horizon portfolio simulation + strategy defense | 4 | RULE + RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `ieo` | International Economics Olympiad | Economics exam + team business case | ~1 open set + ~10+ case/task PDFs | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 16. Law

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `vis_moot` | Willem C. Vis Commercial Arbitration Moot | International arbitration moot (memos + oral) | 7 | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |

---

## 17. Ethics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | Collegiate ethics bowl (adversarial oral cases) | ~140 cases | RUBRIC | [art](art/README.md) |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | HS ethics bowl (dialogic oral cases) | 15 cases | RUBRIC | [art](art/README.md) |

---

## 18. Philosophy

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ipo` | International Philosophy Olympiad | Timed on-site philosophy essay olympiad | ~95 structured topics (31 years) · pick 1 of ~4/year | RUBRIC | [olympiad](olympiad/README.md) |

---

## 19. History

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `history_olympiad` | International History Olympiad | History bee/bowl + written historiography exams | ~90 exam/key PDFs (6 editions) | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 20. Debate

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `debatebench` | WUDC / BP Debate (DebateBench) | British Parliamentary debate (4 teams × 2) | 360 scored speeches | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |

---

## 21. Collaborative writing

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | 3-person staged collaborative essay writing | **42** guiding Qs (+ 3–4 live prompts/session) | RUBRIC | [olympiad](olympiad/README.md) |

---

## 22. Science & general-knowledge quiz

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `science_bowl` | DOE National Science Bowl | Buzzer quiz bowl (Toss-Up + Bonus) | **~23,691** (11,846 Toss-Up + 11,845 Bonus) | RULE | [art](art/README.md) |
| `qanta` | QANTA Quiz Bowl | Pyramidal quiz bowl (buzz on clues) | ~100,000 | RULE | [art](art/README.md) |

---

## 23. Collaborative puzzle hunt

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `mystery_hunt` | MIT Mystery Hunt | Large-team puzzle hunt → metas → coin | **4,202** keyed answers · puzzle body/media mirror in progress | RULE | [olympiad](olympiad/README.md) |

---

## 24. Frontier exams, reasoning & agents

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `HLE` | Humanity's Last Exam | Expert closed-ended exam (100+ subjects) | 2,500 | RULE | [benchmark](../../../benchmark/README.md) |
| `GPQA` | GPQA (Diamond / main) | Graduate-level Google-proof MCQ | 448 (Diamond 198) | RULE | [benchmark](../../../benchmark/README.md) |
| `ARC-AGI-2` | ARC Prize abstraction puzzles | Few-shot grid transformation | 1,000 train + 120 eval | RULE | [benchmark](../../../benchmark/README.md) |
| `GAIA` | GAIA general AI assistant | Tool-using real-world Q&A | 466 | RULE | [benchmark](../../../benchmark/README.md) |

---

## 25. Writing & professional deliverables

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `WritingBench` | WritingBench | Real-world writing with instance rubrics | 1,000 | RUBRIC | [benchmark](../../../benchmark/README.md) |
| `ProfBench` | ProfBench (NVIDIA) | Professional report generation | 40 tasks · 4 domains | RUBRIC | [benchmark](../../../benchmark/README.md) |
| `BiGGen-Bench` | BiGGen-Bench | Instance-rubric generation | 765 | RUBRIC | [benchmark](../../../benchmark/README.md) |
| `FLASK` | FLASK | Fine-grained skill-rubric alignment eval | ~1,700 | RUBRIC | [benchmark](../../../benchmark/README.md) |

---

## Cross-reference by tracker

| Tracker | Role | Competitions (unique) |
|---------|------|----------------------:|
| [`olympiad/README.md`](olympiad/README.md) | Broad olympiad suite + links to art | 43 matrix rows (8 linked to `art/`) |
| [`art/README.md`](art/README.md) | Humanities, quiz, business, law, debate | 9 |
| [`benchmark/README.md`](../../../benchmark/README.md) | Full local suite (incl. frontier + writing packs) | **46** |
| **Union** | | **46** |

---

## Data location

Raw files are **not** stored in this git folder. See download sections in each tracker; local mirrors live under the workspace [`benchmark/`](../../../benchmark/) directory (**46** top-level datasets — see [`benchmark/README.md`](../../../benchmark/README.md)), plus HF [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) for the original private bundle.
