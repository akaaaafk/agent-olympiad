"""Aggregate Qwen/Tinker Agent Olympiad batches into stable CSV/JSON outputs."""
from __future__ import annotations

import collections
import csv
import json
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contest_reporting import REPORT_FIELDS, report_row
from saved_run_metrics import flat_metrics, coordination_complete, valid_coordination

BATCHES = [
    ("tinker_task_based_arml_icpc_20260914", ROOT / "results" / "tinker_task_based_arml_icpc_20260914"),
    ("tinker_requested_remaining_20260915", ROOT / "results" / "tinker_requested_remaining_20260915"),
]
if (ROOT / 'results/tinker_requested_current_20260916/registry.json').exists():
    BATCHES.append(('tinker_requested_current_20260916', ROOT / 'results/tinker_requested_current_20260916'))
for registry in sorted((ROOT / 'results').glob('*/registry.json')):
    if registry.parent.name not in {name for name, _ in BATCHES}:
        BATCHES.append((registry.parent.name, registry.parent))

BASE_FIELDS = [
    "batch",
    "job_id",
    "competition",
    "session_id",
    "variant",
    "status",
    "task_count",
    "problem_ids",
    "limitations",
    "result_path",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def lane_statuses(batch_dir: Path):
    statuses = {}
    for path in sorted(batch_dir.glob("lane*.json")):
        try:
            rows = read_json(path)
        except Exception:
            continue
        for row in rows:
            job_id = row.get("id")
            status = row.get("status")
            if job_id and status in {"running", "skipped_by_variant", "failed"}:
                statuses[job_id] = status
    return statuses


def aggregate_batch(batch_name: str, batch_dir: Path):
    registry = read_json(batch_dir / "registry.json")
    lane_state = lane_statuses(batch_dir)
    rows = []
    for job in registry.get("jobs", []):
        # Unified queue also references older outputs for resume/evaluation.
        # Count those in their original batches rather than duplicating them.
        if job.get('output') and Path(job['output']).parent != batch_dir / 'runs':
            continue
        directory = batch_dir / 'runs' / job['id']
        artifact = (job.get('kind') == 'artifact' or job.get('route') in {'document', 'slides'}
                    or batch_name == 'tinker_mcm_pdftext_20260916')
        result_path = directory / ('result.json' if artifact else 'contest_session.json')
        base = {
            "batch": batch_name,
            "job_id": job["id"],
            "competition": job.get("competition"),
            "session_id": job.get("session_id"),
            "variant": job.get("variant"),
            "task_count": job.get("task_count"),
            "problem_ids": json.dumps(job.get("problem_ids", []), ensure_ascii=True),
            "limitations": json.dumps(job.get("limitations", []), ensure_ascii=True),
            "result_path": str(result_path) if result_path.exists() else "",
        }
        metrics = {field: "" for field in REPORT_FIELDS}
        if result_path.exists():
            result = read_json(result_path)
            contest = read_json(directory / 'contest_session.json') if artifact else result
            sidecar_path = directory / 'coordination_required.json'
            sidecar = read_json(sidecar_path) if sidecar_path.is_file() else None
            if sidecar and not coordination_complete(directory, result):
                sidecar = {'status': 'pending', 'error': 'Required collaboration evaluation missing or stale'}
            if artifact and sidecar is None:
                sidecar = {'status': 'pending', 'error': 'Required collaboration evaluation missing'}
            status = result.get('status', 'complete')
            if result.get('evaluation_pending') or sidecar and sidecar.get('status') not in {'complete', 'not_applicable'}:
                status = 'evaluation_pending'
            elif not artifact and (result.get('grade') or {}).get('graded') is not True:
                status = 'ungraded'
            elif (not artifact and sidecar is None and contest.get('system_variant') != 'single_agent'
                  and not valid_coordination(contest.get('coordination'))):
                status = 'evaluation_pending'
            metrics.update(flat_metrics(contest, result if artifact else None, sidecar))
            settings = (contest.get('run_identity') or {}).get('settings') or {}
            base['competition'] = base['competition'] or settings.get('competition_id')
            base['variant'] = base['variant'] or contest.get('system_variant')
            base['session_id'] = base['session_id'] or contest.get('session_id')
            base['problem_ids'] = json.dumps(job.get('problem_ids') or [job.get('problem_id')], ensure_ascii=True)
        else:
            status = lane_state.get(job["id"], "unfinished")
            state_path = batch_dir / 'states' / (job['id'] + '.json')
            if state_path.exists():
                status = read_json(state_path).get('status', status)
        rows.append({**base, "status": status, **metrics})
    return rows


def main():
    rows = []
    for batch_name, batch_dir in BATCHES:
        rows.extend(aggregate_batch(batch_name, batch_dir))
    preferred = ROOT / 'results/tinker_requested_current_20260916'
    out_dir = (preferred if preferred.is_dir() else BATCHES[-1][1]) / 'aggregates'
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fields = BASE_FIELDS + [field for field in REPORT_FIELDS if field not in BASE_FIELDS]
    csv_path = out_dir / f"combined_results_{stamp}.csv"
    latest_csv = out_dir / "combined_results_latest.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    latest_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")

    summary = {
        "generated_at": stamp,
        "total": len(rows),
        "counts": dict(collections.Counter(row["status"] for row in rows)),
        "by_batch": {},
        "by_competition": {},
        "by_variant": {},
        "csv": str(latest_csv),
    }
    for key_name, field in (("by_batch", "batch"), ("by_competition", "competition"), ("by_variant", "variant")):
        grouped = collections.defaultdict(collections.Counter)
        for row in rows:
            grouped[row[field]][row["status"]] += 1
        summary[key_name] = {key: dict(counter) for key, counter in sorted(grouped.items())}
    json_path = out_dir / f"combined_results_summary_{stamp}.json"
    latest_json = out_dir / "combined_results_summary_latest.json"
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    json_path.write_text(payload + "\n", encoding="utf-8")
    latest_json.write_text(payload + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
