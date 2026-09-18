# Current dataset status

Updated: 2026-09-18T01:36:23.124875+00:00

Main data: 39 competitions, 899 records.
Mini data: 39 competitions, 109 records; selected membership preserved.

| Main readiness | Records |
| --- | ---: |
| ready | 441 |
| ready_with_limitations | 300 |
| remote_judge_ready | 158 |

Cybench retains 38 validated tasks (2022: 8; 2023: 10; 2024: 20).
NYU CTF retains 44 validated tasks, including 2021 Interoperable.
Unresolved CTF tasks were removed from active membership and archived.
IOAI currently contains only 2025 Factory, scored as static program/design review.
IIOT is static source review; CCDC is written-plan review. These are not official runtime scores.
WRO simulation is excluded.

Latest checks:

- Main integrity: zero structural issues; 6,099 unique file hashes checked.
- Additional 27 competitions: 135 representative five-baseline offline route cases passed.
- Mini: 479 asset checks, zero errors; 445 prepared commands, zero pending/failed.
- CTF: Cybench 190 and NYU 220 five-baseline preparation checks passed.
- Mini dependency snapshots refreshed for 18 changed JSON files.

Offline/mock checks do not establish live-model solving success or official contest equivalence.
0 non-CTF records remain not_ready. 21 semantic review candidates remain
(12 printed-total versus answer-weight differences; 9 identical public/judge asset hashes).
Those candidates are not certified errors and were not silently changed.

Current evidence:

- [Main integrity](../output/pdf_locations_main_integrity_final_20260918/after.json)
- [Representative routes](../output/other_main_routes_20260917/summary.json)
- [Mini default verification](../data/mini_data/verification.json)
- [Cybench preparation](../output/ctf_docker/cybench_ready_only_preflight_20260917.json)
- [NYU preparation](../output/ctf_docker/nyu_ready_only_preflight_20260917.json)

Previous status documents are archived outside the active documentation tree.
Historical paid results, source materials, runtime evidence cited by task metadata,
and recovery backups are preserved.

Problem PDFs are canonical data assets under `data/raw`; mini inputs remain under `data/mini_data/raw`. Output holds validation/run reports, not canonical task PDFs. PDF delivery: 1649 main and 265 mini approved pages rendered successfully. See [location and access checks](../output/pdf_data_locations_repair_20260918.json).
