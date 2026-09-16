"""Current MCM PDFs -> extracted text -> canonical artifact baseline -> rubric.

Uses the current checkout, never the older text contest snapshot. One serial
lane preserves provider capacity. Completed paid jobs are not rerun.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/tinker_mcm_pdftext_20260916'
MODEL = 'Qwen/Qwen3.6-35B-A3B'
VARIANTS = ('single_agent', 'vallina_otc', 'otc')
sys.path.insert(0, str(ROOT / 'src'))
from artifacts.assets import load_assets
from llm import LLMRequest, LLMAttachment, pdf_text_request
from otc_artifact_pipeline import prepare_artifact_run


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def options(job):
    return dict(competition='mcm', task_pdf=ROOT / job['task_pdf'],
        task_pages=job['task_pages'], output=OUT / 'runs' / job['id'],
        provider='tinker', model=MODEL, judge_provider='tinker', judge_model=MODEL,
        max_output_tokens=8192, max_tokens=220000, system_variant=job['variant'])


def command(job):
    opts = options(job)
    cmd = [sys.executable, '-u', str(ROOT / 'src/run_otc_artifact.py')]
    for name, value in opts.items():
        cmd += ['--' + name.replace('_', '-'), str(value)]
    return cmd


def prepare():
    if (OUT / 'registry.json').exists():
        raise ValueError('Existing registry must be preserved; run without prepare to resume')
    jobs, excluded = [], []
    for row in read(ROOT / 'data/benchmarks/mcm/benchmark.json'):
        if (row.get('evaluation') or {}).get('status') != 'ready':
            excluded.append({'problem_id': row['problem_id'], 'reason': 'not ready'})
            continue
        assets = load_assets(row, ROOT)
        pdfs = [a for a in assets if a.role == 'agent_visible' and a.mime_type == 'application/pdf']
        if len(pdfs) != 1:
            raise ValueError(f"Expected one contestant PDF for {row['problem_id']}")
        asset = pdfs[0]
        from pypdf import PdfReader
        start, end = asset.page_start or 1, asset.page_end or len(PdfReader(asset.path).pages)
        text = pdf_text_request(LLMRequest('', '', attachments=(
            LLMAttachment(asset.path, 'application/pdf', page_start=start, page_end=end),))).user_prompt
        packet = OUT / 'tasks' / (row['problem_id'] + '.txt')
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(text, encoding='utf-8')
        for variant in VARIANTS:
            job = dict(id=f"{row['problem_id'].lower()}_{variant}_qwen3.6-35b-a3b",
                problem_id=row['problem_id'], variant=variant,
                task_pdf=str(asset.path.relative_to(ROOT)), task_pages=f'{start}-{end}',
                task_pdf_sha256=asset.sha256,
                task_text_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
            prepared = prepare_artifact_run(**options(job))
            if (prepared['benchmark'] or {}).get('problem_id') != row['problem_id']:
                raise ValueError('PDF did not map to the expected benchmark')
            job['run_identity'] = prepared['identity']
            jobs.append(job)
        print(f"prepared {row['problem_id']} pages={start}-{end} text_chars={len(text)}", flush=True)
    write(OUT / 'registry.json', dict(provider='tinker', model=MODEL,
        mode='pdf_extracted_text_artifact', jobs=jobs, excluded=excluded,
        limitations=['Extracted text can lose diagrams/equations/layout; no OCR.',
                     'Scores are rubric LLM proxies, not official COMAP awards.']))
    print(f'prepared jobs={len(jobs)} cases={len(jobs) // len(VARIANTS)}', flush=True)


def run():
    from dotenv import dotenv_values
    for name, value in dotenv_values(ROOT / '.env').items():
        if value is not None:
            os.environ[name] = value
    if not os.environ.get('TINKER_API_KEY'):
        raise ValueError('TINKER_API_KEY is required')
    registry = read(OUT / 'registry.json')
    only_variants = {v.strip() for v in os.environ.get('QWEN_MCM_ONLY_VARIANTS', '').split(',') if v.strip()}
    if only_variants - set(VARIANTS):
        raise ValueError('Unknown MCM baseline filter: ' + ', '.join(sorted(only_variants - set(VARIANTS))))
    jobs = [job for job in registry['jobs'] if not only_variants or job['variant'] in only_variants]
    lock = OUT / 'supervisor.lock'
    idle_seconds = int(os.environ.get('QWEN_MCM_WATCHDOG_IDLE_SECONDS', '600'))
    records = read(OUT / 'progress.json') if (OUT / 'progress.json').exists() else []
    with lock.open('x') as stream:
        stream.write(str(os.getpid()))
    try:
        print(f"jobs={len(jobs)} lanes=1 model={MODEL} delivery=pdf_text only_variants={sorted(only_variants)}", flush=True)
        for job in jobs:
            dest = OUT / 'runs' / job['id']
            result_path = dest / 'result.json'
            if result_path.exists() and read(result_path).get('status') in {'complete', 'unsubmitted'}:
                print(f"skip_terminal {job['id']}", flush=True)
                continue
            if prepare_artifact_run(**options(job))['identity'] != job['run_identity']:
                raise ValueError('Runtime/config changed; preserve this run and use a fresh output')
            cmd = command(job)
            if (dest / 'run_identity.json').exists():
                cmd.append('--resume')
            log = OUT / 'logs' / (job['id'] + '.log')
            log.parent.mkdir(parents=True, exist_ok=True)
            record = dict(id=job['id'], problem_id=job['problem_id'],
                          variant=job['variant'], status='running')
            records.append(record)
            write(OUT / 'progress.json', records)
            print(f"start {job['id']}", flush=True)
            last_progress = time.time()
            paths = [log, dest / 'contest_checkpoint.json', dest / 'calls.jsonl', result_path]
            with log.open('a', encoding='utf-8') as stream:
                proc = subprocess.Popen(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
                while proc.poll() is None:
                    latest = max((p.stat().st_mtime for p in paths if p.exists()), default=0)
                    last_progress = max(last_progress, latest)
                    if idle_seconds and time.time() - last_progress > idle_seconds:
                        stream.write(f'\n[watchdog] no progress for {idle_seconds}s\n')
                        stream.flush()
                        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        proc.wait()
                        record['watchdog_killed'] = True
                        break
                    time.sleep(10)
            record['exit_code'] = proc.returncode
            if result_path.exists():
                result = read(result_path)
                record['status'] = result['status']
                record['score'] = (result.get('evaluation') or {}).get('total_score')
                record['max_score'] = (result.get('evaluation') or {}).get('max_score')
            else:
                record['status'] = 'failed'
            write(OUT / 'progress.json', records)
            print(f"finish {job['id']} status={record['status']} score={record.get('score')}", flush=True)
            if record['status'] == 'failed':
                raise RuntimeError(f"Run failed; queue paused, see {log}")
        finished_name = 'finished.json' if not only_variants else 'finished_' + '_'.join(sorted(only_variants)) + '.json'
        write(OUT / finished_name, {'status': 'queue_exhausted', 'variants': sorted(only_variants) or list(VARIANTS)})
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    prepare() if sys.argv[1:] == ['prepare'] else run()
