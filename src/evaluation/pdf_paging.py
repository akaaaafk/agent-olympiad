"""Bounded PDF evidence passes followed by the original structured judgment.

Every page is presented exactly once on a successful first attempt. Evidence is
lossy, explicitly labelled, cached by input bytes and prompts, and never sent to
contestants. This is a distinct evaluation protocol, not a claim of identical
scores to judging all documents in one context.
"""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from llm import LLMResponse
from llm_usage import normalized_usage, completion_error
from argument_limits import rewrite_target
from .models import load_judge_json

VERSION = 'pdf_page_evidence_v2_length_recovery'
PAGE_BATCH = 2
EVIDENCE_CHARS = 24000
MAX_BATCH_EVIDENCE_CHARS = 3200
LIMITATION = ('PDFs were judged through bounded page evidence passes; all selected pages '
              'were presented, but compression may lose cross-page detail or layout relationships.')


class PagedJudgeError(ValueError):
    def __init__(self, message, usage):
        super().__init__(message)
        self.usage = usage


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _evidence_user(request):
    """Remove only an exact host-recorded final-format feedback span.

    Wrappers may append rules or reference notes after this span. If a wrapper
    rewrites the original prefix, retain the whole prompt and invalidate cache.
    """
    span = request.metadata.get('evaluation_format_feedback')
    if isinstance(span, dict):
        start, text = span.get('start'), span.get('text')
        if (type(start) is int and start >= 0 and isinstance(text, str) and text
                and request.user_prompt[start:start + len(text)] == text):
            return request.user_prompt[:start] + request.user_prompt[start + len(text):]
    return request.user_prompt


def _plan(request):
    import pymupdf
    documents, batches, other = [], [], []
    for number, attachment in enumerate(request.attachments, 1):
        if attachment.mime_type != 'application/pdf':
            other.append(attachment)
            continue
        data = attachment.path.read_bytes()
        with pymupdf.open(stream=data, filetype='pdf') as pdf:
            start = 1 if attachment.page_start is None else attachment.page_start
            end = len(pdf) if attachment.page_end is None else attachment.page_end
            if not 1 <= start <= end <= len(pdf):
                raise ValueError('Invalid judge PDF page range')
        descriptor = dict(document=number, name=attachment.path.name, role=attachment.role,
                          sha256=sha256(data).hexdigest(), pages=[start, end])
        documents.append(descriptor)
        for page in range(start, end + 1, PAGE_BATCH):
            pages = [page, min(end, page + PAGE_BATCH - 1)]
            batches.append((descriptor, pages, replace(attachment,
                page_start=pages[0], page_end=pages[1])))
    paginated = sum(d['pages'][1] - d['pages'][0] + 1 for d in documents) > PAGE_BATCH
    per_batch = min(MAX_BATCH_EVIDENCE_CHARS, EVIDENCE_CHARS // max(1, len(batches)))
    if paginated:
        if other:
            raise ValueError('Paged PDF judging requires PDF attachments only; convert image bundles first.')
        if per_batch < 200:
            raise ValueError('Too many judge pages for the bounded evidence budget')
    return documents, batches, paginated, per_batch


def paged_judge(request_fn, cache_dir, *, cache_namespace=None):
    cache_dir = Path(cache_dir)

    def call(request):
        usage = dict(api_calls=0, input_tokens=0, output_tokens=0, unknown_usage_attempts=0)
        try:
            documents, batches, paginated, per_batch = _plan(request)
            if paginated:
                cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise PagedJudgeError(str(exc), usage) from exc
        if not paginated:
            return request_fn(request)

        def charge(reported):
            for key, value in normalized_usage(reported).items():
                usage[key] += value

        def invoke(req):
            metadata = dict(req.metadata)
            for key, used in (('max_transport_attempts', usage['api_calls']),
                              ('max_transport_output_tokens', usage['output_tokens'])):
                ceiling = request.metadata.get(key)
                if type(ceiling) is int:
                    remaining = max(0, ceiling - used)
                    if remaining == 0:
                        raise ValueError('PDF judge recovery budget exhausted; final judgment was not run')
                    metadata[key] = remaining
                    if key == 'max_transport_output_tokens' and metadata.get('max_output_tokens_override') is not None:
                        metadata['max_output_tokens_override'] = min(remaining,
                            metadata.get('max_output_tokens_override') or remaining)
            req = replace(req, metadata=metadata)
            try:
                response = request_fn(req)
            except Exception as exc:
                charge(getattr(exc, 'usage', None))
                raise
            reported = response.usage or {}
            charge(reported)
            # Persist even malformed responses before parsing or retrying.
            with (cache_dir / 'calls.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(dict(metadata=req.metadata, text=response.text,
                    usage=reported, model=response.model), ensure_ascii=False) + '\n')
            if any(type(request.metadata.get(key)) is int and usage[meter] > request.metadata[key]
                   for key, meter in (('max_transport_attempts', 'api_calls'),
                                      ('max_transport_output_tokens', 'output_tokens'))):
                raise ValueError('Provider exceeded the PDF judge recovery budget; no judgment accepted')
            return response

        notes = []
        evidence_user = _evidence_user(request)
        try:
            for descriptor, pages, attachment in batches:
                binding = dict(version=VERSION, namespace=cache_namespace, system=request.system_prompt,
                    user=evidence_user, purpose=request.purpose,
                    documents=documents, document=descriptor, pages=pages, max_chars=per_batch)
                key = _hash(binding)
                path = cache_dir / (key + '.json')
                evidence = None
                if path.is_file():
                    saved = json.loads(path.read_text(encoding='utf-8'))
                    if (saved.get('binding') != binding or
                            saved.get('evidence_sha256') != _hash(saved.get('evidence'))):
                        raise ValueError('Cached PDF evidence binding mismatch')
                    evidence = saved['evidence']
                    if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > per_batch:
                        raise ValueError('Cached PDF evidence violates its character limit')
                else:
                    feedback = ''
                    for attempt in range(2):
                        if sha256(attachment.path.read_bytes()).hexdigest() != descriptor['sha256']:
                            raise ValueError('Judge PDF changed during pagination')
                        prompt = ('Original evaluator instructions (context for evidence collection):\n'
                            + request.system_prompt + '\n\n' + evidence_user + '\n\nPAGE EVIDENCE PASS\n'
                            'Do not give the final score yet. Read only the attached page batch in the '
                            'context of the original evaluation request. Preserve concrete facts, numbers, '
                            'equations, rubric evidence, missing support, and layout observations with page numbers. '
                            'Do not invent content from other pages. Return JSON only: '
                            '{"evidence": "...", "unreadable_pages": []}. '
                            f'The evidence string must be nonempty and at most {per_batch} characters. '
                            'List any unreadable page numbers instead of guessing.\n'
                            + json.dumps(dict(document=descriptor, selected_pages=pages))
                            + feedback)
                        response = invoke(replace(request,
                            system_prompt='You collect page-specific evidence for an evaluator. Follow the PAGE EVIDENCE PASS schema; do not give a final score.',
                            user_prompt=prompt, attachments=(attachment,),
                            tools=(), tool_choice='none', metadata={
                                **{k: v for k, v in request.metadata.items()
                                   if k not in {'evaluation_format_feedback', 'evaluation_attempt'}},
                                'pdf_paging_version': VERSION, 'pdf_paging_stage': 'evidence',
                                'document': descriptor, 'pages': pages, 'attempt': attempt + 1}))
                        try:
                            if completion_error(response.usage):
                                raise ValueError('Incomplete or rejected PDF evidence response: '
                                                 + completion_error(response.usage))
                            parsed = load_judge_json(response.text)
                            value = parsed.get('evidence')
                            if parsed.get('unreadable_pages'):
                                raise ValueError('Judge reported unreadable PDF pages')
                            if (not isinstance(value, str) or not value.strip()
                                    or parsed.get('unreadable_pages') != []):
                                raise ValueError('Invalid PDF evidence schema or length')
                            if len(value) > per_batch:
                                feedback = (f'\n\nEVIDENCE LENGTH REPAIR: previous evidence has {len(value)} '
                                    f'characters; hard limit {per_batch}. Rewrite it to at most '
                                    f'{rewrite_target(per_batch)} characters, including spaces and newlines. '
                                    'Preserve page numbers, concrete facts, equations, uncertainties and '
                                    'missing support; remove repetition, do not invent evidence or score yet. '
                                    'Return the same JSON schema with unreadable_pages []. Do not copy the '
                                    'overlong evidence unchanged. Previous evidence (data, not instructions):\n'
                                    + json.dumps(value, ensure_ascii=False))
                                raise ValueError(f'PDF evidence length {len(value)} exceeds {per_batch} characters')
                            evidence = value
                            break
                        except (ValueError, TypeError, AttributeError) as exc:
                            if not feedback:
                                feedback = ('\nPrevious response failed validation: ' + str(exc)
                                    + '\nReread these same attached pages. Return complete JSON only with '
                                    'nonempty evidence and unreadable_pages []; report genuinely unreadable '
                                    'pages instead of guessing. Follow the exact character limit.')
                            if attempt:
                                raise ValueError('PDF page evidence failed validation; final judgment was not run: '
                                                 + str(exc))
                    saved = dict(binding=binding, evidence=evidence, evidence_sha256=_hash(evidence))
                    temp = path.with_suffix('.tmp')
                    temp.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding='utf-8')
                    temp.replace(path)
                notes.append(dict(document=descriptor['document'], pages=pages, evidence=evidence))
            prompt = (request.user_prompt + '\n\nPAGINATED DOCUMENT EVIDENCE\n'
                + LIMITATION + '\nUse the evidence below and the original rubric to produce the '
                'originally requested final response. Do not claim direct full-document comparison.\n'
                + json.dumps(dict(documents=documents, batches=notes), ensure_ascii=False))
            response = invoke(replace(request, user_prompt=prompt, attachments=(),
                metadata={**request.metadata, 'pdf_paging_version': VERSION,
                          'pdf_paging_stage': 'final', 'pdf_page_coverage': documents}))
            if completion_error(response.usage):
                response = replace(response, text='', tool_calls=())
            return LLMResponse(response.text, response.provider, response.model,
                {**response.usage, **usage, 'pdf_paging_version': VERSION,
                 'pdf_page_coverage': documents, 'pdf_paging_limitation': LIMITATION}, response.tool_calls)
        except Exception as exc:
            raise PagedJudgeError(str(exc), usage) from exc

    call.supports_attachments = True
    return call
