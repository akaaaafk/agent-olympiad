"""Frozen, explicit benchmark grouping; no invented official packet boundaries."""
from copy import deepcopy
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    report_path = 'data/judge_references/wsc_writing_flow_20260916.json'
    if (ROOT / report_path).exists():
        raise RuntimeError('Frozen batch exists; do not replay')
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    path = 'data/benchmarks/wsc_writing/benchmark.json'
    rows = deepcopy(store.read(path))
    assert len(rows) == 42 and len({r['problem_id'] for r in rows}) == 42
    limitation = ('Three-author staged written benchmark with controller-private writing and cyclic peer editing. '
                  'Groups of three are benchmark groupings in existing record order, not recovered official packets. '
                  'Official stage minutes are unknown; LLM rubric scores are not certified official scores.')
    report = dict(role='judge_only', before_sha256=store.sha(path), grouping='consecutive_existing_record_order_v1', packets=[])
    for start in range(0, len(rows), 3):
        packet = f'wsc_writing_benchmark_packet_{start // 3 + 1:03d}'
        members = rows[start:start + 3]
        report['packets'].append(dict(session_id=packet, problem_ids=[r['problem_id'] for r in members]))
        for row in members:
            row['parent_session_id'] = packet
            row['packet_grouping'] = 'benchmark_consecutive_three_v1_not_official'
            row['evaluation'].update(assessment_scope='three_author_staged_written',
                competition_flow='collaborative_writing_v1', limitations=limitation,
                official_score_equivalent=False)
    store.save(path, rows)
    cp = 'data/rules/wsc_writing/competition.json'
    card = deepcopy(store.read(cp))
    tools = ['start_independent_writing', 'write_writing_response', 'read_writing_response',
             'start_peer_review', 'review_writing_response', 'submit_writing_packet']
    text = ('Three teammates answer three different provided prompts. Plan together, then the captain starts '
            'independent writing. Each author writes only their assigned private response; communication is disabled '
            'during writing. Once three responses exist, the captain starts peer review; each teammate edits one '
            'different response under a cyclic benchmark assignment. After all three edits, Agent_1 submits the packet. '
            'Available drafts are collected at the deadline when deadline submission is enabled; missing responses score zero. '
            'Only provided materials are allowed; no internet, calculator or code execution. '
            'Prompt grouping and cyclic editing are benchmark adaptations; official stage minutes are unknown.')
    card.update(protocol='collaborative_writing_v1', rules_text=text, human_constraints=[text])
    card['allowed_tools'] = list(dict.fromkeys(card['allowed_tools'] + tools))
    card['team']['collaboration'] = 'Shared planning, private independent writing, assigned peer editing, three-response submission.'
    card['deliverable']['answer_format'] = 'Three complete responses to three distinct prompts, one original author per response.'
    card['deliverable']['shared'] = False
    card['provenance']['adaptations'] = [x for x in card['provenance']['adaptations'] if 'Single guiding-question' not in x]
    card['provenance']['adaptations'].append(limitation)
    store.save(cp, card)
    cp = 'data/rules/wsc_writing/collaboration.json'
    collab = deepcopy(store.read(cp))
    collab['agent_constraints'] = [text, 'Do not access judge inputs or hidden reference material.']
    for i, role in enumerate(collab['agent_roles']):
        role['title'] = 'independent writer and assigned peer editor' + ('; captain and final submitter' if i == 0 else '')
        role['duties'] = ['Write your assigned response independently; edit the next response in cyclic assignment during peer review.']
    for key in ['competition_format', 'deliverable_format', 'timeline', 'collaboration_protocol']:
        collab['rule_sections'][key] = [text]
    collab['rule_sections']['runtime_limitations'] = [limitation]
    collab['rule_sections']['evaluation_criteria'] = ['Score each response individually under the four-criterion /100 rubric; packet maximum 300.']
    store.save(cp, collab)
    store.save(report_path, report)
    store.finish(report)
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
