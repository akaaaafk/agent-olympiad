# Artifact-only scope applied on 2026-09-16

| Track | Active records | Assessed artifact | Task score |
|---|---:|---|---|
| ijso_practical | 9 | Shared written report | Archived-material-anchored 40-point benchmark rubric |
| iypt | 16 | Research slides | Normalized 100-point benchmark rubric, not Physics Fight points |
| itym | 15 | Research paper | Normalized 100-point benchmark rubric |
| ichto | 9 | Written chemistry report | 2025 scientific criteria reused across years, 9-point subtotal |
| wsc_writing | 42 | One benchmark essay | Existing route retained |

Physical measurement, instrument operation, live oral defense/debate, external opponents/reviewers, official jury coefficients/aggregation, TP/RP conversion, and team rankings are outside these artifact-only routes. Task LLM judge scoring and the existing separate teammate collaboration evaluation remain enabled. No new paid experiments or historical regrading were performed.

History Olympiad's exact 28 canonical records were archived outside the checkout and removed from the active benchmark index, both generated task catalogs, task directories, input manifests, and active scorecards. The active catalog contains 39 tracks and 1,053 records. Raw sources and historical/frozen experiments remain historical evidence.

## IOL 2014 verification

This request concerns `iol_team_2014`; the full IOL track still contains six records. The [official archive](https://ioling.org/problems/2014/) labels both supplements and solutions Multilingual. The original English problem PDF has four pages; the alphabetically ordered Armenian sentence supplement has three pages. Both are included in contestant inputs, along with the existing derived PDF bundle. The official solution remains judge-only.

The [official results](https://ioling.org/results/2014) report team trophy scores of 29, 24, and 23.5. Fractional scores establish that non-integer scoring occurred, but do not establish the maximum, per-correspondence weights, or partial-credit algorithm. The public problem, supplement, and solution PDFs do not provide a marking scheme. Therefore the official maximum and partial-credit rule remain null; the 100-point worked-answer rubric remains an explicitly identified benchmark proxy. This is a bounded public-source verification, not proof that no marking scheme exists elsewhere.

## Validation

- Both generated layouts contain exactly the canonical set of 1,053 task IDs; neither contains active History tasks or input-manifest entries.
- Affected contestant input file SHA-256 hashes match their declared assets. IOL original English PDF and supplement are present in both layouts.
- Twelve focused existing tests passed for conditional judging, scorecard/catalog consistency, measurement validation, and domain preparation.
- Four affected preparation tools execute successfully. IChTo no longer requires opposition, reporter-response, or live review fields.
- The broader existing tool suite fails on unrelated Codeforces catalog removal and WSC tool allowlisting; requested changes do not repair those contracts. Two named historical rule-test modules are absent from this checkout.
- Full-package rebuild hit Windows resource exhaustion; a bounded rebuild of the five affected tracks (55 tasks, 81 contestant assets) completed and was verified instead.

Deletion manifest and canonical backups: `E:/agent_olympiad/dataset_backups/integrity_repair_20260916T202432Z`. Derived package archive: `E:/agent_olympiad/dataset_backups/integrity_repair_20260916T202505Z`.
