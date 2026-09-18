"""Offline five-baseline smoke on actual registered delivery routes.

Real inputs, rendering, parsers and grading orchestration; deterministic agents
and judge responses. External programming judges remain mocked. No quality claim.
"""
import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import sys
import traceback
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import run_pipeline as pipeline
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_run_identity import build_run_identity
from contest_runner import run_contest
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result
from contest_task_judge import judge_task, task_judge_specs
from run_all_contest_smoke import CatalogSmokeAgent, run_case, write_json
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
from rules.loader import load_rule_card
from llm import LLMResponse, LLMToolCall
from saved_run_metrics import ensure_coordination, write_metrics


class OfflineJudge:
    def __init__(self):
        self.calls = Counter()

    def __call__(self, request):
        self.calls[request.purpose] += 1
        if request.purpose.startswith('collaboration_'):
            payload = {'score': 1, 'justification': 'Deterministic smoke response; no quality assessment.'}
        else:
            marker = 'STRUCTURED RUBRIC:'
            if marker not in request.user_prompt:
                raise ValueError('Unexpected offline judge prompt; refuse guessed response')
            rubric, _ = json.JSONDecoder().raw_decode(request.user_prompt.split(marker, 1)[1].lstrip())
            criteria = [dict(id=c['id'], score=c.get('min_score', 0), max_score=c['max_score'],
                            evidence=['Offline smoke fixture'], justification='Protocol check only.',
                            confidence=1, observable=c.get('observable', True)) for c in rubric['criteria']]
            payload = dict(criteria=criteria, total_score=sum(c['score'] for c in criteria),
                           max_score=rubric['total_points'], warnings=[], limitations=['Mock judge'])
        return LLMResponse(json.dumps(payload), 'mock', 'offline-judge')


class WritingSmokeAgent(CatalogSmokeAgent):
    """Drive the writing-specific stages instead of generic shared work actions."""
    def __call__(self, request):
        if not request.tools:
            return super().__call__(request)
        offered = {t['name']: t for t in request.tools}
        if len(offered) != len(request.tools):
            raise AssertionError('Duplicate writing tool schemas')
        for name in ('submit_writing_packet', 'start_peer_review', 'start_independent_writing',
                     'review_writing_response', 'write_writing_response'):
            if name not in offered:
                continue
            props = offered[name]['parameters'].get('properties', {})
            args = {}
            if 'problem_id' in props:
                ids = props['problem_id'].get('enum', [])
                if not ids:
                    marker = 'WSC WRITING FLOW (enforced for every baseline): '
                    state, _ = json.JSONDecoder().raw_decode(request.user_prompt.split(marker, 1)[1])
                    seat = re.search(r'\bAgent_\d+\b', request.system_prompt.split('\n', 1)[0]).group(0)
                    owners = state['peer_editors' if name == 'review_writing_response' else 'authors']
                    ids = [tid for tid, owner in owners.items() if owner == seat]
                if self.config.system_variant == 'single_agent':
                    marker = 'WSC WRITING FLOW (enforced for every baseline): '
                    state, _ = json.JSONDecoder().raw_decode(request.user_prompt.split(marker, 1)[1])
                    completed = state['edited' if name == 'review_writing_response' else 'draft_present']
                    ids = [tid for tid in ids if tid not in completed]
                if not ids or (self.config.system_variant != 'single_agent' and len(ids) != 1):
                    raise AssertionError('Writing prompt does not identify pending assigned responses')
                args['problem_id'] = ids[0]
            if 'content' in props:
                args['content'] = 'Offline writing smoke draft; not a solution-quality claim.'
            self.called[name] += 1
            return LLMResponse('', 'mock', 'writing-smoke', tool_calls=(LLMToolCall(name, args),))
        return super().__call__(request)


def native(job, variant, dest):
    manifest = load_contest_manifest(Path(job['manifest']), benchmark_root=pipeline.DATA / 'benchmarks')
    # Staged writing is an indivisible three-author session; never truncate it.
    if manifest.metadata.get('competition_flow') != 'collaborative_writing_v1':
        manifest = replace(manifest, tasks=manifest.tasks[:2])
    card = load_rule_card(job['competition'], required=True)
    config = ContestRunConfig(variant, 1 if variant == 'single_agent' else card.team_size_default,
        48, max_tokens=200000, minutes_per_turn=0,
        rule_card=card if variant in {'otc', 'vallina_otc'} else None)
    if manifest.metadata.get('competition_flow') == 'collaborative_writing_v1':
        agent = WritingSmokeAgent(manifest, config)
        result = run_contest(manifest, lambda *_: 'Offline writing preparation.', config,
            action_request_fn=agent, action_transport='native', coach_query_fn=lambda *_: 'Offline blind advice.',
            task_action_executor=Mock(side_effect=AssertionError('unexpected external writing tool')))
        errors = [e for e in result['memory']['events'] if e['kind'] == 'action_error']
        case = dict(result=result, action_errors=errors, checks={
            'no_action_errors': not errors,
            'all_three_submitted': all(result['submissions'].get(t.task_id) for t in manifest.tasks),
            'writing_stage_actions': all(agent.called[a] for a in ('start_independent_writing',
                'write_writing_response', 'start_peer_review', 'review_writing_response', 'submit_writing_packet')),
            'correct_variant': result['system_variant'] == variant,
            'memory_setting': result['modules']['memory'] == (variant == 'otc')})
    else:
        case = run_case(manifest, card, variant, 48)
    result = case['result']
    judge = OfflineJudge()
    specs = task_judge_specs(manifest)
    for task in manifest.tasks:
        if task.task_id in specs:
            result.setdefault('task_judgements', {})[task.task_id] = judge_task(
                task, result['submissions'].get(task.task_id, ''), judge)
    result['grade'] = grade_contest_result(manifest, result)
    result['run_identity'] = build_run_identity(manifest, config,
        execution={'provider': 'mock', 'model': 'catalog-smoke'},
        evaluation={'provider': 'mock', 'model': 'offline-judge', 'task_judges': specs})
    write_json(dest / 'contest_session.json', result)
    coordination = ensure_coordination(dest, result=result,
        task_text='\n'.join(t.prompt for t in manifest.tasks), judge_request=judge,
        judge_provider='mock', judge_model='offline-judge')
    write_metrics(dest, result, coordination=coordination)
    cached = ensure_coordination(dest, result=result,
        task_text='\n'.join(t.prompt for t in manifest.tasks),
        judge_request=Mock(side_effect=AssertionError('coordination judge rerun')),
        judge_provider='mock', judge_model='offline-judge')
    checks = dict(case['checks'], task_grading_complete=bool(result['grade']['graded']),
                  coordination_complete=coordination['status'] in {'complete', 'not_applicable'},
                  coordination_cache_reused=cached == coordination)
    return dict(checks=checks, task_ids=[t.task_id for t in manifest.tasks],
                action_errors=case['action_errors'], grade=result['grade'], judge_calls=dict(judge.calls),
                external_tools='mock except calculator')


def artifact(job, variant, dest):
    prepared = prepare_artifact_run(competition=job['competition'], task_pdf=Path(job['task_pdf']),
        rubric=Path(job['rubric']), output=dest, provider='openai', model='offline-smoke',
        judge_provider='openai', judge_model='offline-judge', system_variant=variant,
        max_turns=48, max_tokens=200000)
    contract = prepared['contract']
    paragraph = 'Offline delivery smoke. This document tests rendering and submission, not solution quality.'
    if contract.source_format == 'latex':
        source = r'\documentclass{article}\begin{document}' + paragraph + r'\end{document}'
    elif contract.kind == 'slides':
        source = '<html><body>' + ''.join('<section><h1>Smoke</h1><p>' + paragraph + '</p></section>'
                                          for _ in range(contract.min_pages)) + '</body></html>'
    else:
        source = 'Offline smoke\n\n' + paragraph
    agent = CatalogSmokeAgent(prepared['manifest'], prepared['config'], candidate_content=source,
                              probe_task_tools=False)
    judge = OfflineJudge()
    result = run_artifact_contest(prepared, agent_request=agent, judge_request=judge)
    contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
    errors = [e for e in contest['memory']['events'] if e['kind'] == 'action_error']
    receipt = result.get('artifact') or {}
    checks = dict(complete=result['status'] == 'complete', no_action_errors=not errors,
                  correct_variant=contest['system_variant'] == variant,
                  memory_setting=contest['modules']['memory'] == (variant == 'otc'),
                  unique_function_schemas=agent.schema_names_unique,
                  source_preserved=bool(receipt) and Path(receipt['source']).read_text(encoding='utf-8') == source,
                  pdf_hash=bool(receipt) and hashlib.sha256(Path(receipt['pdf']).read_bytes()).hexdigest() == receipt['pdf_sha256'])
    checks['completed_resume_no_calls'] = False
    if checks['complete']:
        repeated = run_artifact_contest(prepared, resume=True,
            agent_request=Mock(side_effect=AssertionError('solver rerun')),
            judge_request=Mock(side_effect=AssertionError('judge rerun')))
        checks['completed_resume_no_calls'] = repeated['status'] == 'complete' and repeated['artifact'] == receipt
    return dict(checks=checks, task_ids=job['problem_ids'], action_errors=errors,
                judge_calls=dict(judge.calls), rendering='real', source_format=contract.source_format)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--competition', action='append')
    parser.add_argument('--session', help='Limit representative selection to this registered session.')
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        parser.error('Use a fresh output directory')
    out.mkdir(parents=True)
    registry = pipeline.register(out / 'registration')
    rows = []
    tracks = [t for t in registry['tracks'] if not args.competition or t['competition'] in args.competition]
    for track in tracks:
        jobs = [j for j in registry['jobs'] if j['competition'] == track['competition']]
        eligible = [j for j in jobs if not j['blockers']]
        if args.session:
            eligible = [j for j in eligible if j['session'] == args.session]
        job = next(iter(eligible), None)
        for variant in BASELINE_NAMES:
            row = dict(competition=track['competition'], variant=variant, route=track['route'])
            try:
                if job is None:
                    row.update(status='BLOCKED', blockers=sorted(set(b for j in jobs for b in j['blockers'])) or ['No registered jobs'])
                else:
                    row['selection'] = job
                    dest = out / 'runs' / track['competition'] / variant
                    dest.mkdir(parents=True)
                    details = (native if job['route'] == 'native' else artifact)(job, variant, dest)
                    row.update(details, status='PASS' if all(details['checks'].values()) else 'FAIL')
                    write_json(dest / 'smoke_checks.json', row)
            except Exception:
                row.update(status='FAIL', error=traceback.format_exc())
            rows.append(row)
            summary = dict(live_llm=False, live_judge=False, external_programming_judge='mock',
                           cases=rows, counts=dict(Counter(r['status'] for r in rows)),
                           expected_cases=len(tracks)*len(BASELINE_NAMES))
            write_json(out / 'summary.json', summary)
            print(track['competition'], variant, row['status'], flush=True)
    lines = ['# Five baseline actual-route offline smoke', '',
             'Mock agents and judges; real local inputs, artifact rendering, grading parsers, and artifact resume.',
             'PASS is infrastructure coverage, not solution quality or live-provider validation.', '',
             json.dumps(summary['counts']), '', '| Competition | Baseline | Route | Status | Detail |',
             '| --- | --- | --- | --- | --- |']
    for row in rows:
        reason = row.get('error', '').strip().splitlines()[-1:] or row.get('blockers') or [
            ', '.join(k for k,v in row.get('checks',{}).items() if not v)]
        lines.append('| ' + ' | '.join([row['competition'], row['variant'], row['route'], row['status'],
                                       '; '.join(reason).replace('|','/')]) + ' |')
    (out / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return int(bool(summary['counts'].get('FAIL') or summary['counts'].get('BLOCKED')))


if __name__ == '__main__':
    raise SystemExit(main())
