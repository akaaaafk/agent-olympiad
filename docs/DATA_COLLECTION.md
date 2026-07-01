# Data collected

Last updated: 2026-06-29

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
| **20** | **308** | **4,434** |

| ID | Competition | Domain | Years/sessions | Questions |
|----|-------------|--------|---------------:|----------:|
| `iol_team` | IOL Team Contest | Linguistics | 21 | 73 |
| `ioaa_group` | IOAA Group Competition | Astronomy | 9 | 232 |
| `arml_power` | ARML Power Contest (mail-in) | Mathematics | 15 | 278 |
| `arml_national_team` | ARML National — Team Round | Mathematics | 11 | 110 |
| `arml_national_power` | ARML National — Power Round | Mathematics | 11 | 209 |
| `arml_local` | ARML Local | Mathematics | 6 | 65 |
| `ijso_practical` | IJSO Team Practical | Science | 22 | 74 |
| `ieo_business_case` | IEO Business Case | Economics | 5 | 5 |
| `iypt` | IYPT (Young Physicists' Tournament) | Physics | 39 | 655 |
| `hmmt_team` | HMMT — Team Round | Mathematics | 14 | 140 |
| `hmmt_guts` | HMMT — Guts Round | Mathematics | 21 | 766 |
| `mcm` | MCM (Mathematical Contest in Modeling) | Mathematics | 18 | 18 |
| `icm` | ICM (Interdisciplinary Contest in Modeling) | Interdisciplinary | 19 | 19 |
| `fyziklani` | Physics Brawl Online (Fyziklání) | Physics | 14 | 282 |
| `purple_comet` | Purple Comet! Math Meet | Mathematics | 44 | 1,051 |
| `itym` | ITYM (Young Mathematicians' Tournament) | Mathematics | 17 | 218 |
| `wsc_writing` | WSC — Collaborative Writing | Literature / Humanities | 3 (2024–2026) | 42 |
| `jessup` | Jessup Moot Court Competition | International Law | 1 (2024) | 1 |
| `iiot` | IIOT (Informatics Olympiad in Teams) | Informatics / CS | 4 (2021–2024) | 38 |
| `icpc` | ICPC World Finals | Informatics / CS | 14 (2012–2025) | 158 |
| **Total** | | | **286+** | **4,195+** |

---

## Simulator Matrix

For each competition, the AI agent must be given exactly the same resources a human team has. This table defines what the simulator must provide.

| ID | Full Name | Input Modality | Team Setup | Computers / Devices | Allowed Tools & Resources | Materials Provided by Organiser | Final Deliverable |
|----|-----------|----------------|------------|---------------------|--------------------------|-------------------------------|-------------------|
| `iol_team` | International Linguistics Olympiad | PDF + embedded images | 4 agents | **None** | **Strict closed-book: paper & pencil only.** No calculator, no reference material. | Problem packet PDF | Written answers on team answer sheet |
| `ioaa_group` | Intl. Olympiad on Astronomy & Astrophysics | PDF + data tables + star-chart images | 5 agents | **None** (1 scientific calculator per student) | Scientific calculator; compass, ruler, protractor; provided constants/formulae sheet. No internet. | Problem PDF, constants sheet, star charts, CSV data files, graph paper | Boxed numerical answers with units |
| `arml_power` | American Regions Mathematics League — Power | PDF | Flexible team size | **None** | **Paper & pencil only; no calculator.** Proofs may be written in any format. | Problem packet | Written proofs / justifications (partial credit per sub-part) |
| `arml_national_team` | ARML National — Team Round | PDF / printed cards | ~15 agents | **None** | **Calculator allowed** (scientific or graphing). No internet. | Problem cards | Single numerical answer per question |
| `arml_national_power` | ARML National — Power Round | PDF | ~15 agents | **None** | **Calculator allowed** (scientific or graphing). No internet. | Problem packet | Written proofs / justifications |
| `arml_local` | ARML Local | PDF | 6 agents | **None** | **Calculator allowed** (scientific or graphing). No internet. | Problem sheet | Single numerical answer per question |
| `ijso_practical` | International Junior Science Olympiad — Team Practical | PDF protocol + physical lab setup | 3 agents | **None** | Scientific calculator; physical lab instruments (glassware, chemicals, thermometer, scale, etc.); graph paper. No internet. | Protocol PDF, lab equipment list, data tables | Lab report: measurements, calculations, tables, graphs, drawings |
| `ieo_business_case` | International Economics Olympiad — Business Case | PDF case study + data files | 5 agents | **1+ computers** | **Full internet research** allowed; spreadsheet (Excel/Google Sheets); slide software (PowerPoint/Google Slides). ~24 h window. | Case PDF, supporting data files | Presentation slides (PDF) + oral Q&A |
| `iypt` | International Young Physicists' Tournament | Annual text problem list | 5 agents | Varies; presentation slides required | **Months of prep:** any books, papers, software, experiments allowed. **At tournament:** printed materials & slides only; no live internet. | 17 open-ended physics problems per year | Oral physics presentation (~12 min) + live Reporter/Opponent/Reviewer debate |
| `hmmt_team` | Harvard-MIT Mathematics Tournament — Team Round | PDF | 6–8 agents | **None** | **Paper & pencil only; no calculator.** Problems often build on each other sequentially. | Problem sheet | Short numerical or algebraic answers (problems may reference earlier answers) |
| `hmmt_guts` | HMMT — Guts Round | Paper batches delivered progressively | 6–8 agents | **None** | **Paper & pencil only; no calculator.** Answers submitted as each batch is completed. | Sets of 3–4 problems delivered one batch at a time | Numerical answers per set, submitted progressively; live leaderboard feedback |
| `mcm` | Mathematical Contest in Modeling | PDF problem statement | 3 agents | **1 computer** | **Full internet, any software** (Python, MATLAB, R, Excel, LaTeX/Word). Data downloads permitted. 99-hour window. | Problem PDF (Problems A, B, or C) | PDF report ≤ 25 pages + 1-page summary sheet |
| `icm` | Interdisciplinary Contest in Modeling | PDF problem statement | 3 agents | **1 computer** | Same as MCM. | Problem PDF (Problems D, E, or F) | PDF report ≤ 25 pages + 1-page summary sheet |
| `fyziklani` | Physics Brawl Online (Fyziklání) | Online text + images (progressive queue) | Up to 5 agents | **1 computer** (online judge only) | Scientific calculator; paper. **No internet browsing.** Only the online judge portal is accessible. Problems unlock based on correct answers. | Progressive problem queue (harder problems unlock as easier ones are solved) | Numerical / short-text answers submitted via online judge; live score visible |
| `purple_comet` | Purple Comet! Math Meet | PDF or online text | Up to 6 agents | **1 computer** (online submission) | **Calculator allowed.** Online submission only; no internet research during contest. | Problem PDF (HS or MS division) | Integer or rational numerical answers submitted online |
| `itym` | International Tournament of Young Mathematicians | Annual text problem list | 4–6 agents | Varies; presentation slides required | **Months of prep:** any books, papers, software, tools. **At tournament:** printed materials & slides only; no live internet. | 10–11 open-ended math problems per year | Oral math presentation + live Reporter/Opponent/Reviewer debate |
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | 6 text prompts (revealed at start of event) | 3 agents | **None** | **Nothing — fully closed.** No devices, no notes from outside. During 20-min team prep: 1 sheet of blank paper per team member for notes only (discarded before writing). | 6 prompts (1 per subject area); blank lined paper | 3 handwritten essays (1 per agent, ~1 page each), 40 min individual writing |
| `jessup` | Philip C. Jessup International Law Moot Court Competition | PDF Compromis (legal problem scenario, ~15 pp.) | 2–5 agents | **Computers** (multi-month prep window) | **Full internet, legal databases** (Westlaw, LexisNexis, HeinOnline), any legal texts, international law treaties. | Compromis PDF (released annually each September) | Written memorials (Applicant ≤ 45 pp., Respondent ≤ 45 pp.) + oral pleading rounds |
| `iiot` | Informatics Olympiad in Teams | PDF problem statements | 4 agents | **2 computers** per team | 2 computers (organizer-provided VM, identical software on both); **internet restricted to grading/judge system only** (no browsing); USB ports disabled; **only C++ allowed**; language reference docs provided by organizer (no personal materials, no textbooks). Source: [IIOT Regulations 2022–23](https://iio.team/documents/Regulations.pdf), [IIOT 2026 online rules](http://iiot2026.cni.nt.edu.ro/online-participation-rules/) | Problem PDFs, online judge interface | Code solutions in C++ submitted to automated judge; judge returns AC / WA / TLE / RE per test case |
| `icpc` | International Collegiate Programming Contest — World Finals | PDF problem set | 3 agents | **1 computer** | 1 computer; **no internet**; **team reference sheet allowed** (self-prepared, ≤ 25 pages, printed, brought in). Common IDEs. Language choice: C++, Java, Python, Kotlin. | Problem PDF, 1 computer, blank scratch paper | Code solutions submitted to automated judge; ranked by # problems solved then total time penalty |

---

## IOL Team (International Linguistics Olympiad) · `iol_team`

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

## IOAA Group (International Olympiad on Astronomy and Astrophysics) · `ioaa_group`

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

## ARML Power Contest — mail-in (American Regions Mathematics League) · `arml_power`

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

## ARML National — Team Round (American Regions Mathematics League) · `arml_national_team`

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

## ARML National — Power Round (American Regions Mathematics League) · `arml_national_power`

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

## ARML Local (American Regions Mathematics League) · `arml_local`

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

## IJSO Team Practical (International Junior Science Olympiad) · `ijso_practical`

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

## IEO Business Case (International Economics Olympiad) · `ieo_business_case`

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

## IYPT (International Young Physicists' Tournament) · `iypt`

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

## HMMT — Team Round (Harvard-MIT Mathematics Tournament) · `hmmt_team`

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

## HMMT — Guts Round (Harvard-MIT Mathematics Tournament) · `hmmt_guts`

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

## MCM (Mathematical Contest in Modeling) · `mcm`

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

## ICM (Interdisciplinary Contest in Modeling) · `icm`

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

## Physics Brawl Online (Fyziklání) · `fyziklani`

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

## ITYM (International Tournament of Young Mathematicians) · `itym`

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

## WSC Collaborative Writing (World Scholar's Cup) · `wsc_writing`

| | |
|---|---|
| **Domain** | Literature / Humanities |
| **Years/sessions** | 3 (2024, 2025, 2026) |
| **Questions** | 42 guiding questions (discussion prompts) |
| **Team size** | 3 students |
| **Time** | 75 min total: 20 min team prep → 40 min individual writing → 15 min peer edit |
| **Answer type** | Persuasive essays; 6 prompts offered (1 per subject area), team picks 3, each member writes one |
| **Grading** | 4 criteria × 1–7 = max 28 pts per essay; contributes 18.75% of team total |
| **Source** | Official WSC themes site (themes.scholarscup.org); prompts are guiding questions from the annual curriculum |
| **Link** | [themes.scholarscup.org](https://themes.scholarscup.org) |
| **Data** | `data/raw/wsc_writing/all_guiding_questions.json` (42 prompts), `data/benchmarks/wsc_writing/benchmark.json` |
| **Notes** | Actual competition writing prompts are not published in advance. The 42 guiding questions extracted from the official themes SPA are the closest public proxy — these ARE what students prep with. Covers 2024 ("Reimagining the Present"), 2025 ("Reigniting the Future"), 2026 ("Are We There Yet?"). |

---

## Jessup Moot Court (Philip C. Jessup International Law Moot Court Competition) · `jessup`

| | |
|---|---|
| **Domain** | International Law |
| **Years/sessions** | 1 (2024, via Wayback Machine; full archive pending ILSA.org maintenance) |
| **Questions** | 1 Compromis |
| **Team size** | 2–5 students (law school / collegiate) |
| **Time** | Months of preparation; written memorials + oral rounds |
| **Answer type** | Written memorials (Applicant + Respondent) and oral pleadings |
| **Grading** | Rubric: legal analysis, argumentation, writing quality, oral advocacy |
| **Source** | Compromis (problem) released annually each September since 1960; ~100 countries, 700 schools |
| **Link** | [ilsa.org/jessup](https://www.ilsa.org/jessup/) |
| **PDFs** | `data/raw/jessup/` — 2024 recovered via Wayback Machine; full archive available once ILSA.org returns from maintenance (closed May–June 2026, expected back July 2026) |

---

## IIOT (Informatics Olympiad in Teams) · `iiot`

| | |
|---|---|
| **Domain** | Informatics / Computer Science |
| **Years/sessions** | 4 (2021–2024) |
| **Questions** | 38 problem statements |
| **Team size** | 4 students (high school) |
| **Time** | 3 hours (international round: 4 hours); 2 PCs per team |
| **Answer type** | Algorithmic code solutions submitted to an online judge |
| **Grading** | Automated judge: accepted / wrong answer / time-limit exceeded per test case |
| **Source** | Paper, 2 computers; no internet |
| **Link** | [iio.team](https://iio.team/) |
| **Data** | `data/raw/iiot/` (38 PDFs), `data/benchmarks/iiot/benchmark.json` |

---

## ICPC World Finals (International Collegiate Programming Contest) · `icpc`

| | |
|---|---|
| **Domain** | Informatics / Computer Science |
| **Years/sessions** | 14 (2012–2025) |
| **Questions** | 158 problem statements |
| **Team size** | 3 students (collegiate) |
| **Time** | 5 hours; 1 computer per team |
| **Answer type** | Algorithmic code solutions; multiple problems per contest |
| **Grading** | Automated judge; ranked by problems solved then time penalty |
| **Source** | 1 computer; no internet; reference materials allowed |
| **Link** | [icpc.global](https://icpc.global/) / [problems.icpc.io](https://problems.icpc.io/) |
| **Data** | `data/raw/icpc/` (158 `.txt` problem statements, 2012–2025), `data/benchmarks/icpc/benchmark.json` |

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
| `wsc_writing` | Collect essay prompts + rubrics from scholarscup.org per season |
| `jessup` | Re-run `collectors/jessup.py` once ILSA.org returns from maintenance (expected July 2026); URL pattern confirmed: `ilsa.org/Jessup/Jessup{YEAR}/{YEAR} Jessup Compromis.pdf` |
| `iiot` | Collect task PDFs + solutions from iio.team/competition/tasks |
| `icpc` | Collect World Finals problem sets from problems.icpc.io |
