---
license: other
task_categories:
  - text-generation
  - question-answering
language:
  - en
tags:
  - multi-agent
  - olympiad
  - team-competition
  - benchmark
pretty_name: Agent Olympiad Benchmarks
size_categories:
  - 1K<n<10K
---

# Agent Olympiad — Processed Team Competition Benchmarks

Extracted multi-agent team competition problems for the **Agent Olympiad** research project (DAPLab).

## Contents

- Per-competition folders with `benchmark.json` (records with explicit evaluation readiness)
- Catalog: `index.json` — each olympiad lists `benchmark_path` (extracted JSON)
  and `rule_card_path`, record counts, evaluation units, and status counts.

The catalog retains 43 track configurations, all with catalog records after
subsequent curated exclusions (currently 1,720 records). Catalog presence does not mean
evaluation readiness. It is intentionally mixed-unit. Every record
declares `eval_unit`: `session` denotes a packet/session, while `question` and
`problem` denote individual questions or challenges. Record counts do not imply
complete contest sessions or evaluator readiness. Use each record's `evaluation`
status and limitations before selecting tasks.

Every record includes `split`, `license`, and `provenance`. `unspecified` means
no split has been assigned; `not_verified` is an unresolved license, not a grant
of redistribution rights. Provenance records source locations and asset hashes;
it does not itself establish authorship, licensing, or source completeness.
The structural repair script preserves existing curated metadata. Source or
asset changes require a separate provenance review.

## Formal-packet review and scoring tables (historical restoration snapshot)

`data/excluded/formal_packet_review_20260911/manifest.json` preserves the full
113 previously removed records, reasons, and raw-file inventories for recovery.
109 non-Envirothon records have now been restored for user review: CFA 19,
DebateBench 32, IJSO 9, and Odyssey 49. Envirothon remains excluded. Restored
records preserve the original exclusion reason and remain not ready when the
original task is absent/incomplete. Raw files for restored tracks were not
deleted. At that restoration stage, missing answers or an unavailable live judge
alone were not grounds for removing a problem. The subsequent user-approved
2026-09-13 policy reversibly excludes years with no verified edition-specific
answer reference after source checks; an unavailable runtime alone still does
not justify removing valid source material. Readable scanned PDFs remain valid sources;
IOL 2003 and 2012 require complete PDF images rather than extracted text alone.
The Odyssey practice packet and restored synopses are not complete official
yearly contests. Their evaluation remains deferred.

Same-competition cross-year rubric reuse is permitted and explicitly recorded
in `evaluation.rubric_reuse`. Other-year answer keys are never substituted.
IJSO 2007/2008 previously used the shared 40-point report rubric without an official
answer anchor; those years are now excluded from active records and scorecards.
IChTo uses the 2025 scientific subcriteria as a 9-point report
subtotal across editions, not official tournament TP/RP. These are limited
benchmark adaptations. EOES and GCCH protocols may be reused across editions,
but still lack executable numeric criteria; earlier ready labels are corrected.
No unpublished official weights have been invented. See
`restoration_review_20260911.json` for restored counts, policy, and readiness.

`data/rubrics/task_scorecards/<track>.json` provides judge-only, per-record
scoring tables keyed by `problem_id`; each benchmark evaluation links to its
table and key. Tables retain numeric criteria, maxima, floors, source hashes,
answer-key paths, judge-only references, and evaluation limitations. Protocols
without published point weights remain explicitly nonnumeric. These tables
index existing evaluator inputs; they do not replace executable judges or make
an incomplete evaluation ready.

Each problem typically includes:

- `problem_id`, `competition`, `year`, `task_type`, `team_size`
- `problem_description`
- `gold_label` (`expected_answer` and/or `grading_rubric` when available)
- source metadata (`source_url`, `source_file`, `solution_file`)

Subsampled question-level tracks (for example Science Bowl, QANTA, Cybench)
retain only the promoted `benchmark.json`; full pre-subsample inventories are
not kept in-tree. Raw source packets, where available, remain under `data/raw/`.

## Intended use

Benchmarking **multi-agent AI teams** on olympiad-style team tasks (paper contests, programming, debate, mystery hunt, science bowl, etc.).

## Notes

- Source materials remain subject to their original competition licenses/terms.
- This dataset is for research evaluation; do not redistribute restricted contest materials beyond the terms of the original sources.

## Integrity repair (September 2026)

IYPT sources use publisher edition headings and retain local illustrations. HMMT Guts includes both seasons of the verified 45-session archive. HMMT 2024 uses printed weights; other Guts records use an explicitly normalized reference-anchored rubric. Rule scoring defaults have explicit per-record overrides. Generated task inputs contain only agent-visible assets. External source references are materialized under data/raw/external. Unspecified splits and unverified licenses remain unresolved.

Repair report: `integrity_repair_report.json`. Regenerate packages and figures with `python scripts/repair_data_catalog.py --derived-only`.

## Source-verified content repair (2026-09-12)

Official local source files support the corrected ARML answers, restored grid questions, History Bowl answer boundaries, and refreshed PDF text previews. One byte-identical EOES record is an alias, not an independent task. Mystery Hunt answer variants are confirmed by archived official solutions, not removed as incorrect duplicates. Original sources remain unchanged. See `data/benchmarks/source_verified_repair_report.json`.

## Missing-year cleanup (2026-09-13)

At this cleanup snapshot: 43 tracks, 1,748 records, including 723 not_ready records; later source repairs and user-selected exclusions changed these totals. Twelve records lacking usable packets or scoring references were excluded; all valid raw material and full original rows are retained. Seventeen original source/marking files were recovered, and the IOL 2003 solution was relinked. ARML Power 2023-2025 now have reference-anchored rubrics. ARML 2022 remains not_ready because its printed weights total 39 despite the 40-point header, and problem 16 has no printed weight. Environmental, physical, image-delivery and source-isolation limitations are not treated as reasons to erase otherwise valid sources. See `data/benchmarks/not_ready_cleanup_report.json` and `data/benchmarks/unavailable_year_exclusions_20260913.json`.


## Formal-only IIOT and CCDC source repair (2026-09-13)

IIOT retains 31 international-final tasks; seven publisher-labeled 2017 practice tasks are archived in the exclusion manifest. Reference programs and official subtask weights are archived, but missing original judge material keeps the records not_ready. Six scanned CCDC packets have automatic, page-labeled OCR transcripts; consult the original PDFs for exact text, addresses, tables, and diagrams. CCDC 2022's missing network map and unavailable original execution/scoring environments remain unresolved.

Report: `data/benchmarks/iiot_ccdc_repair_20260913.json`. No execution tests were run.

## Cybench input separation (2026-09-13)

The 39 Cybench records have separate contestant inputs and judge references.
Prompts use the upstream objective/target/file-list format, replacing README
writeups; six previous descriptions contained the exact final flag. Both generated
layouts contain 115 reviewed attachments, and the answer coverage map now links
39 final-subtask answers directly to upstream metadata. Original files and record
membership are preserved. One public service config containing the final flag is
withheld and its missing dependency is recorded.

The 13 static-artifact and 26 service-related tasks remain `not_ready` pending
isolated delivery, exact-match grading and applicable service integration. Readback
checked 230 attachment copies, 1,174 unchanged upstream files and the other 42
canonical tracks. No challenge, solver or live service was executed.
See `cybench_asset_repair_20260913.json` for the detailed repair and remaining gaps.

## DebateBench source recovery (2026-09-13)

Recovered official round motions for 25 of 32 debates, including 10 published
infoslides, with exact HTML snapshots and round-local extraction checks. The
remaining two Cambridge and five Natolin packets are unresolved. A published
blank/absent infoslide is not evidence that no slide ever existed.

The original workbook and all transcripts remain unchanged. Twenty-eight titles
have one matching score row; three have none and LSE 2023 Round 5 has conflicting
rows. Speaker scores use role-name mapping rather than worksheet column order;
10 transcripts retain unresolved role-tag boundaries without guessed corrections.

All 32 records retain the existing speech-generation task and `not_ready` status.
Historical transcripts and scores are judge-only references: the publisher's
original adjudication task is distinct from generating new speeches. Both derived
layouts passed motion-only input checks, with 50 verified motion copies, 45
unchanged original raw files, and no changes to the other 42 canonical tracks.
No live evaluation was run. See `debatebench_source_repair_20260913.json` and
`data/rubrics/debatebench_historical_scores_20260913.json`.

## IOAI historical source repair (2026-09-13)

Both historical task texts now have page-labeled, whitespace-only repairs against unchanged PDFs. All 26 original 2024 contestant files match the official task ZIP. Edition-specific task contracts replace future-edition restrictions and incorrect code/prediction output defaults. The 2024 image and video each have 40 raw points, while their final-ranking weights are 40:60; 80 is not an official final-ranking scale. The archived 2025 rules cover says version 2.4 despite the URL's 2.3 filename. Current public simulator/referee metadata is pinned, but its historical version and restricted licensing remain unresolved; no implementation or baseline code enters contestant inputs. Both records remain not_ready, with no live execution performed. See `data/benchmarks/ioai_source_repair_20260913.json`.

## Current user-selected Mystery Hunt subset (2026-09-13)

At the Mystery Hunt exclusion snapshot: 43 tracks, 1,727 records, including 702 not_ready. Mystery Hunt has 247 active rows. Fourteen source-reviewed rows were reversibly excluded by user choice, not declared invalid; their manifest is `data/excluded/mystery_hunt_curated_exclusion_20260913/manifest.json`. The active one-point-per-record benchmark denominator is 247; full per-year membership and score bounds are in `data/rubrics/mystery_hunt_active_score_summary.json`. Official full-hunt scoring, evaluator readiness, other tracks and surviving problem weights are unchanged.

## IJSO answerless-year exclusion (2026-09-13)

At the IJSO exclusion snapshot: 43 tracks, 1,722 records, including 699 not_ready. IJSO Practical has 15 active years (11 ready_with_limitations and 4 not_ready). Years 2005, 2007, 2008, 2024 and 2025 were reversibly excluded because no verified edition-specific answer reference was recovered from checked sources. 2011 remains not_ready with Biology/Chemistry answers and a missing Physics reference. All original files and historical scores are preserved; existing records, scoring capacities and other competitions are unchanged. Active scorecards and task entries omit excluded years; proxy rubric capacities are not pooled as official points.

See `data/excluded/ijso_answerless_years_20260913/manifest.json`, `data/rubrics/ijso_practical_active_score_membership.json`, and `data/benchmarks/ijso_answerless_exclusion_20260913.json`. Earlier totals are historical snapshots.

## IOL source and score repair (2026-09-13)

At the first IOL repair snapshot: 43 tracks, 1,720 records, including 702 not_ready. IOL has 18 active records (12 ready, 1 ready_with_limitations, 5 not_ready). 2004 and 2005 were reversibly excluded after HTML masquerading as solutions was identified and no genuine answer recovered. 2007 and 2024 now use genuine partial graphical references, not HTML; 2014 now includes its Armenian supplement; 2016 includes all 114 original WAV recordings. Multilingual .m references are not Mongolian editions. 2016 printed points are 114+6=120; 2024 has 90 regular points plus a separate conditional 10-point tie-breaker. 2007, 2016 and 2024 remain not_ready for incomplete references/unvalidated multimodal grading. Original sources, historical results, 14 other IOL records and 42 other tracks are preserved. See `data/benchmarks/iol_source_repair_20260913.json`, `data/excluded/iol_answerless_years_20260913/manifest.json`, `data/rubrics/iol_team_active_score_membership.json`. Earlier totals are historical snapshots.

## IOL follow-up source repair (2026-09-13)

At the prior IOL follow-up snapshot: 43 tracks, 1,720 records, including 705 not_ready. IOL still has 18 years (9 ready, 1 ready_with_limitations, 8 not_ready); no years were excluded in this batch. 2011 initial input now contains only original pages 1-2; five later hint releases remain withheld in the preserved archive. 2019 now includes all 18 official example AVIs. 2022 now has official part subtotals of 25+25+25+25=100, not the generic 50/30/20 proxy split. All three records are not_ready pending timed-release or image/video/script-aware runtime and grading validation. Original references and historical results are preserved. See `data/benchmarks/iol_followup_repair_20260913.json` and `docs/from_zhongzheng/iol-followup-repair-20260913.md`.

## IOL 2017 emoji repair (2026-09-13)

Current catalog: 43 tracks, 1,720 records, including 706 not_ready. IOL remains at 18 years (8 ready, 1 ready_with_limitations, 9 not_ready); no years were excluded. 2017 now has clean public descriptions and two original-page PNGs; judge-only structured references preserve all 93 matches and four unmatched-emoji descriptions. Its old 100-point generic proxy is disabled, official weights remain unknown, and status is not_ready pending full dictionary/grammar scoring and image-aware runtime validation. Original PDFs and historical results are preserved. See `data/benchmarks/iol_emoji_repair_20260913.json` and `docs/from_zhongzheng/iol-emoji-repair-20260913.md`.

## IOL 2012 Lao reference repair (2026-09-13)

2012 is retained: the official solution contains all 57 country identifications and pronunciations. The empty judge-assets link is repaired, the public input now includes the original Lao page image, and the judge-only reference includes a 57-country ID map and the original pronunciation image. Flattened phonetic text is no longer treated as gold. Official weights remain unknown; the old 100-point proxy is disabled. 2012 remains not_ready pending image-aware delivery and pronunciation grading. Catalog membership and readiness counts are unchanged (43 tracks, 1,720 records; IOL 18 years; 706 not_ready globally). See `data/benchmarks/iol_lao_repair_20260913.json` and `docs/from_zhongzheng/iol-lao-repair-20260913.md`.
