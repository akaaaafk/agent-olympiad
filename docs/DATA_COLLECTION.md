# Data collected

Last updated: 2026-06-26

Experiment results: [`docs/STATUS.md`](STATUS.md)

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published team exam (one PDF / one `problem_id`).  
**Question** = one numbered sub-part inside a year/session (e.g. ARML problem 7, IOL sub-problem (c)).

---

## Summary

### Collected

| Competitions | Years/sessions | Questions |
|-------------:|---------------:|----------:|
| **8** | **100** | **1,046** |

| ID | Competition | Years/sessions | Questions |
|----|-------------|---------------:|----------:|
| `iol_team` | IOL Team Contest | 21 | 73 |
| `ioaa_group` | IOAA Group Competition | 9 | 232 |
| `arml_power` | ARML Power Contest (mail-in) | 15 | 278 |
| `arml_national_team` | ARML National — Team Round | 11 | 110 |
| `arml_national_power` | ARML National — Power Round | 11 | 209 |
| `arml_local` | ARML Local | 6 | 65 |
| `ijso_practical` | IJSO Team Practical | 22 | 74 |
| `ieo_business_case` | IEO Business Case | 5 | 5 |
| **Total** | **100** | **1,046** |

10 years/sessions have no extracted text yet (2 IOL, 8 IJSO) — question counts above are for sessions with text only.

### Proposed (not collected yet)

| Competitions | Years/sessions | Questions |
|-------------:|---------------:|----------:|
| **4** | **0** | **0** |

| ID | Competition | Years/sessions | Questions |
|----|-------------|---------------:|----------:|
| `hmmt_guts` | HMMT Guts Round | 0 | 0 |
| `pumac_power` | PUMaC Power Round | 0 | 0 |
| `iypt` | IYPT | 0 | 0 |
| `euso` | EUSO Team Practical | 0 | 0 |

### All tracked

| | Competitions | Years/sessions | Questions |
|--|-------------:|---------------:|----------:|
| Collected + proposed | **12** | **100** | **1,046** |

---

## IOL Team · `iol_team`

| | |
|---|---|
| **Years/sessions** | 21 |
| **Questions** | 73 (across sessions with text) |
| **Team size** | 4 students |
| **Time** | 4 hours |
| **Answer type** | Written answers on one team answer sheet; linguistics puzzles with sub-parts |
| **Grading** | Points per sub-part; official solution PDF per year; team total varies by year (e.g. /200 in 2025) |
| **Internet** | No |
| **Source** | [ioling.org/problems](https://ioling.org/problems/by_year/) |

---

## IOAA Group · `ioaa_group`

| | |
|---|---|
| **Years/sessions** | 9 |
| **Questions** | 232 (2013 alone has 181 scored items in one group exam) |
| **Team size** | 5 students (one per country on the team) |
| **Time** | 90 minutes |
| **Answer type** | Boxed final answers (astronomy / astrophysics) |
| **Grading** | Marking scheme in solution PDF; **human winner = fastest time** (not point total) |
| **Internet** | No |
| **Source** | [ioaastrophysics.org](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |

---

## ARML Power Contest (mail-in) · `arml_power` · collected

| | |
|---|---|
| **Years/sessions** | 15 rounds (Fall and/or Spring 2018–2025) |
| **Questions** | 278 total |
| **Team size** | No strict limit |
| **Time** | ~1 hour per round |
| **Answer type** | Written proofs and justifications; open-ended; partial credit per sub-problem |
| **Grading** | Points printed at end of each sub-problem; all sub-parts in one packet sum to **40** per round; human standings also show Fall + Spring combined |
| **Internet** | No |
| **Source** | [ARML Power Contest archive](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=power_results) |
| **PDFs** | `data/raw/arml/` (re-download via `collectors/arml_power.py`) |

**Questions per round**

| Round | Questions |
|-------|----------:|
| Fall 2018 | 16 |
| Fall 2019 | 20 |
| Spring 2019 | 22 |
| Fall 2020 | 16 |
| Spring 2020 | 26 |
| Fall 2021 | 20 |
| Spring 2021 | 18 |
| Fall 2022 | 14 |
| Spring 2022 | 17 |
| Fall 2023 | 16 |
| Spring 2023 | 20 |
| Fall 2024 | 17 |
| Spring 2024 | 21 |
| Fall 2025 | 18 |
| Spring 2025 | 17 |

---

## ARML National — Team Round · `arml_national_team` · collected

| | |
|---|---|
| **Years/sessions** | 11 (2009–2014 book + 2016–2019, 2023 national meet PDFs) |
| **Questions** | 110 (10 per year) |
| **Team size** | ~15 students |
| **Time** | ~20 minutes |
| **Answer type** | Final answer only — no proof required |
| **Grading** | 5 points per correct answer (10 questions = /50) |
| **Internet** | No |
| **Source** | [ARML national meet archives](https://www.arml.com/) |
| **PDFs** | `data/raw/arml_national/` + `ARML_2009_2014.pdf` book (re-download via `collectors/arml_national.py`) |

Different event from mail-in Power Contest.

---

## ARML National — Power Round · `arml_national_power` · collected

| | |
|---|---|
| **Years/sessions** | 11 (same years as national team round) |
| **Questions** | 209 scored sub-parts |
| **Team size** | ~15 students |
| **Time** | ~1 hour |
| **Answer type** | Multi-part proof write-up; partial credit on reasoning and style |
| **Grading** | Rubric-based; **50 points** per round at national meet (not the mail-in 40-point packets) |
| **Internet** | No |
| **Source** | [ARML competition rules](https://www.arml2.com/arml_2019/page/index.php?page=competition_rules&page_type=public) |
| **PDFs** | Same sources as `arml_national_team` |

Same name as mail-in “Power Round” but a **different exam** on site.

**Questions per year**

| Year | Questions |
|------|----------:|
| 2009 | 29 |
| 2010 | 23 |
| 2011 | 26 |
| 2012 | 16 |
| 2013 | 30 |
| 2014 | 24 |
| 2016 | 17 |
| 2017 | 19 |
| 2018 | 13 |
| 2019 | 6 |
| 2023 | 6 |

---

## ARML Local · `arml_local` · collected

| | |
|---|---|
| **Years/sessions** | 6 (2009–2014 from ARML book) |
| **Questions** | 65 (10 per year 2009–2013; 15 in 2014) |
| **Team size** | 6 students |
| **Time** | ~45 minutes (team round) |
| **Answer type** | Numerical final answers |
| **Grading** | 4 points per question (10 q pre-2014; 15 q from 2014) |
| **Internet** | No |
| **Source** | [ARML 2009–2014 book](https://www.arml.com/ARML/arml_2019/public_contest_files/2009_2014_book/ARML_2009_2014.pdf) |
| **PDFs** | `data/raw/arml_local/ARML_2009_2014.pdf` (re-download via `collectors/arml_local.py`) |

---

## IJSO Team Practical · `ijso_practical`

| | |
|---|---|
| **Years/sessions** | 22 |
| **Questions** | 74 (sessions with text) |
| **Team size** | 3 students |
| **Time** | 3–4 hours |
| **Answer type** | Lab report — measurements, tables, graphs, drawings |
| **Grading** | Marking scheme in answer PDF; /40 per practical |
| **Internet** | No |
| **Source** | [ijsoweb.org](https://ijsoweb.org/downloads) |

**Note:** Agents only see protocol text — no wet lab, equipment, or timed hands-on work.

---

## IEO Business Case · `ieo_business_case`

| | |
|---|---|
| **Years/sessions** | 5 (2021–2025) |
| **Questions** | 5 (one case per year) |
| **Team size** | 5 students |
| **Time** | ~24 h preparation + presentation |
| **Answer type** | Slides or written strategic report |
| **Grading** | Rubric: Analytical, Conceptual, Quantitative, Communication (4 dimensions) |
| **Internet** | Yes (in real competition; not wired into our pipeline) |
| **Source** | `data/raw/business_case/` |

---

## Proposed (other) · awaiting approval

| ID | Competition | Approved |
|----|-------------|:--------:|
| `hmmt_guts` | HMMT Guts Round | ☐ |
| `pumac_power` | PUMaC Power Round | ☐ |
| `iypt` | IYPT | ☐ |
| `euso` | EUSO Team Practical | ☐ |

---

## Collection backlog

| ID | Action |
|----|--------|
| `arml_power` | Collect older mail-in Fall/Spring seasons |
| `arml_national_team` | More national meet years (2020–2022, 2024+) |
| `arml_national_power` | Same years as national team |
| `arml_local` | Post-2014 local exams if published |
| `ioaa_group` | More years + solution PDFs |
| `iol_team` | OCR 2003, 2012 (missing text) |
| `ijso_practical` | Extract 8 years missing text |
| `ieo_business_case` | Pre-2021 cases if published |
