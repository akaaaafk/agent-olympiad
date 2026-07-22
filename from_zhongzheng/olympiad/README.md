# Data collected — `olympiad/`

Last updated: 2026-07-21

> **Data files are not in git.** The three original datasets (`OlympicArena`, `modeling_agent`, `MLAgentBench`) are mirrored on the private HF dataset [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) — run `python download_data.py` at the repo root. The newly added benchmarks below are pulled directly from their public HF / GitHub sources — see [Downloading](#downloading). Local copies live in the workspace-level [`benchmark/`](../../../benchmark/) folder.

**Current focus:** a curated benchmark suite for multi-agent team competitions across STEM, AI, engineering, security, medicine, finance, law, debate, linguistics, geography, earth science, philosophy, history, economics, astronomy, biology, collaborative writing, and puzzle solving — plus humanities/arts/business material in `art/`. Grading type is marked per row in the [Simulator Matrix](#simulator-matrix) (**RULE** = auto-graded closed-form / tests / flags; **RUBRIC** = open-ended deliverable scored by rubric or jury).

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published contest release, split, or benchmark edition (e.g. AIME 2024, OlympicArena `val`/`test`, one CTF challenge set).  
**Question** = one scored problem / task / conversation / paper leaf inside a year/session.

---

## Simulator Matrix

For each competition, the AI agent team must be given the same resources a human competitor (or human team) would have in the origin setting. Rules below are taken from the upstream benchmark papers / contest regulations and the source pages linked in **Sources**.

| ID | Full Name | Grading | Input Modality | Team Setup | Computers | Allowed Tools & Resources | Materials Provided | Final Deliverable | Sources |
|----|-----------|---------|----------------|------------|-----------|--------------------------|-------------------|-------------------|---------|
| `OlympicArena` | OlympicArena benchmark | RULE | Problem text + figures (EN/ZH; text-only & multimodal) | Individual in origin; adaptable to per-discipline specialist agents | None in origin olympiads | Closed-book · fine-grained answer types (single/multi-value, expression, code with test cases) enable auto-grading | Parquet splits per discipline; `val` includes answers, `test` withheld | Short answers / expressions / code, auto-judged | [HF](https://huggingface.co/datasets/GAIR/OlympicArena) · [GitHub](https://github.com/GAIR-NLP/OlympicArena) · [arXiv:2406.12753](https://arxiv.org/abs/2406.12753) |
| `OlympiadBench` | Olympiad math + physics | RULE | Problem text + figures (EN/ZH, multimodal) | Individual in origin; math vs physics specialists possible | None | Closed-book olympiad conditions · final numeric/expression answers | Dataset with gold final answers; upstream answer-checker | Final answer string / expression | [HF](https://huggingface.co/datasets/Hothan/OlympiadBench) · [arXiv:2402.14008](https://arxiv.org/abs/2402.14008) |
| `AIME` | American Invitational Mathematics Examination | RULE | Problem text | Individual; multi-solver + majority vote / verifier for team sim | None | Closed-book · no calculators · answers are integers 0–999 | AIME 2024 + 2025 problem sets with gold integers | Integer answer, exact match | [aime24](https://huggingface.co/datasets/math-ai/aime24) · [aime25](https://huggingface.co/datasets/math-ai/aime25) |
| `USACO` | USA Computing Olympiad | RULE | Problem statement + I/O spec | Individual; reader / coder / tester split for team sim | Required — write & run code | Open programming environment · submit against hidden cases · bronze→platinum tiers | Formatted problems + hidden test cases in parquet | Source code; score = fraction of cases passed | [HF](https://huggingface.co/datasets/codegenning/usacobench_formatted) |
| `SWE-bench_Verified` | SWE-bench Verified | RULE | GitHub issue text + repo checkout | Locator / patcher / reviewer on a shared checkout | Required — clone, edit, run tests in Docker | Full repo tools · apply patch · run `FAIL_TO_PASS` + `PASS_TO_PASS` | Issue metadata; per-repo Docker images at eval time | Git patch that turns failing tests green | [HF](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified) |
| `MLAgentBench` | MLAgentBench | RULE | Research goal + starter code workspace | Designed for one agent; engineer / researcher / reviewer natural split | Required — edit & run code on GPU/CPU | Open experimentation · install packages · Kaggle API for some tasks | Per-task `env/` (starter code) + hidden `scripts/` (`prepare.py`, `eval.py`) | Improved model / script + `submission.csv` | [GitHub](https://github.com/snap-stanford/MLAgentBench) · [arXiv:2310.03302](https://arxiv.org/abs/2310.03302) |
| `LiveCodeBench` | LiveCodeBench | RULE | Competitive programming problem text | Individual or small coding team | Required | Write code · graded on hidden tests · use post-cutoff release windows for contamination-free eval | Timestamped problems from LeetCode / AtCoder / Codeforces | Passing program | [HF](https://huggingface.co/datasets/livecodebench/code_generation_lite) · [arXiv:2403.07974](https://arxiv.org/abs/2403.07974) |
| `CodeContests` | CodeContests (AlphaCode) | RULE | Contest problem text | **ICPC analogue:** 3 agents, one shared submission queue, penalty per wrong submit | 1 shared machine | Languages as in ICPC-style contests · hidden test cases · penalty budget | Codeforces / ICPC-style problems with private tests | Code accepted by hidden judge | [HF](https://huggingface.co/datasets/deepmind/code_contests) |
| `NYU_CTF_Bench` | NYU CTF Bench (CSAW) | RULE | Challenge brief + dockerized service / files | CTF team split by category (web / pwn / crypto / rev / forensics / misc) | Required — Docker challenge envs | Full CTF tooling inside the challenge container · no external flag leaks | 200 CSAW challenges via `nyuctf` package | Exact flag string | [GitHub](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench) · [site](https://nyu-llm-ctf.github.io/) |
| `Cybench` | Cybench | RULE | Challenge brief + per-task Docker image | Same CTF category split; subtask decomposition available | Required — per-task Docker | Professional CTF tooling (HackTheBox / Sekai-style) | 40 tasks with subtask checks | Flag match + subtask progress | [GitHub](https://github.com/andyzorigin/cybench) |
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | RUBRIC | Open-ended problem statement (text + described images) | 3–4 students per team (COMAP rules) | Unrestricted | Multi-day open-book · full internet & software · judged on modeling quality | JSON with problem text, `requirements`, `eval_roles`, `decomposition` | Modeling paper (analysis + model + recommendations) | [COMAP](https://www.comap.com/contests) |
| `MLR-Bench` | MLR-Bench | RUBRIC | Research task prompt (idea → paper pipeline) | Ideator / proposer / experimenter / writer (+ verifier) | Required for experiment stages | Literature + code execution · stepwise or end-to-end | 201 ML research tasks across 9 topics | Idea / proposal / experiments / writeup | [HF](https://huggingface.co/datasets/chchenhui/mlrbench-tasks) · [arXiv:2505.19955](https://arxiv.org/abs/2505.19955) |
| `HealthBench` | HealthBench | RUBRIC | Multi-turn clinical conversation | Clinician / safety-reviewer / communicator | Unrestricted research tools (origin is chat) | Model must answer as a health assistant; `red_teaming` stresses refusal & safety | Conversations + physician-written weighted criteria | Free-form clinical response | [HF](https://huggingface.co/datasets/openai/healthbench) · [arXiv:2505.08775](https://arxiv.org/abs/2505.08775) |
| `PaperBench` | PaperBench | RUBRIC | ICML 2024 paper PDF | Read-paper / implement / run-experiments in a sandbox | Required — long-horizon code execution | Full research stack · rubric hidden from solver | 20 papers + hierarchical rubric trees (8,316 leaves) | Replication codebase scored by rubric | [GitHub](https://github.com/openai/preparedness/tree/main/project/paperbench) · [arXiv:2504.01848](https://arxiv.org/abs/2504.01848) |
| `cfa_research_challenge` | CFA Institute Research Challenge | RUBRIC | Assigned public company + filings | 3–5 agents | Unrestricted | Full public-market research · industry rubric | Subject company; 19 champion reports as gold | 10-page equity research report + oral defense | See [`art/README.md`](../art/README.md) |
| `gcch_harvard` | Global Case Competition at Harvard | RUBRIC | Case PDF | 2–5 agents | Unrestricted | Full internet & any software · winning decks as gold | Case PDF + 9 past winning decks | Slide deck + pitch | See [`art/README.md`](../art/README.md) |
| `wharton_investment` | Wharton Global HS Investment Competition | RULE + RUBRIC | Client case + trading simulator | 4–7 agents | Online simulator | 10-week portfolio management · full research | Client case with investment constraints | Portfolio track record + strategy report | See [`art/README.md`](../art/README.md) |
| `vis_moot` | Willem C. Vis Moot | RUBRIC | Problem PDF (60–90 pp. case record) | 2–8 agents | Unrestricted | Full legal research · months of prep · PO2 clarifications | Problem + PO2 + rules; Pace winning memos | Claimant & Respondent memoranda + oral pleading | See [`art/README.md`](../art/README.md) |
| `debatebench` | WUDC / BP Debate (DebateBench) | RUBRIC | Motion text (15 min prep) | 8 agents (4 teams × 2) | None during prep | Printed materials only during prep · no internet · 7-min speeches | Motion; 32 matches with official judge scores | Speeches ranked by judges | See [`art/README.md`](../art/README.md) |
| `ethics_bowl` | APPE + NHSEB Ethics Bowl | RUBRIC | Case set PDF (released in advance) | 3–7 agents (APPE: 5) | None during match | Cases studied in advance · oral discussion only at match · official scoring guides | Case sets + judging/scoring guides | Oral case presentation / dialogic discussion | See [`art/README.md`](../art/README.md) |
| `ioai` | International Olympiad in Artificial Intelligence | RULE + RUBRIC | Task notebooks + datasets (CV / NLP / ML); Team Challenge brief | Individual contestants + **national Team Challenge** (robotics / generative) | Required — code + GPU for Individual; Team uses contest platform / robots | Python · ML libraries · contest-provided data only for Individual · Team Challenge tools per year rules | Official task repos + HF datasets (statements, train/val/test, reference solutions) | Trained models / predictions (Individual) · Team Challenge deliverable (robotics / generative artifact) | [HF IOAI2025](https://huggingface.co/datasets/IOAI-official/IOAI2025) · [GitHub IOAI-official](https://github.com/IOAI-official) · [Education Hub](https://ioai-official.org/resources/) |
| `eoes` | European Olympiad of Experimental Science (EOES; formerly EUSO) | RUBRIC | Lab protocol PDFs + appendices + answer sheets | **3 agents** (integrated physics / chemistry / biology practical) | None during exam (lab benches provided) | Organizer lab equipment · calculators as permitted · no outside help | Experiment A/B packs + marking schemes | Completed answer sheets / lab report | [EUSO experiments](http://euso.eu/about/experiments/) · [EOES previous](https://www.eoes.science/Previous%20olympiads/previous.html) |
| `ichto` | International Chemistry Tournament | RUBRIC | Annual open-ended chemistry problem set (~10–15 problems) | Team with **Reporter / Opponent / Reviewer** roles (IYPT-style fights) | Laptops for prep; oral rounds on-site | Full literature during prep · fight protocol limits live aids | Official problem-set PDFs (2017–2026) | Oral report + opposition / review | [ichto.org/problems](http://ichto.org/en/problems/) · [Rules](http://ichto.org/en/rules/) |
| `pumac_power` | PUMaC Power Round | RUBRIC | Proof-based multi-part problem packet (PDF) | **8 agents** collaborating over ~1 week | Unrestricted during Power Round window | Collaboration within team · write proofs · no outside human help | Power Round problem + solution PDFs (2007–2025) | Written proof packet submitted as a team | [PUMaC Archives](https://jason-shi-f9dm.squarespace.com/archives) · [Power Round](https://jason-shi-f9dm.squarespace.com/power-round) |
| `mystery_hunt` | MIT Mystery Hunt | RULE | Web / PDF / multimedia puzzles + metas | **5–150 agents** with specialty squads | Shared workstations / Discord / spreadsheets | Full internet · arbitrary tooling · extreme division of labor | Official year archives + answer keys + puzzle index | Puzzle answers → meta answers → coin | [puzzles.mit.edu](https://puzzles.mit.edu/) · [Archive](https://puzzles.mit.edu/huntsbyyear.html) · [mh_answers](https://github.com/dgulotta/mh_answers) |
| `iol` | International Linguistics Olympiad | RULE | Problem PDFs (paradigms, glosses, scripts; some figures) | Individual main contest; **4-agent Team Contest** in origin | None | Paper & pencil · no electronic devices · free team collaboration on Team Contest | Official IOL problem + solution PDFs; HF structured extract | Written answers / rule inferences | [ioling.org](https://ioling.org/problems/by_year/) · [HF agurung/ioling](https://huggingface.co/datasets/agurung/ioling) · [IOLBENCH](https://arxiv.org/abs/2501.04249) |
| `igeo` | International Geography Olympiad (iGeo) | RULE + RUBRIC | Written Response Test booklets + fieldwork briefs | Individual WRT/MMT; fieldwork can be team-supported | Limited / organizer rules | Maps · resource booklets · field observation · no unrestricted internet in exam | Past WRT / FWE PDFs from document library | Written responses + fieldwork report | [iGeo document library](https://geoolympiad.org/document-library/) |
| `ieso` | International Earth Science Olympiad | RULE | Theory + practical papers (geology, meteorology, oceanography, astronomy, environment) | Individual; practicals may use shared lab roles in sim | Lab equipment for practicals | Organizer instruments · answer sheets · marking keys | Past IESO theory/practical PDFs + keys | MCQ / short answers / practical sheets | [IESO past questions](http://www.geosocindia.org/index.php/ieso/Questions_From_Past_IESOs) |
| `ipo` | International Philosophy Olympiad | RUBRIC | Essay topics (multi-language PDFs) | Individual essays; multi-agent critique / drafting teams for sim | None during exam | Closed-book essay · topics released at start · philosophy-olympiad rubrics | Official topic PDFs by year | Philosophical essay | [philosophy-olympiad.org](https://www.philosophy-olympiad.org/) |
| `history_olympiad` | International History Olympiad | RULE + RUBRIC | Bee/Bowl quizzes + written / historiography exams | Individual events + team Bowl formats | None for bees | Study guides · timed rounds · official answer keys + rubrics | Past exams, keys, rubrics by year | Short answers / essays ranked by rubric | [historyolympiad.com/resources](https://www.historyolympiad.com/resources/) |
| `ieo` | International Economics Olympiad | RULE + RUBRIC | Economics problem sets + business case PDFs | Individual economics; **3–5 agents** Business Case | Unrestricted for Business Case | Full research for case · slides + oral defense · economics open problems closed-book-ish | Official tasks under files.ieo-official.org | Numeric/short economics answers + case deck | [IEO prepare](https://ieo-official.org/prepare) · [Syllabus](https://files.ieo-official.org/IEO_Syllabus.pdf) |
| `ioaa` | Intl. Olympiad on Astronomy & Astrophysics | RULE | Theory + data analysis + observation; Group Competition packets | Individual rounds; **5-agent Group Competition** (cross-country) | Organizer calculator only | Constants sheets · star charts · data tables · no personal formula books | Past IOAA problem PDFs (theory / data / group) | Boxed numerical answers with units | [IOAA past problems](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | RUBRIC | 3–4 writing prompts revealed at event start | **3 agents** | None (devices banned) | Handwritten only · Stage 1 plan · Stage 2 individual write · Stage 3 peer edit | Prompts + blank paper | 3 handwritten essays (one per agent) | [WSC Events](https://scholarscup.org/events/) · [WSC Wiki](https://www.owiki.org/wiki/World_Scholar%27s_Cup) |
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

## OlympiadBench · `OlympiadBench/`

| | |
|---|---|
| **Domain** | Olympiad mathematics + physics (bilingual EN/ZH, text + multimodal) |
| **Years/sessions** | 1 (ACL 2024 release) |
| **Questions** | 8,476 |
| **Team size** | Individual in origin; adaptable to subject specialists (math vs physics) + verifier |
| **Time** | Origin: timed olympiad rounds |
| **Answer type** | Final numeric / expression answer |
| **Grading** | Final-answer extraction + match against gold; use the upstream answer-checker, not raw string equality |
| **Source** | Closed-book; multimodal problems need a vision-capable solver |
| **Link** | [HF: Hothan/OlympiadBench](https://huggingface.co/datasets/Hothan/OlympiadBench) · [arXiv:2402.14008](https://arxiv.org/abs/2402.14008) |
| **Data** | `OlympiadBench/` (~104 MB) |
| **Notes** | Complements OlympicArena with a denser math/physics focus and an official checker pipeline. |

---

## AIME · `AIME/`

| | |
|---|---|
| **Domain** | Competition mathematics |
| **Years/sessions** | 2 (AIME 2024, AIME 2025) |
| **Questions** | 60 (30 per year) |
| **Team size** | Individual in origin; multi-independent solvers + majority vote / verifier for team simulation |
| **Time** | Origin: 3-hour timed exam |
| **Answer type** | Integer 0–999; no partial credit |
| **Grading** | Deterministic integer match via `math-verify` |
| **Source** | Closed-book; no calculators |
| **Link** | [HF math-ai/aime24](https://huggingface.co/datasets/math-ai/aime24) · [aime25](https://huggingface.co/datasets/math-ai/aime25) |
| **Data** | `AIME/aime24/`, `AIME/aime25/` |
| **Notes** | Small, high-signal set for team-voting experiments at equal token budget. Prefer AIME 2025 for contamination-sensitive headline numbers. |

---

## USACO · `USACO/`

| | |
|---|---|
| **Domain** | Competitive programming — USA Computing Olympiad (bronze → platinum) |
| **Years/sessions** | Multi-year USACO archive (formatted benchmark release) |
| **Questions** | 307 |
| **Team size** | Individual in origin; reader / coder / tester split for team simulation |
| **Time** | Origin: timed programming contest windows |
| **Answer type** | Source program graded on hidden test cases |
| **Grading** | Run submission against hidden cases; score = fraction of cases passed per problem |
| **Source** | Open programming environment; submit to automated judge |
| **Link** | [HF: codegenning/usacobench_formatted](https://huggingface.co/datasets/codegenning/usacobench_formatted) |
| **Data** | `USACO/` — formatted parquet shards (~3.8 GB) |
| **Notes** | Tester agent writing local cases before submit is a natural team role. |

---

## SWE-bench Verified · `SWE-bench_Verified/`

| | |
|---|---|
| **Domain** | Software engineering — real GitHub issue resolution |
| **Years/sessions** | 1 (human-validated SWE-bench subset) |
| **Questions** | 500 |
| **Team size** | Origin: individual PR author; locator / patcher / reviewer roles for team sim |
| **Time** | Open-ended interactive editing episodes |
| **Answer type** | Git patch against a real repository |
| **Grading** | Apply patch → run `FAIL_TO_PASS` + `PASS_TO_PASS` test sets; pass only if all target tests go green |
| **Source** | Full repo tools inside per-repo Docker images |
| **Link** | [HF: princeton-nlp/SWE-bench_Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified) |
| **Data** | `SWE-bench_Verified/` (~2 MB metadata; repos cloned at eval time) |
| **Notes** | Needs per-repo Docker. Solo baseline at equal edit budget is the natural control. |

---

## MLAgentBench · `MLAgentBench/`

| | |
|---|---|
| **Domain** | ML experimentation / research engineering — agent must autonomously improve or build ML models given a dataset + goal |
| **Years/sessions** | 1 (single benchmark release; ICML 2024) |
| **Questions** | 15 tasks: 6 Kaggle challenges (`house-price`, `spaceship-titanic`, `amp-parkinsons-disease-progression-prediction`, `fathomnet`, `feedback`, `identify-contrails`) · 3 classic datasets (`cifar10`, `imdb`, `ogbn-arxiv`) · 2 recent-research tasks (`CLRS`, `babylm`) · 2 code-speedup tasks (`llama-inference`, `vectorization`) · 2 LLM-tool-building tasks (`bibtex-generation`, `literature-review-tool`) |
| **Team size** | Designed for a single agent; decomposes naturally into engineer / researcher / reviewer roles for team simulation |
| **Time** | Open-ended interactive episodes (typically capped at ~50 agent actions in the original harness) |
| **Answer type** | Working code + trained model; most tasks produce a `submission.csv` scored by a hidden `eval.py` |
| **Grading** | Automatic: task metric (accuracy / RMSE / MAP / speed) vs. baseline starter code; original paper counts >10% improvement over baseline as success |
| **Source** | Open-book: agent reads/edits/executes files, installs packages; heavy datasets pulled at prepare-time (Kaggle API / HF / TF datasets) |
| **Link** | [GitHub](https://github.com/snap-stanford/MLAgentBench) · [arXiv:2310.03302](https://arxiv.org/abs/2310.03302) |
| **Data** | `MLAgentBench/benchmarks/` — one folder per task: `env/` (starter code + data descriptions the agent sees) and `scripts/` (hidden `prepare.py` / `eval.py` / `research_problem.txt`); plus upstream `SOURCE_README.md` + MIT `LICENSE` (~0.5 MB task definitions; raw datasets are downloaded at prepare-time, not stored) |
| **Notes** | MIT license. Unlike Q&A olympiad items, tasks are **interactive environments** — the deliverable is a code artifact, so runs need a sandboxed executor (upstream Docker image `qhwang123/researchassistant`). Kaggle-derived tasks need Kaggle API credentials at prepare-time. Good complement to `modeling_agent`: same open-ended team workflow but with fully automatic grading. |

---

## LiveCodeBench · `LiveCodeBench/` (on demand)

| | |
|---|---|
| **Domain** | Competitive programming — LeetCode / AtCoder / Codeforces, contamination-free |
| **Years/sessions** | Continuously dated release windows |
| **Questions** | ~1,055 |
| **Team size** | Individual or small coding team (same roles as USACO) |
| **Time** | Origin: online judge contest timing; for agents, time-boxed "contest round" simulation |
| **Answer type** | Passing program against hidden tests |
| **Grading** | Hidden test cases; evaluate on the release window **after** each model's cutoff |
| **Source** | Standard coding tools; no looking up the specific problem solution |
| **Link** | [HF: livecodebench/code_generation_lite](https://huggingface.co/datasets/livecodebench/code_generation_lite) · [arXiv:2403.07974](https://arxiv.org/abs/2403.07974) |
| **Data** | ⏳ on demand (~4.4 GB) — see [Downloading](#downloading) |
| **Notes** | Primary contamination control for coding-track headline numbers. |

---

## CodeContests · `CodeContests/` (on demand)

| | |
|---|---|
| **Domain** | Competitive programming — Codeforces / ICPC-style (AlphaCode training data) |
| **Years/sessions** | Multi-year contest archive |
| **Questions** | ~13,600 |
| **Team size** | **Closest ICPC analogue:** 3 agents, one shared submission queue, penalty per wrong submission |
| **Time** | ICPC-style contest window with time penalty |
| **Answer type** | Source code accepted by hidden judge |
| **Grading** | Hidden test cases |
| **Source** | One shared machine; languages as in ICPC-style settings |
| **Link** | [HF: deepmind/code_contests](https://huggingface.co/datasets/deepmind/code_contests) |
| **Data** | ⏳ on demand (~7.6 GB) — see [Downloading](#downloading) |
| **Notes** | Best fit for simulating a real 3-person programming team under a shared penalty budget. |

---

## NYU CTF Bench · `NYU_CTF_Bench/` (on demand)

| | |
|---|---|
| **Domain** | Cybersecurity — CSAW capture-the-flag |
| **Years/sessions** | CSAW CTF challenge archive (NeurIPS 2024 benchmark) |
| **Questions** | 200 across 6 categories (web, pwn, forensics, rev, crypto, misc) |
| **Team size** | CTF team split by category specialist |
| **Time** | Open-ended within challenge Docker lifetime |
| **Answer type** | Exact flag string |
| **Grading** | Exact flag match inside the challenge's Docker environment; fully automatic |
| **Source** | Full CTF tooling inside the container; challenges cloned on first use |
| **Link** | [GitHub NYU-LLM-CTF/NYU_CTF_Bench](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench) · [site](https://nyu-llm-ctf.github.io/) |
| **Data** | ⏳ on demand — `pip install nyuctf`; challenges cloned on first `CTFDataset(split=...)` call |
| **Notes** | Log which specialist solved each flag for role-specialization metrics. |

---

## Cybench · `Cybench/` (on demand)

| | |
|---|---|
| **Domain** | Cybersecurity — professional CTF (HackTheBox / Sekai etc.) |
| **Years/sessions** | 1 (Cybench release) |
| **Questions** | 40 tasks with subtask decomposition |
| **Team size** | Same CTF category split as NYU CTF Bench |
| **Time** | Open-ended within per-task Docker |
| **Answer type** | Flag (+ intermediate subtask checkpoints) |
| **Grading** | Flag match + per-subtask checks in Docker |
| **Source** | Per-task Docker images with professional CTF tooling |
| **Link** | [GitHub andyzorigin/cybench](https://github.com/andyzorigin/cybench) |
| **Data** | ⏳ on demand (GitHub + per-task Docker images) |
| **Notes** | Harder / more professional tier than NYU CTF Bench; subtasks support partial-progress scoring. |

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

## MLR-Bench · `MLR-Bench/`

| | |
|---|---|
| **Domain** | AI/ML research — open-ended research tasks from NeurIPS/ICLR/ICML workshops |
| **Years/sessions** | 1 (MLR-Bench release) |
| **Questions** | 201 tasks across 9 ML topics |
| **Team size** | Ideator / proposer / experimenter / writer (+ verifier) |
| **Time** | Stepwise (idea → proposal → experiment → writeup) or end-to-end |
| **Answer type** | Research artifacts at each stage; final writeup |
| **Grading** | MLR-Judge rubric across up to 9 dimensions (consistency, novelty, clarity, feasibility, completeness, soundness, insightfulness, significance, overall), 1–10 per dim, dual-judge averaged |
| **Source** | Literature access + code execution for experiment stages |
| **Link** | [HF: chchenhui/mlrbench-tasks](https://huggingface.co/datasets/chchenhui/mlrbench-tasks) · [arXiv:2505.19955](https://arxiv.org/abs/2505.19955) |
| **Data** | `MLR-Bench/` (~0.6 MB) |
| **Notes** | Paper finds coding agents fabricate ~80% of results — add a verifier role. Judge panel must pass the calibration gate in `art/README.md`. |

---

## HealthBench · `HealthBench/`

| | |
|---|---|
| **Domain** | Medicine — realistic clinical conversations |
| **Years/sessions** | 1 (OpenAI HealthBench release) |
| **Questions** | 5,000 conversations (subsets: consensus 3,671 · hard 1,000; plus other splits) |
| **Team size** | Clinician / safety-reviewer / communicator roles |
| **Time** | Multi-turn chat; open-ended response length |
| **Answer type** | Free-form response to a health conversation |
| **Grading** | 48,562 physician-written weighted criteria; model-based grader checks each criterion met/unmet → weighted score |
| **Source** | Chat setting; safety/refusal behavior is part of the task on `red_teaming` |
| **Link** | [HF: openai/healthbench](https://huggingface.co/datasets/openai/healthbench) · [arXiv:2505.08775](https://arxiv.org/abs/2505.08775) |
| **Data** | `HealthBench/` — JSONL (`oss_eval`, `consensus`, `hard`) (~246 MB) |
| **Notes** | Each conversation carries its own criterion set — no single global rubric. |

---

## PaperBench · `PaperBench/` (on demand)

| | |
|---|---|
| **Domain** | AI/ML research — replicate ICML 2024 papers from scratch |
| **Years/sessions** | 1 (20 ICML 2024 papers) |
| **Questions** | 20 papers · 8,316 individually gradable leaf criteria |
| **Team size** | Read-paper / implement / run-experiments split sharing a workspace |
| **Time** | Long-horizon sandboxed execution (similar scale to MLAgentBench) |
| **Answer type** | Full replication codebase built from the paper |
| **Grading** | Hierarchical author-co-designed rubric tree (leaf = binary pass/fail, weighted up to a root Replication Score); rubric hidden from the solver; LLM judge co-validated against a separate judge benchmark |
| **Source** | Full research stack inside a sandbox |
| **Link** | [GitHub openai/preparedness (paperbench)](https://github.com/openai/preparedness/tree/main/project/paperbench) · [arXiv:2504.01848](https://arxiv.org/abs/2504.01848) |
| **Data** | ⏳ on demand (GitHub LFS) — see [Downloading](#downloading) |
| **Notes** | Needs sandboxed long-horizon execution. Judge calibration gate applies (see Evaluation design). |

---

## Newly collected olympiads

Real competitions added for multi-agent coverage. Local data under workspace [`benchmark/`](../../../benchmark/).

### Batch 2026-07-21a — team STEM / AI / puzzle

Five contests: `ioai`, `eoes`, `ichto`, `pumac_power`, `mystery_hunt` (cards below).

### Batch 2026-07-21b — diversity domains

Nine contests filling linguistics, geography, earth science, philosophy, history, economics, astronomy, and collaborative writing.

### IOAI · `IOAI/`

| | |
|---|---|
| **Domain** | Artificial intelligence olympiad — ML, CV, NLP + Team Challenge |
| **Years/sessions** | 2024 (Burgas), 2025 (Beijing), 2026 (Astana) |
| **Questions** | Individual: ~6 ML tasks in the 2025 HF release (train/val/test); Team Challenge: 1 robotics / generative brief per year × 2024–2026 |
| **Team size** | Individual contestants for Scientific / Individual round; **national Team Challenge** for the collaborative / robotics track |
| **Time** | At-home + on-site Individual windows; Team Challenge timed on-site |
| **Answer type** | Model predictions / code notebooks (Individual); Team Challenge artifact (robotics / generative) |
| **Grading** | Task metrics on hidden tests for Individual; rubric / jury for Team Challenge |
| **Source** | Contest-provided data only; Python + standard ML stack |
| **Link** | [HF: IOAI-official/IOAI2025](https://huggingface.co/datasets/IOAI-official/IOAI2025) · [GitHub 2024](https://github.com/IOAI-official/IOAI-2024) · [2025](https://github.com/IOAI-official/IOAI-2025) · [2026](https://github.com/IOAI-official/IOAI-2026) · [Resources](https://ioai-official.org/resources/) |
| **Data** | `benchmark/IOAI/` — `IOAI2025/` (HF, ~2.2 GB) + cloned `IOAI-2024/`, `IOAI-2025/`, `IOAI-2026/` task repos |
| **Notes** | Best new multi-agent AI olympiad with official datasets. Pair ML-specialist agents on Individual tasks; use a separate robotics / planning team for the Team Challenge. CC-BY-4.0. |

---

### EOES / EUSO · `EOES/`

| | |
|---|---|
| **Domain** | Interdisciplinary experimental science (physics + chemistry + biology practicals) |
| **Years/sessions** | EUSO 2003–2019; EOES 2021–2025 |
| **Questions** | 2 integrated experiments (A/B) per year; local mirror: EUSO archive PDFs + EOES 2021/2024 packs (~36 PDFs) |
| **Team size** | **3 agents** |
| **Time** | Multi-hour lab practicals during olympiad week |
| **Answer type** | Completed answer sheets / measurements / short lab writeups |
| **Grading** | Official marking schemes (partial credit); rubric-style for open responses |
| **Source** | Organizer-provided lab equipment; no outside help during exam |
| **Link** | [EUSO experiments](http://euso.eu/about/experiments/) · [EOES previous olympiads](https://www.eoes.science/Previous%20olympiads/previous.html) |
| **Data** | `benchmark/EOES/` — `euso/` experiment PDFs + `eoes/<year>/` packs + official syllabus/rules |
| **Notes** | Closest European counterpart to `ijso_practical`. Natural roles: experimentalist / data-analyst / report writer. |

---

### IChTo · `IChTo/`

| | |
|---|---|
| **Domain** | Chemistry research / open problems (IYPT-style tournament) |
| **Years/sessions** | 2017–2026 (9 published problem sets; 2020/2021 combined) |
| **Questions** | 9 published problem sets (2017–2026; ~10–15 open-ended chemistry problems per set) |
| **Team size** | Tournament team with **Reporter / Opponent / Reviewer** role rotation |
| **Time** | Months of prep; timed oral fights at the tournament |
| **Answer type** | Oral scientific report + opposition / review speeches |
| **Grading** | Jury rubric during Physics-Fight-style chemistry rounds |
| **Source** | Full literature during prep; fight-protocol limits on live aids |
| **Link** | [ichto.org/en/problems](http://ichto.org/en/problems/) · [Rules](http://ichto.org/en/rules/) |
| **Data** | `benchmark/IChTo/` — official problem-set PDFs (2017–2026) |
| **Notes** | Chemistry twin of `iypt`. Strong multi-agent fit: assign Reporter / Opponent / Reviewer agents and score with a calibrated LLM-judge panel. |

---

### PUMaC Power Round · `PUMaC_Power/`

| | |
|---|---|
| **Domain** | Proof-based team mathematics |
| **Years/sessions** | 2007–2025 Power Rounds (archive coverage) |
| **Questions** | ~19 Power packets locally (2007–2025; one multi-part proof packet per year) |
| **Team size** | **8 agents** |
| **Time** | ~1 week collaborative window before contest day |
| **Answer type** | Written proof packet submitted as a team |
| **Grading** | Proof rubric / official solutions for reference |
| **Source** | Team collaboration allowed; no outside human help |
| **Link** | [PUMaC Archives](https://jason-shi-f9dm.squarespace.com/archives) · [Power Round page](https://jason-shi-f9dm.squarespace.com/power-round) |
| **Data** | `benchmark/PUMaC_Power/` — Power Round problem (+ solution) PDFs |
| **Notes** | Longer collaboration window than ARML Power / HMMT Team. Good stress test for multi-session agent teams that must share lemmas and write a coherent proof document. |

---

### MIT Mystery Hunt · `MIT_Mystery_Hunt/`

| | |
|---|---|
| **Domain** | Large-scale collaborative puzzle hunt (not a classical STEM olympiad; included for extreme multi-agent structure) |
| **Years/sessions** | 1982 + 1994–2025 indexed; answer keys 1994–present |
| **Questions** | ~2,300 keyed answers in `answers.tsv`; ~4,000+ puzzles indexed across hunts; metas feed a final coin |
| **Team size** | **5–150 agents** with specialty squads (crossword, cipher, music, programming, …) |
| **Time** | ~48-hour hunt weekend (remote-capable in recent years) |
| **Answer type** | Short string answers → meta answers → coin location |
| **Grading** | Exact / normalized answer match (RULE); structure in `metapuzzles.yml` |
| **Source** | Full internet and arbitrary tooling; extreme division of labor |
| **Link** | [puzzles.mit.edu](https://puzzles.mit.edu/) · [Archive by year](https://puzzles.mit.edu/huntsbyyear.html) · [Puzzle Index](http://devjoe.appspot.com/huntindex/) · [mh_answers](https://github.com/dgulotta/mh_answers) |
| **Data** | `benchmark/MIT_Mystery_Hunt/` — `mh_answers/` (answer keys + metas), `answers.tsv`, hunt index pages, year landing pages |
| **Notes** | Strongest public multi-agent collaboration dataset. Start with answer-key grading on text-extractable puzzles; treat multimedia / on-campus physical puzzles as optional. Full puzzle media remain on year hunt sites — expand locally as needed. |

---

### IOL · `IOL/`

| | |
|---|---|
| **Domain** | Linguistics — morphology, phonology, syntax, semantics, writing systems |
| **Years/sessions** | Official IOL archive from 2003 onward; HF extract covers solution-backed problems |
| **Questions** | 130 solution-backed source problems · 555 HF records (478 text-strict); ~1,500 sub-instances in IOLBENCH-style splits |
| **Team size** | Individual main contest; **4 agents** on the IOL Team Contest |
| **Time** | Timed olympiad rounds |
| **Answer type** | Rule inference + short answers / paradigms |
| **Grading** | RULE — match against official solutions / structured answer units |
| **Source** | Closed-book; paper & pencil; no devices |
| **Link** | [ioling.org/problems](https://ioling.org/problems/by_year/) · [HF agurung/ioling](https://huggingface.co/datasets/agurung/ioling) · [IOLBENCH](https://arxiv.org/abs/2501.04249) |
| **Data** | `benchmark/IOL/` — HF `ioling_hf/` + official PDF mirrors where available |
| **Notes** | Strongest new humanities-STEM bridge. Prefer HF structured rows for auto-grading; keep PDFs for figures/scripts. |

---

### iGeo · `iGeo/`

| | |
|---|---|
| **Domain** | Geography — human, physical, environmental, fieldwork |
| **Years/sessions** | Multi-year Written Response Tests (+ fieldwork where published) |
| **Questions** | ~17 WRT editions with question booklets (1996–2025) + fieldwork packs · 151 PDFs locally |
| **Team size** | Individual in origin; fieldwork exercise supports cooperative roles in simulation |
| **Time** | Timed WRT; multi-hour fieldwork |
| **Answer type** | Short written responses, map interpretation, field report |
| **Grading** | RULE for keyed items; RUBRIC for open fieldwork writeups |
| **Source** | Resource booklets provided; exam-hall constraints |
| **Link** | [iGeo document library](https://geoolympiad.org/document-library/) |
| **Data** | `benchmark/iGeo/` — WRT PDF booklets |
| **Notes** | Adds spatial / environmental reasoning missing from pure STEM olympiad sets. |

---

### IESO · `IESO/`

| | |
|---|---|
| **Domain** | Earth science — geology, geophysics, meteorology, oceanography, astronomy, environment |
| **Years/sessions** | International finals from ~2007; national entrance archives also public |
| **Questions** | ~125 theory/practical PDFs (+ keys) in the local archive |
| **Team size** | Individual; practicals map to lab-role teams |
| **Time** | Timed theory + practical sessions |
| **Answer type** | MCQ / short answers / practical sheets |
| **Grading** | RULE via official keys |
| **Source** | Organizer lab equipment for practicals |
| **Link** | [Past IESO questions](http://www.geosocindia.org/index.php/ieso/Questions_From_Past_IESOs) |
| **Data** | `benchmark/IESO/` — theory/practical PDFs + keys |
| **Notes** | Complements `eoes` with earth-system focus rather than integrated school-lab science. |

---

### IPO · `IPO/`

| | |
|---|---|
| **Domain** | Philosophy — essay olympiad |
| **Years/sessions** | Annual topics archive (multi-language) |
| **Questions** | ~25 topic PDFs (several essay topics per year; multi-language archive) |
| **Team size** | Individual essays; multi-agent draft / critique / polish for simulation |
| **Time** | Timed on-site essay |
| **Answer type** | Philosophical essay |
| **Grading** | RUBRIC (IPO / national jury criteria) |
| **Source** | Closed-book; topics revealed at start |
| **Link** | [philosophy-olympiad.org](https://www.philosophy-olympiad.org/) |
| **Data** | `benchmark/IPO/` — topic PDFs + archive HTML |
| **Notes** | Pairs with `ethics_bowl`: essay vs dialogic oral ethics. |

---

### International History Olympiad · `History_Olympiad/`

| | |
|---|---|
| **Domain** | History — bees, bowls, written exams, historiography, art history |
| **Years/sessions** | Multi-year resource archive (exams + keys + rubrics) |
| **Questions** | ~90 exam/key/rubric PDFs across 6 editions (2014, 2018–2019, 2022–2024); multiple event types per edition |
| **Team size** | Individual bees + **team Bowl** formats |
| **Time** | Timed rounds per event |
| **Answer type** | Short answers / buzzes / essays |
| **Grading** | RULE for keyed bees; RUBRIC for historiography / written exams |
| **Source** | Study guides; no devices in bees |
| **Link** | [historyolympiad.com/resources](https://www.historyolympiad.com/resources/) |
| **Data** | `benchmark/History_Olympiad/` — year folders of exams/keys/rubrics |
| **Notes** | Best public history olympiad dump with mixed auto-gradable and rubric tracks. |

---

### IEO · `IEO/`

| | |
|---|---|
| **Domain** | Economics + business case |
| **Years/sessions** | Annual olympiad tasks (economics open + business case) |
| **Questions** | ~1 economics open set (2018) + ~10+ business-case / task PDFs locally; typically multi-problem economics + 1 team case per year |
| **Team size** | Individual economics; **3–5 agents** Business Case |
| **Time** | Timed economics; multi-hour case with slides |
| **Answer type** | Short/numeric economics answers; slide deck + pitch |
| **Grading** | RULE for economics keys; RUBRIC for case presentation |
| **Source** | Full research allowed on Business Case |
| **Link** | [ieo-official.org/prepare](https://ieo-official.org/prepare) · [Syllabus PDF](https://files.ieo-official.org/IEO_Syllabus.pdf) |
| **Data** | `benchmark/IEO/` — syllabus/regulations + task PDFs |
| **Notes** | Complements `gcch_harvard` / `cfa` with an official international olympiad brand. |

---

### IOAA · `IOAA/`

| | |
|---|---|
| **Domain** | Astronomy & astrophysics |
| **Years/sessions** | Annual IOAA theory / data / observation / group packets |
| **Questions** | ~20 years of multi-paper sets (174 PDFs, 2007–2025); 16 Group/Team Competition packets for multi-agent runs |
| **Team size** | Individual rounds; **5 agents** Group Competition |
| **Time** | Timed papers; group session |
| **Answer type** | Numerical answers with units; data-analysis writeups |
| **Grading** | RULE (official marking) |
| **Source** | Organizer calculator + constants / charts; no personal formula books |
| **Link** | [IOAA past problems](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |
| **Data** | `benchmark/IOAA/` — ~176 PDFs (~209 MB), years 2007–2025 (theory / data / observation / group) |
| **Notes** | Prefer Group Competition / Team Competition packets for multi-agent simulation. |

---

### WSC Collaborative Writing · `WSC_Writing/`

| | |
|---|---|
| **Domain** | Collaborative creative / analytical writing |
| **Years/sessions** | Seasonal WSC events (prompts vary) |
| **Questions** | 3–4 prompts per session; local mirror also has ~42 guiding questions + discussion prompts |
| **Team size** | **3 agents** |
| **Time** | Staged: plan → individual write → peer edit |
| **Answer type** | Three handwritten essays |
| **Grading** | RUBRIC (WSC judging criteria) |
| **Source** | No electronic devices; handwritten only |
| **Link** | [WSC Events](https://scholarscup.org/events/) · [WSC Wiki](https://www.owiki.org/wiki/World_Scholar%27s_Cup) |
| **Data** | `benchmark/WSC_Writing/` — prompts / guides when published; may include copies from repo `data/raw/wsc_writing` |
| **Notes** | Extreme constraint on tools (no devices) makes it a clean test of pure collaboration protocols. |

---

## Entries living under `art/`

These six open-ended competitions are part of this olympiad catalog but their files and full deep-dive tables live in [`art/README.md`](../art/README.md):

| ID | Where documented |
|----|------------------|
| `cfa_research_challenge` | [`art/README.md`](../art/README.md) → CFA Institute Research Challenge |
| `gcch_harvard` | [`art/README.md`](../art/README.md) → Global Case Competition at Harvard |
| `wharton_investment` | [`art/README.md`](../art/README.md) → Wharton Global HS Investment Competition |
| `vis_moot` | [`art/README.md`](../art/README.md) → Willem C. Vis Moot |
| `debatebench` | [`art/README.md`](../art/README.md) → WUDC / BP Debate |
| `ethics_bowl` (`ethics_bowl_appe` + `ethics_bowl_nhseb`) | [`art/README.md`](../art/README.md) → APPE / NHSEB Ethics Bowl |

---

## Downloading

The five compact/medium additions are already fetched into `olympiad/`. To (re)download any dataset:

```bash
# Rule-based (HF datasets)
hf download Hothan/OlympiadBench            --repo-type dataset --local-dir olympiad/OlympiadBench
hf download math-ai/aime24                  --repo-type dataset --local-dir olympiad/AIME/aime24
hf download math-ai/aime25                  --repo-type dataset --local-dir olympiad/AIME/aime25
hf download princeton-nlp/SWE-bench_Verified --repo-type dataset --local-dir olympiad/SWE-bench_Verified
hf download codegenning/usacobench_formatted --repo-type dataset --local-dir olympiad/USACO   # 3.8 GB

# Large rule-based — pull only when needed
hf download livecodebench/code_generation_lite --repo-type dataset --local-dir olympiad/LiveCodeBench  # 4.4 GB
hf download deepmind/code_contests             --repo-type dataset --local-dir olympiad/CodeContests    # 7.6 GB

# Open-ended (HF datasets)
hf download chchenhui/mlrbench-tasks --repo-type dataset --local-dir olympiad/MLR-Bench
hf download openai/healthbench       --repo-type dataset --local-dir olympiad/HealthBench

# Docker / GitHub-based (not plain HF pulls)
#   NYU CTF Bench : pip install nyuctf ; challenges cloned on first CTFDataset(split=...) call
#   Cybench       : git clone https://github.com/andyzorigin/cybench (per-task Docker images)
#   PaperBench    : git clone https://github.com/openai/preparedness --filter=blob:none ; git lfs fetch --include "project/paperbench/data/**"

# Newly collected team olympiads → workspace benchmark/
hf download IOAI-official/IOAI2025 --repo-type dataset --local-dir benchmark/IOAI/IOAI2025   # ~2.2 GB
git clone --depth 1 https://github.com/IOAI-official/IOAI-2024.git benchmark/IOAI/IOAI-2024
git clone --depth 1 https://github.com/IOAI-official/IOAI-2025.git benchmark/IOAI/IOAI-2025
git clone --depth 1 https://github.com/IOAI-official/IOAI-2026.git benchmark/IOAI/IOAI-2026
# IChTo / PUMaC Power / EOES: official PDF archives (see collector script or links in deep-dive cards)
# Mystery Hunt answers:
git clone --depth 1 https://github.com/dgulotta/mh_answers.git benchmark/MIT_Mystery_Hunt/mh_answers

# Diversity domains → workspace benchmark/
hf download agurung/ioling --repo-type dataset --local-dir benchmark/IOL/ioling_hf
# iGeo / IESO / IPO / History / IEO / IOAA / WSC: official PDF / HTML archives
#   (see deep-dive cards; collector: workspace `_download_diverse.py` when present)
```

---

## Collection backlog

| ID | Action |
|----|--------|
| `OlympicArena` | Fetch figure images referenced by `figure_urls` for offline multimodal runs; register on the official platform to score `test`-split submissions |
| `modeling_agent` | Collect Outstanding-winner papers (COMAP publishes abstracts; full papers via UMAP Journal) as gold-standard references |
| `MLAgentBench` | Set up Kaggle API credentials + run `prepare.py` per task to cache raw datasets; pin the upstream Docker image for sandboxed execution |
| `LiveCodeBench` / `CodeContests` | Pull locally when coding-track evals start (4.4 GB / 7.6 GB) |
| `NYU_CTF_Bench` / `Cybench` | Install Docker tooling and smoke-test one challenge per category |
| `PaperBench` | Clone preparedness repo with LFS for the 20-paper rubric trees |
| `ioai` | Expand Team Challenge simulation assets (robotics env / generative briefs beyond statements) |
| `eoes` | Fill gaps for years where host sites only publish partial packs; pair with marking schemes |
| `ichto` | Optional: collect winning fight recordings / written solutions if published |
| `pumac_power` | Rename PDFs to `YYYY_problems.pdf` / `YYYY_solutions.pdf` for uniform loading |
| `mystery_hunt` | Optionally mirror full puzzle media for selected years (2020–2025) from year hunt sites |
| `iol` | Prefer HF structured answers; backfill figure/script PDFs for multimodal rows |
| `igeo` | Pull remaining years from iGeo document library (MMT temporarily offline upstream) |
| `ieso` | Normalize year folders; ensure practical keys sit beside theory PDFs |
| `ipo` | Collect national marking criteria PDFs where published |
| `history_olympiad` | Flatten year event names; separate RULE bees from RUBRIC written exams |
| `ieo` | Fill missing year business-case PDFs from ieo-official.org/prepare |
| `ioaa` | Prioritize Group Competition packets for multi-agent runs |
| `wsc_writing` | Archive seasonal prompts + rubrics from scholarscup.org each season |

---

## Evaluation design

**RULE** contests are fully auto-gradable (harness / executor). **RUBRIC** contests use judges that must pass the **calibration gate** in `art/README.md` (Evaluation design → Judge validation) — `debatebench` human scores are the anchor.

### RULE

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `OlympicArena` | Answer-type-aware rule matching on the `val` split (638 questions, fully local); `test` split via the official platform. Use the upstream grader — answer types include expressions, intervals, and code with test cases. | Per-discipline specialist agents + aggregator; compare against a single generalist at equal token budget. |
| `OlympiadBench` | Final-answer extraction + match against gold (numeric / expression); use the upstream answer-checker. Multimodal problems need a vision-capable solver. | Per-subject specialists (math vs physics) + verifier that re-derives before submitting. |
| `AIME` | Deterministic integer match via `math-verify` (answers 0–999, no partial credit). | Multiple independent solvers + majority vote / verifier; measure whether team voting beats a single solver at equal budget. |
| `USACO` | Run submitted code against hidden test cases; score = fraction of cases passed (bronze→platinum tiers). | Reader / coder / tester split; tester writes local cases before submitting. |
| `SWE-bench_Verified` | Apply the generated patch, run `FAIL_TO_PASS` + `PASS_TO_PASS`; pass only if all target tests go green. Needs per-repo Docker. | Locator / patcher / reviewer on a shared checkout; solo baseline at equal edit budget. |
| `MLAgentBench` | Run each task's hidden `eval.py`; success = >10% improvement over baseline starter code. Needs sandboxed Docker executor. | Engineer / researcher / reviewer sharing one workspace; solo-agent baseline at the same action budget. |
| `LiveCodeBench` | Hidden test cases; use the release window **after** each model's cutoff. | Same as USACO; good for time-boxed "contest round" simulation. |
| `CodeContests` | Hidden test cases; ICPC-style (one shared machine, penalty per wrong submission). | 3 agents sharing one submission queue under a penalty budget — direct ICPC analogue. |
| `NYU_CTF_Bench` / `Cybench` | Exact flag match (and per-subtask checks for Cybench) inside Docker; fully automatic. | CTF teams split by category (pwn / crypto / web / rev); log which specialist solved each flag. |
| `mystery_hunt` | Exact / normalized answer match; meta structure from `metapuzzles.yml`. | Specialty squads + meta lead; log unlock graph, idle time, and cross-squad handoffs. |
| `ioai` (Individual) | Task metrics on hidden tests. | ML specialists per modality (CV / NLP / tabular) + aggregator. |
| `iol` | Match against official / HF answer units; keep figure-dependent items for vision solvers. | 4-agent Team Contest simulation; compare vs solo on the same problems. |
| `ieso` / `ioaa` (individual papers) | Official keys / numeric tolerances. | Optional lab-role split on practicals; Group Competition for IOAA. |
| `igeo` (keyed WRT items) | Marking scheme match on short answers. | Map-reader / data-analyst / writer roles on resource booklets. |
| `history_olympiad` (bees / bowls) | Exact / normalized answer match. | Team Bowl conferring vs individual Bee. |
| `ieo` (economics) | Official numeric / short-answer keys. | Solo economics baseline before team case. |

### RUBRIC

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `modeling_agent` | LLM-judge panel walking per-problem `requirements` with `eval_roles` as judge personas. | 3–4 agents per COMAP rules (modeler / coder / writer); `decomposition` field seeds the role split. |
| `MLR-Bench` | MLR-Judge across up to 9 dims, dual-judge averaged; stepwise or end-to-end. | Ideator / proposer / experimenter / writer; add a verifier (fabrication risk). |
| `HealthBench` | Per-conversation physician-written weighted criteria; model grader → weighted score. | Clinician / safety-reviewer / communicator; `red_teaming` stresses refusal & safety coordination. |
| `PaperBench` | Hierarchical rubric tree (leaf = binary, weighted to Replication Score); rubric hidden from solver. | Read-paper / implement / run-experiments; sandboxed long-horizon like MLAgentBench. |
| `cfa` / `gcch` / `wharton` / `vis_moot` / `debatebench` / `ethics_bowl` | See Evaluation design in [`art/README.md`](../art/README.md). | Same as `art/` — those contests define the humanities/business/law team protocols. |
| `eoes` | Official marking schemes on answer sheets; partial credit as published. | 3 agents as experimentalist / analyst / scribe; compare against solo agent at equal lab steps. |
| `ichto` | Tournament jury rubric (Reporter / Opponent / Reviewer). Calibrate LLM judges like `iypt`. | Role-rotating agents; score both content quality and opposition/review usefulness. |
| `pumac_power` | Proof rubric against official solutions; stepwise credit on subparts. | 8 agents sharing lemmas over a multi-day window; measure document coherence + coverage. |
| `ioai` (Team Challenge) | Jury / rubric for robotics or generative deliverable. | Separate planning / control / perception team. |
| `ipo` | IPO essay rubrics (argument, clarity, originality). | Drafter / critic / editor agents under a shared time budget. |
| `igeo` (fieldwork) / `history_olympiad` (historiography) | Official fieldwork / written-exam rubrics. | Observer / analyst / writer split. |
| `ieo` (Business Case) | Case deck + oral presentation rubric. | 3–5 agents (research / model / slides / pitch). |
| `wsc_writing` | WSC collaborative-writing criteria; score plan / draft / peer-edit stages. | Strict 3-agent staged protocol with no tools. |

All RUBRIC judges must report inter-judge agreement and run pairwise comparisons position-swapped. Cross-cutting: log the same team-level metrics as `art/` (budget consumed, inter-agent messages, role-specialization entropy, team-vs-solo delta). For contamination, prefer withheld/newest splits — OlympicArena `test`, AIME 2025, LiveCodeBench post-cutoff windows, post-2023 modeling problems, and IOAI 2025/2026 tasks — for headline numbers.
