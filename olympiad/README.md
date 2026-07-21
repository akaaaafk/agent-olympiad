# Data collected — `olympiad/`

Last updated: 2026-07-15

> **Data files are not in git.** The three original datasets (`OlympicArena`, `modeling_agent`, `MLAgentBench`) are mirrored on the private HF dataset [`akaaafk/multiagent_bench`](https://huggingface.co/datasets/akaaafk/multiagent_bench) — run `python download_data.py` at the repo root. The newly added benchmarks below are pulled directly from their public HF / GitHub sources — see [Downloading](#downloading).

**Current focus:** a curated benchmark suite for multi-agent team competitions, organized into **two tracks** — **10 rule-based** (closed-form answers, fully auto-graded, no LLM judge) and **10 open-ended** (free-form deliverables scored against an explicit rubric). Together with the humanities/arts/business raw material in `art/`, this gives paired auto-gradable and rubric-judged tasks across STEM, engineering, security, medicine, finance, law, and debate.

**Competition** = one contest type (one row). **Question** = one scored problem/task. **Rule-based** = grader is a deterministic function (exact match, test cases, `eval.py`, flag match). **Open-ended** = deliverable is a paper/report/plan/answer graded by a rubric (human scores where available, otherwise an LLM-judge panel).

---

## Track A — 10 rule-based (auto-graded)

| # | ID | Source contest | Questions | Grading | Location / access |
|---|----|----------------|----------:|---------|-------------------|
| 1 | `OlympicArena` | OlympicArena — 7 STEM olympiads | 10,615 | answer-type-aware rule match; `val` local, `test` withheld | ✅ `olympiad/OlympicArena/` (HF `akaaafk/multiagent_bench`) |
| 2 | `OlympiadBench` | Olympiad math + physics (bilingual, multimodal) | 8,476 | final-answer match against gold | ✅ `olympiad/OlympiadBench/` ([HF `Hothan/OlympiadBench`](https://huggingface.co/datasets/Hothan/OlympiadBench)) |
| 3 | `AIME` | AIME 2024 + 2025 | 60 | integer exact match (`math-verify`) | ✅ `olympiad/AIME/` ([HF `math-ai/aime24`](https://huggingface.co/datasets/math-ai/aime24) · [`aime25`](https://huggingface.co/datasets/math-ai/aime25)) |
| 4 | `USACO` | USA Computing Olympiad | 307 | hidden test cases (pass/fail per subtask) | ✅ `olympiad/USACO/` ([HF `codegenning/usacobench_formatted`](https://huggingface.co/datasets/codegenning/usacobench_formatted)) |
| 5 | `SWE-bench_Verified` | Real GitHub issues (human-validated) | 500 | apply patch → run repo unit tests | ✅ `olympiad/SWE-bench_Verified/` ([HF `princeton-nlp/SWE-bench_Verified`](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified)) |
| 6 | `MLAgentBench` | ML engineering tasks | 15 | hidden `eval.py`; >10% over baseline = success | ✅ `olympiad/MLAgentBench/` (HF `akaaafk/multiagent_bench`) |
| 7 | `LiveCodeBench` | Competitive programming (LeetCode/AtCoder/Codeforces), contamination-free | ~1,055 | hidden test cases | ⏳ on-demand (4.4 GB) ([HF `livecodebench/code_generation_lite`](https://huggingface.co/datasets/livecodebench/code_generation_lite)) |
| 8 | `CodeContests` | Codeforces / ICPC-style (AlphaCode data) | ~13,600 | hidden test cases | ⏳ on-demand (7.6 GB) ([HF `deepmind/code_contests`](https://huggingface.co/datasets/deepmind/code_contests)) |
| 9 | `NYU_CTF_Bench` | CSAW CTF (cybersecurity capture-the-flag) | 200 | exact flag match in dockerized env | ⏳ on-demand (GitHub + Docker) ([repo](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench)) |
| 10 | `Cybench` | Professional CTF (HackTheBox / Sekai etc.) | 40 | flag match + subtask checks in Docker | ⏳ on-demand (GitHub + Docker) ([repo](https://github.com/andyzorigin/cybench)) |

## Track B — 10 open-ended (rubric-judged)

| # | ID | Source contest | Questions | Rubric / ground truth | Location / access |
|---|----|----------------|----------:|-----------------------|-------------------|
| 1 | `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | 68 | per-problem `requirements` grading points + `eval_roles` | ✅ `olympiad/modeling_agent/` (HF `akaaafk/multiagent_bench`) |
| 2 | `MLR-Bench` | ML research tasks (NeurIPS/ICLR/ICML workshops) | 201 | MLR-Judge rubric across 9 dims (novelty, soundness, …) | ✅ `olympiad/MLR-Bench/` ([HF `chchenhui/mlrbench-tasks`](https://huggingface.co/datasets/chchenhui/mlrbench-tasks)) |
| 3 | `HealthBench` | Realistic clinical conversations | 5,000 | 48,562 physician-written weighted criteria | ✅ `olympiad/HealthBench/` ([HF `openai/healthbench`](https://huggingface.co/datasets/openai/healthbench)) |
| 4 | `PaperBench` | Replicate 20 ICML 2024 papers from scratch | 20 (8,316 leaves) | hierarchical author-co-designed rubric tree | ⏳ on-demand (GitHub LFS) ([repo](https://github.com/openai/preparedness/tree/main/project/paperbench)) |
| 5 | `cfa_research_challenge` | CFA Institute Research Challenge | 19 | valuation/writing/presentation rubric; 19 champion reports | 📁 `art/cfa_research_challenge/` |
| 6 | `gcch_harvard` | Global Case Competition at Harvard | 7 | case rubric; 9 winning decks as gold | 📁 `art/gcch_harvard/` |
| 7 | `wharton_investment` | Wharton Global HS Investment Competition | 4 | strategy rubric + portfolio replay | 📁 `art/wharton_investment/` |
| 8 | `vis_moot` | Willem C. Vis Commercial Arbitration Moot | 7 | memorandum + oral rubrics; Pace winning memos | 📁 `art/vis_moot/` |
| 9 | `debatebench` | WUDC / BP Debate | 256 speeches | **official human judge speaker scores + rankings** | 📁 `art/debatebench/` |
| 10 | `ethics_bowl` | APPE + National HS Ethics Bowl | ~155 cases | official judging/scoring guides | 📁 `art/ethics_bowl_appe/`, `art/ethics_bowl_nhseb/` |

Legend: ✅ downloaded locally · ⏳ fetch on demand (large or Docker-based) · 📁 already collected under `art/`.

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
```

---

## Deep dives — original three datasets

> The tables and per-dataset sections below detail the three datasets collected first (`OlympicArena`, `modeling_agent`, `MLAgentBench`). The seven additions in the two tracks above are single-source benchmarks; their grading and team-adaptation notes live in [Evaluation design](#evaluation-design). Per-question counts for the additions: OlympiadBench 8,476 · AIME 60 · SWE-bench_Verified 500 · MLR-Bench 201 · HealthBench 5,000.

### Simulator Matrix

| ID | Full Name | Input Modality | Team Setup | Computers | Allowed Tools & Resources | Materials Provided | Final Deliverable | Sources |
|----|-----------|----------------|------------|-----------|--------------------------|-------------------|-------------------|---------|
| `OlympicArena` | OlympicArena benchmark | Problem text + figures (EN/ZH, text-only & multimodal) | Individual in origin contests; adaptable to per-discipline specialist agents | None in origin olympiads | Closed-book olympiad conditions · fine-grained answer types (single/multi-value, expression, code with test cases) enable auto-grading | Parquet splits per discipline; `val` includes answers, `test` answers withheld (submit to official platform) | Short answers / expressions / code, auto-judged | [HF dataset](https://huggingface.co/datasets/GAIR/OlympicArena) · [GitHub](https://github.com/GAIR-NLP/OlympicArena) · [arXiv:2406.12753](https://arxiv.org/abs/2406.12753) |
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM math modeling | Open-ended problem statement (text + described images) | 3–4 students per team (origin rules) | Unrestricted | Multi-day open-book contest · full internet & software · judged on modeling quality, not single answers | JSON with problem text, grading requirements, suggested evaluator roles, decomposition | Modeling paper (analysis + model + recommendations), rubric-judged | [COMAP](https://www.comap.com/contests) |
| `MLAgentBench` | MLAgentBench — ML experimentation tasks | Research goal (text) + starter code workspace per task | Designed for a single agent; natural fit for engineer/researcher/reviewer team split | Required — agent edits & runs code on GPU/CPU | Open-ended experimentation · read/edit/execute scripts · install packages · Kaggle API for some tasks | Per-task `env/` folder (starter `train.py`, data descriptions) + hidden `scripts/` (`prepare.py`, `eval.py`, grading) | Improved model / script + `submission.csv`; scored vs baseline (>10% improvement = success) | [GitHub](https://github.com/snap-stanford/MLAgentBench) · [arXiv:2310.03302](https://arxiv.org/abs/2310.03302) |

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
| **Notes** | MIT license. Unlike the other datasets here, tasks are **interactive environments**, not Q&A items — the deliverable is a code artifact, so runs need a sandboxed executor (upstream provides a Docker image `qhwang123/researchassistant`). Kaggle-derived tasks need Kaggle API credentials at prepare-time. Good complement to `modeling_agent`: same open-ended team workflow but with fully automatic grading. |

---

## Collection backlog

| ID | Action |
|----|--------|
| `OlympicArena` | Fetch figure images referenced by `figure_urls` for offline multimodal runs; register on the official platform to score `test`-split submissions |
| `modeling_agent` | Collect Outstanding-winner papers (COMAP publishes abstracts; full papers via UMAP Journal) as gold-standard references |
| `MLAgentBench` | Set up Kaggle API credentials + run `prepare.py` per task to cache raw datasets; pin the upstream Docker image for sandboxed execution |

---

## Evaluation design

All three datasets are auto-gradable, so evaluation here is about the harness, not the judge.

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `OlympicArena` | Answer-type-aware rule matching on the `val` split (638 questions, fully local); `test` split via the official platform. Use the upstream repo's grader rather than plain string match — answer types include expressions, intervals, and code with test cases. | Per-discipline specialist agents + an aggregator; compare against a single generalist agent at equal token budget. |
| `modeling_agent` | Exception in this folder: open-ended papers, scored by an LLM-judge panel walking the per-problem `requirements` (grading points) with the suggested `eval_roles` as judge personas. Judge panel must pass the calibration gate defined in `art/README.md` (Evaluation design → Judge validation). | 3–4 agents per COMAP rules (modeler / coder / writer); `decomposition` field seeds the role split. |
| `MLAgentBench` | Run each task's hidden `eval.py` on the produced artifact; success = >10% improvement over baseline starter code (upstream definition). Needs the sandboxed Docker executor. | Engineer / researcher / reviewer split sharing one workspace; solo-agent baseline at the same action budget. |

### Track A additions — rule-based

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `OlympiadBench` | Final-answer extraction + match against gold (numeric / expression); use the upstream answer-checker, not raw string equality. Multimodal problems need a vision-capable solver. | Per-subject specialists (math vs physics) + verifier agent that re-derives before submitting. |
| `AIME` | Deterministic integer match via `math-verify` (answers 0–999, no partial credit). | Multiple independent solvers + majority vote / verifier; measure whether team voting beats a single solver at equal budget. |
| `USACO` | Run submitted code against hidden test cases; score = fraction of cases passed per problem (bronze→platinum tiers). | Reader / coder / tester split; tester writes local cases before submitting. |
| `SWE-bench_Verified` | Apply the generated patch to the repo, run the project's `FAIL_TO_PASS` + `PASS_TO_PASS` test sets; pass only if all target tests go green. Needs per-repo Docker images. | Locator / patcher / reviewer roles on a shared checkout; solo baseline at equal edit budget. |
| `LiveCodeBench` | Hidden test cases per problem; use the release window **after** each model's cutoff to stay contamination-free. | Same as USACO; good for time-boxed "contest round" simulation. |
| `CodeContests` | Hidden test cases; ICPC-style (one shared machine, penalty per wrong submission) makes it the closest fit to a real 3-person programming team. | 3 agents sharing one submission queue under a penalty budget — direct ICPC analogue. |
| `NYU_CTF_Bench` / `Cybench` | Exact flag match (and per-subtask checks for Cybench) inside the challenge's Docker environment; fully automatic. | CTF teams split by category (pwn / crypto / web / rev); log which specialist solved each flag. |

### Track B additions — open-ended (rubric)

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `MLR-Bench` | MLR-Judge rubric across up to 9 dimensions (consistency, novelty, clarity, feasibility, completeness, soundness, insightfulness, significance, overall), 1–10 per dimension, dual-judge averaged. Supports stepwise (idea/proposal/experiment/writeup) or end-to-end. | Ideator / proposer / experimenter / writer stages map onto agent roles; watch for the paper's finding that coding agents fabricate ~80% of results — add a verifier. |
| `HealthBench` | Each conversation carries its own set of physician-written criteria with point weights; model-based grader checks each criterion met/unmet → weighted score. | Clinician / safety-reviewer / communicator roles; the `red_teaming` split stresses refusal & safety coordination. |
| `PaperBench` | Hierarchical rubric tree per paper (leaf = binary pass/fail, weighted up to a root Replication Score); rubric hidden from the solver; LLM judge co-validated against a separate judge benchmark. | Read-paper / implement / run-experiments split sharing a workspace; needs sandboxed long-horizon execution like MLAgentBench. |

All Track B judges must pass the **calibration gate** defined in `art/README.md` (Evaluation design → Judge validation) — `debatebench` human scores are the anchor. Report inter-judge agreement and run pairwise comparisons position-swapped.

Cross-cutting: log the same team-level metrics as `art/` (budget consumed, inter-agent messages, role-specialization entropy, team-vs-solo delta). For contamination, prefer withheld/newest splits — OlympicArena `test`, AIME 2025, LiveCodeBench post-cutoff windows, and post-2023 modeling problems — for headline numbers.
