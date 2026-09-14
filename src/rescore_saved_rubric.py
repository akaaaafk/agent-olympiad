"""Post-hoc registered rubric judge for saved submissions; never rerun contestants."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from env_config import load_repo_dotenv
from evaluation.finalize import _reference_text
from evaluation.models import load_rubric, scale_rubric
from evaluation.rubric_llm import RubricDocumentEvaluator
from llm import resolve_request_fn

ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


class FullTextRubricEvaluator(RubricDocumentEvaluator):
    """Keep the complete saved submission and task, including long case packets."""

    def _user_prompt(self) -> str:
        prompt = super()._user_prompt()
        for heading, value, limit in (
            ('TASK TEXT:', self.task_text, 12000),
            ('SUBMISSION TEXT:', self.submission_text, 16000),
            ('OFFICIAL REFERENCE / MARKING NOTES (judge-only):', self.reference_text, 12000),
        ):
            value = value.strip()
            if value:
                prompt = prompt.replace(heading + '\n\n' + value[:limit], heading + '\n\n' + value, 1)
        return prompt


def score_saved(job: dict, *, request_fn, model: str) -> dict:
    output = Path(job['output'])
    source = output / 'contest_session.json'
    raw = source.read_bytes()
    session = json.loads(raw)
    catalog = ROOT / 'data/benchmarks' / job['competition'] / 'benchmark.json'
    problem = next(r for r in json.loads(catalog.read_text(encoding='utf-8')) if r['problem_id'] == job['problem_id'])
    evaluation = problem.get('evaluation', {})
    if evaluation.get('evaluator_id') != 'rubric_llm_v1':
        return {'status': 'not_applicable', 'reason': 'Registered evaluator is not rubric_llm_v1'}
    submission = str(session.get('submissions', {}).get(job['problem_id']) or '').strip()
    target = output / 'task_rubric_posthoc.json'
    if job['competition'] == 'fyziklani':
        result = {'status': 'excluded', 'reason': 'Known invalid solver input: task PDF was not delivered; no valid paired submission to evaluate', 'source_sha256': hashlib.sha256(raw).hexdigest()}
        write(target, result)
        return result
    if not submission:
        result = {'status': 'excluded', 'reason': 'No saved submission; do not invent an answer or grade', 'source_sha256': hashlib.sha256(raw).hexdigest()}
        write(target, result)
        return result
    rubric_path = ROOT / evaluation['rubric_path']
    binding = {
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'problem_sha256': hashlib.sha256(json.dumps(problem, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        'rubric_sha256': hashlib.sha256(rubric_path.read_bytes()).hexdigest(),
        'judge_model': model, 'judge_temperature': 0.0,
        'prompt_version': 'saved_rubric_full_text_v1',
    }
    if target.exists():
        old = json.loads(target.read_text(encoding='utf-8'))
        if old.get('status') == 'complete' and all(old.get(k) == v for k, v in binding.items()):
            return old
    rubric = load_rubric(rubric_path)
    if problem.get('total_points'):
        rubric = scale_rubric(rubric, float(problem['total_points']))
    calls = []
    def judge(request):
        write(output / 'task_rubric_posthoc_prompt.json', {'system_prompt': request.system_prompt, 'user_prompt': request.user_prompt, 'purpose': request.purpose})
        response = request_fn(request)
        calls.append({'usage': response.usage, 'text': response.text, 'model': response.model})
        write(output / 'task_rubric_posthoc_calls.json', {'calls': calls})
        return response
    started = time.monotonic()
    result = FullTextRubricEvaluator(
        request_fn=judge, rubric=rubric, task_text=str(problem.get('problem_description') or ''),
        submission_text=submission, reference_text=_reference_text(problem), media='text',
        task_label=job['problem_id'], deliverable_label=evaluation.get('deliverable', 'submission'),
        prompt_version='saved_rubric_full_text_v1',
    ).evaluate()
    limitations = evaluation.get('limitations') or []
    if isinstance(limitations, str):
        limitations = [limitations]
    result.limitations.extend(x for x in limitations if x not in result.limitations)
    value = dict(binding, status='complete', method='rubric_llm_v1', score=result.total_score,
                 max_score=result.max_score, accuracy=result.total_score/result.max_score,
                 evaluation=result.to_dict(), rubric_path=str(rubric_path.relative_to(ROOT)),
                 judge_api_calls=len(calls), judge_sec=time.monotonic()-started,
                 scope='Post-hoc score of unchanged saved text submission; not an official competition verdict')
    write(target, value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--model', default='openai/gpt-5.4-mini')
    args = parser.parse_args()
    load_repo_dotenv(ROOT / '.env')
    base_request = resolve_request_fn(provider='perplexity', model=args.model, max_output_tokens=8192, temperature=0.0)
    def request(req):
        # A paid judge can be resumed from its sidecar. Fail promptly on quota/auth errors.
        return base_request(req, max_retries=1)
    jobs = json.loads((args.batch/'status.json').read_text(encoding='utf-8'))['jobs']
    results = []
    for job in jobs:
        source = Path(job['output'])/'contest_session.json'
        if not source.exists() or json.loads(source.read_text(encoding='utf-8')).get('grade', {}).get('graded'):
            continue
        if (Path(job['output'])/'result.json').exists():
            continue
        try:
            result = score_saved(job, request_fn=request, model=args.model)
        except Exception as exc:
            response = getattr(exc, 'response', None)
            result = {'status': 'failed', 'error_type': type(exc).__name__,
                      'error': str(exc)[:1200],
                      'http_status': getattr(response, 'status_code', None)}
        row = {'competition': job['competition'], 'variant': job['variant'], 'output': job['output'], **result}
        results.append(row)
        quota_blocked = 'insufficient_quota' in result.get('error', '')
        write(args.batch/'rubric_posthoc_status.json', {
            'status': 'blocked_quota' if quota_blocked else 'in_progress',
            'results': results,
            'resume_command': 'python src/rescore_saved_rubric.py --batch ' + str(args.batch),
        })
        print(job['competition'],job['variant'],result['status'],result.get('score'),result.get('max_score'),flush=True)
        if quota_blocked:
            print('BLOCKED: Perplexity insufficient_quota; saved submissions remain unchanged.', flush=True)
            return
    write(args.batch/'rubric_posthoc_status.json', {'status': 'finished', 'results': results})


if __name__ == '__main__':
    main()
