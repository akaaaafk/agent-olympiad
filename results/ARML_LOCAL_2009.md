# Evaluation run — ARML Local 2009

**Command:** `python3 src/run_exam.py --all-schemas`

**Models:** agents = `openai/gpt-5.4-mini`, judge = `anthropic/claude-sonnet-4-6` (via Perplexity)

**Problem:** ARML Local 2009 Team Round (10 problems, 40 pts, team of 6)

## Results (latest batch, `20260710-144019`)

| Schema | Score | Answer parts | Turns | Chat msgs |
|--------|-------|--------------|-------|-----------|
| Centralized | 20/40 | 10/10 | 7 | 6 |
| Decentralized | 20/40 | 8/10  | 12 | 11 |
| Round Table | 17/40 | 10/10 | 13 | 12 |

Full traces: `arml_local_2009_{schema}_20260710-144019.json` in this directory.

## What worked

P1, P2, P6 correct across schemas. Round table produced rich peer discussion (agents self-assigned problems, cross-checked).

## What broke / limitations

- **P10 KenKen** — PDF extraction dropped the puzzle grid; agents correctly flagged it as unsolvable
- **Hard problems wrong** — P3 (expected value), P5 (hexagon area), P7 (probability) all missed official answers
- **P4** — agents left answer in log form instead of simplifying to 5√11

