# Olympiad Format Reference

How each competition format maps to our multi-agent benchmark pipeline.

**Five test-based olympiads** (OlympiadMAS) + **IEO Business Case** (rubric pilot).

---

## Master comparison

| | **IOL Team** | **IOAA Group** | **ARML Power** | **EUSO** | **IJSO Practical** | **IEO Business Case** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Type** | Test | Test | Test | Test | Test | Rubric |
| **Team size** | 4 | 5 | 10–15 (typical) | 3 | 3 | 5 |
| **Time limit** | 4 hours | 90 min | 45 min | 4 hours / task | 3–4 hours | ~24 h prep + presentation |
| **Internet / external tools** | **No** | **No** | **No** | **No** | **No** | **Yes** |
| **Deliverable** | Answer sheet | Answer sheet | Proof / computation sheet | Lab report | Lab report | Slides / report |
| **Human score out of** | **Varies by year** (problem-set max) | **Time** (not points) | **40** | **100** (as %) | **40** | **50** raw BC; **100** overall IEO |
| **AI judge out of** | **100** | **100** | **40** | **100** | **40** | **50** |
| **Gold label (AI judge)** | Official solution PDF | Marking scheme PDF | Solution PDF | Model answers PDF | Marking scheme PDF | Grading rubric |
| **Human gold (best published)** | See table below | See table below | See table below | See table below | See table below | See table below |

\*IOAA Group Competition is won by **shortest total time** after penalties, not a fixed point total. Our pipeline still judges AI answers out of **100** for comparability.

---

## Scoring: what scores are out of

| Olympiad | Human competition | Our AI judge | Notes |
|----------|-------------------|--------------|-------|
| **IOL Team** | **Varies** — e.g. 200.0/200 (2025), 68.1/? (2022); not always /100 | **/100** | Problem-set max changes each year. Judge normalizes to /100. |
| **IOAA Group** | **Time + penalties** (90 min cap); winner = fastest | **/100** | No official /100 human score; we use /100 for AI only. |
| **ARML Power** | **/40** per season | **/40** | 40 pts = sum of sub-problem weights on answer sheet. |
| **EUSO** | **/100** reported as **%** (e.g. 97.5%) | **/100** | Two experiments per year; each ~4 h. |
| **IJSO Practical** | **/40** (team score shared by all 3 members) | **/40** | Practical = 40% of individual total (MCQ 30 + Theory 30 + Practical 40). |
| **IEO Business Case** | **/50** raw (4 rubric dims × 12.5); overall IEO **/100** after normalization | **/50** | 2025 winner Canada **92.5/100** = overall IEO raw, not BC-only. |

---

## Human gold scores (best published team performance)

These are **human baselines** for comparison with AI runs — not the same as official solution keys used for grading.

| Olympiad | Human out of | Human gold (example) | AI judge out of | Notes / source |
|----------|-------------|----------------------|-----------------|----------------|
| **IOL Team** | Varies (e.g. **/200** in 2025) | **200.0/200** — Taiwan Blue Magpie (2025); **68.1/?** Korea Mal (2022) | **/100** | Max depends on problem set. [Results 2025](https://ioling.org/results/2025/) |
| **IOAA Group** | Time-ranked | Fastest team wins (no /100) | **/100** | 90 min cap. [2023 instructions](https://cdn.ioaastrophysics.org/assets/IOAA%20problems/16th%20IOAA%202023/Group%20Competition%202023%20IOAA.pdf) |
| **ARML Power** | **/40** | Top teams **36–40/40**; perfect 40 possible | **/40** | [ARML Power](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public) |
| **EUSO / EOES** | **/100** (%) | **97.5/100** — Germany (2004); **80/100** — UK (2003) | **/100** | [EUSO history](http://euso.eu/history-of-euso/) |
| **IJSO Practical** | **/40** | Gold team = highest **/40** that year (~30–40) | **/40** | [IJSO statutes](http://www.ijsoweb.org/qna/Statutes20140324.pdf) |
| **IEO Business Case** | **/50** BC raw; **/100** overall | **92.5/100** overall — Canada (2025 winner) | **/50** | BC = 4 dims × 12.5. [2025 results](https://2025.ieo-official.org/results) |

Store per-problem values in benchmark JSON as `gold_label.human_baseline` when collected.

---

## 1. IOL Team Contest

| Setting | Real competition | Our benchmark |
|---------|------------------|---------------|
| **Type** | Test-based (objective answers) | `task_type: team_contest`, format `answer` |
| **Team size** | 4 students (same country) | 4 agents |
| **Duration** | 3–4 hours | Not enforced (~15–25 min/problem via API) |
| **External tools** | **Not allowed** — no internet, phones, laptops, dictionaries; calculators only if organizers provide for all | **Not allowed** — Agent API `model` + `input` only |
| **Collaboration** | Free discussion; one shared submission | 3 discussion rounds + synthesis |
| **Deliverable** | Handwritten answer sheet (a, b, c…) | `final_answer` |
| **Grading** | Official solution / marking scheme | Judge vs `gold_label.expected_answer` (/100) |
| **Human gold** | Top team score published each year (e.g. 200.0 in 2025) | `human_baseline`: null (to collect from [ioling.org/results](https://ioling.org/results/)) |

**Sources:** [IOL regulations](https://ioling.org/rules/rules.pdf), [guidelines](https://ioling.org/guidelines/en/)

```bash
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 agent:openai/gpt-5.5 answer \
  --olympiad iol_team --with-gold --rounds 3
```

---

## 2. IOAA Group Competition

| Setting | Real competition | Our benchmark |
|---------|------------------|---------------|
| **Type** | Test-based (short-answer tasks) | `task_type: team_contest`, format `answer` |
| **Team size** | 5 students from **5 different countries** (random mix) | 5 agents |
| **Duration** | **90 minutes** max | Not enforced |
| **External tools** | **Not allowed** to bring own; organizers provide calculator, paper, constants table, geometry tools | **Not allowed** in pipeline |
| **Collaboration** | One table per team; no talking to other teams | Multi-round discussion |
| **Deliverable** | Answer sheets (boxed answers) | `final_answer` |
| **Grading** | Jury marks + **time penalties**; winner = fastest correct finish | Judge vs official solutions where available |
| **Human gold** | Winning team time (year-specific; not /100) | `human_baseline`: null |

**Sources:** [IOAA problems archive](https://ioaastrophysics.org/resources/problems-from-past-ioaa), [2023 group instructions PDF](https://cdn.ioaastrophysics.org/assets/IOAA%20problems/16th%20IOAA%202023/Group%20Competition%202023%20IOAA.pdf)

```bash
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 answer \
  --olympiad ioaa_group --with-gold --rounds 3
```

---

## 3. ARML Power Contest

| Setting | Real competition | Our benchmark |
|---------|------------------|---------------|
| **Type** | Test-based (proofs + computations) | `task_type: team_power`, format `answer` |
| **Team size** | No hard cap; **10–15 recommended** | `team_size: null` (configurable via `--agents`) |
| **Duration** | **45 minutes** | Not enforced |
| **External tools** | **Not allowed** — paper contest at school; no internet | **Not allowed** in pipeline |
| **Collaboration** | Whole team works together; one submission per problem | Multi-round discussion |
| **Deliverable** | Written solutions on answer sheets | `final_answer` |
| **Grading** | Official solution packet; **40 points** total per season | Judge vs solution PDF (/40 or rescaled) |
| **Human gold** | Top teams **36–40/40** | `human_baseline`: null |

**Sources:** [ARML Power Contest](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public)

```bash
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 answer \
  --olympiad arml_power --with-gold --rounds 3
```

---

## 4. EUSO / EOES (European Olympiad of Experimental Science)

| Setting | Real competition | Our benchmark |
|---------|------------------|---------------|
| **Type** | Test-based (integrated lab experiment) | `task_type: team_practical`, format `answer` |
| **Team size** | 3 students (2 teams per country) | 3 agents |
| **Duration** | **4 hours** per experiment (2 experiments over 2 days) | Not enforced |
| **External tools** | **Not allowed** — lab equipment and materials provided; no formula sheets | **Not allowed** in pipeline |
| **Collaboration** | Team divides lab work; one joint report | Multi-round discussion |
| **Deliverable** | Written experimental report + answer sheets | `final_answer` |
| **Grading** | Marking scheme / model answers (Waxmann book 2008–2012; euso.eu 2003–2017) | Judge vs `expected_answer` |
| **Human gold** | Winning team **~80–97.5%** (year-dependent) | `human_baseline`: null |

**Sources:** [euso.eu experiments](http://euso.eu/about/experiments/), [EOES](https://www.eoes.science/)

```bash
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 answer \
  --olympiad euso --with-gold --rounds 3
```

---

## 5. IJSO Practical (Team Experiment)

| Setting | Real competition | Our benchmark |
|---------|------------------|---------------|
| **Type** | Test-based (hands-on lab) | `task_type: team_practical`, format `answer` |
| **Team size** | 3 students (same country; up to 2 teams/country) | 3 agents |
| **Duration** | **3–4 hours** | Not enforced |
| **External tools** | **Not allowed** — standardized lab equipment supplied; no formula collections | **Not allowed** in pipeline |
| **Collaboration** | Team experiment; all members receive **same score** | Multi-round discussion |
| **Deliverable** | Lab write-up (≤4 sub-tasks, Bio/Chem/Physics) | `final_answer` |
| **Grading** | Marking scheme in answer PDFs | Judge vs `expected_answer` (/40) |
| **Human gold** | Gold practical team = highest **/40** that year | `human_baseline`: null |

**Sources:** [IJSO downloads](https://ijsoweb.org/downloads), [statutes](http://www.ijsoweb.org/qna/Statutes20140324.pdf)

```bash
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 answer \
  --olympiad ijso_practical --with-gold --rounds 3
```

---

## 6. IEO Business Case (rubric pilot)

| Setting | Real competition | Our benchmark |
|---------|------------------|---------------|
| **Type** | Rubric-based (qualitative dimensions) | `task_type: business_case`, format `slides` or `report` |
| **Team size** | 5 students | 5 agents |
| **Duration** | **~24 hours** preparation (official: prep day + presentation day) | Not enforced; configurable rounds |
| **External tools** | **Internet and research allowed** — online/offline materials; **no contacting outsiders** | **Not yet enabled** (no web search in pipeline) |
| **Collaboration** | Team divides research and slide writing | Multi-round discussion |
| **Deliverable** | Slide deck (~10 min oral) or strategic report | `final_slides` or `final_report` |
| **Grading** | 4 dimensions × 12.5 = **50 raw** (Analytical, Conceptual, Quantitative, Communication) | Judge vs rubric (/50) |
| **Human gold** | **Canada 92.5/100** overall raw (2025 winner) | In `index.json`; per-year BC raw TBD |

**Sources:** [IEO syllabus](https://files.ieo-official.org/IEO_Syllabus.pdf), `data/raw/business_case/`

```bash
python3 run_multiagent_experiment.py agent:openai/gpt-5.5 agent:openai/gpt-5.5 slides --rounds 20
```

---

## Gold vs human baseline (terminology)

| Field | Meaning |
|-------|---------|
| `gold_label.expected_answer` | **Official solution / marking scheme** — used by the AI judge to grade |
| `gold_label.grading_rubric` | Point breakdown or rubric text |
| `gold_label.human_baseline` | **Best published human team score** for that problem/year — for benchmarking AI against humans |

---

## Pipeline settings (all olympiads)

| Setting | Test-based (5 olympiads) | IEO Business Case |
|---------|--------------------------|-------------------|
| API | Perplexity `POST /v1/agent` | Same |
| Tools | **None** | **None** (should add web search to match real rules) |
| Default format | `answer` | `slides` |
| Default rounds | 3 | 3 (20 for full BC runs) |
| Checkpoint save | After each problem (`--merge-into`) | Same |

---

## Alignment gaps

1. **IOL / IOAA / IJSO:** PDF text extraction drops images and diagrams.
2. **EUSO / IJSO:** Benchmark collection not yet complete (0 problems filled).
3. **IEO Business Case:** Web search not enabled — biggest mismatch with real competition.
4. **Human baselines:** Mostly `null` in benchmark JSON — need per-year extraction from results pages.
5. **Time limits:** Not enforced in API runs (4 h, 90 min, 45 min, 24 h).
