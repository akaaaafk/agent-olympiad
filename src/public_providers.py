"""Public model APIs behind the canonical request, attachment and action contract.

Native REST adapters use existing requests; no additional SDK is required.
They return all tool calls for the contest dispatcher to validate atomically.
"""
import base64
import os
from urllib.parse import quote

import requests

from env_config import provider_config, require_explicit_model
from llm_usage import local_preflight


@local_preflight
def _limit(request, configured):
    if not isinstance(configured, int) or isinstance(configured, bool) or configured <= 0:
        raise ValueError('max_output_tokens must be a positive integer')
    attempts = request.metadata.get('max_transport_attempts')
    if isinstance(attempts, int) and attempts <= 0:
        raise ValueError('Transport call budget exhausted')
    value = request.metadata.get('max_output_tokens_override', configured)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError('max_output_tokens must be a positive integer')
    remaining = request.metadata.get('max_transport_output_tokens')
    if isinstance(remaining, int):
        if remaining <= 0:
            raise ValueError('Transport output budget exhausted')
        value = min(value, remaining)
    return min(value, configured)


def _post(provider, url, headers, payload):
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180, allow_redirects=False)
    except requests.RequestException:
        # Never include request headers, a secret-bearing SDK exception or body.
        raise RuntimeError(f'{provider} connection failed; check endpoint/network') from None
    if not response.ok:
        raise RuntimeError(f'{provider} HTTP {response.status_code}; check credentials, '
                           'model access, context limits and provider dashboard')
    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(f'{provider} returned invalid JSON') from None
    if not isinstance(data, dict):
        raise ValueError(f'{provider} returned a non-object response')
    return data


@local_preflight
def _tools(request):
    for tool in request.tools:
        if tool.get('type', 'function') != 'function':
            raise ValueError('Only canonical function tools are supported')
    return request.tools


def _finish_usage(reason):
    return {'finish_reason': 'length' if reason in {'max_tokens', 'MAX_TOKENS'} else reason,
            'provider_finish_reason': reason}


def make_public_caller(provider, model, *, max_output_tokens=8192, temperature=0.2):
    from llm import (LLMResponse, LLMToolCall, _attachment_bytes,
                     parse_response_tool_calls, pdf_text_request)
    profile = provider_config(provider)
    model = require_explicit_model(model or profile['model'])
    key = os.environ.get(profile['api_key_env'])
    if not key:
        raise ValueError(f"Set {profile['api_key_env']} to use {provider}")
    base_url = profile['base_url'].rstrip('/')

    def invalid(usage, reason='Invalid function-call payload'):
        # The HTTP call completed. Keep its usage even when parsing fails, and
        # reject the entire batch without exposing any partial calls.
        return LLMResponse('', provider, model, usage={**usage,
            'tool_error': reason + '; no action executed'})

    if provider in {'deepseek', 'openai_compatible'}:
        def call_text(request):
            request = pdf_text_request(request)
            limit = _limit(request, max_output_tokens)
            payload = {'model': model, 'max_tokens': limit, 'temperature': temperature,
                       'messages': [{'role': 'system', 'content': request.system_prompt},
                                    {'role': 'user', 'content': request.user_prompt}]}
            if request.tools:
                payload['tools'] = [{'type': 'function', 'function': {
                    'name': t['name'], 'description': t.get('description', ''),
                    'parameters': t['parameters']}} for t in _tools(request)]
                payload['tool_choice'] = request.tool_choice
                if request.parallel_tool_calls is not None:
                    payload['parallel_tool_calls'] = request.parallel_tool_calls
            data = _post(provider, base_url + '/chat/completions',
                         {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, payload)
            choices = data.get('choices') or []
            raw_usage = data.get('usage') or {}
            usage = {**raw_usage, 'api_calls': 1, 'max_output_tokens': limit,
                     'pdf_delivery': request.metadata.get('pdf_delivery')}
            if 'prompt_tokens' in raw_usage:
                usage['input_tokens'] = raw_usage['prompt_tokens']
            if 'completion_tokens' in raw_usage:
                usage['output_tokens'] = raw_usage['completion_tokens']
            if len(choices) != 1 or not isinstance(choices[0], dict):
                return invalid(usage, 'No unique completion choice')
            choice = choices[0]
            finish = choice.get('finish_reason')
            usage.update(_finish_usage(finish))
            if finish not in {'stop', 'tool_calls'}:
                return LLMResponse('', provider, model, usage={**usage,
                    'tool_error': f'Incomplete or filtered response ({finish}); no action executed'})
            try:
                message = choice['message']
                calls = parse_response_tool_calls({'output': [
                    {'type': 'function_call', 'call_id': item.get('id', ''), **item['function']}
                    for item in message.get('tool_calls') or []]})
            except (KeyError, TypeError, ValueError, AttributeError):
                return invalid(usage)
            return LLMResponse(message.get('content') or '', provider, model, usage, calls)
        call_text.supports_attachments = False
        call_text.supports_pdf_text = True
        return call_text

    @local_preflight
    def encode_assets(request):
        encoded_assets = []
        for asset in request.attachments:
            if asset.mime_type != 'application/pdf' and not asset.mime_type.startswith('image/'):
                raise ValueError(f'Unsupported attachment MIME type: {asset.mime_type}')
            encoded_assets.append((asset.mime_type,
                base64.b64encode(_attachment_bytes(asset)).decode('ascii')))
        return encoded_assets

    def call(request):
        limit = _limit(request, max_output_tokens)
        encoded_assets = encode_assets(request)
        if provider == 'anthropic':
            content = [{'type': 'text', 'text': request.user_prompt}]
            for mime, data in encoded_assets:
                content.append({'type': 'document' if mime == 'application/pdf' else 'image',
                                'source': {'type': 'base64', 'media_type': mime, 'data': data}})
            payload = dict(model=model, max_tokens=limit, temperature=temperature,
                           messages=[{'role': 'user', 'content': content}])
            if request.system_prompt:
                payload['system'] = request.system_prompt
            if request.tools:
                payload['tools'] = [dict(name=t['name'], description=t.get('description', ''),
                                        input_schema=t['parameters']) for t in _tools(request)]
                payload['tool_choice'] = {'type': {'required': 'any', 'auto': 'auto', 'none': 'none'}[request.tool_choice]}
                if request.tool_choice != 'none' and request.parallel_tool_calls is not None:
                    payload['tool_choice']['disable_parallel_tool_use'] = not request.parallel_tool_calls
            data = _post(provider, base_url + '/messages',
                         {'x-api-key': key, 'anthropic-version': '2023-06-01',
                          'Content-Type': 'application/json'}, payload)
            finish = data.get('stop_reason')
            usage = {**(data.get('usage') or {}), 'api_calls': 1,
                     'max_output_tokens': limit, **_finish_usage(finish)}
            if finish not in {'end_turn', 'tool_use', 'stop_sequence'}:
                return LLMResponse('', provider, model, usage={**usage,
                    'tool_error': f'Incomplete or refused response ({finish}); no action executed'})
            blocks = data.get('content') or []
            try:
                calls = tuple(LLMToolCall(b['name'], b['input'], b.get('id', ''))
                              for b in blocks if b.get('type') == 'tool_use')
                if any(not isinstance(c.arguments, dict) or not isinstance(c.name, str)
                       or not c.name.strip() for c in calls):
                    return invalid(usage)
            except (KeyError, TypeError, AttributeError):
                return invalid(usage)
            return LLMResponse('\n'.join(b.get('text', '') for b in blocks
                                         if b.get('type') == 'text'), provider, model, usage, calls)
        if provider != 'gemini':
            raise ValueError(f'Unsupported public provider: {provider}')
        parts = [{'text': request.user_prompt}]
        parts.extend({'inlineData': {'mimeType': mime, 'data': data}} for mime, data in encoded_assets)
        payload = {'contents': [{'role': 'user', 'parts': parts}],
                   'generationConfig': {'maxOutputTokens': limit, 'temperature': temperature,
                                        'candidateCount': 1}}
        if request.system_prompt:
            payload['systemInstruction'] = {'parts': [{'text': request.system_prompt}]}
        if request.tools:
            payload['tools'] = [{'functionDeclarations': [
                {'name': t['name'], 'description': t.get('description', ''),
                 'parametersJsonSchema': t['parameters']} for t in _tools(request)]}]
            payload['toolConfig'] = {'functionCallingConfig': {
                'mode': {'required': 'ANY', 'auto': 'AUTO', 'none': 'NONE'}[request.tool_choice]}}
        data = _post(provider, base_url + '/models/' + quote(model.removeprefix('models/'), safe='')
                     + ':generateContent', {'x-goog-api-key': key, 'Content-Type': 'application/json'}, payload)
        raw = data.get('usageMetadata') or {}
        usage = {'api_calls': 1, 'max_output_tokens': limit, 'provider_usage': raw}
        if 'promptTokenCount' in raw:
            usage['input_tokens'] = raw['promptTokenCount']
        if 'candidatesTokenCount' in raw or 'thoughtsTokenCount' in raw:
            usage['output_tokens'] = raw.get('candidatesTokenCount', 0) + raw.get('thoughtsTokenCount', 0)
        candidates = data.get('candidates') or []
        if len(candidates) != 1:
            return LLMResponse('', provider, model, usage={**usage,
                'tool_error': 'No unique Gemini candidate; request blocked or response invalid'})
        candidate = candidates[0]
        finish = candidate.get('finishReason')
        usage.update(_finish_usage(finish))
        if finish != 'STOP':
            return LLMResponse('', provider, model, usage={**usage,
                'tool_error': f'Incomplete or blocked response ({finish}); no action executed'})
        parts = (candidate.get('content') or {}).get('parts') or []
        try:
            calls = tuple(LLMToolCall(p['functionCall']['name'], p['functionCall'].get('args', {}),
                                     p['functionCall'].get('id', '')) for p in parts if 'functionCall' in p)
            if any(not isinstance(c.arguments, dict) or not isinstance(c.name, str)
                   or not c.name.strip() for c in calls):
                return invalid(usage)
        except (KeyError, TypeError, AttributeError):
            return invalid(usage)
        # Each contest turn is reconstructed as a fresh request, not a continued
        # Gemini conversation; thought parts/signatures are not contestant text.
        return LLMResponse('\n'.join(p['text'] for p in parts if 'text' in p and not p.get('thought')),
                           provider, model, usage, calls)
    call.supports_attachments = True
    call.supports_pdf_text = False
    return call
