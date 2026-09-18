# Vallina OTC: strict no-memory control

Canonical preset: `vallina_otc`; aliases `vanilla_otc` and `otc_rule_card`.
`vanilla` / `vanilla_team` continue to mean `decentralized`.

The control now sees **only the current team round**. Private, group and public
history all expire at the boundary, including shared drafts, answer versions,
reviews, conversations and tool results. `inspect_problem` cannot retrieve old
content; native schemas and direct handlers cannot review an old version or
reuse an old proposal. This is the user-requested meaning of without memory.

Both OTC presets retain the same blind turn-0 Coach, rule card, private-message
permissions, independent-review requirements, structured discussion and resource
limits. The control may communicate and review within the current round. A
round means `budget.turns_used`, including every contestant seat in that round.
Static questions, rules, the blind pre-contest brief and current official
contest/resource state remain available. Backend answers and full logs remain
available for grading and audit, not for cross-round contestant context.

The full `otc` preset retains automatic memory v3. The other three baselines
retain their existing definitions. See
[pipeline overview §7](from_zhongzheng/final-pipeline-20260914.md).

Run with `--system-variant vallina_otc` and a **fresh output directory**. Match
manifest, model, judge, roster, rule card and budgets when comparing with `otc`.
The checkpoint records `current_turn_context_version=1` and refuses checkpoints
from the old shared-history control before model calls.

Earlier experiments are preserved with their original scores. They used a
control that could retain shared drafts and conversation; they are not results
for this strict no-memory condition. Offline smoke uses mock solvers/judges and
does not establish a score improvement on a real model.
