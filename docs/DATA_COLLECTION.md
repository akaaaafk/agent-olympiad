# Data collected

Last updated: 2026-06-26

**Current focus:** raw PDF collection only (`data/raw/`). No benchmark or experiment work for now.

Past experiment results: [`initial_experiments/docs/STATUS.md`](../initial_experiments/docs/STATUS.md)

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published team exam (one PDF / one `problem_id`).  
**Question** = one numbered sub-part inside a year/session (e.g. ARML problem 7, IOL sub-problem (c)).

---

## Summary

### Collected

| Competitions | Years/sessions | Questions |
|-------------:|---------------:|----------:|
| **16** | **286** | **4,195** |

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
| `iypt` | IYPT (Young Physicists' Tournament) | 39 | 655 |
| `hmmt_team` | HMMT — Team Round | 14 | 140 |
| `hmmt_guts` | HMMT — Guts Round | 21 | 766 |
| `mcm` | MCM (Mathematical Contest in Modeling) | 18 | 18 |
| `icm` | ICM (Interdisciplinary Contest in Modeling) | 19 | 19 |
| `fyziklani` | Physics Brawl Online (Fyziklání) | 14 | 282 |
| `purple_comet` | Purple Comet! Math Meet | 44 | 1,051 |
| `itym` | ITYM (Young Mathematicians' Tournament) | 17 | 218 |
| **Total** | **286** | **4,195** |

---

## IOL Team · `iol_team`

| | |
|---|---|
| **Years/sessions** | 21 |
| **Questions** | 73 |
| **Team size** | 4 students |
| **Time** | 4 hours |
| **Answer type** | Written answers on one team answer sheet; linguistics puzzles with sub-parts |
| **Grading** | Points per sub-part; official solution PDF per year; team total varies by year (e.g. /200 in 2025) |
| **Source** | Paper, pencils; no internet |
| **Link** | [ioling.org/problems](https://ioling.org/problems/by_year/) |
| **PDFs** | `data/raw/iol/` |

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
| **Source** | Calculator, constants sheet, geometry tools; often CSV data, star charts, graph paper, telescope/radio-observatory software or room video (varies by year); no internet |
| **Link** | [ioaastrophysics.org](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |
| **PDFs** | `data/raw/ioaa/` |

---

## ARML Power Contest (mail-in) · `arml_power`

| | |
|---|---|
| **Years/sessions** | 15 rounds (Fall and/or Spring 2018–2025) |
| **Questions** | 278 total |
| **Team size** | No strict limit |
| **Time** | ~1 hour per round |
| **Answer type** | Written proofs and justifications; open-ended; partial credit per sub-problem |
| **Grading** | Points printed at end of each sub-problem; all sub-parts in one packet sum to **40** per round |
| **Source** | Paper only; no internet |
| **Link** | [ARML Power Contest archive](https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=power_results) |
| **PDFs** | `data/raw/arml/` |

---

## ARML National — Team Round · `arml_national_team`

| | |
|---|---|
| **Years/sessions** | 11 |
| **Questions** | 110 (10 per year) |
| **Team size** | ~15 students |
| **Time** | ~20 minutes |
| **Answer type** | Final answer only — no proof required |
| **Grading** | 5 points per correct answer (/50) |
| **Source** | Paper only; no internet |
| **Link** | [ARML national meet archives](https://www.arml.com/) |
| **PDFs** | `data/raw/arml_national/` |

---

## ARML National — Power Round · `arml_national_power`

| | |
|---|---|
| **Years/sessions** | 11 |
| **Questions** | 209 scored sub-parts |
| **Team size** | ~15 students |
| **Time** | ~1 hour |
| **Answer type** | Multi-part proof write-up |
| **Grading** | Rubric-based; **50 points** per round at national meet |
| **Source** | Paper only; no internet |
| **Link** | [ARML competition rules](https://www.arml2.com/arml_2019/page/index.php?page=competition_rules&page_type=public) |
| **PDFs** | `data/raw/arml_national/` |

---

## ARML Local · `arml_local`

| | |
|---|---|
| **Years/sessions** | 6 (2009–2014) |
| **Questions** | 65 |
| **Team size** | 6 students |
| **Time** | ~45 minutes |
| **Answer type** | Numerical final answers |
| **Grading** | 4 points per question |
| **Source** | Paper only; no internet |
| **Link** | [ARML 2009–2014 book](https://www.arml.com/ARML/arml_2019/public_contest_files/2009_2014_book/ARML_2009_2014.pdf) |
| **PDFs** | `data/raw/arml_local/` |

---

## IJSO Team Practical · `ijso_practical`

| | |
|---|---|
| **Years/sessions** | 22 |
| **Questions** | 74 |
| **Team size** | 3 students |
| **Time** | 3–4 hours |
| **Answer type** | Lab report — measurements, tables, graphs, drawings |
| **Grading** | Marking scheme in answer PDF; /40 per practical |
| **Source** | Wet-lab kit, chemicals, glassware, measuring instruments; protocol provided; no internet |
| **Link** | [ijsoweb.org](https://ijsoweb.org/downloads) |
| **PDFs** | `data/raw/ijso/` |

---

## IEO Business Case · `ieo_business_case`

| | |
|---|---|
| **Years/sessions** | 5 (2021–2025) |
| **Questions** | 5 (one case per year) |
| **Team size** | 5 students |
| **Time** | ~24 h preparation + presentation |
| **Answer type** | Slides or written strategic report |
| **Grading** | Rubric: Analytical, Conceptual, Quantitative, Communication |
| **Source** | Internet for research |
| **Link** | [ieo-official.org/prepare](https://ieo-official.org/prepare) |
| **PDFs** | `data/raw/business_case/` |

---

## IYPT · `iypt`

| | |
|---|---|
| **Years/sessions** | 39 (1988–2026, annual problem lists) |
| **Questions** | 655 (~17 open-ended physics problems per year) |
| **Team size** | ~5 students |
| **Time** | Months of research + tournament week |
| **Answer type** | Open-ended physics research problems; Reporter / Opponent / Reviewer debate |
| **Grading** | Jury scores on presentation, opposition, and review |
| **Source** | Research materials, experiments; no internet at tournament |
| **Link** | [iypt.org/problems](https://www.iypt.org/problems/) |
| **PDFs** | `data/raw/iypt/` |

---

## HMMT — Team Round · `hmmt_team`

| | |
|---|---|
| **Years/sessions** | 14 (February meets, 2013–2026) |
| **Questions** | 140 (~10 interrelated problems per round) |
| **Team size** | 6–8 students |
| **Time** | 60 minutes |
| **Answer type** | Short answer and proof; problems build on each other |
| **Grading** | Points per problem (often weighted) |
| **Source** | Paper, pencils; no internet |
| **Link** | [hmmt.org archive](https://www.hmmt.org/www/archive/problems) |
| **PDFs** | `data/raw/hmmt/` (`hmmt_team_YYYY.pdf`) |

---

## HMMT — Guts Round · `hmmt_guts`

| | |
|---|---|
| **Years/sessions** | 21 (2006–2026 February meets) |
| **Questions** | 766 (~36 sets per round) |
| **Team size** | 6–8 students |
| **Time** | 80 minutes |
| **Answer type** | Immediate-feedback team round; short answers in sets |
| **Grading** | Live scoring; points per set |
| **Source** | Paper, pencils; no internet |
| **Link** | [hmmt.org archive](https://www.hmmt.org/www/archive/problems) |
| **PDFs** | `data/raw/hmmt/` (`hmmt_guts_YYYY.pdf`) |

---

## MCM · `mcm`

| | |
|---|---|
| **Years/sessions** | 18 problem statements (Problems A/B/C, partial years 2000–2025) |
| **Questions** | 18 (one open-ended modeling problem per PDF) |
| **Team size** | 3 students |
| **Time** | 99 hours (weekend) |
| **Answer type** | Written modeling report |
| **Grading** | Rubric; Outstanding/Meritorious/Honorable tiers |
| **Source** | Internet, data, references allowed |
| **Link** | [comap.com MCM](https://www.contest.comap.com/undergraduate/contests/mcm/) |
| **PDFs** | `data/raw/mcm_icm/` (`mcm_icm_A|B|C_YYYY.pdf`) |

---

## ICM · `icm`

| | |
|---|---|
| **Years/sessions** | 19 problem statements (Problems D/E/F, partial years 2000–2025) |
| **Questions** | 19 (one interdisciplinary modeling problem per PDF) |
| **Team size** | 3 students |
| **Time** | 99 hours (weekend) |
| **Answer type** | Written modeling report |
| **Grading** | Same rubric as MCM |
| **Source** | Internet, data, references allowed |
| **Link** | [comap.com ICM](https://www.contest.comap.com/undergraduate/contests/mcm/) |
| **PDFs** | `data/raw/mcm_icm/` (`mcm_icm_D|E|F_YYYY.pdf`) |

---

## Physics Brawl Online · `fyziklani`

| | |
|---|---|
| **Years/sessions** | 14 (2012–2025) |
| **Questions** | 282 (~20 unlockable physics problems per brawl) |
| **Team size** | Up to 5 students |
| **Time** | 3 hours |
| **Answer type** | Numerical / short written; solving unlocks harder problems |
| **Grading** | Points per problem (3–5 pts); live submission |
| **Source** | Paper, calculator; no internet |
| **Link** | [physicsbrawl.org/archive](https://physicsbrawl.org/archive) |
| **PDFs** | `data/raw/fyziklani/` |

---

## Purple Comet! Math Meet · `purple_comet`

| | |
|---|---|
| **Years/sessions** | 44 (HS + MS divisions, 2005–2026) |
| **Questions** | 1,051 (~30 problems per division per year) |
| **Team size** | Up to 6 students |
| **Time** | 60–90 minutes |
| **Answer type** | Short-answer numeric |
| **Grading** | Automatic / answer key |
| **Source** | Paper, calculator; no internet |
| **Link** | [purplecomet.org/answers](https://purplecomet.org/answers) |
| **PDFs** | `data/raw/purple_comet/` |

---

## ITYM · `itym`

| | |
|---|---|
| **Years/sessions** | 17 (2009–2025) |
| **Questions** | 218 (~10–11 open-ended math problems per year) |
| **Team size** | 4–6 students |
| **Time** | Months of research + tournament week |
| **Answer type** | Math research problems; Reporter / Opponent / Reviewer "math fights" |
| **Grading** | Jury scores on presentation, opposition, and review |
| **Source** | Research, references; no internet at tournament |
| **Link** | [itym.org/archive](https://www.itym.org/archive) |
| **PDFs** | `data/raw/itym/` |

---

## Proposed (other) · awaiting approval

| ID | Competition | Approved |
|----|-------------|:--------:|
| `pumac_power` | PUMaC Power Round | ☐ |
| `euso` | EUSO Team Practical | ☐ |

---

## Collection backlog (raw PDFs only)

| ID | Action |
|----|--------|
| `mcm` / `icm` | More years (2000–2014, 2018–2020, 2023) — COMAP URLs vary |
| `hmmt_team` | Earlier years if published on archive |
| `iypt` | Verify 2021–2025 problem-list PDFs match official IOC versions |
| `arml_power` | Older mail-in Fall/Spring seasons |
| `ioaa_group` | More years + attachment files |
| `iol_team` | Missing problem/solution PDFs |
| `ijso_practical` | Missing years + answer PDFs |
| `ieo_business_case` | Pre-2021 cases if published |
