"""Required collaboration evaluation of immutable saved contestant evidence.

Sidecars bind to the session, task text, outcome and judge configuration. A
retry only calls missing judges, never contestants or completed rubric judges.
"""
import json
from hashlib import sha256
from pathlib import Path
from dataclasses import replace

from contest_reporting import finite, metered_judge, report_row
from contest_run_identity import content_hash
from evaluation.collaboration_score import score_coordination, _parse_score
from llm import LLMResponse, LLMAttachment


def task_context_judge(directory, contest, request_fn, provider, *, model=None):
    """Scanned tasks use verified original task media, never judge-only sources."""
    from llm import provider_capabilities
    path = Path(directory) / 'coordination_task_assets.json'
    if not path.is_file():
        return request_fn
    if not getattr(request_fn, 'supports_attachments', provider_capabilities(provider).attachments):
        raise ValueError('Scanned collaboration task requires a visual judge provider')
    asset = json.loads(path.read_text(encoding='utf-8'))
    original = contest['run_identity']['settings']['execution']
    if (asset['sha256'] != original.get('task_pdf_sha256') or asset['pages'] != original.get('task_pages')
            or sha256(Path(asset['path']).read_bytes()).hexdigest() != asset['sha256']):
        raise ValueError('Collaboration task media differs from original contestant input')
    attachment = LLMAttachment(Path(asset['path']), 'application/pdf', page_start=asset['pages'][0], page_end=asset['pages'][1])
    if provider in {'perplexity', 'pplx'}:
        from evaluation.slides_pipeline import build_task_asset
        from otc_artifact_pipeline import _attachments
        task = build_task_asset(Path(asset['path']), f"{asset['pages'][0]}-{asset['pages'][1]}")
        attachments = _attachments(task, provider, Path(directory) / 'coordination_task_pages')
    else:
        attachments = (attachment,)
    if provider in {'tinker', 'tml'}:
        from evaluation.pdf_paging import paged_judge
        evaluation = ((contest.get('run_identity') or {}).get('settings') or {}).get('evaluation') or {}
        request_fn = paged_judge(request_fn, Path(directory) / 'coordination_pdf_evidence',
                                cache_namespace={'provider': provider, 'model': model or evaluation.get('model')})
    def request(req):
        return request_fn(replace(req, attachments=attachments)
                          if req.purpose == 'collaboration_communication_score' else req)
    return request


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def valid_coordination(value):
    if not isinstance(value, dict):
        return False
    c, p, cs = (value.get(k) for k in
                ('communication_score', 'planning_score', 'coordination_score'))
    return (all(finite(v) for v in (c, p, cs)) and 0 <= c <= 5
            and 1 <= p <= 5 and abs(cs - (c + p) / 2) < 1e-9)


def coordination_complete(directory, result=None):
    """Missing sidecars are pending, including historical 'complete' runs."""
    directory = Path(directory)
    session_path = directory / 'contest_session.json'
    sidecar = directory / 'coordination_required.json'
    if not sidecar.is_file() or not session_path.is_file():
        return False
    try:
        saved = json.loads(sidecar.read_text(encoding='utf-8'))
        if saved['binding'].get('evaluator_sha256') != sha256((Path(__file__).parent / 'evaluation/collaboration_score.py').read_bytes()).hexdigest():
            return False
        if saved['binding']['session_sha256'] != sha256(session_path.read_bytes()).hexdigest():
            return False
        media = directory / 'coordination_task_assets.json'
        if media.is_file():
            asset = json.loads(media.read_text(encoding='utf-8'))
            if (saved['binding'].get('task_media_sha256') != content_hash(asset)
                    or sha256(Path(asset['path']).read_bytes()).hexdigest() != asset['sha256']):
                return False
        task = directory / 'task_extracted.txt'
        if not task.is_file():
            task = directory / 'coordination_task.txt'
        if task.is_file() and saved['binding'].get('task_file_sha256') != sha256(task.read_bytes()).hexdigest():
            return False
        if result is not None:
            grade = result.get('evaluation') or result.get('grade') or {}
            if saved['binding'].get('outcome_sha256') != content_hash(grade):
                return False
        if saved.get('status') == 'not_applicable':
            contest = json.loads(session_path.read_text(encoding='utf-8'))
            config = ((contest.get('run_identity') or {}).get('settings') or {}).get('config') or {}
            return (contest.get('system_variant') or config.get('system_variant')) == 'single_agent'
        if result is not None and result.get('coordination_required'):
            if result.get('coordination') != saved.get('coordination'):
                return False
        return saved.get('status') == 'complete' and valid_coordination(saved.get('coordination'))
    except (KeyError, ValueError, OSError, TypeError):
        return False


def ensure_coordination(directory, *, result, task_text, judge_request, judge_provider, judge_model):
    directory = Path(directory)
    session_path = directory / 'contest_session.json'
    raw = session_path.read_bytes()
    contest = json.loads(raw)
    settings = (contest.get('run_identity') or {}).get('settings') or {}
    config = settings.get('config') or {}
    variant = contest.get('system_variant') or config.get('system_variant')
    if not variant:
        raise ValueError('Saved session has no baseline identity')
    count = config.get('team_size')
    if not isinstance(count, int) or count < 1:
        raise ValueError('Saved session has no verified team size')
    grade = result.get('evaluation') or result.get('grade') or {}
    task_file = directory / 'task_extracted.txt'
    if not task_file.is_file():
        task_file = directory / 'coordination_task.txt'
    binding = dict(session_sha256=sha256(raw).hexdigest(), task_sha256=content_hash(task_text),
                   task_file_sha256=sha256(task_file.read_bytes()).hexdigest() if task_file.is_file() else None,
                   outcome_sha256=content_hash(grade), judge_provider=judge_provider,
                   judge_model=judge_model, evaluator='multiagentbench_required_v1',
                   evaluator_sha256=sha256((Path(__file__).parent / 'evaluation/collaboration_score.py').read_bytes()).hexdigest())
    media = directory / 'coordination_task_assets.json'
    binding['task_media_sha256'] = content_hash(json.loads(media.read_text(encoding='utf-8'))) if media.is_file() else None
    path = directory / 'coordination_required.json'
    saved = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if saved.get('binding') != binding:
        saved = dict(binding=binding, status='pending', cached_responses={},
                     limitations=['Existing evaluator truncates communications to 12000 characters and planning to the last 80 actions.'])
    if variant == 'single_agent':
        saved.update(status='not_applicable', reason='not_applicable_single_agent')
        write_json(path, saved)
        return saved
    if saved.get('status') == 'complete' and valid_coordination(saved.get('coordination')):
        return saved
    agents = [f'Agent_{i+1}' for i in range(count)]
    events = (contest.get('memory') or {}).get('events')
    if not isinstance(events, list):
        raise ValueError('Saved session lacks interaction evidence')
    chats = [dict(sender=e['actor'], content=str((e.get('payload') or {}).get('content')
             or (e.get('payload') or {}).get('report') or e.get('payload') or ''))
             for e in events if e.get('actor') in agents and e.get('kind') in
             {'speak', 'direct_message', 'request_review', 'review_answer'}]
    actions = [dict(agent=e['actor'], action=e['kind'], payload=e.get('payload', {}))
               for e in events if e.get('actor') in agents]
    measured = metered_judge(judge_request, saved)

    def request(req):
        key = content_hash(dict(system=req.system_prompt, user=req.user_prompt, purpose=req.purpose))
        cached = saved.setdefault('cached_responses', {})
        if key in cached:
            return LLMResponse(**cached[key])
        response = measured(req)
        limitation = response.usage.get('pdf_paging_limitation')
        if limitation and limitation not in saved.setdefault('limitations', []):
            saved['limitations'].append(limitation)
        score, _ = _parse_score(response.text)
        minimum = 1 if req.purpose == 'collaboration_planning_score' else 0
        if not finite(score) or not minimum <= score <= 5:
            raise ValueError('Invalid required collaboration judge score')
        cached[key] = dict(text=response.text, provider=response.provider,
                           model=response.model, usage=response.usage)
        write_json(path, saved)
        return response

    saved['status'] = 'started'
    write_json(path, saved)
    try:
        value = score_coordination(request_fn=request, task_text=task_text, agents=agents,
                    schema=variant, chat_history=chats, action_log=actions,
                    task_results=json.dumps(grade, ensure_ascii=False)).to_dict()
        if not valid_coordination(value):
            raise ValueError('Required collaboration scores are incomplete')
        saved.update(status='complete', coordination=value)
        saved.pop('error', None)
    except Exception as exc:
        saved.update(status='failed', error=f'{type(exc).__name__}: required collaboration evaluation failed; retry evaluation only')
        saved.pop('coordination', None)
    write_json(path, saved)
    return saved


def flat_metrics(contest, result=None, coordination=None):
    """One report contract for native and artifact routes, separate judge usage."""
    combined = dict(contest)
    combined['metrics'] = dict(contest.get('metrics') or {})
    if not coordination and valid_coordination(contest.get('coordination')):
        combined['metrics'].update(contest['coordination'])
    if result and 'evaluation' in result:
        grade = result['evaluation']
        combined['grade'] = dict(score=grade.get('total_score'), max_score=grade.get('max_score'))
    if coordination:
        identity = dict(combined.get('run_identity') or {})
        settings = dict(identity.get('settings') or {})
        settings['evaluation'] = {**(settings.get('evaluation') or {}), 'judge_collab': True,
                                  'provider': coordination.get('binding', {}).get('judge_provider')
                                              or (settings.get('evaluation') or {}).get('provider')}
        identity['settings'] = settings
        combined['run_identity'] = identity
        status = coordination.get('status')
        combined['evaluation_stages'] = {'coordination': dict(status=status,
             error=coordination.get('error') or coordination.get('reason'))}
        if status == 'complete':
            combined['metrics'].update(coordination['coordination'])
            combined['coordination'] = coordination['coordination']
        else:
            for key in ('communication_score', 'planning_score', 'coordination_score'):
                combined['metrics'].pop(key, None)
        combined['evaluation_usage'] = coordination.get('evaluation_usage')
        if result and 'evaluation' in result:
            task_usage = result.get('task_evaluation_usage')
            collab_usage = coordination.get('evaluation_usage') or {}
            if task_usage:
                combined['evaluation_usage'] = {key: task_usage.get(key, 0) + collab_usage.get(key, 0)
                    for key in ('api_calls', 'output_tokens', 'sec', 'unmetered_calls')}
            else:
                # Historical rubric usage cannot be reconstructed by counting
                # collaboration calls alone. Leave combined evaluator use unknown.
                combined['evaluation_usage'] = None
    return report_row(combined)


def write_metrics(directory, contest, result=None, coordination=None):
    import csv
    directory = Path(directory)
    row = flat_metrics(contest, result, coordination)
    write_json(directory / 'required_metrics.json', row)
    target = directory / 'required_metrics.csv'
    temp = target.with_suffix('.csv.tmp')
    with temp.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    temp.replace(target)
    return row
