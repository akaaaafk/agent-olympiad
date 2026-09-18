"""Contest collaboration -> versioned PDF -> rubric judge for all baselines.

Uses the canonical contest engine. There is no separate team loop or unreviewed
post-contest synthesis. Judge configuration never reaches contestant prompts.
"""
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import json

from artifact_contract import contract_for, resolve_rubric
from artifacts.assets import file_sha256
from artifacts.contest_delivery import ArtifactRenderer, preflight_renderer
from artifacts.pdf_ingest import parse_pdf
from contest_config import ContestRunConfig, canonical_baseline
from contest_adapters import EnvironmentTaskExecutor
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import run_contest
from contest_run_identity import build_run_identity, validate_run_identity, content_hash
from evaluation.models import CriterionResult, EvaluationResult, load_rubric
from evaluation.slides_pipeline import build_task_asset, evaluate_slide_deck
from evaluation.rubric_llm import RubricDocumentEvaluator
from evaluation.finalize import _reference_text
from llm import LLMAttachment, LLMRequest, provider_capabilities, pdf_text_request
from rules.loader import load_rule_card
from dataset_paths import data_root

ROOT = Path(__file__).resolve().parents[1]


def submission_diagnostics(task, review_required):
    """Explain a non-submission without changing approval or grading semantics."""
    versions = task.get('versions') or []
    if not versions:
        return {'code': 'no_rendered_version', 'rejections': []}
    latest = versions[-1]
    current = [r for r in task.get('reviews', []) if not r.get('stale')
               and r.get('version_hash') == latest['version_hash']]
    rejections = [{'reviewer': r['reviewer'], 'body': r['body']}
                  for r in current if r['decision'] == 'reject']
    approved = any(r['decision'] == 'approve' and r['reviewer'] != latest['author']
                   for r in current)
    if not latest.get('evidence_refs'):
        code = 'missing_render_evidence'
    elif review_required and rejections:
        code = 'current_version_rejected'
    elif review_required and not approved:
        code = 'awaiting_independent_approval'
    else:
        code = 'eligible_version_not_submitted'
    return {'code': code, 'version_hash': latest['version_hash'],
            'author': latest['author'], 'current_review_count': len(current),
            'rejections': rejections}


def _write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)
    if path.name == 'contest_session.json':
        from contest_transcript import write_communication_sidecars
        write_communication_sidecars(path.parent, value)


def prepare_artifact_run(*, competition, task_pdf, output, rubric=None, task_pages=None,
                         task_text='', team_size=None, max_turns=None, max_api_calls=None,
                         max_tokens=None, provider='perplexity', model=None,
                         judge_provider=None, judge_model=None, rules_root=None,
                         max_output_tokens=None, system_variant='otc', temperature=0.2):
    system_variant = canonical_baseline(system_variant)
    aliases = {'pplx': 'perplexity', 'oai': 'openai', 'tml': 'tinker'}
    provider = aliases.get(provider, provider)
    from env_config import resolve_run_provider
    judge_provider = resolve_run_provider(provider, judge_provider)
    from env_config import PUBLIC_PROFILE_PROVIDERS
    allowed_providers = {'perplexity', 'openai', 'openagents', 'tinker', *PUBLIC_PROFILE_PROVIDERS}
    if provider not in allowed_providers or judge_provider not in allowed_providers:
        raise ValueError('Artifact runner requires a PDF/image-capable provider')
    from env_config import require_explicit_model
    model = require_explicit_model(model)
    judge_model = require_explicit_model(judge_model) if judge_model is not None else model
    from contest_budget import resolve_contest_budget
    budget = resolve_contest_budget(competition, max_turns=max_turns,
        max_api_calls=max_api_calls, max_total_tokens=max_tokens)
    if max_output_tokens is None:
        max_output_tokens = budget.max_output_tokens_per_call or 8192
    from contest_budget import validate_temperature
    validate_temperature(temperature)
    if max_output_tokens <= 0:
        raise ValueError('max_output_tokens must be positive')
    card = load_rule_card(competition, rules_root=rules_root, required=True)
    contract = contract_for(card)
    rubric_path = resolve_rubric(card, ROOT, rubric)
    rubric_obj = load_rubric(rubric_path)  # Fail before any model calls or output writes.
    task_asset = build_task_asset(Path(task_pdf), task_pages)
    from judge_references import benchmark_for_asset, winner_references
    benchmark = benchmark_for_asset(competition, task_asset.sha256)
    if benchmark:
        from evaluation_readiness import require_ready
        require_ready([benchmark])
    references = ([] if (benchmark or {}).get('evaluation', {}).get('reference_policy') == 'rubric_only'
                  else winner_references(benchmark.get('problem_id') if benchmark else None))
    if benchmark and rubric is None and (benchmark.get('evaluation') or {}).get('rubric_path'):
        rubric_path = ROOT / benchmark['evaluation']['rubric_path']
        rubric_obj = load_rubric(rubric_path)
    if references and judge_provider == 'perplexity':
        raise ValueError('Award reference PDFs require a PDF-capable judge provider')
    if task_asset.page_end - task_asset.page_start + 1 > 100:
        raise ValueError('Task exceeds 100 pages; explicitly select the intended page range')
    task_delivery = ('paged_pdf_v1' if provider == 'tinker' and provider_capabilities(provider, model).attachments
                     else 'extracted_text_v1' if provider_capabilities(provider, model).pdf_text else 'pdf_or_images')
    if task_delivery == 'extracted_text_v1':
        # Preflight extraction before model calls; save the exact packet at run time.
        pdf_text_request(LLMRequest('', '', attachments=(LLMAttachment(
            task_asset.path, 'application/pdf', page_start=task_asset.page_start,
            page_end=task_asset.page_end),)))
    compiler_identity = preflight_renderer(contract)
    if contract.source_format != 'latex':
        compiler_identity = None
    if judge_provider == 'perplexity' and contract.max_pages > 20:
        raise ValueError('Image rubric judge supports up to 20 submission pages; use a PDF judge')
    if ((judge_provider or provider) in {'perplexity', 'pplx'} and
            task_asset.page_end - task_asset.page_start + 1 > 20):
        raise ValueError('Image rubric judge supports up to 20 task pages; select --task-pages '
                         'explicitly or use a PDF-capable judge provider')
    from competition_guidance import fixed_team_size
    count = fixed_team_size(competition, system_variant, requested=team_size, rules_root=rules_root)
    config = ContestRunConfig(system_variant, count, budget.max_turns,
                              max_api_calls=budget.max_api_calls,
                              max_tokens=budget.max_total_tokens,
                              rule_card=card if system_variant in {'otc', 'vallina_otc'} else None,
                              minutes_per_turn=budget.minutes_per_turn,
                              max_simulated_minutes=max(budget.duration_minutes or 0,
                                  budget.max_turns * budget.minutes_per_turn),
                              submission_turn=budget.max_turns)
    if config.otc_policy is not None and config.otc_policy.char_limit('work') < contract.max_source_chars:
        raise ValueError('Rule card work limit is smaller than artifact source limit')
    task_instructions = task_text or 'Solve the attached official task and produce the required deliverable.'
    benchmark_instructions = (benchmark or {}).get('evaluation', {}).get('benchmark_instructions')
    if benchmark_instructions:
        task_instructions += '\n\n' + str(benchmark_instructions)
    metadata = {'task_family': 'general', 'artifact_contract': asdict(contract)}
    if task_delivery == 'paged_pdf_v1':
        from artifact_pdf_reader import asset_document
        metadata['artifact_task_pdf'] = asset_document(task_asset)
    manifest = ContestManifest(f'{competition}-artifact', competition, (
        ManifestTask('deliverable', 'deliverable', None,
                     task_instructions,
                     'artifact', rubric_obj.total_points, False, {}),
    ), metadata=metadata)
    from competition_guidance import competition_guidance
    config = replace(config, rule_guidance=competition_guidance(manifest, config, rules_root=rules_root))
    from rules.runtime import bind_runtime_budget
    card = bind_runtime_budget(card, config)
    identity = build_run_identity(manifest, config, execution={
        'pipeline': contract.version, 'provider': provider, 'model': model,
        'max_output_tokens': max_output_tokens, 'temperature': temperature,
        'action_transport': provider_capabilities(provider).action_transport,
        'task_delivery': task_delivery,
        'budget_basis': 'contest_budget: duration-derived defaults, 5 minutes/turn, 10-90 turns',
        'task_pdf_sha256': task_asset.sha256,
        'compiler_identity': compiler_identity,
        'task_pages': [task_asset.page_start, task_asset.page_end],
    }, evaluation={'provider': judge_provider or provider, 'model': judge_model,
                   'pdf_delivery': 'pdf_page_evidence_v1' if judge_provider == 'tinker' else 'full_document',
                   'temperature': 0.2,
                   'judge_collab': system_variant != 'single_agent',
                   'required_metrics_version': 0 if system_variant == 'single_agent' else 1,
                   'rubric_sha256': file_sha256(rubric_path),
                   'benchmark_problem_id': (benchmark or {}).get('problem_id'),
                   'benchmark_reference_sha256': content_hash(_reference_text(benchmark or {})),
                   'rubric_override': rubric is not None, 'winner_references': references}, source_root=ROOT / 'src')
    return dict(card=card, contract=contract, rubric=rubric_path, task_asset=task_asset,
                benchmark=benchmark, winner_references=references,
                config=config, manifest=manifest, identity=identity, output=Path(output),
                provider=provider, judge_provider=judge_provider or provider,
                model=model, judge_model=judge_model, max_output_tokens=max_output_tokens,
                temperature=temperature)


def _attachments(asset, provider, work_dir, role='agent_visible'):
    if provider in {'perplexity', 'pplx'}:
        parsed = parse_pdf(asset.path, work_dir, media='images', max_pages=100,
                           page_start=asset.page_start, page_end=asset.page_end)
        return tuple(LLMAttachment(path=p.path, mime_type=p.mime_type, role=role)
                     for p in parsed.page_images)
    return (LLMAttachment(path=asset.path, mime_type='application/pdf', role=role,
                          page_start=asset.page_start, page_end=asset.page_end),)


def _evaluation_binding(identity, receipt, evaluation):
    return {'run_fingerprint': identity['fingerprint'],
            'source_sha256': receipt['source_sha256'],
            'pdf_sha256': receipt['pdf_sha256'],
            'evaluation_sha256': content_hash(evaluation)}


def _validate_completed_result(prepared, result, output, *, require_metrics=True):
    """Certify the result snapshot, not just the directory's identity file."""
    validate_run_identity(result.get('run_identity'), prepared['identity'],
                          artifact=output / 'result.json')
    if result.get('graded') is not True or not isinstance(result.get('evaluation'), dict):
        raise ValueError('Completed artifact lacks a successful evaluation')
    try:
        receipt, evaluation = result['artifact'], result['evaluation']
        binding = _evaluation_binding(prepared['identity'], receipt, evaluation)
        if result.get('evaluation_binding') != binding:
            raise ValueError('Completed artifact evaluation binding mismatch')
        if (file_sha256(Path(receipt['pdf'])) != receipt['pdf_sha256'] or
                file_sha256(Path(receipt['source'])) != receipt['source_sha256']):
            raise ValueError('Completed artifact PDF or source was modified')
        session_path = output / 'contest_session.json'
        if Path(result['contest_file']).resolve() != session_path:
            raise ValueError('Completed artifact points to a different contest session')
        contest = json.loads(session_path.read_text(encoding='utf-8'))
        validate_run_identity(contest.get('run_identity'), prepared['identity'], artifact=session_path)
        source = contest.get('submissions', {}).get('deliverable')
        if (not source or sha256(source.encode('utf-8')).hexdigest() != receipt['source_sha256']
                or contest.get('session_checkpoint', {}).get('final_summary') is None):
            raise ValueError('Completed artifact is not bound to the finalized submission')
        rubric = load_rubric(prepared['rubric'])
        if evaluation.get('rubric_id') != rubric.rubric_id:
            raise ValueError('Completed artifact evaluation uses a different rubric')
        checked = EvaluationResult(**{**evaluation, 'criteria': [
            CriterionResult(**item) for item in evaluation['criteria']]})
        checked.validate(rubric)
        if require_metrics and (prepared['identity']['settings'].get('evaluation', {}).get('required_metrics_version')
                                or result.get('coordination_required')):
            from saved_run_metrics import coordination_complete
            if not coordination_complete(output, result):
                raise ValueError('Required collaboration evaluation is pending')
    except (KeyError, TypeError, OSError) as exc:
        raise ValueError(f'Incomplete completed artifact: {exc}') from exc


def _coordination_context(prepared, output, contest, judge_request):
    if contest.get('system_variant') == 'single_agent':
        return '', judge_request
    if prepared['judge_provider'] == 'tinker':
        # Keep full task images out of a single coordination request too.
        asset = prepared['task_asset']
        _write(output / 'coordination_task_assets.json', dict(path=str(asset.path.resolve()),
            sha256=asset.sha256, pages=[asset.page_start, asset.page_end]))
        text_path = output / 'coordination_task.txt'
        text_path.write_text('\n\n'.join(t.prompt for t in prepared['manifest'].tasks), encoding='utf-8')
        from saved_run_metrics import task_context_judge
        return text_path.read_text(encoding='utf-8'), task_context_judge(
            output, contest, judge_request, prepared['judge_provider'], model=prepared['judge_model'])
    text_path = output / 'task_extracted.txt'
    if not text_path.exists():
        text_path = output / 'coordination_task.txt'
        if not text_path.exists():
            asset = prepared['task_asset']
            try:
                packet = pdf_text_request(LLMRequest('', '\n\n'.join(t.prompt for t in prepared['manifest'].tasks),
                    attachments=(LLMAttachment(asset.path, 'application/pdf', page_start=asset.page_start,
                                               page_end=asset.page_end),)))
                text = packet.user_prompt
            except ValueError:
                # Visual providers can solve scanned tasks. Do not require text
                # extraction for their post-contest collaboration evaluation.
                text = '\n\n'.join(t.prompt for t in prepared['manifest'].tasks)
                _write(output / 'coordination_task_assets.json', dict(path=str(asset.path.resolve()),
                    sha256=asset.sha256, pages=[asset.page_start, asset.page_end]))
            text_path.write_text(text, encoding='utf-8')
    task_text = text_path.read_text(encoding='utf-8')
    from saved_run_metrics import task_context_judge
    judge_request = task_context_judge(output, contest, judge_request, prepared['judge_provider'], model=prepared['judge_model'])
    return task_text, judge_request


def _finish_required_metrics(prepared, result, output, judge_request):
    from saved_run_metrics import ensure_coordination, write_metrics
    contest = json.loads((output / 'contest_session.json').read_text(encoding='utf-8'))
    task_text, judge_request = _coordination_context(prepared, output, contest, judge_request)
    saved = ensure_coordination(output, result=result, task_text=task_text,
        judge_request=judge_request, judge_provider=prepared['judge_provider'],
        judge_model=prepared['judge_model'])
    result['coordination_required'] = contest.get('system_variant') != 'single_agent'
    result['evaluation_pending'] = [] if saved['status'] in {'complete', 'not_applicable'} else ['coordination']
    result['coordination'] = saved.get('coordination')
    result['coordination_evaluation_usage'] = saved.get('evaluation_usage')
    result['required_metrics'] = write_metrics(output, contest, result, saved)
    if result.get('graded'):
        result['status'] = 'evaluation_pending' if result['evaluation_pending'] else 'complete'
    elif result['evaluation_pending']:
        result['status'] = 'evaluation_pending'
    else:
        result['status'] = 'unsubmitted'
    _write(output / 'result.json', result)
    return result


def run_artifact_contest(prepared, *, agent_request, judge_request, resume=False,
                         renderer=None, evaluation_only=False):
    p = prepared
    output = p['output'].resolve()
    identity_path = output / 'run_identity.json'
    if evaluation_only:
        if not resume:
            raise ValueError('evaluation_only requires resume')
        # Completed solver work is immutable. Permit source changes only for
        # explicit re-evaluation, recording the current evaluator provenance.
        stored = json.loads(identity_path.read_text(encoding='utf-8'))
        validate_run_identity(stored, stored, artifact=identity_path)
        session_path = output / 'contest_session.json'
        contest = json.loads(session_path.read_text(encoding='utf-8'))
        validate_run_identity(contest.get('run_identity'), stored, artifact=session_path)
        if (contest.get('session_checkpoint') or {}).get('final_summary') is None:
            raise ValueError('evaluation_only requires finalized contestants')
        settings = dict(p['identity']['settings'])
        for key in ('source_hashes', 'action_set_version', 'protocol_version', 'module_version'):
            settings[key] = stored['settings'][key]
        # An explicitly supplied archived rubric is equivalent only when its
        # byte hash matches the original; the hash remains strictly checked.
        settings['evaluation'] = dict(settings['evaluation'])
        settings['evaluation']['rubric_override'] = stored['settings']['evaluation']['rubric_override']
        validate_run_identity(stored, {'settings': settings, 'fingerprint': content_hash(settings)},
                              artifact=identity_path)
        with (output / 'evaluation_resume_identity.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'solver_identity': stored['fingerprint'],
                'evaluation_identity': p['identity']}, ensure_ascii=False) + '\n')
        p = dict(p, identity=stored)
    if output.exists() and any(output.iterdir()):
        if not resume or not identity_path.is_file():
            raise ValueError('Nonempty output requires --resume and a matching run identity')
        validate_run_identity(json.loads(identity_path.read_text(encoding='utf-8')),
                              p['identity'], artifact=identity_path)
    elif resume:
        raise ValueError('No existing artifact run to resume')
    output.mkdir(parents=True, exist_ok=True)
    _write(identity_path, p['identity'])
    if (output / 'result.json').is_file():
        result = json.loads((output / 'result.json').read_text(encoding='utf-8'))
        if result.get('status') == 'complete' or result.get('graded') and result.get('status') == 'evaluation_pending':
            _validate_completed_result(p, result, output, require_metrics=False)
            return _finish_required_metrics(p, result, output, judge_request)
        if result.get('status') in {'unsubmitted', 'evaluation_pending'} and not result.get('graded'):
            return _finish_required_metrics(p, result, output, judge_request)
    renderer = renderer or ArtifactRenderer(output / 'versions', p['contract'])
    if p['contract'].source_format == 'latex' and getattr(renderer, 'compiler_identity', None) != p['identity']['settings']['execution']['compiler_identity']:
        raise ValueError('LaTeX compiler changed after preflight; prepare a fresh run')
    executor = EnvironmentTaskExecutor(p['manifest'], benchmark_root=data_root() / 'benchmarks',
                                      renderer=renderer, rule_card=p['card'])
    paged = bool(p['manifest'].metadata.get('artifact_task_pdf'))
    initial_asset = replace(p['task_asset'], page_end=min(p['task_asset'].page_end,
                            p['task_asset'].page_start + 1)) if paged else p['task_asset']
    task_attachments = _attachments(initial_asset, p['provider'], output / 'task_pages')
    if provider_capabilities(p['provider'], p['model']).pdf_text:
        packet = pdf_text_request(LLMRequest('', '', attachments=task_attachments))
        (output / 'task_extracted.txt').write_text(packet.user_prompt, encoding='utf-8')
        _write(output / 'task_delivery.json', {'mode': 'extracted_text_v1',
            'task_pdf_sha256': p['task_asset'].sha256,
            'text_sha256': sha256(packet.user_prompt.encode('utf-8')).hexdigest(),
            'pages': [p['task_asset'].page_start, p['task_asset'].page_end],
            'limitations': ['Text extraction can lose diagrams, equations and layout; no OCR.']})
    live_session = None
    review_attachment_cache = {}
    checkpoint = None
    checkpoint_path = output / 'contest_checkpoint.json'
    if checkpoint_path.is_file():
        checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        validate_run_identity(checkpoint['run_identity'], p['identity'], artifact=checkpoint_path)
        task = checkpoint['session']['tasks'][0]
        if task['versions']:
            renderer(None, 'render_pdf', {'content': task['versions'][-1]['content']})
    calls_path = output / 'calls.jsonl'

    def invoke(fn, request):
        response = fn(request)
        if request.purpose == 'evaluation':
            # Persist before parsing so malformed responses remain diagnosable.
            with (output / 'judge_responses.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'model': response.model, 'usage': response.usage,
                    'metadata': request.metadata, 'text': response.text},
                    ensure_ascii=False) + '\n')
        with calls_path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'purpose': request.purpose, 'model': response.model,
                'usage': response.usage, 'tool_calls': [asdict(x) for x in response.tool_calls]},
                ensure_ascii=False) + '\n')
        return response

    def review_visible():
        visible = bool(renderer.latest)
        if visible and p['config'].current_turn_only:
            visible = live_session is not None and any(
                live_session.version_created_this_turn(version.version_hash)
                and sha256(version.content.encode('utf-8')).hexdigest() == renderer.latest['source_sha256']
                for task in live_session.tasks for version in task.versions)
        return visible

    def review_document():
        if not review_visible():
            return None
        from artifact_pdf_reader import asset_document
        asset = build_task_asset(Path(renderer.latest['pdf']))
        if asset.sha256 != renderer.latest['pdf_sha256']:
            raise ValueError('Rendered candidate PDF changed before review')
        return asset_document(asset, label='Current rendered candidate')

    def decorate(request, *, coach=False):
        if coach:
            return request  # Coach must never see the task PDF or rendered answer.
        if paged:
            selected = request.metadata.get('problem_pdf_read')
            attachments = request.attachments if selected else task_attachments
            reading = ('\nPDF delivery is paginated. Document 1 is the official task; '
                       'document 2, when listed, is the current rendered candidate. '
                       'To read other pages, select the actual read_problem_pdf action and supply '
                       'problem_id, pages (at most two) and document in its tool arguments. '
                       'Do not put a reader command in work.content or render_pdf.content; '
                       'those fields are the answer itself, not operations to execute. '
                       'Only the selected pages are attached; other pages remain available.\n')
            if selected:
                reading += 'Attached selection: ' + json.dumps(selected) + '\n'
            else:
                reading += f'Attached document 1 pages {initial_asset.page_start}-{initial_asset.page_end}.\n'
            return replace(request, system_prompt=request.system_prompt + '\n' +
                p['contract'].prompt(review_required=p['config'].review_required),
                user_prompt=request.user_prompt + reading, attachments=attachments)
        attachments = task_attachments + request.attachments
        if review_visible():
            key = renderer.latest['source_sha256']
            if key not in review_attachment_cache:
                asset = build_task_asset(Path(renderer.latest['pdf']))
                review_attachment_cache[key] = _attachments(asset, p['provider'],
                    output / 'review_pages' / key)
            attachments += review_attachment_cache[key]
        return replace(request, system_prompt=request.system_prompt + '\n' + p['contract'].prompt(review_required=p['config'].review_required),
                       attachments=attachments)

    def query(system, user):
        coach = system.startswith('You are Coach')
        request = LLMRequest(system_prompt=system, user_prompt=user,
                             purpose='coach' if coach else 'private_think')
        return invoke(agent_request, decorate(request, coach=coach)).text
    query.request = lambda request: invoke(agent_request, decorate(request, coach=request.purpose == 'coach'))
    query.supports_budgeted_requests = True
    query.max_output_tokens = p['max_output_tokens']

    def act(request):
        return invoke(agent_request, decorate(request))
    def bind_session(session):
        nonlocal live_session
        live_session = session
        if paged:
            session.artifact_review_document = review_document
    act.bind_session = bind_session
    act.supports_attachments = provider_capabilities(p['provider'], p['model']).attachments
    act.supports_pdf_text = provider_capabilities(p['provider'], p['model']).pdf_text

    def persist(session, memory):
        _write(checkpoint_path, {'session': session, 'memory': memory,
                                 'run_identity': p['identity']})

    session_path = output / 'contest_session.json'
    if session_path.is_file():
        contest = json.loads(session_path.read_text(encoding='utf-8'))
        validate_run_identity(contest['run_identity'], p['identity'], artifact=session_path)
    else:
        contest = run_contest(p['manifest'], query, p['config'], action_request_fn=act,
            action_transport=provider_capabilities(p['provider']).action_transport,
            coach_query_fn=query, task_action_executor=executor,
            checkpoint_callback=persist,
            session_checkpoint=checkpoint['session'] if checkpoint else None,
            memory_checkpoint=checkpoint['memory'] if checkpoint else None)
        contest['run_identity'] = p['identity']
        _write(session_path, contest)
    source = contest['submissions'].get('deliverable', '')
    if not source:
        result = dict(status='evaluation_pending', graded=False,
                      coordination_required=True, evaluation_pending=['coordination'],
                      reason='No artifact candidate was available for submission',
                      contest_file=str(session_path), run_identity=p['identity'])
        result['submission_diagnostics'] = submission_diagnostics(
            contest['session_checkpoint']['tasks'][0], p['config'].review_required)
        _write(output / 'result.json', result)
        return _finish_required_metrics(p, result, output, judge_request)
    task = contest['session_checkpoint']['tasks'][0]
    latest = task['versions'][-1]
    current_reviews = [r for r in task['reviews'] if not r['stale']
                       and r['version_hash'] == latest['version_hash']]
    deadline_collected = any(
        e['kind'] == 'deadline_drafts_submitted'
        and e['payload'].get('selected_versions', {}).get('deliverable', {}).get('version_hash') == latest['version_hash']
        for e in contest['memory']['events']
    )
    if (latest['content'] != source or (not deadline_collected and (
            not latest['evidence_refs'] or
            (p['config'].review_required and (any(r['decision'] == 'reject' for r in current_reviews) or
            not any(r['decision'] == 'approve' and r['reviewer'] != latest['author']
                    for r in current_reviews)))))):
        raise ValueError('Submitted artifact lacks current independent approval/render evidence')
    receipt = renderer(None, 'render_pdf', {'content': source})
    rubric = load_rubric(p['rubric'])
    from contest_reporting import metered_judge
    task_judge_state = {}
    measured_task_judge = metered_judge(judge_request, task_judge_state)
    def judge(request):
        if request.metadata.get('pdf_paging_stage') == 'final':
            task_judge_state['pdf_paging'] = {
                'version': request.metadata['pdf_paging_version'],
                'coverage': request.metadata['pdf_page_coverage']}
        return invoke(measured_task_judge, request)
    if p['judge_provider'] == 'tinker':
        from evaluation.pdf_paging import paged_judge
        judge = paged_judge(judge, output / 'rubric_pdf_evidence',
                           cache_namespace=p['identity']['settings']['evaluation'])
    _write(output / 'evaluation_status.json', {'status': 'started', 'pdf_sha256': receipt['pdf_sha256']})
    from judge_references import with_rule_context
    judge = with_rule_context(judge, p['card'].rules_text)
    if p.get('winner_references'):
        from judge_references import with_winner_references
        judge = with_winner_references(judge, p['winner_references'])
    try:
        if p['contract'].kind == 'slides':
            evaluated = evaluate_slide_deck(task_pdf=p['task_asset'].path,
                task_pages=f"{p['task_asset'].page_start}-{p['task_asset'].page_end}",
                submission=Path(receipt['pdf']), rubric=rubric, work_dir=output / 'evaluation',
                provider=p['judge_provider'], model=p['judge_model'],
                media='images' if p['judge_provider'] in {'perplexity', 'pplx'} else 'pdf',
                min_slides=p['contract'].min_pages, max_slides=p['contract'].max_pages,
                max_file_size_mb=p['contract'].max_file_size_mb, request_fn=judge)
            evaluation = evaluated.evaluation.to_dict()
        else:
            evaluated = RubricDocumentEvaluator(request_fn=judge, rubric=rubric,
                task_asset=p['task_asset'], submission_pdf=Path(receipt['pdf']),
                reference_text=_reference_text(p.get('benchmark') or {}),
                media='images' if p['judge_provider'] in {'perplexity', 'pplx'} else 'pdf',
                image_work_dir=output / 'evaluation', task_label=p['card'].competition_id)
            evaluation = evaluated.evaluate().to_dict()
    except Exception as exc:
        _write(output / 'evaluation_status.json', {'status': 'failed', 'error': str(exc),
                                                  **task_judge_state})
        raise
    if task_judge_state.get('pdf_paging'):
        from evaluation.pdf_paging import LIMITATION
        evaluation.setdefault('limitations', []).append(LIMITATION)
        evaluation['prompt_version'] += '+pdf_page_evidence_v1'
    result = dict(status='evaluation_pending', graded=True, artifact=receipt, evaluation=evaluation,
                  official_score_equivalent=False,
                  coordination_required=True, evaluation_pending=['coordination'],
                  run_identity=p['identity'], contest_file=str(session_path),
                  comparability=p['card'].comparability,
                  scope='artifact-only proxy; does not score live/physical performance',
                  generation_budget=contest['budget'], judge_budget_separate=True)
    benchmark_evaluation = (p.get('benchmark') or {}).get('evaluation') or {}
    for key in ('grading_scope', 'score_basis', 'execution_verified'):
        if key in benchmark_evaluation:
            result[key] = benchmark_evaluation[key]
    result['task_evaluation_usage'] = task_judge_state.get('evaluation_usage')
    if task_judge_state.get('pdf_paging'):
        result['pdf_paging'] = task_judge_state['pdf_paging']
    result['evaluation_binding'] = _evaluation_binding(p['identity'], receipt, evaluation)
    _write(output / 'result.json', result)
    _write(output / 'evaluation_status.json', {'status': 'complete'})
    return _finish_required_metrics(p, result, output, judge_request)
