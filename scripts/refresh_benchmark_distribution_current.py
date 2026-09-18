"""Refresh the existing report without overwriting historical experiments or scoring prose."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from scripts.repair_data_catalog import Store
from build_mini_data import question_units
from write_benchmark_distribution_helpers import years_text

TARGET = 'docs/from_zhongzheng/benchmark_distribution_and_completed_runs_20260916.md'


def main():
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_distribution_docs_' + uuid.uuid4().hex[:8])
    old = store.path(TARGET).read_text(encoding='utf-8-sig')
    text = old
    text = re.sub(r'\n### Current readiness and delivery\n.*?(?=\n## Applied scope reductions)', '', text, flags=re.S)
    text = re.sub(r'\n## Refreshed saved-run inventory\n.*\Z', '', text, flags=re.S)
    timestamp = datetime.now(timezone.utc).isoformat()
    index = store.read('data/benchmarks/index.json')
    catalog = {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']}
    total = sum(map(len, catalog.values()))
    units = sum(question_units(r)[0] for rows in catalog.values() for r in rows)
    readiness = Counter(r['evaluation']['status'] for rows in catalog.values() for r in rows)
    assert total == index['total_records']
    editions = {
        'cfa_research_challenge': '1 retained original company/report packet (2016)',
        'debatebench': f"{len(catalog['debatebench'])} retained debate round/room transcript packets across multiple events",
        'eoes': f"{len(catalog['eoes'])} retained task packets; written scientific-analysis scope only",
        'mystery_hunt': f"{len({r['year'] for r in catalog['mystery_hunt']})} hunt years represented by {len(catalog['mystery_hunt'])} isolated puzzles; not complete hunts",
    }
    matched = set()
    lines = []
    for line in text.splitlines():
        match = re.match(r'^\| .*\(`([^`]+)`\) \|', line)
        if match and match[1] in catalog:
            cid = match[1]
            rows = catalog[cid]
            cells = [c.strip() for c in line.split('|')[1:-1]]
            assert len(cells) == 7
            years = sorted({r['year'] for r in rows if type(r.get('year')) is int})
            if cid == 'wsc_writing':
                years = sorted({y for r in rows for y in r.get('source_years', [])})
            cells[2:4] = [years_text(years), str(len(years))]
            cells[5:7] = [str(len(rows)), f"{sum(question_units(r)[0] for r in rows):,}"]
            if cid in editions:
                cells[1] = editions[cid]
                cells[4] = f'{len(rows)} isolated puzzle tasks' if cid == 'mystery_hunt' else f'{len(rows)} task/case packets; internal count not verified'
            line = '| ' + ' | '.join(cells) + ' |'
            matched.add(cid)
        lines.append(line)
    assert matched == set(catalog)
    text = '\n'.join(lines) + '\n'
    text = re.sub(r'Catalog inventory refreshed:.*?(?=\n\n)',
        f'Catalog inventory refreshed: {timestamp} (UTC). Active main catalog: {len(catalog)} tracks, {total:,} records, {units:,} mixed question/task units. Independent mini: 39 tracks, 109 records. Original generation date and prior paid-run tables below are retained as historical snapshots; the refreshed saved-run inventory at the end is current as of this update. See [current data status](../CURRENT_DATA_STATUS.md).', text, count=1)
    text = text.replace('including all 1,018 records', f'including all {total:,} records')
    text = text.replace('**Total question/task units: 3,334.**', f'**Total question/task units: {units:,}.**')
    text = text.replace('**Total: 39 tracks and 1,018 mixed-unit records.**', f'**Total: {len(catalog)} tracks and {total:,} mixed-unit records.**')
    status_block = '\n\n### Current readiness and delivery\n\n'
    status_block += '| Status | Records |\n|---|---:|\n'
    status_block += ''.join(f'| `{status}` | {readiness.get(status, 0)} |\n' for status in ['ready', 'ready_with_limitations', 'remote_judge_ready', 'not_ready'])
    status_block += '\nReadiness is not official-contest equivalence or live-model solving validation. The current audit has zero structural issues, with 21 unconfirmed semantic review candidates (12 HMMT score-scale differences; 9 Cybench public/judge file overlaps).\n\n'
    status_block += 'Canonical task PDFs live under `data/raw`; mini inputs are independent under `data/mini_data/raw`. No active PDF asset references `output/pdf`. Reviewed reader checks rendered 1,649 main and 265 mini approved pages. Mini preflight passed 479 asset checks and prepared 445 commands across five modes; no paid calls. See [integrity](../../output/pdf_locations_main_integrity_final_20260918/after.json) and [PDF location/access evidence](../../output/pdf_data_locations_repair_20260918.json).\n'
    text = text.replace('\n## Applied scope reductions', status_block + '\n## Applied scope reductions', 1)
    for cid, before in [('cfa_research_challenge',17), ('debatebench',32), ('eoes',19), ('mystery_hunt',117)]:
        pattern = rf'^\| `{cid}` \|.*$'
        row = f'| `{cid}` | {before} | {len(catalog[cid])} |'
        if re.search(pattern, text, re.M):
            text = re.sub(pattern, row, text, count=1, flags=re.M)
        else:
            text = text.replace('These are verified inventory differences.', row+'\n\nThese are verified inventory differences.', 1)
    text = text.replace('Earlier reduction rows below describe counts at those historical cleanup steps.', 'Previous counts are retained snapshot baselines; current counts above reflect the latest active catalog. Earlier reduction rows below describe historical cleanup steps, not current membership.')
    table_start = text.index('### Catalog changes since the previous table')
    table_end = text.index('These are verified inventory differences.', table_start)
    table_lines = [line for line in text[table_start:table_end].splitlines() if line.startswith('|')]
    text = text[:table_start] + '### Catalog changes since the previous table\n\n' + '\n'.join(table_lines) + '\n\n' + text[table_end:]
    text = text.replace('Records with runnable status labels: 109; runtime preflight is still required.', 'Records with runnable status labels: 109; the refreshed offline preflight prepared all 445 five-mode commands without failures. This does not establish live-model solving success.')
    text = text.replace('## Mini scoring (2026-09-17)', '## Mini scoring (retained 2026-09-17 scope; PDF delivery revalidated)')
    text = text.replace('The continuing extension runner does **not** read', 'The historical extension runner does **not** read')
    text = text.replace('The running queue has not been retargeted to the edited catalog.', 'This documentation update does not retarget, launch, resume, or modify any queue; current process activity is not inferred from historical dispatch configuration.')
    text = text.replace('Remaining `vallina_otc` jobs are paused by request.', 'The historical dispatch policy paused remaining `vallina_otc` solving; this is not a current process-status check.')
    text = text.replace('### Current-catalog membership subset at the historical snapshot (not a rescored cohort)', '### Retained historical membership subset (not recomputed or rescored)')
    text = text.replace('| Restrict the active evaluation subset to ready records | 151 `not_ready` records |', '| Restrict the active evaluation subset to runnable records | 0 `not_ready` records; already applied |')
    text = text.replace('| Exclude MIT Mystery Hunt from a compact first release | 117 records: 1 ready, 116 not_ready | Removes an unresolved track; retain its source archive. |', f"| Exclude MIT Mystery Hunt from a compact first release | {len(catalog['mystery_hunt'])} retained isolated puzzles: 1 ready, 28 ready_with_limitations | Optional format reduction; no longer an unresolved-track cleanup. |")
    text = text.replace('Recommended first reduction: use an evaluation-ready subset and remove overview/example material from that subset.', 'The runnable-status subset is already applied. Removing overview/example material remains an optional scope choice, not an automatic repair.')
    text = text.replace('The current dispatcher is', 'The dispatcher recorded at the historical snapshot is')
    text = text.replace('Ten non-ready document records remain excluded:', 'At that historical dispatch, ten non-ready document records were excluded:')
    text = text.replace('Catalog and mini inventory were refreshed on 2026-09-17. Paid-run, membership and dispatch counts remain historical snapshots. Membership filtering is reported separately from historical totals.', 'Catalog and PDF/mini delivery are refreshed above. Prior paid-run, membership and dispatch tables retain their earlier snapshots; refreshed run-file counts follow below, without rescoring.')
    text = text.replace('## PDF-text artifact completion snapshot', '## Retained prior PDF-text artifact completion snapshot')
    # Read saved outputs once, deduplicating unified references by resolved output directory.
    batches = ['tinker_task_based_arml_icpc_20260914', 'tinker_requested_remaining_20260915', 'tinker_requested_current_20260916']
    native, artifact, seen = [], [], set()
    source_hashes = {}
    def read_evidence(path):
        raw = path.read_bytes()
        source_hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw.decode('utf-8-sig'))
    for batch in batches:
        folder = ROOT / 'results' / batch
        for job in read_evidence(folder / 'registry.json')['jobs']:
            output = Path(job.get('output') or folder / 'runs' / job['id']).resolve()
            assert output.is_relative_to(ROOT / 'results')
            if output in seen:
                continue
            seen.add(output)
            is_artifact = job.get('kind') == 'artifact'
            result_path = output / ('result.json' if is_artifact else 'contest_session.json')
            result = read_evidence(result_path) if result_path.is_file() else {}
            grade = result.get('evaluation' if is_artifact else 'grade') or {}
            finished = result.get('status') in {'complete','unsubmitted'} if is_artifact else bool(result)
            row = dict(batch=batch, id=job['id'], competition=job['competition'], variant=job['variant'],
                output=output.relative_to(ROOT).as_posix(), saved_finished=finished,
                task_graded=result.get('graded') is True if is_artifact else grade.get('graded') is True,
                evaluation_pending=bool(result.get('evaluation_pending')), unsubmitted=result.get('status') == 'unsubmitted')
            ids = job.get('problem_ids') or ([job['problem_id']] if job.get('problem_id') else [])
            row['current_ids_eligible'] = bool(ids) and set(ids) <= {r['problem_id'] for r in catalog.get(job['competition'], [])}
            (artifact if is_artifact else native).append(row)
    section = ['\n## Refreshed saved-run inventory', '', f'Checked: {timestamp} (UTC). Read-only recount of three registered batches; deduplicated by resolved output directory. No experiment was rerun, rescored, or edited.', '',
        'Native saved/finished uses the existing `contest_session.json` presence contract; task-graded requires `grade.graded: true`. Evaluation-pending is reported separately and may overlap task-graded when only auxiliary stages are pending. Artifact finished requires final `result.json` status `complete` or `unsubmitted`; graded requires top-level `graded: true`. File presence is not a quality or official-score claim.', '']
    for label, records in [('Native registered outputs',native), ('PDF-text artifact registered outputs',artifact)]:
        section += [f'### {label}', '', '| Track | single_agent saved/registered | vallina_otc saved/registered | otc saved/registered | Task graded | Evaluation pending | Finished with current IDs |', '|---|---:|---:|---:|---:|---:|---:|']
        for cid in sorted({r['competition'] for r in records}):
            group = [r for r in records if r['competition'] == cid]
            values = []
            for variant in ['single_agent','vallina_otc','otc']:
                g = [r for r in group if r['variant'] == variant]
                values.append(f"{sum(r['saved_finished'] for r in g)}/{len(g)}")
            section.append(f'| {cid} | ' + ' | '.join(values) + f" | {sum(r['task_graded'] for r in group)} | {sum(r['evaluation_pending'] for r in group)} | {sum(r['saved_finished'] and r['current_ids_eligible'] for r in group)} |")
        section += ['', f"Total: {sum(r['saved_finished'] for r in records)} saved/finished out of {len(records)} unique registered outputs; {sum(r['task_graded'] for r in records)} task-graded; {sum(r['evaluation_pending'] for r in records)} evaluation-pending; {sum(r['unsubmitted'] for r in records)} unsubmitted.", '']
    section += ['Current-ID eligibility checks record membership only, not identical content, rubric, versions, or budgets. It is not a matched comparison cohort. Old historical tables and aggregate CSVs above were not overwritten.', '', 'Recount evidence: [saved-run inventory](../../output/benchmark_distribution_refresh_20260918.json).', '']
    text += '\n'.join(section)
    # Preserve the existing detailed mini-scoring section exactly apart from its dated heading.
    scoring_old = old.split('How the independent mini catalog grades',1)[1].split('## Data source and experiment scope alignment',1)[0]
    scoring_new = text.split('How the independent mini catalog grades',1)[1].split('## Data source and experiment scope alignment',1)[0]
    assert scoring_old == scoring_new
    for path, digest in source_hashes.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'Run evidence changed during recount; retry safely'
    report = dict(timestamp_utc=timestamp, tracks=len(catalog), records=total, question_task_units=units,
        readiness=dict(readiness), native=native, artifact=artifact, source_hashes=source_hashes, paid_model_calls=0)
    store.save('output/benchmark_distribution_refresh_20260918.json',report)
    store.save_text(TARGET,text)
    store.finish(dict(operation='refresh_distribution_document', records=total, historical_results='untouched'))
    print(dict(records=total, units=units, native_saved=sum(r['saved_finished'] for r in native),
               artifact_finished=sum(r['saved_finished'] for r in artifact), backup=str(store.backup)))


if __name__ == '__main__':
    main()
