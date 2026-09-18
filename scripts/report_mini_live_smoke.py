"""Read-only evidence export for per-competition live mini smoke runs."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path


def read(path, fallback=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else fallback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    selected = read(root / 'smoke_selection.json')
    states = read(root / 'batch_status.json', {}).get('jobs', {})
    corrections = read(root / 'scope_corrections.json', {})
    score_audits = read(root / 'score_audit/verified_corrections.json', {})
    rows = []
    for choice in selected:
        case_root = root
        case_states = states
        correction = corrections.get(choice['competition'])
        if correction:
            case_root = Path(correction['output'])
            choice = read(case_root / 'smoke_selection.json')[0]
            case_states = read(case_root / 'batch_status.json', {}).get('jobs', {})
        folder = case_root / 'runs' / choice['job_id']
        contest = read(folder / 'contest_session.json', {})
        artifact = read(folder / 'result.json', {}) if choice['route'] != 'native' else {}
        result = artifact or contest
        grade = result.get('grade') or result.get('evaluation') or {}
        errors = [e.get('payload', {}) for e in contest.get('memory', {}).get('events', [])
                  if e.get('kind') == 'action_error']
        tool_failures = [e for e in contest.get('memory', {}).get('events', [])
                         if e.get('kind', '').endswith('_result') and (
                             e.get('payload', {}).get('valid') is False or
                             isinstance(e.get('payload', {}).get('result'), dict) and
                             e['payload']['result'].get('command_failed'))]
        submissions = contest.get('submissions', {})
        budget = contest.get('budget', {})
        state = case_states.get(choice['job_id'], {
            'status': 'blocked' if choice.get('blockers') else 'pending',
            'reason': '; '.join(choice.get('blockers', []))})
        status = artifact.get('status') if artifact.get('status') == 'unsubmitted' else state.get('status', 'pending')
        stage_errors = [f'{key}: {value.get("error", "failed")}'
                        for key, value in contest.get('evaluation_stages', {}).items()
                        if value.get('status') == 'failed']
        row = {**choice, 'status': status, 'pipeline_status': state.get('status'),
               'reason': artifact.get('reason') or state.get('reason', ''),
               'has_final_result': bool(result), 'graded': grade.get('graded', result.get('graded', False)),
               'score': grade.get('score', grade.get('total_score', result.get('score'))),
               'max_score': grade.get('max_score', result.get('max_score')),
               'turns': budget.get('turns_used'), 'api_calls': budget.get('api_calls_used'),
               'tokens': budget.get('tokens_used'), 'action_errors': len(errors),
               'truncation_errors': sum('token limit' in str(e).lower() or 'truncated' in str(e).lower() for e in errors),
               'submissions': submissions, 'error_details': errors,
               'nonempty_submissions': sum(bool(str(v).strip()) for v in submissions.values()) if isinstance(submissions, dict) else None,
               'tool_failures': tool_failures,
               'grade_details': grade,
               'artifact': artifact.get('artifact'),
               'evaluation_errors': stage_errors,
               'scope_correction': correction,
               'score_audit': score_audits.get(choice['competition']),
               'result_directory': str(folder)}
        has_submission = bool(artifact.get('artifact', {}).get('valid')) if artifact else bool(row['nonempty_submissions'])
        row['has_submission'] = has_submission
        if status != 'complete':
            outcome = status
        elif not has_submission:
            outcome = 'graded_empty_submission'
        elif errors:
            outcome = 'graded_with_action_errors'
        elif row['score'] == 0:
            outcome = 'graded_zero'
        else:
            outcome = 'graded_nonzero_no_action_errors'
        row['smoke_outcome'] = outcome
        rows.append(row)
    payload = {'counts': dict(Counter(r['status'] for r in rows)),
               'outcomes': dict(Counter(r['smoke_outcome'] for r in rows)), 'competitions': len(rows), 'rows': rows}
    (root / 'smoke_results.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fields = ['competition', 'problem_id', 'question_id', 'status', 'smoke_outcome', 'graded', 'score', 'max_score',
              'turns', 'api_calls', 'tokens', 'nonempty_submissions', 'action_errors', 'truncation_errors', 'reason', 'result_directory']
    with (root / 'smoke_results.tsv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    lines = ['# mini_data live smoke', '',
             'One selected task per competition. Rubric/source-review scores are benchmark proxy scores, not official contest results.', '',
             'States: ' + json.dumps(payload['counts']) + '.', '',
             'Outcomes: ' + json.dumps(payload['outcomes']) + '.', '',
             '| Competition | State | Score | Nonempty submissions | Action errors | Output |',
             '| --- | --- | --- | --- | --- | --- |']
    for row in rows:
        score = f"{row['score']}/{row['max_score']}" if row['score'] is not None else '—'
        if row['score_audit']:
            score += f" (source audit: {row['score_audit']['audited_score']}/{row['score_audit']['audited_max_score']})"
        relative = Path(row['result_directory']).relative_to(root).as_posix()
        filename = 'result.json' if row['route'] != 'native' else 'contest_session.json'
        target = f'{relative}/{filename}'
        if not (root / target).exists():
            target = f'logs/{row["job_id"]}.log'
        lines.append(f"| {row['competition']} | {row['status']} | {score} | {row['nonempty_submissions']} | {row['action_errors']} | [result/log]({target}) |")
    lines += ['', '## Submitted output previews', '']
    for row in rows:
        if row['has_final_result']:
            preview = json.dumps(row['submissions'], ensure_ascii=False, indent=2)
            lines += [f"### {row['competition']}", '', row['scope'] + '.', '',
                      '```text', preview[:2400].replace('```', "'''"), '```', '']
            if row['artifact']:
                for key in ('source', 'pdf'):
                    if row['artifact'].get(key):
                        relative = Path(row['artifact'][key]).relative_to(root).as_posix()
                        lines += [f'[{key}]({relative})', '']
            if len(preview) > 2400:
                lines += ['Preview truncated; full submissions are in the linked result files and smoke_results.json.', '']
            for error in row['evaluation_errors']:
                lines += ['Evaluation failure: ' + error, '']
            for error in row['error_details']:
                lines += ['Action failure: ' + str(error), '']
            if row['score_audit']:
                lines += ['Source-verified gold encoding error; saved result retained. '
                          '[Offline reevaluation](score_audit/verified_corrections.json): '
                          + row['score_audit']['review']['note'], '']
    (root / 'smoke_results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(payload['counts']))
    for row in rows:
        if row['status'] not in {'pending', 'running'}:
            print(row['competition'], row['status'], row['score'], '/', row['max_score'],
                  'errors=', row['action_errors'], row['reason'][:180])


if __name__ == '__main__':
    main()
