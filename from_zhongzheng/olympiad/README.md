# Data collected — `olympiad/`

Last updated: 2026-07-22

> **Data files are not in git.** The three original datasets (`OlympicArena`, `modeling_agent`, `MLAgentBench`) are mirrored on the private HF dataset [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) — run `python download_data.py` at the repo root. The newly added benchmarks below are pulled directly from their public HF / GitHub sources — see [Downloading](#downloading). Local copies live in the workspace-level [`benchmark/`](../../../benchmark/) folder.

**Current focus:** a curated benchmark suite for multi-agent team competitions across STEM, AI, engineering, security, medicine, finance, law, debate, linguistics, geography, earth science, philosophy, history, economics, astronomy, biology, collaborative writing, and puzzle solving — plus humanities/arts/business material in `art/`. Grading type is marked per row in the [Simulator Matrix](#simulator-matrix) (**RULE** = auto-graded closed-form / tests / flags; **RUBRIC** = open-ended deliverable scored by rubric or jury).

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published contest release, split, or benchmark edition (e.g. AIME 2024, OlympicArena `val`/`test`, one CTF challenge set).  
**Question** = one scored problem / task / conversation / paper leaf inside a year/session.

**Team size notation** (matrix + deep-dive cards):
- **Origin** — how many humans the real contest uses (official rules).
- **Rec** — recommended agent count for multi-agent simulation. Always shown for **solo (Origin: 1)** tasks; for native team contests, Rec usually matches Origin.

---

## Simulator Matrix

For each competition, the AI agent team must be given the same resources a human competitor (or human team) would have in the origin setting. Rules below are taken from the upstream benchmark papers / contest regulations and the source pages linked in **Sources**.

| ID | Full Name | Grading | Origin | Rec (sim) | Input Modality | Computers | Allowed Tools & Resources | Final Deliverable | Sources |
|----|-----------|---------|--------|-----------|----------------|-----------|--------------------------|-------------------|---------|
| `OlympicArena` | OlympicArena benchmark | RULE | 1 | 3–7 (per-discipline + aggregator) | Problem text + figures (EN/ZH) | None in origin | Closed-book · typed answers / code | Short answers / expressions / code | [HF](https://huggingface.co/datasets/GAIR/OlympicArena) · [arXiv:2406.12753](https://arxiv.org/abs/2406.12753) |
| `OlympiadBench` | Olympiad math + physics | RULE | 1 | 2–3 (subject specialist + verifier) | Problem text + figures (EN/ZH) | None | Closed-book | Final answer string / expression | [HF](https://huggingface.co/datasets/Hothan/OlympiadBench) · [arXiv:2402.14008](https://arxiv.org/abs/2402.14008) |
| `AIME` | American Invitational Mathematics Examination | RULE | 1 | 3 (solvers + majority / verifier) | Problem text | None | Closed-book · no calculators · answers 0–999 | Integer answer | [aime24](https://huggingface.co/datasets/math-ai/aime24) · [aime25](https://huggingface.co/datasets/math-ai/aime25) · [aime26](https://huggingface.co/datasets/math-ai/aime26) |
| `USACO` | USA Computing Olympiad | RULE | 1 | 3 (reader / coder / tester) | Problem + I/O spec | Required | Submit vs hidden cases | Source code | [HF](https://huggingface.co/datasets/codegenning/usacobench_formatted) |
| `SWE-bench_Verified` | SWE-bench Verified | RULE | 1 | 3 (locator / patcher / reviewer) | GitHub issue + repo | Required (Docker) | Full repo tools · run tests | Git patch | [HF](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified) |
| `MLAgentBench` | MLAgentBench | RULE | 1 | 3 (engineer / researcher / reviewer) | Research goal + starter code | Required (GPU/CPU) | Open experimentation · Kaggle API on some tasks | Improved model / `submission.csv` | [GitHub](https://github.com/snap-stanford/MLAgentBench) · [arXiv:2310.03302](https://arxiv.org/abs/2310.03302) |
| `LiveCodeBench` | LiveCodeBench | RULE | 1 | 2–3 (coder + tester) | Contest problem text | Required | Hidden tests · post-cutoff windows | Passing program | [HF](https://huggingface.co/datasets/livecodebench/code_generation_lite) · [arXiv:2403.07974](https://arxiv.org/abs/2403.07974) |
| `CodeContests` | CodeContests (AlphaCode) | RULE | 3 (ICPC-style) | 3 (shared machine + penalty queue) | Contest problem text | 1 shared machine | Hidden tests · wrong-submit penalty | Accepted code | [HF](https://huggingface.co/datasets/deepmind/code_contests) |
| `NYU_CTF_Bench` | NYU CTF Bench (CSAW) | RULE | 4–6 (typical CTF team) | 4–6 (by category) | Challenge brief + Docker | Required | CTF tooling in container | Flag string | [GitHub](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench) |
| `Cybench` | Cybench | RULE | 4–6 (typical CTF team) | 4–6 (by category / subtask) | Challenge brief + Docker | Required | Professional CTF tooling | Flag + subtask progress | [GitHub](https://github.com/andyzorigin/cybench) |
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | RUBRIC | 3–4 (COMAP) | 3–4 | Open-ended modeling statement | Unrestricted | Multi-day open-book | Modeling paper | [COMAP](https://www.comap.com/contests) |
| `MLR-Bench` | MLR-Bench | RUBRIC | 1 (task assignee) | 4–5 (ideator / proposer / experimenter / writer ± verifier) | Research task prompt | Required for experiments | Literature + code | Idea → experiments → writeup | [HF](https://huggingface.co/datasets/chchenhui/mlrbench-tasks) · [arXiv:2505.19955](https://arxiv.org/abs/2505.19955) |
| `HealthBench` | HealthBench | RUBRIC | 1 (assistant) | 3 (clinician / safety / communicator) | Multi-turn clinical chat | Unrestricted | Health-assistant constraints | Free-form clinical response | [HF](https://huggingface.co/datasets/openai/healthbench) · [arXiv:2505.08775](https://arxiv.org/abs/2505.08775) |
| `HealthBench-Professional` | HealthBench Professional | RUBRIC | 1 (assistant) | 3 (specialist / safety / medical-writer) | Physician workflow chat | Unrestricted | Clinical consult / writing / research | Free-form + physician reference | [HF](https://huggingface.co/datasets/openai/healthbench-professional) |
| `PaperBench` | PaperBench | RUBRIC | 1–3 (researchers) | 3 (read / implement / run) | ICML 2024 paper PDF | Required | Full research stack | Replication codebase | [GitHub](https://github.com/openai/preparedness/tree/main/project/paperbench) · [arXiv:2504.01848](https://arxiv.org/abs/2504.01848) |
| `cfa_research_challenge` | CFA Institute Research Challenge | RUBRIC | 3–5 | 3–5 | Public company + filings | Unrestricted | Full market research | Equity report + defense | See [`art/README.md`](../art/README.md) |
| `gcch_harvard` | Global Case Competition at Harvard | RUBRIC | 2–5 | 2–5 | Case PDF | Unrestricted | Full internet | Deck + pitch | See [`art/README.md`](../art/README.md) |
| `wharton_investment` | Wharton Global HS Investment Competition | RULE + RUBRIC | 4–7 | 4–7 | Client case + simulator | Online simulator | 10-week portfolio | Track record + strategy report | See [`art/README.md`](../art/README.md) |
| `vis_moot` | Willem C. Vis Moot | RUBRIC | 2–8 | 2–8 | 60–90 pp. case record | Unrestricted | Full legal research | Memos + oral pleading | See [`art/README.md`](../art/README.md) |
| `debatebench` | WUDC / BP Debate (DebateBench) | RUBRIC | 8 (4×2) | 8 | Motion (15 min prep) | None during prep | Printed materials only in prep | Speeches ranked by judges | See [`art/README.md`](../art/README.md) |
| `ethics_bowl` | APPE + NHSEB Ethics Bowl | RUBRIC | APPE 5 · NHSEB 3–7 | 5 (APPE) / 3–7 (NHSEB) | Case set PDF | None during match | Oral discussion only at match | Oral case presentation | See [`art/README.md`](../art/README.md) |
| `ioai` | Intl. Olympiad in AI | RULE + RUBRIC | Indiv. 1 · Team Challenge national team | Indiv. Rec 3 · Team Rec 3–5 | Notebooks + datasets / Team brief | Required (GPU) for Individual | Contest data + ML stack | Predictions / Team artifact | [HF IOAI2025](https://huggingface.co/datasets/IOAI-official/IOAI2025) · [GitHub](https://github.com/IOAI-official) |
| `eoes` | EOES / EUSO | RUBRIC | 3 | 3 | Lab protocols + answer sheets | Lab benches (no personal computers) | Organizer equipment | Answer sheets / lab report | [EUSO](http://euso.eu/about/experiments/) · [EOES](https://www.eoes.science/Previous%20olympiads/previous.html) |
| `ichto` | International Chemistry Tournament | RUBRIC | 3+ (Reporter / Opponent / Reviewer) | 3+ (role rotation) | Open chemistry problem set | Prep: laptops; fights: on-site | Literature in prep | Oral report + opposition / review | [ichto.org](http://ichto.org/en/problems/) |
| `pumac_power` | PUMaC Power Round | RUBRIC | 8 | 8 | Multi-part proof packet | Unrestricted in window | Team collaboration · no outside humans | Written proof packet | [PUMaC Archives](https://jason-shi-f9dm.squarespace.com/archives) |
| `mystery_hunt` | MIT Mystery Hunt | RULE | 5–150 (specialty squads) | 8–20 for lab sims (scale as needed) | Web / PDF / multimedia puzzles | Shared workstations | Full internet · arbitrary tooling | Puzzle → meta → coin | [puzzles.mit.edu](https://puzzles.mit.edu/) · [mh_answers](https://github.com/dgulotta/mh_answers) |
| `iol` | International Linguistics Olympiad | RULE | Indiv. 1 · Team Contest 4 | Indiv. Rec 2–3 · Team Rec 4 | Problem PDFs | None | Paper & pencil · no devices | Written answers / rule inferences | [ioling.org](https://ioling.org/problems/by_year/) · [HF](https://huggingface.co/datasets/agurung/ioling) |
| `igeo` | International Geography Olympiad (iGeo) | RULE + RUBRIC | 1 (WRT/MMT) | 3 (map / data / writer) for fieldwork-style sim | 600 items (WRT 505 · FWE 55 · MMT 40) | Limited | Maps · resource booklets | Written responses + field report | [iGeo library](https://geoolympiad.org/document-library/) |
| `ieso` | International Earth Science Olympiad | RULE | 1 | 2–3 (lab-role split on practicals) | Theory + practical papers | Lab equipment | Organizer instruments | MCQ / short / practical sheets | [IESO past](http://www.geosocindia.org/index.php/ieso/Questions_From_Past_IESOs) |
| `ipo` | International Philosophy Olympiad | RUBRIC | 1 (essay; ≤2 per country) | 3 (drafter / critic / editor) | 4 quotation-topics (pick 1) | None | Closed-book timed essay | Philosophical essay | [philosophy-olympiad.org](https://www.philosophy-olympiad.org/) |
| `history_olympiad` | International History Olympiad | RULE + RUBRIC | Bee 1 · Bowl team | Bee Rec 2–3 · Bowl Rec 4 | Bee/Bowl + written exams | None for bees | Study guides · timed rounds | Short answers / essays | [historyolympiad.com](https://www.historyolympiad.com/resources/) |
| `ieo` | International Economics Olympiad | RULE + RUBRIC | Econ 1 · Business Case 3–5 | Econ Rec 2–3 · Case Rec 3–5 | Problem sets + case PDFs | Unrestricted for case | Research on Business Case | Numeric answers + case deck | [IEO prepare](https://ieo-official.org/prepare) |
| `ioaa` | Intl. Olympiad on Astronomy & Astrophysics | RULE | Indiv. 1 · Group 5 | Indiv. Rec 2–3 · Group Rec 5 | Theory / data / observation / group | Organizer calculator only | Constants · charts · data tables | Boxed numerical answers | [IOAA past](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | RUBRIC | 3 | 3 | 3–4 prompts | None (devices banned) | Handwritten staged collab | 3 essays (one per writer) | [WSC Events](https://scholarscup.org/events/) |
---

## OlympicArena · `OlympicArena/`

| | |
|---|---|
| **Domain** | STEM olympiads — Math, Physics, Chemistry, Biology, Geography, Astronomy, CS |
| **Years/sessions** | 14 (7 disciplines × val/test splits) |
| **Questions** | 10,615 (test 9,977 with withheld answers · val 638 with public answers) |
| **Team size** | **Origin: 1** · **Rec: 3–7** (per-discipline specialists + aggregator) |
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
| **Team size** | **Origin: 1** · **Rec: 2–3** (subject specialist + verifier) |
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
| **Years/sessions** | 3 (AIME 2024, 2025, 2026) |
| **Questions** | 90 (30 per year) |
| **Team size** | **Origin: 1** · **Rec: 3** (independent solvers + majority / verifier) |
| **Time** | Origin: 3-hour timed exam |
| **Answer type** | Integer 0–999; no partial credit |
| **Grading** | Deterministic integer match via `math-verify` |
| **Source** | Closed-book; no calculators |
| **Link** | [HF math-ai/aime24](https://huggingface.co/datasets/math-ai/aime24) · [aime25](https://huggingface.co/datasets/math-ai/aime25) · [aime26](https://huggingface.co/datasets/math-ai/aime26) |
| **Data** | `benchmark/AIME/aime24|25|26/` — `test.jsonl` + `test.json` (JSON; aime24 converted from upstream parquet) |
| **Notes** | Small, high-signal set for team-voting experiments. Prefer newest year for contamination-sensitive headline numbers. Upstream `aime24` ships parquet only; local copy is JSON. |

---

## USACO · `USACO/`

| | |
|---|---|
| **Domain** | Competitive programming — USA Computing Olympiad (bronze → platinum) |
| **Years/sessions** | Multi-year USACO archive (formatted benchmark release) |
| **Questions** | 520 (bronze 148 · silver 144 · gold 142 · platinum 86) |
| **Team size** | **Origin: 1** · **Rec: 3** (reader / coder / tester) |
| **Time** | Origin: timed programming contest windows |
| **Answer type** | Source program graded on hidden test cases |
| **Grading** | Run submission against hidden cases; score = fraction of cases passed per problem |
| **Source** | Open programming environment; submit to automated judge |
| **Link** | [HF: codegenning/usacobench_formatted](https://huggingface.co/datasets/codegenning/usacobench_formatted) |
| **Data** | `benchmark/USACO/` — 12 parquet shards under `data/` (~3.8 GB download) |
| **Notes** | Upstream card lists `num_examples: 520`; local unique ids match. Tester agent writing local cases before submit is a natural team role. |

---

## SWE-bench Verified · `SWE-bench_Verified/`

| | |
|---|---|
| **Domain** | Software engineering — real GitHub issue resolution |
| **Years/sessions** | 1 (human-validated SWE-bench subset) |
| **Questions** | 500 |
| **Team size** | **Origin: 1** · **Rec: 3** (locator / patcher / reviewer) |
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
| **Questions** | **15 problems total** (= 15 tasks, one research goal each): 6 Kaggle (`house-price`, `spaceship-titanic`, `amp-parkinsons-disease-progression-prediction`, `fathomnet`, `feedback`, `identify-contrails`) · 3 classic (`cifar10`, `imdb`, `ogbn-arxiv`) · 2 research (`CLRS`, `babylm`) · 2 code-speedup (`llama-inference`, `vectorization`) · 2 LLM-tool (`bibtex-generation`, `literature-review-tool`) |
| **Team size** | **Origin: 1** · **Rec: 3** (engineer / researcher / reviewer) |
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
| **Team size** | **Origin: 1** · **Rec: 2–3** (coder + tester) |
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
| **Questions** | **13,610** (train 13,328 · valid 117 · test 165) |
| **Team size** | **Origin: 3** (ICPC-style) · **Rec: 3** (shared machine + penalty queue) |
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
| **Team size** | **Origin: 4–6** (typical CTF team) · **Rec: 4–6** (split by category) |
| **Time** | Open-ended within challenge Docker lifetime |
| **Answer type** | Exact flag string |
| **Grading** | Exact flag match inside the challenge's Docker environment; fully automatic |
| **Source** | Full CTF tooling inside the container; challenges cloned on first use |
| **Link** | [GitHub NYU-LLM-CTF/NYU_CTF_Bench](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench) · [site](https://nyu-llm-ctf.github.io/) |
| **Data** | ⏳ on demand — `pip install nyuctf`; challenges cloned on first `CTFDataset(split=...)` call |
| **Notes** | Log which specialist solved each flag for role-specialization metrics. |

---

## Cybench · `Cybench/`

| | |
|---|---|
| **Domain** | Cybersecurity — professional CTF (HackTheBox / Sekai / HKCERT) |
| **Years/sessions** | 1 (Cybench release) |
| **Questions** | **40** tasks with subtask decomposition (local packs under HackTheBox / Project Sekai / HKCERT) |
| **Team size** | **Origin: 4–6** (typical CTF team) · **Rec: 4–6** (category / subtask split) |
| **Time** | Open-ended within per-task Docker |
| **Answer type** | Flag (+ intermediate subtask checkpoints) |
| **Grading** | Flag match + per-subtask checks in Docker |
| **Source** | Per-task Docker images with professional CTF tooling |
| **Link** | [GitHub andyzorigin/cybench](https://github.com/andyzorigin/cybench) · [cybench.github.io](https://cybench.github.io) · [arXiv:2408.08926](https://arxiv.org/abs/2408.08926) |
| **Data** | `benchmark/Cybench/benchmark/` — per-challenge folders (`README.md`, `challenge/`/`dist/`, `metadata/metadata.json` with `easy_prompt`/`hard_prompt`); Docker images still needed for interactive web/pwn eval |
| **Notes** | Harder / more professional tier than NYU CTF Bench. For **problem-only** use: take `README` + `challenge`/`dist` + prompts; hide `metadata/solution` and `answer` fields. Full agent eval still needs the Cybench runner + Docker. |

---

## Math modeling contests · `modeling_agent/`

| | |
|---|---|
| **Domain** | Applied math modeling — statistics, optimization, simulation, data analysis |
| **Years/sessions** | 2001–2025 across 5 contest series: MCM (24), ICM (20), HiMCM (19), MidMCM (3), IM2C (2) |
| **Questions** | 68 full modeling problems (Middle School 3 · High School 21 · Undergraduate 44) |
| **Team size** | **Origin: 3–4** (COMAP) · **Rec: 3–4** |
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
| **Team size** | **Origin: 1** (task assignee) · **Rec: 4–5** (ideator / proposer / experimenter / writer ± verifier) |
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
| **Team size** | **Origin: 1** (assistant) · **Rec: 3** (clinician / safety / communicator) |
| **Time** | Multi-turn chat; open-ended response length |
| **Answer type** | Free-form response to a health conversation |
| **Grading** | 48,562 physician-written weighted criteria; model-based grader checks each criterion met/unmet → weighted score |
| **Source** | Chat setting; safety/refusal behavior is part of the task on `red_teaming` |
| **Link** | [HF: openai/healthbench](https://huggingface.co/datasets/openai/healthbench) · [arXiv:2505.08775](https://arxiv.org/abs/2505.08775) |
| **Data** | `HealthBench/` — JSONL (`oss_eval`, `consensus`, `hard`) (~246 MB) |
| **Notes** | Each conversation carries its own criterion set — no single global rubric. |

---

## HealthBench Professional · `HealthBench-Professional/`

| | |
|---|---|
| **Domain** | Medicine — physician-facing clinical workflows (harder tier than HealthBench) |
| **Years/sessions** | 1 (OpenAI HealthBench Professional release) |
| **Questions** | **525** examples (`consult` / `writing` / `research`; `good_faith` + `red_teaming`; `difficult` / `typical`) |
| **Team size** | **Origin: 1** (assistant) · **Rec: 3** (specialist / safety / medical-writer) |
| **Time** | Multi-turn chat; open-ended response length |
| **Answer type** | Free-form clinical response; each item ships a physician-written reference response |
| **Grading** | Per-example physician-written `rubric_items` (criterion + points); model grader met/unmet → weighted score |
| **Source** | Clinician workflow setting; specialty labels present |
| **Link** | [HF: openai/healthbench-professional](https://huggingface.co/datasets/openai/healthbench-professional) · [OpenAI post](https://openai.com/index/making-chatgpt-better-for-clinicians/) |
| **Data** | `benchmark/HealthBench-Professional/` — `healthbench_professional_eval.jsonl` (~2.8 MB) |
| **Notes** | Consumer HealthBench = patient/public Q&A (~5,000). Professional = doctor-side tasks (~525) with reference answers — better Tier-2 gold + Tier-3 rubric hybrid. |

---

## PaperBench · `PaperBench/` (on demand)

| | |
|---|---|
| **Domain** | AI/ML research — replicate ICML 2024 papers from scratch |
| **Years/sessions** | 1 (20 ICML 2024 papers) |
| **Questions** | 20 eval papers · 8,316 leaf criteria (local also ships 3 development papers → 23 / 8,921) |
| **Team size** | **Origin: 1–3** (researchers) · **Rec: 3** (read / implement / run) |
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
| **Questions** | **17** tasks (deduped local packs; `IOAI2025/` HF mirror not double-counted) |
| **Team size** | **Origin:** Individual **1** · Team Challenge national team · **Rec:** Individual **3** · Team **3–5** |
| **Time** | At-home + on-site Individual windows; Team Challenge timed on-site |
| **Answer type** | Model predictions / code notebooks (Individual); Team Challenge artifact (robotics / generative) |
| **Grading** | Task metrics on hidden tests for Individual; rubric / jury for Team Challenge |
| **Source** | Contest-provided data only; Python + standard ML stack |
| **Link** | [HF: IOAI-official/IOAI2025](https://huggingface.co/datasets/IOAI-official/IOAI2025) · [GitHub 2024](https://github.com/IOAI-official/IOAI-2024) · [2025](https://github.com/IOAI-official/IOAI-2025) · [2026](https://github.com/IOAI-official/IOAI-2026) · [Resources](https://ioai-official.org/resources/) |
| **Data** | `benchmark/IOAI/` — see `README.md` (**17** tasks); `IOAI2025/` HF mirror + `IOAI-2024/` · `IOAI-2025/` · `IOAI-2026/` |
| **Notes** | Best new multi-agent AI olympiad with official datasets. Pair ML-specialist agents on Individual tasks; use a separate robotics / planning team for the Team Challenge. CC-BY-4.0. |

---

### EOES / EUSO · `EOES/`

| | |
|---|---|
| **Domain** | Interdisciplinary experimental science (physics + chemistry + biology practicals) |
| **Years/sessions** | EUSO 2003–2019; EOES 2021–2025 |
| **Questions** | 2 integrated experiments (A/B) per year; local mirror **~90 PDFs / ~172 MB** (EUSO 2003–2017 partial + EOES 2021/2023–2025 task packs; 2022 tasks still unpublished on host) |
| **Team size** | **Origin: 3** · **Rec: 3** |
| **Time** | Multi-hour lab practicals during olympiad week |
| **Answer type** | Completed answer sheets / measurements / short lab writeups |
| **Grading** | Official marking schemes (partial credit); rubric-style for open responses |
| **Source** | Organizer-provided lab equipment; no outside help during exam |
| **Link** | [EUSO experiments](http://euso.eu/about/experiments/) · [EOES previous olympiads](https://www.eoes.science/Previous%20olympiads/previous.html) |
| **Data** | `benchmark/EOES/` — `euso/<year>/` experiment PDFs + `eoes/<year>/` task packs + `eoes/mirrors/` national reports + syllabus/rules; see `INVENTORY.md` |
| **Notes** | Closest European counterpart to `ijso_practical`. Natural roles: experimentalist / data-analyst / report writer. EOES 2022 official task PDFs not public yet (`eoes2022.uhk.cz`); older EUSO years 2005/2008–2010/2016/2018–2019 mostly dead-host only. |

---

### IChTo · `IChTo/`

| | |
|---|---|
| **Domain** | Chemistry research / open problems (IYPT-style tournament) |
| **Years/sessions** | 2017–2026 (9 published problem sets; 2020/2021 combined) |
| **Questions** | **106** open problems across 9 sets (2017–2024 & 2026: 12 each; 2025: 10; no separate 2021 PDF) |
| **Team size** | **Origin: 3+** (Reporter / Opponent / Reviewer) · **Rec: 3+** (role rotation) |
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
| **Team size** | **Origin: 8** · **Rec: 8** |
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
| **Questions** | **4,202** keyed answers (`mh_answers`); puzzle bodies+media mirrored under `puzzles/` (see local README) |
| **Team size** | **Origin: 5–150** (specialty squads) · **Rec: 8–20** for lab sims (scale as needed) |
| **Time** | ~48-hour hunt weekend (remote-capable in recent years) |
| **Answer type** | Short string answers → meta answers → coin location |
| **Grading** | Exact / normalized answer match (RULE); structure in `metapuzzles.yml` |
| **Source** | Full internet and arbitrary tooling; extreme division of labor |
| **Link** | [puzzles.mit.edu](https://puzzles.mit.edu/) · [Archive by year](https://puzzles.mit.edu/huntsbyyear.html) · [Puzzle Index](http://devjoe.appspot.com/huntindex/) · [mh_answers](https://github.com/dgulotta/mh_answers) |
| **Data** | `benchmark/MIT_Mystery_Hunt/` — `mh_answers/`, `answers.tsv`, `puzzles/` (HTML+multimedia mirror), hunt index pages |
| **Notes** | Strongest public multi-agent collaboration dataset. Local mirror links answers→puzzle pages via `answers.tsv` + huntindex. Procedurally generated rounds (e.g. Infinite Corridor / Hydra) excluded from keys. |

---

### IOL · `IOL/`

| | |
|---|---|
| **Domain** | Linguistics — morphology, phonology, syntax, semantics, writing systems |
| **Years/sessions** | Official IOL archive from 2003 onward; HF extract covers solution-backed problems |
| **Questions** | 130 solution-backed source problems · 555 HF records (478 text-strict); ~1,500 sub-instances in IOLBENCH-style splits |
| **Team size** | **Origin:** Individual **1** · Team Contest **4** · **Rec:** Individual **2–3** · Team **4** |
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
| **Years/sessions** | WRT: 1996, 2006–2019, 2021–2025 (17 eds) · FWE: 1996–2025 (partial) · MMT: sample only |
| **Questions** | **600** total — **WRT 505** · **FWE 55** · **MMT 40** (scored response units) |
| **Team size** | **Origin: 1** (WRT/MMT) · **Rec: 3** (map / data / writer) for fieldwork-style sim |
| **Time** | Timed WRT; multi-hour fieldwork |
| **Answer type** | Short written responses, map interpretation, field report; MMT = MCQ |
| **Grading** | RULE for keyed items (marking schemes); RUBRIC for open fieldwork writeups |
| **Source** | Resource booklets provided; exam-hall constraints |
| **Link** | [iGeo document library](https://geoolympiad.org/document-library/) |
| **Data** | `benchmark/iGeo/` — `igeo_questions.json` / `.jsonl` + `summary.json` (+ source PDFs) |
| **Notes** | Canonical index is the JSON (not PDF file count). Some scanned years have `question: null`. See `benchmark/iGeo/README.md`. |

---

### IESO · `IESO/`

| | |
|---|---|
| **Domain** | Earth science — geology, geophysics, meteorology, oceanography, astronomy, environment |
| **Years/sessions** | International finals from ~2007; national entrance archives also public |
| **Questions** | ~125 theory/practical PDFs (+ keys) in the local archive |
| **Team size** | **Origin: 1** · **Rec: 2–3** (lab-role split on practicals) |
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
| **Years/sessions** | Topic archive ~1993–2026 (31 years extracted; gaps where HTML is sparse) |
| **Questions** | ~95 structured Topic prompts (`topics.jsonl`); typically 4 quotes/year, contestant picks 1 |
| **Team size** | **Origin: 1** (≤2 students per country) · **Rec: 3** (drafter / critic / editor) |
| **Time** | Timed on-site essay |
| **Answer type** | Philosophical essay |
| **Grading** | RUBRIC (IPO / national jury criteria) |
| **Source** | Closed-book; topics revealed at start |
| **Link** | [philosophy-olympiad.org](https://www.philosophy-olympiad.org/) · [Topics](https://www.philosophy-olympiad.org/?page_id=72) |
| **Data** | `benchmark/IPO/topics/` — `IPO_YYYY_topics.md/.json`, `ALL_TOPICS.md`, `topics.jsonl`, `index.json`, 2026 official PDF; `essays/` = winning/sample answers (not prompts); `page_1.html` = Topics page mirror |
| **Notes** | Prompts are philosophical quotations, not short-answer items. Do not treat `essays/*.pdf` as questions. A few early years still need manual cleanup from the HTML mirror. |

---

### International History Olympiad · `History_Olympiad/`

| | |
|---|---|
| **Domain** | History — bees, bowls, written exams, historiography, art history |
| **Years/sessions** | Multi-year resource archive (exams + keys + rubrics) |
| **Questions** | ~90 exam/key/rubric PDFs across 6 editions (2014, 2018–2019, 2022–2024); multiple event types per edition |
| **Team size** | **Origin:** Bee **1** · Bowl team · **Rec:** Bee **2–3** · Bowl **4** |
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
| **Team size** | **Origin:** Economics **1** · Business Case **3–5** · **Rec:** Econ **2–3** · Case **3–5** |
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
| **Team size** | **Origin:** Individual **1** · Group **5** · **Rec:** Individual **2–3** · Group **5** |
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
| **Questions** | **42** public guiding questions locally; live Collaborative Writing uses **3–4 prompts/session** (not pre-published) |
| **Team size** | **Origin: 3** · **Rec: 3** |
| **Time** | Staged: plan → individual write → peer edit |
| **Answer type** | Three handwritten essays |
| **Grading** | RUBRIC (WSC judging criteria) |
| **Source** | No electronic devices; handwritten only |
| **Link** | [WSC Events](https://scholarscup.org/events/) · [WSC Wiki](https://www.owiki.org/wiki/World_Scholar%27s_Cup) |
| **Data** | `benchmark/WSC_Writing/` — guiding questions + discussion prompts; may include copies from repo `data/raw/wsc_writing` |
| **Notes** | The 42 guiding Qs are prep/proxy items from official themes — not the sealed on-site prompts. |

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
hf download math-ai/aime26                  --repo-type dataset --local-dir olympiad/AIME/aime26
# Note: aime24 upstream is parquet; convert to test.jsonl locally if needed
hf download princeton-nlp/SWE-bench_Verified --repo-type dataset --local-dir olympiad/SWE-bench_Verified
hf download codegenning/usacobench_formatted --repo-type dataset --local-dir olympiad/USACO   # 3.8 GB

# Large rule-based — pull only when needed
hf download livecodebench/code_generation_lite --repo-type dataset --local-dir olympiad/LiveCodeBench  # 4.4 GB
hf download deepmind/code_contests             --repo-type dataset --local-dir olympiad/CodeContests    # 7.6 GB

# Open-ended (HF datasets)
hf download chchenhui/mlrbench-tasks --repo-type dataset --local-dir olympiad/MLR-Bench
hf download openai/healthbench       --repo-type dataset --local-dir olympiad/HealthBench
hf download openai/healthbench-professional --repo-type dataset --local-dir olympiad/HealthBench-Professional

# Docker / GitHub-based (not plain HF pulls)
#   NYU CTF Bench : pip install nyuctf ; challenges cloned on first CTFDataset(split=...) call
#   Cybench       : local packs in benchmark/Cybench/benchmark/ (problem-only OK); Docker images for full eval
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
# iGeo / IESO / History / IEO / IOAA / WSC: official PDF / HTML archives
# IPO: structured topics already under benchmark/IPO/topics/ (from Topics page HTML)
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
| `NYU_CTF_Bench` / `Cybench` | Cybench challenge packs already local; install Docker and smoke-test one challenge per category for full flag grading |
| `PaperBench` | Clone preparedness repo with LFS for the 20-paper rubric trees |
| `ioai` | Expand Team Challenge simulation assets (robotics env / generative briefs beyond statements) |
| `eoes` | Local mirror ~90 PDFs (`benchmark/EOES/INVENTORY.md`); still missing EOES 2022 official tasks + several dead-host EUSO years |
| `ichto` | Optional: collect winning fight recordings / written solutions if published |
| `pumac_power` | Rename PDFs to `YYYY_problems.pdf` / `YYYY_solutions.pdf` for uniform loading |
| `mystery_hunt` | Answer→puzzle body+media mirror in progress under `benchmark/MIT_Mystery_Hunt/puzzles/` (`answers.tsv` queue + huntindex); continue with `mirror_*.py` |
| `iol` | Prefer HF structured answers; backfill figure/script PDFs for multimodal rows |
| `igeo` | Structured extract done (`igeo_questions.json`); optional: backfill early WRT gaps + yearly MMT when upstream republishes |
| `ieso` | Normalize year folders; ensure practical keys sit beside theory PDFs |
| `ipo` | Fill sparse early years (1994/1996/1998/1999/2006) from `page_1.html`; collect official marking criteria |
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
| `HealthBench-Professional` | Per-example `rubric_items` + physician reference response; model grader → weighted score. | Specialist / safety / medical-writer; harder clinician-facing tier than HealthBench. |
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
