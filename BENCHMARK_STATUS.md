# Olympiad Benchmark — Status & Results

Last updated: 2026-06-19

**Use this file instead of `README.md` + `FORMAT.md` for a quick overview.**

Pipeline: problem text → N agents × R discussion rounds → synthesized answer → external judge vs gold solution.

Repo: https://github.com/selinkaracaa/agent-olympiad

---

## 1. Competition format & our setup

| | **IOL Team** | **IOAA Group** | **ARML Power** | **IJSO Practical** | **IEO Business Case** |
|---|:---:|:---:|:---:|:---:|:---:|
| **Type** | Test | Test | Test | Test | Rubric |
| **Team size** | 4 | 5 | 12 (real: 10–15) | 3 | 5 |
| **Time** | 4 h | 90 min | 45 min | 3–4 h | ~24 h |
| **Internet** | No | No | No | No | Yes (not in pipeline) |
| **Deliverable** | Answer sheet | Boxed answers | Proofs / computations | Lab report | Slides / report |
| **Human score** | Team pts (varies; e.g. 200/200 in 2025) | **Time-ranked** (not points) | **/40** | **/40** | **/50** BC; **/100** overall |
| **AI judge** | **/100** | **/100** (or problem max) | **/40** | **/40** or **/100** | **/50** |
| **Real competition needs** | Paper, pencils; one hard puzzle | Calculator, constants sheet, geometry tools; often **CSV data**, **star charts**, **graph paper**, **radio-telescope software**, **room video** (e.g. Arecibo 2023); 5 students from 5 countries | Paper only | **Lab kit**, chemicals, glassware, measuring instruments, timed hands-on protocol | Research + slides; internet allowed |
| **What we provide** | PDF problem + solution text | PDF text only | PDF text only | Protocol PDF text only | Rubric + case text |
| **Missing in our setup** | — (good fit) | No telescope, no CSV attachments, no video, no timed submission, no physical constants table | — (good fit) | No lab equipment, no measurements, no wet lab | No presentation mode; internet not wired in |
| **Fit** | ★★★★★ | ★★★★ | ★★★★★ | ★★ | pilot only |

IJSO scores are a text-only proxy — agents cannot run the experiment. IOAA human winners are ranked by **fastest finish** after penalties; our AI scores are point-based from the marking scheme, so human gold is not directly comparable.

---

## 2. Questions & data collected

| Olympiad | Collected | Problem text | Gold solution | **Runnable** (Q + solution) | Human gold in JSON | Target |
|----------|----------:|-------------:|--------------:|----------------------------:|-------------------:|-------:|
| IOL Team | 21 | 19 | 15 | **14** | **13** | 21 |
| IOAA Group | 9 | 9 | 4 | **4** | 0 | 18 |
| ARML Power | 15 | 15 | 11 | **11** | **9** | 30 |
| IJSO Practical | 22 | 14 | 12 | **12** | **1** | 22 |
| IEO Business Case | 5 | 5 | rubric | 5 | 1 | 30 |
| **4 test olympiads** | **67** | **57** | **42** | **41** | **23** | ~91 |

**Runnable** = `--with-gold` works (problem + `gold_label.expected_answer` from solution PDF).

| Olympiad | Runnable count | Years / seasons |
|----------|---------------:|-----------------|
| IOL Team | 14 | 2008–2011, 2014–2019, 2021–2023, 2025 |
| IOAA Group | 4 | 2014, 2015, 2021, 2025 |
| ARML Power | 11 | Fall 2018–2025 (11 seasons with solutions) |
| IJSO Practical | 12 | 2009–2011, 2013–2014, 2016–2019, 2021–2023 |

Human gold sources: [ioling.org/results](https://ioling.org/results/), [ARML power results](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=power_results), [IJSO past results](http://www.ijsoweb.org/past-results). Populated via `scripts/populate_human_baselines.py`.

---

## 3. Experiment results

### Smoke tests — GPT-5.4-mini agents, 2 agents × 2 rounds, Claude Sonnet 4.6 judge

| Olympiad | Problem | AI score | Human gold |
|----------|---------|----------|------------|
| IOL Team | 2008 Fanqie | **29/100** | 85 |
| IOAA Group | 2025 Group Competition | **9/150** | time-ranked |
| ARML Power | Fall 2018 Chip-Firing | **19/40** | 40/40 |
| IJSO Practical | 2009 | **46/100** | — |

### Gold batch — GPT-5.4-mini agents, real team size, 2 rounds, Claude Sonnet 4.6 judge

Finished **Fri Jun 19, 1:19 PM EDT** (~59 min). Log: `data/processed/gold_batch_full_teams.log`. Output: `data/processed/multiagent_*_2r_openai_gpt-5_4-mini_judgedby_anthropic_claude-sonnet-4-6.{json,md}`

#### IOL Team (4 agents) — 4/14 complete

| Year | Problem | AI score | Human gold (team pts) |
|------|---------|----------|----------------------|
| 2008 | Fanqie | **27/100** | 85 |
| 2009 | Vietnamese | **19/100** | 2261 (different scale that year) |
| 2010 | Mongolian | **86/100** | 96 |
| 2011 | Sanskrit Poetry | **37/100** | 85 |
| 2014+ | — | not run | batch crashed on judge API error |

Pending rerun (2014–2025): human gold available for 2014 (29), 2016 (57), 2018 (84.83), 2019 (113), 2021 (56.8), 2022 (68.1), 2023 (256, different scale), 2025 (200/200).

#### IOAA Group (5 agents) — 4/4 complete

| Year | Problem | AI score | Human gold |
|------|---------|----------|------------|
| 2014 | Team Competition | **43/100** | time-ranked |
| 2015 | Team Competition | **15/100** | time-ranked |
| 2021 | Team Competition | **15/115** | time-ranked |
| 2025 | Group Competition | **8/150** | time-ranked |

#### ARML Power (12 agents) — 11/11 complete

| Season | Problem | AI score | Human gold |
|--------|---------|----------|------------|
| Fall 2018 | Chip-Firing Games | **19/40** | 40/40 |
| Fall 2019 | Diffygons | **27/40** | 40/40 |
| Spring 2019 | Parking Problems | **22/40** | 39/40 |
| Fall 2020 | Fractional Follies | **20/40** | 40/40 |
| Spring 2020 | Whose Seat Am I In? | **27/40** | 38/40 |
| Fall 2021 | Zigzags and Triangles | **31/40** | 40/40 |
| Spring 2021 | Bipartitions / Beatty | **24/40** | 38/40 |
| Fall 2022 | Paths In A Grid | **21/40** | — |
| Fall 2023 | The Heat Is On | **22/40** | — |
| Fall 2024 | Find My Polynomial | **33/40** | 37/40 |
| Fall 2025 | Thue-Morse Sequence | **35/40** | 40/40 |

#### IJSO Practical (3 agents) — 12/12 complete

| Year | Problem | AI score | Human gold |
|------|---------|----------|------------|
| 2009 | Team Practical | **15/40** | — |
| 2010 | Team Practical | **43/100** | — |
| 2011 | Team Practical | **85/100** | — |
| 2013 | Team Practical | **8.5/40** | — |
| 2014 | Team Practical | **6.5/40** | — |
| 2016 | Team Practical | **21/40** | — |
| 2017 | Team Practical | **15/100** | — |
| 2018 | Team Practical | **31/100** | — |
| 2019 | Team Practical | **13/100** | — |
| 2021 | Team Practical | **5/100** | — |
| 2022 | Team Practical | **35/100** | — |
| 2023 | Team Practical | **0/100** | — |

Only **2007** human gold collected so far: **39.4/40** (Russia) — not in gold batch set.

### IOL Team — GPT-5.5 agents, 4 agents × 3 rounds, GPT-5.5 self-judged

| Year | Problem | AI score | Human gold (team pts) |
|------|---------|----------|----------------------|
| 2008 | Fanqie | **93/100** | 85 |
| 2010 | Mongolian | **93/100** | 96 |
| 2017 | Emoji/Indonesian | **81/100** | — |
| 2018 | Mẽbêngôkre / Xavante | **0/100** (truncation) | 84.83 |
| 2019 | Rhythmic Gymnastics | **44.8/100** | 113 |
| 2021 | Garífuna / Lokono | **76/100** | 56.8 |
| 2022 | Manchu | **96/100** | 68.1 |
| 2023 | Murrinh-patha | **0/100** (truncation) | 256 (different scale) |
| 2025 | Camling / Bantawa | **48/100** | 200/200 |

### IEO Business Case 2025 — GPT-5.5 self-judged (human gold: Canada **92.5/100** overall)

| Format | Rounds | AI score | Human gold |
|--------|-------:|----------|------------|
| Slides | 20 | **45/50** | 92.5/100 overall |
| Slides | 3 | **44/50** | 92.5/100 overall |
| Report | 3 | **46/50** | 92.5/100 overall |
