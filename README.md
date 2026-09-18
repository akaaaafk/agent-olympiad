# Agent Olympiad

Agent Olympiad benchmarks AI teams on olympiad-style team tasks. It models one
participating team's roles, coordination, resources, phases, submissions, and
scoring. Opposing teams are outside the implementation scope.

The current entry point is the manifest-driven contest pipeline, with five
baselines, typed actions, resumable runs, and deterministic, remote, or rubric
judging. This checkout provides CLI runners and Python model adapters; it is not
a hosted benchmark API or an installable benchmark SDK.

## Install

Run from the repository root. Python 3.12 is the tested environment.

```sh
python -m venv .venv
```

Activate it on PowerShell with `.\.venv\Scripts\Activate.ps1`, or on Linux/macOS
with `source .venv/bin/activate`, then install:

```sh
python -m pip install -r requirements.txt
python -m pip check
```

Tinker is pinned to the validated 0.29.0 SDK. `pip check` checks installed
package consistency; it does not install missing requirements. For tests, install
`requirements-dev.txt`, which includes runtime dependencies.

Copy `.env.example` to `.env` only if you do not already have one. Configure your
chosen provider's key without replacing existing settings. Every live run
requires an explicit model ID available to your account.

| Providers | Configuration |
|---|---|
| `tinker`, `perplexity`, `openai`, `openagents`, `vectorengine` | [Provider configuration](configs/providers/README.md) |
| `anthropic`, `gemini`, `deepseek`, `openai_compatible` | [Additional model interfaces](docs/public_model_interfaces.md) |

Contestants and judges use the same provider. A separate judge model on that
provider is optional. Credentials are excluded from saved run identities.

## First run with mini_data

The independent catalog is **`data/mini_data` inside this checkout**. As of
2026-09-17 it contains 39 tracks, 109 records, and 89 execution sessions. A session
can contain a complete packet; mini_data does not imply one small subquestion.

Check data and execution preparation without model calls, then register sessions:

```sh
python scripts/verify_mini_dataset.py --output results/mini_preflight.json
python scripts/run_mini_dataset.py register --output results/mini_first
```

Read both `passed` and `all_jobs_environment_ready`. The preflight checks all five
baselines, separating data errors from missing external services. It does not
establish model quality or official score equivalence.

Tinker vision artifact runs use [paginated PDF reading](docs/pdf_pagination_20260918.md):
`read_problem_pdf` selects up to two pages from the complete authorized packet or
current rendered candidate. Long PDFs are also read in batches during judging,
with cached evidence and an explicit compression limitation. IEO Business Case
permits online research during preparation; its unsupported fixed-turn search
ban has been removed. Runtime rule views now display the actual configured budgets.
The [earlier parameter audit](docs/competition_parameter_audit_20260917.md) records
the original findings. Passing preflight does not certify an all-track live run.

Replace `YOUR_MODEL_ID` with an exact model your account supports. The probe makes
two small authenticated calls and may incur charges:

```sh
python scripts/check_provider.py --provider tinker --model YOUR_MODEL_ID
```

Run one ARML mini session with explicit smoke budgets:

```sh
python scripts/run_mini_dataset.py run --provider tinker --model YOUR_MODEL_ID --competitions arml_local --system-variant single_agent --limit 1 --max-turns 10 --max-api-calls 24 --max-total-tokens 20000 --output results/mini_first
```

Change provider and credentials for another service. Use a fresh output directory
for each new experimental condition. `all` combines registration and execution;
`run` uses an existing registry. Omit `--limit` for all selected sessions. Full
baseline comparisons should use matched budgets.

See the [English PowerShell guide](docs/from_zhongzheng/mini_pipeline_powershell.md)
for all five baselines, track/year filters, gateway setup, and resume commands.

## Baselines and budgets

| `--system-variant` | Behavior |
|---|---|
| `single_agent` | One contestant; collaboration metrics are not applicable |
| `decentralized` | Team coordination without a central leader |
| `centralized` | The existing leader coordination workflow |
| `vallina_otc` | Rule-card Open Table Coach without cross-round memory |
| `otc` | The matched Open Table Coach baseline with memory |

`vallina_otc` is the historical CLI spelling. The OTC pair shares coordination
policy; see [its memory boundary](docs/vallina-otc.md). Ordinary baselines require
rules mode `off`; both OTC variants require `enforced`. Team sizes come from each
competition's `competition.json`; `single_agent` uses one contestant.

Production budgets use five simulated minutes per turn, rounded up and clamped
to **10-90** turns. Explicit `--max-turns` uses the same bounds. A turn may include
several model calls for deliberation, memory, or transport recovery. API-call and
total output-token caps are separate options and are unset by default.
`--max-total-tokens` tracks generated output, including reported thinking tokens;
it is not an input-plus-output billing cap.

Built-in live runners pass remaining budgets to Coach, private-think and leader
planning as well as ordinary actions. They retain reported retry/continuation
usage and stop after a reported overrun. Network failures save usage and pending
work before exiting, so resume uses only the remaining allowance. Custom text-only
callbacks still use estimates. See the [action, provider and checkpoint repairs](docs/call_contract_repairs_20260918.md)
and [pagination repairs](docs/code_repairs_20260918.md) for the accounting contract
and validation limits.

Tinker uses staged action sampling with bounded continuation. Native providers
use bounded retries for truncation. Incomplete actions and ambiguous batches do
not execute. See [Tinker transport](docs/tinker_action_transport.md) and
[interface behavior](docs/public_model_interfaces.md).
The [centralized and OTC recovery follow-up](docs/centralized_transport_repair_20260918.md)
documents task-assignment focus and direct rewriting of rejected raw arguments,
including bounded live Qwen validation.

Ordinary shared drafts use an 8,000-character hard limit across contest baselines,
with a suggested 2,000-4,000-character length. Accepted drafts are saved in full;
`inspect_problem` can read an exact version in character pages. Source and
document contracts retain their separate limits. See
[draft limits and answer pagination](docs/work_content_limits_20260918.md).

## Outputs, evaluation, and resume

Each output directory contains:

- `registry.json`: catalog sessions and execution routes.
- `batch_status.json` and `summary.tsv`: states, scores, usage, and reasons.
- `logs/<job>.log`: runner output.
- `runs/<job>/`: checkpoints, traces, and `contest_session.json`; artifact routes
  also write `result.json`.

`complete`, `evaluation_pending`, `ungraded`, and `blocked` are different states.
A finished contestant run does not guarantee a usable score. Pending evaluation
can resume without rerunning contestants. Single-agent runs skip collaboration
scores. Rubric and static code-review scores are not official execution results.

Resume with the same `run` command, output directory, provider, model, baseline,
and budgets. The pipeline continues checkpoints and skips verified completed
work. Refresh saved reports with:

```sh
python scripts/run_mini_dataset.py report --output results/mini_first
```

Source/configuration changes require a fresh output directory. Do not edit old
identities to force reuse. Use one supervisor per output directory; inspect its
lock owner and child processes before treating a lock as stale. See
[run identity and resume](docs/contest-run-reuse.md).

## External tools

| Workflow | Additional setup |
|---|---|
| Isolated Python, programming tools, CTF | Docker with Linux containers and the selected runner's images; `docker info` must succeed |
| CTF | Reviewed task mapping and `agent-olympiad-ctf:v1`; see [CTF delivery](docs/ctf.md) |
| ICPC remote judging | Configured local VJudge gateway and authenticated online-judge access |
| LaTeX submissions | `docker build -t agent-olympiad-latex:v1 docker/latex` |
| HTML/slides to PDF | Chrome, Chromium, or Edge recognized by `src/artifacts/slides.py` |
| Selected PDF collection/repair scripts | Poppler; check the selected script's executable paths |

Prepare only the tools needed by your track. Model access, Docker startup, remote
judging, and scoring readiness are separate checks.

## Data and development

`data/benchmarks` and `data/rules` are canonical; `data/base`, `data/last_exam`, and
`data/viz` are derived. Use `scripts/run_pipeline.py` for the main catalog and
`scripts/run_mini_dataset.py` for mini. Per-record evaluation metadata is
authoritative: `not_ready` records are blocked, and `ready_with_limitations`
records retain explicit scoring/environment limitations. Hash checks do not
certify every formula, rule interpretation, or solution.

Run the offline tests:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Provider protocol tests mock HTTP responses; check live access with your own
account/model. Historical experiment tables are not current validation evidence.

References: [documentation map](docs/README.md),
[pipeline architecture](docs/from_zhongzheng/final-pipeline-20260914.md),
[action reference](docs/from_zhongzheng/final-pipeline-appendix-actions-20260914.md),
[evaluation](docs/EVALUATION.md), [mini catalog](data/mini_data/README.md),
and [newcomer inspection](docs/newcomer_inspection_20260917.md).
