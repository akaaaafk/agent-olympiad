"""Exclude two verified host-dependent tasks without fabricating interactions."""
from copy import deepcopy
from pathlib import Path
import sys
import uuid
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from src.dataset_catalog import update_track_index

TARGETS = {
    'mystery_hunt_01266': ('Call HQ for an appointment.',
        'Missing physical-room challenge, host assignment and interactive delivery; appointment instructions alone are incomplete.'),
    'mystery_hunt_01377': ('submit the dummy answer GONDRY',
        'Missing organizer-assigned film and video acceptance workflow; GONDRY is an explicit dummy response, not a solved final answer.'),
}


def main(targets=None, report_path='output/hunt_interactive_exclusion_20260917.json',
         required_limitation='not implemented', external_evidence=None):
    targets = TARGETS if targets is None else targets
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_hunt_interactive_' + uuid.uuid4().hex[:8])
    cid = 'mystery_hunt'
    path = f'data/benchmarks/{cid}/benchmark.json'
    original = deepcopy(store.read(path))
    removed = [r for r in original if r['problem_id'] in targets]
    retained = [r for r in original if r['problem_id'] not in targets]
    assert {r['problem_id'] for r in removed} == set(targets)
    evidence = []
    for row in removed:
        assert row['year'] == 2010 and row['evaluation']['status'] == 'not_ready'
        source = store.path(row['source_file'])
        text = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser').get_text(' ', strip=True)
        marker, reason = targets[row['problem_id']]
        assert marker in text
        assert required_limitation in row['evaluation']['limitations']
        evidence.append({'record': row, 'reason': reason, 'source_text': text,
                         'source_sha256': store.sha(row['source_file'])})
    mini = store.read(f'data/mini_data/benchmarks/{cid}/benchmark.json')
    assert {r['problem_id'] for r in mini} <= {r['problem_id'] for r in retained}
    store.save(path, retained)
    rule_path = f'data/rules/{cid}/evaluation.json'
    rule = store.read(rule_path)
    sync_rules(cid, rule, retained)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, cid, retained)
    store.save('data/benchmarks/index.json', index)
    summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    report = {'competition': cid, 'promoted': [], 'removed': evidence,
              'retained_ids': [r['problem_id'] for r in retained],
              'mini_membership': 'unchanged', 'raw_sources': 'preserved', 'paid_model_calls': 0}
    if external_evidence is not None:
        report['external_evidence'] = external_evidence
    store.save(report_path, report)
    store.finish(report)
    assert retained == [r for r in original if r['problem_id'] not in targets]
    print({'removed': len(removed), 'retained': len(retained), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
