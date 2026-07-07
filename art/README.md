# Data collected — `art/`

Last updated: 2026-07-06

> **Data files are not in git.** They are hosted on the private HF dataset [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) — run `python download_data.py` at the repo root to fetch them.

**Current focus:** raw material collection only (problems, cases, rubrics, winning samples) for 12 proposed team competitions in humanities, arts appreciation, ethics debate, and business case (~5-agent teams). All files downloaded from official public channels on 2026-07-06.

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published case set / problem release (one PDF or archive).  
**Question** = one case, problem, or scored item inside a year/session (e.g. one ethics case, one toss-up question, one debate speech).

---

## Summary

### Collected

| Competitions | Years/sessions | Questions |
|-------------:|---------------:|----------:|
| **12** | **117** | **~114,000** |

| ID | Competition | Domain | Years/sessions | Questions |
|----|-------------|--------|---------------:|----------:|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | Philosophy / Ethics | 9 (2021–2026 case sets) | ~140 cases |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | Ethics | 1 (2025–26) | 15 cases |
| `science_bowl` | DOE National Science Bowl | Science (buzzer quiz) | 33 sample-set groups (508 PDFs) | ~14,000+ |
| `qanta` | QANTA Quiz Bowl | General knowledge | 1 (2021.12.20 release) | ~100,000 tossups |
| `gcch_harvard` | Global Case Competition at Harvard | Business (M&A / strategy) | 7 (2018–2026) | 7 cases |
| `case_world_cup` | Undergrad Case Competition World Cup | Business (consulting) | 1 (2026, rules only) | 0 (case pending registration) |
| `cfa_research_challenge` | CFA Institute Research Challenge | Finance (equity research) | 19 (2008–2026) | 19 champion reports |
| `wharton_investment` | Wharton Global HS Investment Competition | Finance (portfolio, long-horizon) | 4 (2019–22 + current) | 4 case studies |
| `igem` | iGEM | Synthetic biology (project) | 2 (2019, 2025 handbooks) | — (rubrics only) |
| `nhd` | National History Day (Group entries) | History | 1 (rule book + 5 category rubrics) | — (rubrics only) |
| `debatebench` | WUDC / BP Debate (DebateBench) | Debate | 32 debates | 256 speeches |
| `vis_moot` | Willem C. Vis Moot | International commercial law | 7 (26th–33rd editions) | 7 Problems |
| **Total** | | | **117** | **~114,000** |

---

## Simulator Matrix

For each competition, the AI agent must be given exactly the same resources a human team has. Rules below are based on the official documents downloaded into each folder and the source pages linked in the **Sources** column.

| ID | Full Name | Input Modality | Team Setup | Computers | Allowed Tools & Resources | Materials Provided | Final Deliverable | Sources |
|----|-----------|----------------|------------|-----------|--------------------------|-------------------|-------------------|---------|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | Case set PDF (released weeks in advance) | 5 agents | None during match | Cases studied in advance · during match: oral discussion only, no electronic devices · full rules & scoring guides in folder | Case set, rules PDF, judging/scoring guides | Oral presentation → opposing commentary → response → judge Q&A | [appe-ethics.org](https://www.appe-ethics.org/cases-rules-guidelines/) |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | Case set PDF (released in advance) | 3–7 agents | None during match | Same structure as APPE with a dialogic (non-adversarial) format · cases CC-licensed | National case set (15 cases + discussion questions) | Oral case discussion judged by rubric | [nhseb.org/case-library](https://nhseb.org/case-library) |
| `science_bowl` | DOE National Science Bowl | Question sets (read aloud; PDF here) | 4 agents + 1 alternate | None | No calculators · no reference materials · Toss-Up: **no conferring**; Bonus: team conferring allowed · buzzer-based | Toss-Up + Bonus question rounds (~25 questions/round) | Spoken short answers on buzzer | [science.osti.gov NSB](https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources) |
| `qanta` | QANTA Quiz Bowl | Pyramidal tossup text, revealed clue by clue | 4 agents | None | Clues revealed incrementally · earlier buzz = more knowledge credit · no external references · buzz-timing decision is part of the task | JSON question stream with answers & metadata | Answer at chosen buzz point, auto-judged | [qanta-org.github.io](https://qanta-org.github.io/data-and-code/) · [HF mirror](https://huggingface.co/datasets/TasnimKabir12/qanta) |
| `gcch_harvard` | Global Case Competition at Harvard | Case PDF | 2–5 agents | Unrestricted | Full internet & any software · winning decks from past editions serve as gold-standard references | Case PDF | Slide deck + recorded/live pitch | [thecasecompetition.org](https://www.thecasecompetition.org/past-editions) |
| `case_world_cup` | Undergrad Case Competition World Cup | Case (distributed by email after registration) | 4–5 agents | Unrestricted | Full internet & any software · two-stage format: written deck qualifies for video/live pitch | Case prompt (pending), scoring criteria page archived | Round 1 written deck → Round 2 pitch | [managementconsulted.com](https://managementconsulted.com/undergrad-case-competition-world-cup-2026/) |
| `cfa_research_challenge` | CFA Institute Research Challenge | Assigned public company + public filings | 3–5 agents | Unrestricted | Full internet research · public company data · industry-standard rubric (valuation, writing, presentation) | Subject company; 19 years of champion reports as reference | 10-page equity research report (buy/sell) + oral defense | [cfainstitute.org](https://www.cfainstitute.org/insights/events/research-challenge/past-champions) |
| `wharton_investment` | Wharton Global HS Investment Competition | Client case study (HTML) + trading simulator | 4–7 agents | Online simulator | 10-week simulated portfolio management · full research allowed · client constraints defined in case | Client case study with background & investment constraints | Portfolio track record + final strategy report & defense | [globalyouth.wharton.upenn.edu](https://globalyouth.wharton.upenn.edu/investment-competition/) |
| `igem` | iGEM | Project brief + judging handbook | 8–15 agents | Unrestricted | Season-long synthetic-biology project · full lab & internet · two-layer judging: objective medal criteria checklist + subjective award rubric | Judging handbooks (2019, 2025) with medal criteria & rubrics | Team wiki + presentation + judging session | [competition.igem.org](https://competition.igem.org/) |
| `nhd` | National History Day — Group entries | Annual theme + rule book | 2–5 agents | Unrestricted | Year-long historical research · 5 entry categories (paper / exhibit / documentary / performance / website) · weighted rubric: 80% historical quality, 20% presentation | Contest rule book + per-category evaluation forms | Category-specific project entry | [nhd.org contest rules](https://nhd.org/en/contest/contest-rules/) |
| `debatebench` | WUDC / British Parliamentary Debate | Motion text (revealed 15 min before round) | 8 agents (4 teams × 2) | None during prep | BP format: 15-minute prep after motion release · printed materials only, no internet during prep · 7-minute speeches in fixed order | Motion; 32 transcribed matches with official judge scores as ground truth | 7-minute speech per agent; ranked by judges | [DebateBench on HF](https://huggingface.co/datasets/utkarsh2105/DebateBench) · [arXiv:2502.06279](https://arxiv.org/abs/2502.06279) |
| `vis_moot` | Willem C. Vis International Commercial Arbitration Moot | Problem PDF (60–90 pp. case record) | 2–8 agents | Unrestricted | Full legal research · months of preparation · Procedural Order No. 2 provides official clarifications · same structure as Jessup (pipeline reusable) | Problem + PO2 + current rules | Claimant & Respondent memoranda + oral pleading | [vismoot.org](https://www.vismoot.org/previous-moots/) |

---

## APPE Intercollegiate Ethics Bowl · `ethics_bowl_appe`

| | |
|---|---|
| **Domain** | Philosophy / Ethics (humanities) |
| **Years/sessions** | 9 case sets (2021 regional – 2026 national) |
| **Questions** | ~140 cases (~15–17 per set, each with discussion questions) |
| **Team size** | 5 students |
| **Time** | Cases released weeks in advance; timed oral rounds at match |
| **Answer type** | Oral: position statement → opposing commentary → response → judge Q&A |
| **Grading** | Judge rubric (argument quality, responsiveness to objections); official scoring guides included |
| **Source** | Advance case set; no electronic devices during match |
| **Link** | [appe-ethics.org/cases-rules-guidelines](https://www.appe-ethics.org/cases-rules-guidelines/) |
| **Data** | `ethics_bowl_appe/` — 9 case sets + `rules-2025-national.pdf` / `rules-2025-regional.pdf` + `judging-scoring-guide.pdf`, `judging-questions-guide.pdf`, `scoring-sheet-2020.pdf` (14 files) |
| **Notes** | Natural multi-turn adversarial structure; public rubric suits LLM-judge + human-eval hybrid. 2001–2021 Case Library exists on the official Google Drive, organized by 28 topics (incl. Art and Cultural Heritage) — see backlog. |

---

## National High School Ethics Bowl · `ethics_bowl_nhseb`

| | |
|---|---|
| **Domain** | Ethics (humanities) |
| **Years/sessions** | 1 (2025–26 National Case Set) |
| **Questions** | 15 cases + discussion questions |
| **Team size** | 3–7 students |
| **Time** | Cases released in advance; timed oral rounds at match |
| **Answer type** | Dialogic (non-adversarial) case discussion |
| **Grading** | Judge rubric, similar to APPE |
| **Source** | Advance case set (CC-licensed, 300+ cases in library); no devices during match |
| **Link** | [nhseb.org/case-library](https://nhseb.org/case-library) |
| **Data** | `ethics_bowl_nhseb/` — `2025-26-national-case-set.pdf` |
| **Notes** | Same structure as APPE at a lower difficulty tier — usable for curriculum. Historical 2012–2024 sets are archived case-by-case as web pages (see backlog). |

---

## DOE National Science Bowl · `science_bowl`

| | |
|---|---|
| **Domain** | Science — physics, chemistry, biology, earth science, energy, math (buzzer quiz) |
| **Years/sessions** | 33 sample-set groups (HS: 17, MS: 16), 1990s–2022 |
| **Questions** | ~14,000+ across 508 PDFs (~25 questions per round: Toss-Up + Bonus) |
| **Team size** | 4 students + 1 alternate |
| **Time** | Short timed buzzer rounds |
| **Answer type** | Spoken short answers; Toss-Up = no conferring, Bonus = team conferring allowed |
| **Grading** | Objective answers, auto-gradable; buzzer collaboration can be simulated |
| **Source** | No calculators, no references |
| **Link** | [science.osti.gov NSB resources](https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources) |
| **Data** | `science_bowl/` — `HS-Sample-Questions/` (17 sets) + `MS-Sample-Questions/` (16 sets), 508 PDFs |
| **Notes** | Toss-Up (individual decision) vs Bonus (team deliberation) is a built-in "individual vs team" controlled-comparison scenario. |

---

## QANTA Quiz Bowl · `qanta`

| | |
|---|---|
| **Domain** | General knowledge (humanities + sciences) |
| **Years/sessions** | 1 (2021.12.20 dataset release, train + dev) |
| **Questions** | ~100,000 pyramidal tossups with answers, category, tournament, and year metadata |
| **Team size** | 4 students |
| **Time** | Real-time: clues revealed hard-to-easy; earlier buzz = stronger knowledge signal |
| **Answer type** | Short answer at chosen buzz point |
| **Grading** | Automatic |
| **Source** | Incremental clue stream; no external references |
| **Link** | [qanta-org.github.io](https://qanta-org.github.io/data-and-code/) · [HF mirror TasnimKabir12/qanta](https://huggingface.co/datasets/TasnimKabir12/qanta) |
| **Data** | `qanta/` — `qanta.train.2021.12.20.json` (169 MB) + `qanta.dev.2021.12.20.json` |
| **Notes** | Supports simulating a 4-agent team with per-category specialization plus buzz-timing decisions. |

---

## Global Case Competition at Harvard · `gcch_harvard`

| | |
|---|---|
| **Domain** | Business case — finance / M&A / strategy |
| **Years/sessions** | 7 official cases (2018–2026) |
| **Questions** | 7 (one open-ended case per edition) |
| **Team size** | 2–5 students |
| **Time** | Multi-day case window + pitch |
| **Answer type** | Slide deck + pitch |
| **Grading** | Judge rubric on deck + pitch; requires partial human evaluation |
| **Source** | Unrestricted internet & software |
| **Link** | [thecasecompetition.org/past-editions](https://www.thecasecompetition.org/past-editions) |
| **Data** | `gcch_harvard/` — `case-2018-gm-tesla.pdf`, `case-2020/2021/2023/2024/2025/2026.pdf` + 9 winning-team decks (`gcch_03/04/05/06/08/09/10/13/15.pdf`, untitled PDF metadata — open to confirm and rename) + `past-editions-page.html` (17 files) |
| **Notes** | Real M&A/strategy cases with winning decks as gold-standard references. |

---

## Undergrad Case Competition World Cup · `case_world_cup`

| | |
|---|---|
| **Domain** | Business case — consulting |
| **Years/sessions** | 1 (2026 format / scoring / registration page archived) |
| **Questions** | 0 collected (case prompt distributed by email after registration) |
| **Team size** | 4–5 students |
| **Time** | Two rounds: written deck → video/live pitch |
| **Answer type** | Round 1 written deck; Round 2 pitch |
| **Grading** | Public scoring dimensions |
| **Source** | Unrestricted internet & software |
| **Link** | [managementconsulted.com](https://managementconsulted.com/undergrad-case-competition-world-cup-2026/) |
| **Data** | `case_world_cup/` — `competition-info-2026.html` |
| **Notes** | Medium data availability. Either register to obtain the case, or use GCCH / CFA as the primary business-case sources instead. |

---

## CFA Institute Research Challenge · `cfa_research_challenge`

| | |
|---|---|
| **Domain** | Finance — equity research reports |
| **Years/sessions** | 19 (2008–2026, one global champion per year) |
| **Questions** | 19 champion written reports (+ defense presentations), 38 PDFs total |
| **Team size** | 3–5 students |
| **Time** | Months-long: research → 10-page report → oral defense |
| **Answer type** | Buy/sell equity research report on an assigned listed company + defense |
| **Grading** | Industry rubric (valuation, writing, presentation); real winning samples as ground truth |
| **Source** | Unrestricted public research |
| **Link** | [cfainstitute.org past champions](https://www.cfainstitute.org/insights/events/research-challenge/past-champions) |
| **Data** | `cfa_research_challenge/` — 38 PDFs covering real subjects (Commonwealth Bank, Vestas, Canadian Tire, …) |
| **Notes** | Clear task definition; 19 years of champion samples usable as reward-model training / comparison data. Natural 3–5 agent role split: valuation / industry / writing / defense. |

---

## Wharton Global HS Investment Competition · `wharton_investment`

| | |
|---|---|
| **Domain** | Finance — investment strategy (long-horizon) |
| **Years/sessions** | 4 (2019–20, 2020–21, 2021–22 client case studies + current-season case) |
| **Questions** | 4 full case texts (client background + investment constraints) |
| **Team size** | 4–7 students |
| **Time** | 10-week simulated portfolio + final strategy report & defense |
| **Answer type** | Portfolio decisions over time + written strategy report |
| **Grading** | Strategy report & defense judged; portfolio performance observable |
| **Source** | Online trading simulator; full research allowed |
| **Link** | [globalyouth.wharton.upenn.edu](https://globalyouth.wharton.upenn.edu/investment-competition/) |
| **Data** | `wharton_investment/` — `case-study-2019-2020/2020-2021/2021-2022.html` + `case-study-current.html` |
| **Notes** | **Best long-horizon candidate** — deterministic evaluation possible by replaying real historical market data. Analyst/PM role split for 4–7 agents. Past winning reports are scattered on Issuu/SlideShare (see backlog). |

---

## iGEM (International Genetically Engineered Machine) · `igem`

| | |
|---|---|
| **Domain** | Synthetic biology — season-long project competition |
| **Years/sessions** | 2 (2019 + 2025 judging handbooks) |
| **Questions** | — (rubrics only; no problem sets — iGEM is project-based) |
| **Team size** | 8–15 students |
| **Time** | Full season (months) |
| **Answer type** | Team wiki + presentation + judging session |
| **Grading** | Two-layer: objective medal-criteria checklist + subjective award rubric |
| **Source** | Unrestricted (real lab + internet) |
| **Link** | [competition.igem.org](https://competition.igem.org/) · [static.igem.org](https://static.igem.org/) |
| **Data** | `igem/` — `2025-judge-handbook.pdf` (7.5 MB, medal criteria + award rubric + judging process) + `2019-judging-handbook.pdf` |
| **Notes** | Template for large-team, capstone-style project competition. The **two-layer judging structure** (objective checklist + subjective rubric) transfers directly to agent-team evaluation. 20 years of team wikis (`20XX.igem.org/Team:XXX`) are statically crawlable but huge — sample by year/medal (see backlog). |

---

## National History Day — Group entries · `nhd`

| | |
|---|---|
| **Domain** | History (humanities project competition) |
| **Years/sessions** | 1 (2020 contest rule book + 2024 evaluation forms for 5 categories) |
| **Questions** | — (rules & rubrics only; task instances generated from annual themes) |
| **Team size** | 2–5 students (Group entries) |
| **Time** | Year-long project |
| **Answer type** | One of 5 categories: paper / exhibit / documentary / performance / website |
| **Grading** | Weighted rubric: 80% historical quality (argument, sources, theme fit) + 20% presentation |
| **Source** | Unrestricted research |
| **Link** | [nhd.org contest rules](https://nhd.org/en/contest/contest-rules/) |
| **Data** | `nhd/` — `nhd-contest-rule-book-2020.pdf` + 5 category evaluation guides (6 files) |
| **Notes** | Annual themes are public, so task instances can be batch-generated. |

---

## WUDC / BP Debate — DebateBench · `debatebench`

| | |
|---|---|
| **Domain** | Debate (humanities, adversarial) |
| **Years/sessions** | 32 British Parliamentary debates |
| **Questions** | 256 full speech transcripts (8 speeches per debate) |
| **Team size** | 8 speakers per round (4 teams × 2) |
| **Time** | 15-minute prep after motion release; 7-minute speeches |
| **Answer type** | Structured speeches in fixed BP order |
| **Grading** | **Official judge speaker scores + team rankings included as ground truth** (`scores.xlsx`); Debatrix-style LLM-as-adjudicator reproducible |
| **Source** | Printed materials only during prep; no internet |
| **Link** | [DebateBench on HF](https://huggingface.co/datasets/utkarsh2105/DebateBench) · [arXiv:2502.06279](https://arxiv.org/abs/2502.06279) |
| **Data** | `debatebench/` — `cleaned_speeches/` (extracted, 43 files) + `scores.xlsx` |
| **Notes** | The only humanities adversarial dataset here with official judge scores as ground truth. ~32k tokens per match → long-context, multi-party adversarial evaluation. |

---

## Willem C. Vis Moot (International Commercial Arbitration) · `vis_moot`

| | |
|---|---|
| **Domain** | International commercial law (humanities) |
| **Years/sessions** | 7 Problems (26th edition, 2019 → 33rd edition, 2026) |
| **Questions** | 7 (one full arbitration case record per edition, 60–90 pages: contracts, correspondence, witness statements; incl. Procedural Order No. 2 clarifications) |
| **Team size** | 2–8 students |
| **Time** | Months of preparation; written memoranda + oral rounds |
| **Answer type** | Claimant & Respondent memoranda + oral pleading |
| **Grading** | Memorandum + oral advocacy rubrics; past winning memoranda available (Pace database) for comparison |
| **Source** | Unrestricted legal research |
| **Link** | [vismoot.org/previous-moots](https://www.vismoot.org/previous-moots/) |
| **Data** | `vis_moot/` — 7 Problems + 33rd-edition rules (8 PDFs) |
| **Notes** | Complete task chain: read case record → write both memoranda → oral rounds. Structurally identical to the Jessup competition already in the tracker — pipeline is reusable. |

---

## Collection backlog

| ID | Action |
|----|--------|
| `ethics_bowl_appe` | 2001–2021 Case Library on official Google Drive (28 topic categories, incl. Art and Cultural Heritage) |
| `ethics_bowl_nhseb` | 2012–2024 regional/national cases archived page-by-page at `https://nhseb.org/case-library/category/<year>+National+Case+Set` — write a scraper for batch collection |
| `gcch_harvard` | Open the 9 untitled winning decks (`gcch_*.pdf`) to confirm edition and rename |
| `case_world_cup` | Register by email to obtain the actual case prompt, or drop in favor of GCCH / CFA |
| `wharton_investment` | Past winning reports scattered on Issuu/SlideShare (not archived centrally by the organizer) |
| `igem` | Sample team wikis by year/medal from `20XX.igem.org/Team:XXX` static archive (thousands of teams — do not crawl exhaustively) |
| `vis_moot` | Earlier Problems (1994–2018) archived on per-edition pages at vismoot.org; winning memoranda from the Pace database |
