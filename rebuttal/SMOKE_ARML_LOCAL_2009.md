# Smoke run: ARML Local 2009, claude-haiku-4-5 (2026-11-11)

One run per setting, 10 tasks (4 points each), 10-round budget, 3 Claude Code
instances for multi and OTC, `--max-inner-turns 8`.

| setting | score | tasks right (Q1..Q10) | rounds used | Claude Code calls | inner tool steps | cost (USD) |
|---|---|---|---|---|---|---|
| single | 28/40 | 1110110110 | 3 (stopped with `done`) | 3 | 12 | 1.45 |
| multi (3) | 28/40 | 1110110110 | 3 (all agents `done`) | 9 | 29 | 1.17 |
| OTC + Claude Code (3) | 32/40 | 1110111110 | 10 | 61 (30 action, 30 think, 1 Coach) | 185 | 4.79 |

Notes:
- OTC adapter health: 0 transport failures, 0 repair retries, 0 permission
  denials; 2 structured deliberations, 20% review coverage, deadline submit.
- Sandbox check: one multi agent globbed the parent workspace dir looking for
  the Q10 picture and was denied, as intended.
- Q10 (KenKen) references a figure that is not in the text prompt, so no
  setting can solve it from text alone.
- With n=1, single = multi on this packet. Use several packets or seeds
  (`--start-seat` for OTC) before reading the ordering.
