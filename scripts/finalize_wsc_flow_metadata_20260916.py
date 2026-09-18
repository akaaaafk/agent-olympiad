"""Synchronize the staged-flow scoring guidance and diagnostic metadata."""
from copy import deepcopy
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    report_path = 'data/judge_references/wsc_flow_metadata_20260916.json'
    if (ROOT/report_path).exists():
        raise RuntimeError('Frozen batch exists; do not replay')
    store = Store(ROOT, ROOT.parent/'dataset_backups')
    path = 'data/rules/wsc_writing/evaluation.json'
    card = deepcopy(store.read(path))
    card['evaluation_guidance'] = ('Resolve each response rubric from its benchmark record. Score three independently '
        'authored responses separately using Clarity, Content, Style and Originality, each on the published 15-25 scale '
        '(60-100 per nonempty response; blank responses score zero). The three-response packet maximum is 300. '
        'The planning/private-writing/peer-editing stage order is enforced; official stage minutes and human-judge calibration '
        'are not reproduced. Prompt grouping and cyclic peer assignments are explicit benchmark adaptations.')
    card['scoring']['unit'] = 'response'
    card['scoring']['packet_max_score'] = 300
    card['scoring']['official_performance']['mechanics_completeness'] = 'staged_written_flow_encoded_official_clocks_unresolved'
    store.save(path, card)
    path = 'data/rules/wsc_writing/collaboration.json'
    card = deepcopy(store.read(path))
    card['simulation']['deliverable_pipeline']['fidelity'] = 'three_author_staged_written_benchmark'
    store.save(path, card)
    path = 'data/benchmarks/pumac_power/benchmark.json'
    rows = deepcopy(store.read(path))
    row = next(r for r in rows if r['year'] == 2018)
    details = row['source_review']['version_conflict']
    details['reviewed_statement_ids'] = details.pop('changed_statement_ids', details.get('reviewed_statement_ids', []))
    details['confirmed_changed_statement_ids'] = ['1.1.5', '4.2.3', '4.2.4']
    store.save(path, rows)
    report = dict(role='judge_only', changed_paths=[
                  'data/rules/wsc_writing/evaluation.json', 'data/rules/wsc_writing/collaboration.json', path],
                  original_metadata_backup='E:/agent_olympiad/dataset_backups/integrity_repair_20260916T220120Z',
                  scope='Synchronize WSC scoring guidance; distinguish reviewed from confirmed changed PUMaC IDs.')
    store.save(report_path, report)
    store.finish(report)
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
