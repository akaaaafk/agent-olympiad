"""Publish current verified defaults; archive replaced status snapshots."""
from collections import Counter
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integrity-report', default='output/main_integrity_final_20260917/after.json')
    parser.add_argument('--repair-report')
    parser.add_argument('--mini-verification', default='output/mini_post_main_repair_20260917.json')
    parser.add_argument('--pdf-location-report')
    args = parser.parse_args()
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_latest_status_' + uuid.uuid4().hex[:8])
    integrity = store.read(args.integrity_report)
    for relative, digest in integrity['source_snapshot'].items():
        assert store.sha(relative) == digest, 'Main source changed since audit'
    assert not integrity['issues']
    mini = store.read(args.mini_verification)
    assert mini['passed'] and mini['all_jobs_environment_ready']
    routes = store.read('output/other_main_routes_20260917/summary.json')
    assert routes['counts'] == {'PASS': 135}
    store.save('data/mini_data/verification.json', mini)
    index_hash = store.sha('data/benchmarks/index.json')
    selection = store.read('data/mini_data/selection_manifest.json')
    membership = [(t['competition_id'], t['selected_record_ids']) for t in selection['tracks']]
    selection.setdefault('latest_workspace_sync', {}).update(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        canonical_index_sha256=index_hash, membership_preserved=True,
        verification_report='data/mini_data/verification.json',
        scope='Current index binding and verified mini defaults; original source_index_sha256 retained as provenance.')
    store.save('data/mini_data/selection_manifest.json', selection)
    assert membership == [(t['competition_id'], t['selected_record_ids']) for t in selection['tracks']]
    mini_index = store.read('data/mini_data/benchmarks/index.json')
    mini_count = sum(len(store.read(t['benchmark_path'])) for t in mini_index['olympiads'])
    statuses = integrity['status_counts']
    current = 'docs/CURRENT_DATA_STATUS.md'
    text = f'''# Current dataset status

Updated: {datetime.now(timezone.utc).isoformat()}

Main data: {integrity['active_tracks']} competitions, {integrity['active_records']} records.
Mini data: {len(selection['tracks'])} competitions, {mini_count} records; selected membership preserved.

| Main readiness | Records |
| --- | ---: |
'''
    text += ''.join(f'| {key} | {value} |\n' for key, value in statuses.items())
    text += '''
Cybench retains 38 validated tasks (2022: 8; 2023: 10; 2024: 20).
NYU CTF retains 44 validated tasks, including 2021 Interoperable.
Unresolved CTF tasks were removed from active membership and archived.
IOAI currently contains only 2025 Factory, scored as static program/design review.
IIOT is static source review; CCDC is written-plan review. These are not official runtime scores.
WRO simulation is excluded.

Latest checks:

- Main integrity: zero structural issues; 11,858 unique file hashes checked.
- Additional 27 competitions: 135 representative five-baseline offline route cases passed.
- Mini: 479 asset checks, zero errors; 445 prepared commands, zero pending/failed.
- CTF: Cybench 190 and NYU 220 five-baseline preparation checks passed.
- Mini dependency snapshots refreshed for 18 changed JSON files.

Offline/mock checks do not establish live-model solving success or official contest equivalence.
151 non-CTF records remain not_ready. 21 semantic review candidates remain
(12 printed-total versus answer-weight differences; 9 identical public/judge asset hashes).
Those candidates are not certified errors and were not silently changed.

Current evidence:

- [Main integrity](../output/main_integrity_final_20260917/after.json)
- [Representative routes](../output/other_main_routes_20260917/summary.json)
- [Mini default verification](../data/mini_data/verification.json)
- [Cybench preparation](../output/ctf_docker/cybench_ready_only_preflight_20260917.json)
- [NYU preparation](../output/ctf_docker/nyu_ready_only_preflight_20260917.json)

Previous status documents are archived outside the active documentation tree.
Historical paid results, source materials, runtime evidence cited by task metadata,
and recovery backups are preserved.
'''
    text = text.replace('151 non-CTF records remain not_ready.', str(statuses.get('not_ready', 0))+' non-CTF records remain not_ready.')
    text = text.replace('11,858 unique file hashes', f"{integrity['unique_files_hashed']:,} unique file hashes")
    text = text.replace('../output/main_integrity_final_20260917/after.json', '../'+args.integrity_report)
    if args.repair_report:
        repair = store.read(args.repair_report)
        text += f"\nLatest scoped repair: {repair['competition']}; {len(repair['promoted'])} repaired, {len(repair['removed'])} incomplete records excluded. See [repair evidence](../{args.repair_report}).\n"
    if args.pdf_location_report:
        pdf_report = store.read(args.pdf_location_report)
        text += f"\nProblem PDFs are canonical data assets under `data/raw`; mini inputs remain under `data/mini_data/raw`. Output holds validation/run reports, not canonical task PDFs. PDF delivery: {pdf_report['registry_checks']['data']['rendered_pages']} main and {pdf_report['registry_checks']['data/mini_data']['rendered_pages']} mini approved pages rendered successfully. See [location and access checks](../{args.pdf_location_report}).\n"
    store.save_text(current, text)
    obsolete = [
        'docs/CTF_FULL_DATA_EXPANSION_20260917.md',
        'docs/mini_prompt_integrity_repair_20260917.md',
        'docs/from_zhongzheng/mini_data_audit_20260916.md',
        'docs/from_zhongzheng/workspace_sync_20260916.md',
        'docs/from_zhongzheng/main_data_rollout_20260917.md',
        'docs/from_zhongzheng/ready-competitions-20260914.md',
    ]
    for relative in obsolete:
        if (ROOT / relative).exists():
            store.archive(relative)
        link = os.path.relpath(ROOT / current, (ROOT / relative).parent).replace('\\', '/')
        store.save_text(relative, f'# Current status\n\nSee [the latest verified dataset status]({link}).\n')
    store.finish({'operation': 'publish_latest_status', 'archived_documents': obsolete,
                  'mini_membership': 'preserved', 'historical_results': 'preserved'})
    assert store.read('data/mini_data/verification.json')['all_jobs_environment_ready']
    print({'status': current, 'archived_documents': len(obsolete), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
