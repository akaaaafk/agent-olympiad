"""Resume finalized mini judges with hash-bound, visually reviewed PDF pages.

Does not modify shared src, PDFs, contestant traces, or active pipeline state.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

REVIEWED = {
    '5d4a66c8440aa69d0c971f66d2932c23760f9ce1571f234ed9604262b320f0fc': {
        1: '[Visually reviewed image cover; manual transcription: WELCOME TO THE 2025 '
           'NATIONAL COLLEGIATE CYBER DEFENSE COMPETITION. NCCDC logo. '
           'Decorative background; no task instructions on this page.]',
    },
    'da988df705a2a2acef1d91f4446e6b5c7589def04ece15a49e3790a8c105f7e1': {
        14: '[Visually reviewed blank page; no visible text, charts, or task content.]',
    },
}


def reviewed_extractor(original):
    def extract(path, *, page_start=None, page_end=None):
        text, count, warnings = original(path, page_start=page_start, page_end=page_end)
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for number, transcription in REVIEWED.get(digest, {}).items():
            warning = f'Page {number} produced no extractable text.'
            if warning in warnings:
                # Only replace an empty page; never replace existing extracted content.
                marker = f'--- page {number} ---'
                text = text.replace(marker, marker + '\n' + transcription, 1)
                warnings = [item for item in warnings if item != warning]
        return text, count, warnings
    return extract


def deduplicate_packet_excerpts(request, original):
    """Remove only excerpts verified identical to pages still delivered in full."""
    if request.purpose not in {'evaluation', 'grading', 'judge'}:
        return original(request)
    from artifacts.pdf_ingest import extract_pdf_text
    user = request.user_prompt
    removed = []
    for asset in request.attachments:
        digest = hashlib.sha256(Path(asset.path).read_bytes()).hexdigest()
        if digest != 'da988df705a2a2acef1d91f4446e6b5c7589def04ece15a49e3790a8c105f7e1':
            continue
        start = user.index('TASK TEXT:\n\n') + len('TASK TEXT:\n\n')
        end = user.index('\n\nSUBMISSION TEXT:', start)
        task = user[start:end]
        parts = re.split(r'Packet page (\d+):\s*', task)
        if len(parts) == 1:
            continue
        normalize = lambda value: re.sub(r'\s+', '', value)
        for page, excerpt in zip(parts[1::2], parts[2::2]):
            number = int(page)
            if not (asset.page_start <= number <= asset.page_end):
                raise ValueError('Duplicate excerpt outside delivered PDF range')
            text, _, warnings = extract_pdf_text(asset.path, page_start=number, page_end=number)
            text = text.split('\n', 1)[1]
            if warnings or normalize(excerpt) != normalize(text):
                raise ValueError(f'Cannot verify duplicate packet page {number}')
            removed.append(number)
        user = user[:start] + parts[0] + (
            'Repeated packet excerpts omitted here after exact non-whitespace comparison; '
            'all original pages are delivered in full below.\n') + user[end:]
    converted = original(replace(request, user_prompt=user))
    if removed:
        prefix, pdf_text = converted.user_prompt.split('PDF TEXT DELIVERY:', 1)
        compact = re.sub(r'\s+', ' ', pdf_text)
        assert re.sub(r'\s+', '', compact) == re.sub(r'\s+', '', pdf_text)
        converted = replace(converted, user_prompt=prefix + 'PDF TEXT DELIVERY:' + compact,
                            metadata={**converted.metadata,
                            'deduplicated_packet_pages': removed,
                            'pdf_whitespace_normalized': True})
    return converted


def main():
    # Importing the page helpers must not change another runner's dataset.
    with patch.dict(os.environ, {'AGENT_OLYMPIAD_DATA_ROOT': str(ROOT / 'data/mini_data')}):
        _main()


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    dest = args.run.resolve()
    result_path = dest / 'contest_session.json'
    before = json.loads(result_path.read_text(encoding='utf-8'))
    settings = before['run_identity']['settings']
    execution, evaluation = settings['execution'], settings['evaluation']
    if before['system_variant'] != 'single_agent' or evaluation['provider'] != 'tinker':
        raise ValueError('This repair is scoped to the diagnosed single-agent Tinker runs')
    if not before.get('evaluation_pending'):
        raise ValueError('No pending evaluations; refuse to repeat completed judges')
    import artifacts.pdf_ingest as ingest
    import run_competition_batch as runner
    from contest_manifest import load_contest_manifest
    from contest_task_judge import judge_task
    from contest_run_identity import read_finalized_contest_result
    import llm
    original_pdf_request = llm.pdf_text_request
    from env_config import load_repo_dotenv
    load_repo_dotenv(ROOT / '.env')
    manifest_path = Path(before['run']['manifest'])
    cli = ['--live', '--resume', '--benchmark-root', str(ROOT / 'data/mini_data/benchmarks'),
           '--contest-manifest', str(manifest_path), '--no-judge-collab',
           '--system-variant', 'single_agent', '--provider', execution['provider'],
           '--model', execution['model'], '--judge-provider', evaluation['provider'],
           '--judge-model', evaluation['model'], '--max-output-tokens', str(execution['max_output_tokens']),
           '--temperature', str(execution['temperature']), '--output', str(dest)]
    state, identity = runner.inspect_contest_run(cli)
    if state != 'resume':
        raise ValueError(f'Expected finalized resume, got {state}')
    read_finalized_contest_result(dest, identity)
    manifest = load_contest_manifest(manifest_path, benchmark_root=ROOT / 'data/mini_data/benchmarks')
    calls = []
    class Captured(Exception):
        pass
    def capture(request):
        converted = llm.pdf_text_request(request)
        calls.append({'characters': len(converted.user_prompt),
                      'deduplicated_packet_pages': converted.metadata.get('deduplicated_packet_pages', []),
                      'pdfs': [str(a.path) for a in request.attachments]})
        raise Captured()
    capture.supports_pdf_text = True
    capture.supports_attachments = False
    with patch.object(ingest, 'extract_pdf_text', reviewed_extractor(ingest.extract_pdf_text)), patch.object(
            llm, 'pdf_text_request', lambda request: deduplicate_packet_excerpts(request, original_pdf_request)):
        for task in manifest.tasks:
            try:
                judge_task(task, before['submissions'][task.task_id], capture)
            except Captured:
                pass
        if not calls:
            raise ValueError('Expected a captured judge request')
        print(json.dumps({'preflight': 'passed', 'requests': calls}), flush=True)
        if args.preflight:
            return
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup = dest / ('before_pdf_judge_repair_' + stamp)
        backup.mkdir()
        for file in dest.iterdir():
            if file.is_file():
                shutil.copy2(file, backup / file.name)
        audit = {'kind': 'evaluation_only_reviewed_pdf_text', 'started_at': stamp,
                 'original_result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
                 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'reviewed_pages': REVIEWED, 'requests': calls, 'backup': str(backup)}
        is_cfa = any(call['deduplicated_packet_pages'] for call in calls)
        audit['judge_max_output_tokens'] = 3000 if is_cfa else execution['max_output_tokens']
        audit['pdf_whitespace_normalized'] = is_cfa
        (dest / 'pdf_judge_repair.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
        original_resolver = runner.resolve_request_fn
        def judge_resolver(**kwargs):
            if is_cfa:
                kwargs['max_output_tokens'] = 3000
            return original_resolver(**kwargs)
        with patch.object(sys, 'argv', ['run_competition_batch.py', *cli]), patch.object(
                runner, 'resolve_request_fn', judge_resolver):
            try:
                runner.main()
            except BaseException as exc:
                audit.update(status='failed', error=f'{type(exc).__name__}: {exc}')
                (dest / 'pdf_judge_repair.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
                raise
    after = json.loads(result_path.read_text(encoding='utf-8'))
    for key in ('submissions', 'memory', 'budget', 'session_checkpoint', 'run_identity', 'timing'):
        if after.get(key) != before.get(key):
            raise AssertionError(f'Contestant state changed: {key}')
    if after.get('evaluation_pending'):
        raise AssertionError('Evaluations remain pending')
    audit.update(status='complete', contestant_state_unchanged=True,
                 grade=after['grade'])
    (dest / 'pdf_judge_repair.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps({'verified': True, 'grade': after['grade']}), flush=True)


if __name__ == '__main__':
    main()
