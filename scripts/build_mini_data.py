"""Build the deterministic seed-920, one-edition-per-track mini catalog."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE_INDEX = DATA / "benchmarks" / "index.json"
DEST = DATA / "mini_data"
SEED = 920
READY = {"ready", "ready_with_limitations", "remote_judge_ready"}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def question_units(row: dict) -> tuple[int, bool]:
    parts = (row.get("gold_label") or {}).get("parts") or []
    if parts:
        return len(parts), True
    questions = row.get("questions")
    if isinstance(questions, list) and questions:
        return len(questions), True
    for key in ("n_questions", "question_count"):
        value = row.get(key)
        if isinstance(value, int) and value > 0:
            return value, True
    return 1, False


def main():
    source_index = read(SOURCE_INDEX)
    rng = random.Random(SEED)
    selected_by_track = {}
    records = []
    total_units = explicit_units = fallback_units = 0

    for position, track in enumerate(source_index["olympiads"]):
        source_path = ROOT / track["benchmark_path"]
        rows = read(source_path)
        years = sorted({
            int(row["year"])
            for row in rows
            if str(row.get("year", "")).isdigit()
        })
        if len(years) >= 2:
            selected_years = rng.sample(years, 1)
            selected = [
                row for row in rows
                if str(row.get("year", "")).isdigit()
                and int(row["year"]) in selected_years
            ]
            selection_basis = "one_random_year"
        elif years:
            selected_years = years
            selected = [
                row for row in rows
                if str(row.get("year", "")).isdigit()
                and int(row["year"]) in selected_years
            ]
            selection_basis = "only_available_year"
        else:
            sample_size = min(1, len(rows))
            chosen_ids = {
                row["problem_id"]
                for row in rng.sample(sorted(rows, key=lambda row: row["problem_id"]), sample_size)
            }
            selected_years = []
            selected = [row for row in rows if row["problem_id"] in chosen_ids]
            selection_basis = "one_random_record_no_year_available"

        statuses = Counter(
            (row.get("evaluation") or {}).get("status", "missing")
            for row in selected
        )
        track_units = track_explicit = track_fallback = 0
        record_rows = []
        for row in selected:
            units, explicit = question_units(row)
            track_units += units
            if explicit:
                track_explicit += units
            else:
                track_fallback += 1
            record_rows.append({
                "problem_id": row["problem_id"],
                "year": row.get("year"),
                "evaluation_status": (row.get("evaluation") or {}).get("status", "missing"),
                "question_units": units,
                "question_count_explicit": explicit,
            })

        cid = track["id"]
        relative = Path("benchmarks") / cid / "benchmark.json"
        write(DEST / relative, selected)
        selected_by_track[cid] = selected
        total_units += track_units
        explicit_units += track_explicit
        fallback_units += track_fallback
        records.append({
            "index_position": position,
            "competition_id": cid,
            "selection_basis": selection_basis,
            "available_years": years,
            "selected_years": selected_years,
            "selected_record_ids": [row["problem_id"] for row in selected],
            "selected_records": len(selected),
            "question_units": track_units,
            "explicit_question_units": track_explicit,
            "whole_task_fallback_units": track_fallback,
            "evaluation_status_counts": dict(sorted(statuses.items())),
            "source_benchmark_path": track["benchmark_path"],
            "source_benchmark_sha256": digest(source_path),
            "mini_benchmark_path": f"data/mini_data/{relative.as_posix()}",
            "records": record_rows,
        })

    mini_tracks = []
    for track in source_index["olympiads"]:
        cid = track["id"]
        selected = selected_by_track[cid]
        statuses = Counter((row.get("evaluation") or {}).get("status", "missing") for row in selected)
        updated = dict(track)
        updated.update(
            benchmark_path=f"data/mini_data/benchmarks/{cid}/benchmark.json",
            problems_collected=len(selected),
            evaluation_status_counts=dict(sorted(statuses.items())),
            mini_selection_seed=SEED,
        )
        mini_tracks.append(updated)
    mini_index = {
        **{key: value for key, value in source_index.items() if key != "olympiads"},
        "description": f"Agent Olympiad mini_data: seed-920 random one-edition subset of {len(mini_tracks)} active tracks.",
        "olympiads": mini_tracks,
        "total_records": sum(len(value) for value in selected_by_track.values()),
        "selection_manifest": "data/mini_data/selection_manifest.json",
        "asset_storage": "shared_canonical_data_paths",
    }
    write(DEST / "benchmarks" / "index.json", mini_index)

    manifest = {
        "schema_version": 1,
        "selection_algorithm_version": "seeded_one_edition_v1",
        "selection_name": "seed_920_one_edition_per_competition",
        "seed": SEED,
        "random_generator": "python random.Random (MT19937)",
        "track_order": "data/benchmarks/index.json olympiads order",
        "year_population_order": "ascending distinct integer years",
        "sampling": "random.sample(years, 1)",
        "one_year_policy": "retain the only year without consuming RNG state",
        "missing_year_policy": "sample one record by problem_id population using the same RNG",
        "record_policy": "retain every record belonging to the selected year",
        "internal_question_policy": "retain every internal question/part in each selected record",
        "source_index": "data/benchmarks/index.json",
        "source_index_sha256": digest(SOURCE_INDEX),
        "tracks": records,
        "totals": {
            "competitions": len(records),
            "records": sum(row["selected_records"] for row in records),
            "question_or_task_units": total_units,
            "explicit_question_units": explicit_units,
            "whole_task_fallback_units": fallback_units,
            "runnable_status_records": sum(
                1 for rows in selected_by_track.values() for row in rows
                if (row.get("evaluation") or {}).get("status") in READY
            ),
        },
        "path_policy": {
            "benchmarks": "copied into data/mini_data/benchmarks",
            "raw_rules_rubrics_judge_assets": "referenced from canonical data paths in the same repository",
            "visibility": "agent_visible and judge_only roles are unchanged",
        },
    }
    write(DEST / "selection_manifest.json", manifest)

    lines = [
        "# Agent Olympiad mini_data",
        "",
        "## Random selection policy",
        "",
        "This mini catalog is randomly sampled and exactly reproducible. It uses `random.Random(920)` and processes competitions in the order stored in `data/benchmarks/index.json`. For each competition, it samples one year from the sorted available years, then retains every record and internal question in that selected year.",
        "",
        "A competition with only one available year retains that year. WSC Writing has no year metadata, so the same random generator samples one record ID. Existing split labels, evaluation readiness, and `agent_visible`/`judge_only` roles are preserved. One selected year may contain several published packets, categories or tasks; these remain intact.",
        "",
        "The mini benchmark JSON files are stored here. Raw files, rules, rubrics, gold, and judge references continue to use their canonical `data/...` paths in this repository; this avoids a second mutable copy and keeps answer isolation unchanged.",
        "",
        "## Selected competitions and years",
        "",
        "| Competition | Randomly selected year(s) or records | Records | Question/task units | Status counts |",
        "|---|---|---:|---:|---|",
    ]
    for row in records:
        choice = ", ".join(map(str, row["selected_years"]))
        if not choice:
            choice = ", ".join(row["selected_record_ids"])
        statuses = "; ".join(f"{key}: {value}" for key, value in row["evaluation_status_counts"].items())
        lines.append(
            f"| {row['competition_id']} | {choice} | {row['selected_records']} | "
            f"{row['question_units']} | {statuses} |"
        )
    totals = manifest["totals"]
    lines += [
        "",
        "## Totals",
        "",
        f"- Competitions: {totals['competitions']}",
        f"- Top-level records: {totals['records']}",
        f"- Question/task units: {totals['question_or_task_units']}",
        f"- Explicit internal questions/parts: {totals['explicit_question_units']}",
        f"- Whole-record task fallbacks: {totals['whole_task_fallback_units']}",
        f"- Records with a runnable readiness label: {totals['runnable_status_records']}",
        "",
        "`question/task units` counts explicit structured parts where present; a record without an explicit internal count contributes one whole-task unit. A runnable readiness label still requires runtime preflight.",
        "",
        "Full record IDs, source hashes, per-record counts, and the precise RNG contract are in `selection_manifest.json`.",
    ]
    (DEST / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(manifest["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
