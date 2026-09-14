# Agent Olympiad data

Canonical catalog: `benchmarks/index.json` (43 tracks, 1,720 records; 706 not_ready).

Latest verified follow-up checkpoint: `benchmarks/data_followup_audit_20260913.json`
and `docs/from_zhongzheng/data-followup-repairs-20260913.md`. The previous 8
control-character cases are closed; structural checks pass. Dataset-by-dataset
source review is still in progress. Consult the checkpoint timestamp and open-work
list; this is not universal semantic or end-to-end readiness certification.

`benchmarks/all_data_audit_20260913.json` and the corresponding
`all-data-audit-20260913.md` describe the earlier snapshot, before these follow-up repairs.

`benchmarks/` and `rules/` are canonical. `base/`, `last_exam/`, and `viz/` are synchronized derived artifacts. `raw/` preserves source material; `rubrics/` and `evaluators/` are judge-side inputs. `excluded/` contains historical backups.

Only assets explicitly labeled `agent_visible` enter task inputs. Read each record's `evaluation.status`, limitations, and score basis before use. Raw source trees can contain answers and must not be exposed wholesale to contestants.

Run `python scripts/repair_data_catalog.py --derived-only` after curated changes. Current counts are in `viz/summary.json`; readiness labels are not end-to-end validation. Existing split assignments are preserved; `unspecified` is unresolved. `not_verified` licenses do not grant redistribution rights.

## Source-verified content repair (2026-09-12)

Official local source files support the corrected ARML answers, restored grid questions, History Bowl answer boundaries, and refreshed PDF text previews. One byte-identical EOES record is an alias, not an independent task. Mystery Hunt answer variants are confirmed by archived official solutions, not removed as incorrect duplicates. Original sources remain unchanged. See `data/benchmarks/source_verified_repair_report.json`.

## Missing-year cleanup (2026-09-13)

At this cleanup snapshot, the catalog contained 43 tracks and 1,748 records, including 723 not_ready records; later source repairs changed the current total shown above. Twelve records lacking usable packets or scoring references were excluded; all valid raw material and full original rows are retained. Seventeen original source/marking files were recovered, and the IOL 2003 solution was relinked. ARML Power 2023-2025 now have reference-anchored rubrics. ARML 2022 remains not_ready because its printed weights total 39 despite the 40-point header, and problem 16 has no printed weight. Environmental, physical, image-delivery and source-isolation limitations are not treated as reasons to erase otherwise valid sources. See `data/benchmarks/not_ready_cleanup_report.json` and `data/benchmarks/unavailable_year_exclusions_20260913.json`.


## Formal-only IIOT and CCDC source repair (2026-09-13)

IIOT retains 31 international-final tasks; seven publisher-labeled 2017 practice tasks are archived in the exclusion manifest. Reference programs and official subtask weights are archived, but missing original judge material keeps the records not_ready. Six scanned CCDC packets have automatic, page-labeled OCR transcripts; consult the original PDFs for exact text, addresses, tables, and diagrams. CCDC 2022's missing network map and unavailable original execution/scoring environments remain unresolved.

Report: `data/benchmarks/iiot_ccdc_repair_20260913.json`. No execution tests were run.

## Cybench input separation (2026-09-13)

All 39 Cybench prompts now follow the upstream objective/target/file-list format;
README writeups and subtask hints are not contestant prompts. Six old descriptions
contained the exact final flag. The two generated layouts now include 115 reviewed
contestant attachments each, with 39 upstream final-answer references kept on the
judge side. One distribution config containing its service's final flag is withheld.
Original challenge bytes and all 39 records are preserved.

There are 13 static-artifact tasks and 26 service-related tasks. All remain
`not_ready`: isolated delivery, exact-match grading, and applicable services still
need runtime integration. Local readback verified both generated layouts, source
hashes and unchanged neighboring tracks; no challenge or solver was executed.
See `data/benchmarks/cybench_asset_repair_20260913.json` and
`data/raw/cybench/contestant_manifest_20260913.json` for per-task evidence and gaps.

## DebateBench source recovery (2026-09-13)

Official tournament pages now supply round-verified motions for 25 of 32 debates,
including 10 published infoslides. A blank slide field records its absence from
that round's published page, not proof that no slide ever existed. Cambridge's
two debates and Natolin's five still lack verified motion packets.

The unchanged publisher workbook uniquely matches 28 transcript titles; three
have no score row and LSE 2023 Round 5 has two conflicting rows, neither selected.
Scores are associated by speaker-role names, not workbook column order. Ten
transcripts have unresolved role-tag boundaries; their words and tags are kept.

The existing eight-speaker generation adaptation is retained. Original DebateBench
evaluates adjudication of archived human debates, so historical transcripts and
scores remain judge-only references, not gold targets for newly generated speeches.
All 32 records remain `not_ready`. Both generated layouts, 50 motion copies, all
45 original raw files, and the other 42 canonical tracks passed local readback.
No live evaluation was run. See `data/benchmarks/debatebench_source_repair_20260913.json`.

## IOAI historical source repair (2026-09-13)

Both historical task texts now have page-labeled, whitespace-only repairs against unchanged PDFs. All 26 original 2024 contestant files match the official task ZIP. Edition-specific task contracts replace future-edition restrictions and incorrect code/prediction output defaults. The 2024 image and video each have 40 raw points, while their final-ranking weights are 40:60; 80 is not an official final-ranking scale. The archived 2025 rules cover says version 2.4 despite the URL's 2.3 filename. Current public simulator/referee metadata is pinned, but its historical version and restricted licensing remain unresolved; no implementation or baseline code enters contestant inputs. Both records remain not_ready, with no live execution performed. See `data/benchmarks/ioai_source_repair_20260913.json`.

## NYU CTF contestant attachment repair (2026-09-13)

The existing 194-record subset now has 241 explicit contestant attachments in each
generated layout. Four DES2Bites attachment paths are restored from the publisher's
`Challenge -> dist` symlink, which the local Windows archive represented as a text
file. Two listed server-source attachments containing final flags are withheld
from contestant inputs and retained on the judge side. Published forensic and
reversing artifacts keep their original bytes, including embedded puzzle content.

All 194 upstream flag strings, existing prompts, splits, licenses and records are
preserved. Answer metadata now declares exact-string matching; the generic
normalized gold evaluator is not certified as a compatible CTF checker. All 194
remain `not_ready`: 56 have candidate static artifacts, 115 declare services, 22
declare only a host with unresolved runtime requirements, and one welcome poem
has no independent inputs after its existing flag redaction. No challenge was run.

Both generated layouts passed 482 attachment-copy checks and full source/neighbor
readback. At this repair snapshot, the global catalog contained 43 tracks and 1,741 records, with 716
`not_ready`. See `data/benchmarks/nyu_ctf_asset_repair_20260913.json` and
`docs/from_zhongzheng/nyu-ctf-data-repair-20260913.md`.

## Science Olympiad Solar System source repair (2026-09-13)

The 2017-2018 Division B example previously exposed its entire answer key inside
`problem_description`, despite marking the original PDF judge-only. The repaired
task now supplies a 12-page contestant PDF, its cover image and three image-sheet
PNGs. Two original answer pages are judge-only. Red instructor guidance is removed
from six retained pages; all other retained text and pixels are unchanged. The
original 18-page source remains intact and matches the official download by hash.

All 100 printed answer cells were recovered and checked with a second PDF parser.
The two answer pages each say 50/50, so the equal-value sample has 100 one-point
items in total. This corrects the earlier mistaken whole-exam 50-point reading.
Printed sets, ordering, ranges, historical answers and source typos are preserved.
The record now identifies its season, division and event, and both generated
layouts have matching scorecards and hidden references. All 14 output PDF pages
passed visual review; 10 staged attachment copies passed hash checks.

The task remains `not_ready`: image-aware evaluation, answer semantics and the
binding historical event rules are still unvalidated. The research roster of 15
is not claimed as the official number of active participants in this event.
At this repair snapshot, the global catalog contained 43 tracks and 1,741 records, including 716 `not_ready`.
See `data/benchmarks/science_olympiad_source_repair_20260913.json` and
`docs/from_zhongzheng/science-olympiad-data-repair-20260913.md`.

## Mystery Hunt reviewed packet repair (2026-09-13)

Thirteen 1999 puzzles and the 2006 Russian Brunch event now have explicit
contestant packets. One direct post-event answer disclosure was removed from
Russian Brunch; its missing invitation and presentation assets were recovered.
Archive solution navigation and answer-checking scripts are excluded. Original
HTML layout is retained, with only reviewed deletions and local-link changes.

Both generated layouts contain the same 32 allowlisted contestant files, with
64 successful attachment hash checks. Four original PDF pages and all fourteen
HTML pages were visually inspected. Nairobi's different HTML/PDF versions and
the publisher's warning are preserved without guessing a canonical ciphertext.
Prague's staged floppies and Charlotte Amalie's per-team scripts were not merged
into all-at-start packets. Original files, answers, splits, licenses and scores
are unchanged; all fourteen records remain `not_ready`.

Readback preserved all 1,605 original files, 247 unselected Mystery Hunt records,
and the other 42 tracks. Eighteen regression tests passed. The old 28 task trees
are archived with a manifest under `data/excluded/integrity_repair_20260913T154149Z`.
At this repair snapshot, the global catalog contained 43 tracks and 1,741 records, including 716 `not_ready`.
See `data/benchmarks/mystery_hunt_source_repair_20260913.json` and
`docs/from_zhongzheng/mystery-hunt-data-repair-20260913.md`.

## User-selected Mystery Hunt exclusion (2026-09-13)

The fourteen records repaired in the preceding batch were subsequently moved out of the active catalog at the user's request. Their original rows, answers, repaired packets and source material are retained under an exclusion manifest; they are not declared invalid. Mystery Hunt now has 247 records with an unchanged one-point weight each (247 total benchmark weight, not an official whole-hunt score). The 1999 weight sum is 2 instead of 15; 2006 is 13 instead of 14. All other years and remaining per-record weights are unchanged. The answer maps, scorecards, shared scoring metadata, both task catalogs and visualizations are synchronized. Historical run results remain immutable; any selected old result table needs a separate per-record projection, not numerator-preserving rescaling.

See `data/excluded/mystery_hunt_curated_exclusion_20260913/manifest.json`, `data/rubrics/mystery_hunt_active_score_summary.json`, and `data/benchmarks/mystery_hunt_exclusion_20260913.json`. Earlier sections describe historical snapshots.

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
