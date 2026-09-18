"""Read saved mini results and audit staged-transport evidence without rerunning models."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf8')) if path.is_file() else default


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.output.resolve()
    repo = Path(__file__).resolve().parents[1]
    current = {p.relative_to(repo/'src').as_posix(): hashlib.sha256(
        p.read_text(encoding='utf8').encode('utf8')).hexdigest() for p in (repo/'src').rglob('*.py')}
    rows = []
    for selected in sorted(root.glob('*/smoke_selection.json')):
        branch = selected.parent
        states = read(branch/'batch_status.json', {}).get('jobs', {})
        for choice in read(selected):
            folder = branch/'runs'/choice['job_id']
            contest = read(folder/'contest_session.json', {})
            artifact = read(folder/'result.json', {}) if choice['route'] != 'native' else {}
            result = artifact or contest
            grade = result.get('grade') or result.get('evaluation') or {}
            traces = contest.get('action_sampling_log', [])
            errors = [e.get('payload', {}) for e in contest.get('memory', {}).get('events', [])
                      if e.get('kind') == 'action_error']
            budget = contest.get('budget', {})
            identity = contest.get('run_identity', {})
            sources = identity.get('settings', {}).get('source_hashes', {})
            mismatches = [key for key in set(current)|set(sources) if current.get(key) != sources.get(key)] if sources else None
            row = {**choice, 'variant': branch.name,
                'status': result.get('status') or states.get(choice['job_id'], {}).get('status', 'pending'),
                'final_exists': bool(result), 'graded': grade.get('graded', result.get('graded', False)),
                'score': grade.get('score', grade.get('total_score')), 'max_score': grade.get('max_score'),
                'turns': budget.get('turns_used'), 'api_calls': budget.get('api_calls_used'),
                'output_tokens': budget.get('tokens_used'), 'sampling_calls': len(traces),
                'length_samples': [{k:x.get(k) for k in ('turn','agent','stage','argument','output_tokens')}
                                   for x in traces if x.get('finish_reason') == 'length'],
                'cross_request_resumes': [x for x in traces if 'resuming_unexecuted_body_tokens' in x
                                         or 'resuming_unexecuted_metadata_tokens' in x],
                'action_errors': errors,
                'executed_actions': [x['name'] for x in contest.get('action_transport_log', []) if x.get('executed')],
                'unexecuted_draft_agents': list(contest.get('unexecuted_transport_drafts', {})),
                'evaluation_pending': contest.get('evaluation_pending'),
                'source_mismatches': mismatches, 'run_fingerprint': identity.get('fingerprint'),
                'result_file': (folder/('result.json' if artifact else 'contest_session.json')).relative_to(root).as_posix(),
                'budget_accounting_ok': (len(traces) <= budget.get('api_calls_used', 0)
                    and sum(x.get('output_tokens') or 0 for x in traces) <= budget.get('tokens_used', 0)
                    and budget.get('api_calls_used', 0) <= (budget.get('max_api_calls') or float('inf'))
                    and budget.get('tokens_used', 0) <= (budget.get('max_tokens') or float('inf'))) if contest else None}
            # Keep raw samples in the linked result; the audit needs only resume metadata.
            row['cross_request_resumes'] = [{k:v for k,v in x.items() if k != 'text'} for x in row['cross_request_resumes']]
            rows.append(row)
    offline = read(root/'offline_validation.json', {})
    payload = {'offline': offline, 'rows': rows,
        'all_final': all(r['final_exists'] for r in rows),
        'all_source_identities_match': all(r['source_mismatches'] == [] for r in rows),
        'all_budgets_respected': all(r['budget_accounting_ok'] is True for r in rows)}
    (root/'verification.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    lines = ['# Tinker staged transport validation', '',
        'Fresh mini_data tasks; Qwen/Qwen3.6-35B-A3B, temperature 0.2. '
        'Each task has 10 turns, 24 solver API calls, and 65536 output tokens. '
        'Source/rubric review scores are proxies, not official test results.', '',
        f"Offline: {offline.get('tests_passed')} tests and {offline.get('subtests_passed')} subtests passed.", '',
        '| Task | Variant | State | Score | API calls | Output tokens | Length samples | Action errors |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in rows:
        lines.append(f"| [{row['competition']}]({row['result_file']}) | {row['variant']} | {row['status']} | "
            f"{row['score']}/{row['max_score']} | {row['api_calls']} | {row['output_tokens']} | "
            f"{len(row['length_samples'])} | {len(row['action_errors'])} |")
    lines += ['', 'Length samples are sampler events; an action error means the entire bounded action '
              'request failed or runtime policy rejected the action. These counts are not interchangeable.', '',
              'Source identity and budget audit: ' + json.dumps({k:payload[k] for k in
              ('all_final','all_source_identities_match','all_budgets_respected')}) + '.', '']
    for row in rows:
        lines += [f"## {row['competition']}", '', row['scope'] + '.', '',
                  'Executed actions: ' + ', '.join(row['executed_actions']) + '.', '',
                  'Cross-request continuations: ' + str(len(row['cross_request_resumes'])) + '.', '']
        lines += ['- ' + str(e.get('error', e)) for e in row['action_errors']]
        if row['unexecuted_draft_agents']:
            lines += ['', 'Unexecuted buffers retained for: ' + ', '.join(row['unexecuted_draft_agents']) + '.']
        lines.append('')
    (root/'verification.md').write_text('\n'.join(lines), encoding='utf8')
    print(json.dumps({k:v for k,v in payload.items() if k != 'rows' and k != 'offline'}))
    for row in rows:
        print(row['competition'], row['status'], row['score'], '/', row['max_score'],
              'length_samples',len(row['length_samples']), 'action_errors',len(row['action_errors']))


if __name__ == '__main__':
    main()
