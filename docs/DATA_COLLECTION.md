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
| `iiot` | IIOT (Informatics Olympiad in Teams) | Informatics / CS | 4 (2017, 2021–2023) | 38 |
| `icpc` | ICPC World Finals | Informatics / CS | 14 (2012–2025) | 158 |
| **Total** | | | **308** | **4,434** |

---

## Simulator Matrix

For each competition, the AI agent must be given exactly the same resources a human team has. All rules below are verified against primary official sources, linked in the **Sources** column.

| ID | Full Name | Input Modality | Team Setup | Computers | Allowed Tools & Resources | Materials Provided | Final Deliverable | Sources |
|----|-----------|----------------|------------|-----------|--------------------------|-------------------|-------------------|---------|
| `iol_team` | International Linguistics Olympiad | PDF + images/text | 4 agents | **None** | Paper & pencil only. No calculators, no calendars, no electronic devices, no internet. Agents may collaborate freely. Writing paper provided by organizers; no external paper allowed. | Problem packet PDF; blank writing paper | Short written answers on shared answer sheet | [Rules PDF](https://ioling.org/rules/rules.pdf) · [Guidelines](https://ioling.org/guidelines/en/) |
| `ioaa_group` | Intl. Olympiad on Astronomy & Astrophysics | PDF + data tables + star-chart images | 5 agents (cross-country, random) | **None** | Organizer-supplied scientific calculator at the table (e.g. CASIO fx-82CW for 2026 — personal calculators prohibited). Compass, ruler, protractor, constants sheet, graph paper provided. No formula collections from participants. No internet. | Problem PDF, constants sheet, star charts, data files, graph paper | Boxed numerical answers with units | [IOAA Statutes](https://ioaastrophysics.org/about-ioaa/organisation-and-governance) · [Group Competition 2023](https://cdn.ioaastrophysics.org/assets/IOAA%20problems/16th%20IOAA%202023/Group%20Competition%202023%20IOAA.pdf) |
| `arml_power` | ARML — Power Contest | PDF | Flexible team | **None** | Paper & pencil only. No calculators on any ARML round — no exceptions. No electronic devices. | Problem packet | Written proofs / justifications | [ARML Rules](https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public) |
| `arml_national_team` | ARML National — Team Round | PDF / printed cards | ~15 agents | **None** | Paper & pencil only. No calculators on any ARML round. No electronic devices. | Problem cards | Single numerical answer per problem | [ARML Rules](https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public) |
| `arml_national_power` | ARML National — Power Round | PDF | ~15 agents | **None** | Paper & pencil only. No calculators on any ARML round. No electronic devices. | Problem packet | Written proofs / justifications | [ARML Rules](https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public) |
| `arml_local` | ARML Local | PDF | 6 agents | **None** | Paper & pencil only. No calculators on any ARML round. No electronic devices. | Problem sheet | Single numerical answer per problem | [ARML Rules](https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public) |
| `ijso_practical` | IJSO — Team Practical | PDF protocol + physical lab | 3 agents | **None** | Organizer-provided calculator (simple statistical functions) distributed at arrival — own calculators strictly forbidden (point deduction). No bags or personal items in exam hall. No formula collections. All lab equipment, pen, ruler, scrap paper provided. | Protocol PDF, lab equipment, calculator, scrap paper | Lab report: data, calculations, tables, graphs | [IJSO Statutes](https://ijsoweb.org/qna/IJSO-Statutes-Qatar-2019.pdf) |
| `ieo_business_case` | IEO — Business Case | PDF case study | 3–5 agents | **Unrestricted** | Any online and offline materials freely permitted during prep day. Any software (Excel, Python, PowerPoint, etc.). No contact with anyone outside the team — only team members and IEO officials allowed. Slides locked after submission deadline; no edits permitted after. | Case study PDF | Slide deck (PDF) + oral presentation | [IEO Syllabus](https://files.ieo-official.org/IEO_Syllabus.pdf) · [IEO Regulations](https://files.ieo-official.org/IEO_Regulations_of_Competition.pdf) |
| `iypt` | International Young Physicists' Tournament | Annual list of 17 open-ended problems | 5 agents | **Any** | All aids fully permitted during Physics Fights: internet, laptops, literature, notes, calculators, dictionaries — agents may look things up in real time. Only restriction: no communication with non-participants (coaches, outsiders) during a fight. Teams prepare over the full competition season. | 17 open-ended physics problems | Oral talk (≤12 min) + live debate (Reporter / Opponent / Reviewer) | [IYPT Basic Facts](https://www.iypt.org/basic-facts/) · [Regulations 2025](https://www.iypt.org/wp-content/uploads/2025/05/IYPT-Regulations-2025.pdf) |
| `hmmt_team` | HMMT — Team Round | PDF | 6–8 agents | **None** | No calculators, no books, no notes, no drawing aids (rulers, protractors, compasses, graph paper all prohibited). No laptops, phones, or any electronic device. Pencil and organizer-provided scratch paper only. Full team collaboration allowed. | Problem sheet, blank scratch paper | Short answers (Nov) or written proofs (Feb) | [HMMT Testing Info](https://hmmt.co/www/tournaments/testing) |
| `hmmt_guts` | HMMT — Guts Round | Paper batches (3–4 problems, progressive) | 6–8 agents | **None** | Same as Team Round: no calculators, no books, no notes, no devices. Pencil and scratch paper only. Team sends runner to collect next batch after submitting current answers; live score visible. | Problem batches, blank scratch paper | Numerical answers per batch, submitted progressively | [HMMT Testing Info](https://hmmt.co/www/tournaments/testing) |
| `mcm` | Mathematical Contest in Modeling | PDF problem statement | 3 agents | **Unrestricted** | Any inanimate resource: full internet, any software (Python, MATLAB, R, Excel, LaTeX, etc.). AI tools (ChatGPT, etc.) permitted but require an appended "Report on Use of AI" (not counted toward page limit). No outside human help — team members only. 99-hour contest window. | Problem PDF (choose A, B, or C) | PDF report ≤ 25 pages (summary + solution + refs + appendices + code all count toward limit) | [COMAP Rules](https://www.contest.comap.org/undergraduate/contests/mcm/instructions.html) |
| `icm` | Interdisciplinary Contest in Modeling | PDF problem statement | 3 agents | **Unrestricted** | Same as MCM: full internet, any software, AI permitted with disclosure. No outside human help. 99-hour window. | Problem PDF (choose D, E, or F) | PDF report ≤ 25 pages | [COMAP Rules](https://www.contest.comap.org/undergraduate/contests/mcm/instructions.html) |
| `fyziklani` | Physics Brawl Online (Fyziklání online) | Online text + images (progressive queue) | Up to 5 agents | **Internet-connected** | Full internet access and any literature permitted. Electronic calculators allowed. Generative AI (ChatGPT, Copilot, etc.) strictly prohibited — teams caught using it are disqualified. ⚠️ In-person Fyziklání (Prague) has opposite rules: no internet, printed materials only, non-internet calculator only. Our data is from the online variant. | Live online problem queue (new problems unlock on correct submission) | Numerical / short-text answers via online judge | [Online Rules 2025](https://physicsbrawl.org/download/2025/rules-en-250901.pdf) · [In-person rules](https://fyziklani.org/download/2025/infobooklet-en.pdf) |
| `purple_comet` | Purple Comet! Math Meet | PDF (10-day window) | 1–6 agents | **1 computer** (answer submission) | Calculators and computation tools explicitly allowed: Desmos, WolframAlpha, Mathematica, Maple, GeoGebra, Excel, custom code. No AI tools (ChatGPT, Gemini, Copilot, Claude, etc.). No internet search for solution methods — agents must determine the approach themselves; tools may only execute calculations, not explain methods. | Problem PDF (MS: 20 problems / 60 min; HS: 30 problems / 90 min) | Non-negative integer answers submitted online | [Rules](https://purplecomet.org/rules) · [FAQ](https://purplecomet.org/faq) |
| `itym` | International Tournament of Young Mathematicians | Annual list of 10–11 research problems | 4–6 agents | **Laptop + projector** | All resources freely available during multi-month prep (internet, books, software). At the tournament: Reporter may only present content from the pre-submitted PDF — no live edits (minor error corrections allowed verbally). Laptop and projector for slides. No live internet during oral rounds. Quiz (2.5 hrs, written): device policy not explicitly published. | 10–11 open-ended research problems; final PDFs submitted before event | Oral presentation + written Quiz | [ITYM Rules](https://www.itym.org/rules) |
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | 3–4 text prompts revealed at event start | 3 agents | **None** | No electronic devices at any stage (ban introduced late 2022). All writing handwritten. Stage 1 (20 min): team discusses/plans together, no devices, no writing. Stage 2 (40 min): each agent writes their essay individually, handwritten. Stage 3 (15 min): agents may annotate/edit teammates' essays but may not complete an unfinished piece. | Prompts revealed at start; blank lined paper | 3 handwritten essays (one per agent, any form/length) | [WSC Events](https://scholarscup.org/events/) · [WSC Wiki](https://www.owiki.org/wiki/World_Scholar%27s_Cup) |
| `jessup` | Philip C. Jessup International Law Moot Court | PDF Compromis (~15 pp.) released each September | 2–5 agents | **Unrestricted** (multi-month prep) | Full internet research permitted. ILSA provides database access: Jus Mundi, Oxford UP, LexisNexis, HeinOnline. Any legal texts, treaties, case law, scholarship allowed. No AI restriction in current rules. ~5 months to research and draft both memorials. Memorial length/format per annual Official Rules (released each August). | Compromis PDF + ILSA basic materials + database credentials | Written memorials (Applicant + Respondent) + oral pleading rounds | [Jessup FAQ](https://www.ilsa.org/jessup-competitors/jessup-faq/) · [Memorial Judging Guide 2022](https://ilsa.org/Jessup/Jessup2022/Admin/2022%20Memorial%20Judging%20Guide.pdf) |
| `iiot` | Informatics Olympiad in Teams | PDF problem statements | 4 agents | **2 provided VMs** | Internet restricted to online judge/grading system only — no web browsing. USB ports disabled. Only C++ accepted for submissions. C++ language reference documentation provided by organizer. No personal textbooks, notes, or materials. | Problem PDFs, online judge interface, C++ reference docs | C++ code submitted to automated judge (AC / WA / TLE / RE) | [IIOT Regulations](https://iio.team/documents/Regulations.pdf) · [IIOT 2026 Online Rules](http://iiot2026.cni.nt.edu.ro/online-participation-rules/) |
| `icpc` | ICPC World Finals | PDF problem set | 3 agents | **1 shared workstation** | Languages: C, C++, Java, Kotlin, Python 3. Organizer-configured IDEs (IntelliJ, Eclipse, VS Code, vim, emacs). Team Reference Document (TRD) ≤ 25 pages, single-sided, self-printed — the only pre-written code or notes permitted. Each contestant may bring 1 printed natural-language dictionary (unannotated). No internet, no other books, no calculators, no extra devices. | Problem PDF, 1 workstation, blank scratch paper | Code submitted to automated judge; ranked by # solved then time penalty | [ICPC Environment](https://docs.icpc.global/worldfinals-programming-environment) · [ICPC EUC Rules 2026](https://euc.icpc.global/home-2026/rules/) |

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
| **Years/sessions** | 4 (2017, 2021–2023) |
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
