"""Bounded action selection and raw argument sampling for the Tinker adapter.

Only a complete call leaves this module. Raw argument chunks are private
transport buffers, never tool executions, submissions or shared memory.
"""
from __future__ import annotations

import json
import re
from typing import Any

from llm import (LLMRequest, LLMResponse, LLMToolCall, _coerce_emulated_tool_call,
                 _json_objects, _validate_emulated_tool_call)
from llm_usage import normalized_usage, failure_usage
from answer_content import action_content_error
from argument_limits import (field_limits, violations, violation_text, raw_rewrite_prompts,
                             rewrite_target, EDITING_RULES, preserves_structure)

VERSION = 'staged_raw_arguments_v7_answer_command_guard'
HEADER_TOKENS = 512


def _raw_fields(tool: dict) -> list[str]:
    """Free text is streamed separately; identifiers and enums stay metadata.

    Default new string fields to raw transport so adding a report/answer field
    cannot silently put a long payload back inside the small JSON header.
    """
    metadata_names = {'agent', 'reviewer', 'language', 'resource'}
    return [name for name, prop in (tool.get('parameters') or {}).get('properties', {}).items()
            if prop.get('type') == 'string' and not prop.get('enum')
            and name not in metadata_names and not name.endswith(('_id', '_hash'))]


def _partial_call(name: str, arguments: dict, fields: list[str], tools: tuple[dict, ...]) -> LLMToolCall:
    if not isinstance(arguments, dict) or set(arguments).intersection(fields):
        raise ValueError('metadata must be an object without the separately generated raw fields')
    call = LLMToolCall(name, {**arguments, **dict.fromkeys(fields, '')})
    error = _validate_emulated_tool_call(call, tools)
    if error:
        raise ValueError(error)
    return LLMToolCall(name, arguments)


def _stopped_string(raw: str) -> str:
    # The provider can include or exclude the quote stop, including punctuation
    # fused into the same token. Never accept a second key or a prose suffix.
    candidate = '"' + raw.strip()
    try:
        value, end = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError:
        candidate += '"'
        value, end = json.JSONDecoder().raw_decode(candidate)
    if not re.fullmatch(r'[\s,}\"]*', candidate[end:]):
        raise ValueError('unexpected content after metadata value stop')
    return value


def draft_scope(request: LLMRequest) -> dict[str, Any]:
    return {key: request.metadata.get(key) for key in ('session_id', 'agent', 'task_id')}


def _draft_view(text: str) -> str:
    # The complete text remains in the private checkpoint/trace. Limit only
    # its prompt projection; explicitly identify omitted text, never invent it.
    if len(text) <= 40000:
        return text
    return text[:20000] + f'\n[... {len(text) - 40000} draft characters omitted ...]\n' + text[-20000:]


def selection_prompt(tools: tuple[dict, ...]) -> str:
    return (
        '\n\nACTION SELECTION TRANSPORT\n'
        'Choose exactly one available function. This step selects the action; '
        'do not solve the problem or write long content yet. Return one small JSON object only. '
        'For a simple call use {"name":"function_name","arguments":{...}}. '
        'For source code, documents, reasoning or other long string arguments, omit that string '
        'from arguments and name it in body_argument: '
        '{"name":"function_name","arguments":{...},"body_argument":"exact_string_field"}. '
        'The next generation will supply that argument as raw text, without JSON escaping. '
        'body_argument must be an existing non-enum string field in the selected schema. '
        'Supply all other required arguments now. Use exactly the field names in that schema. '
        'No prose, multiple calls, or extra keys. Short arguments may be inline.\n'
        'FUNCTION SCHEMAS:\n' + json.dumps(list(tools), ensure_ascii=False)
    )


def _selection(text: str, tools: tuple[dict, ...]) -> tuple[LLMToolCall, str | None]:
    value = _json_objects(text)[0]
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, dict) or 'body_argument' not in value:
        call = _coerce_emulated_tool_call(text)
        error = _validate_emulated_tool_call(call, tools)
        if error:
            raise ValueError(error)
        return call, None
    if set(value) - {'name', 'arguments', 'body_argument'}:
        raise ValueError('action descriptor has unknown keys')
    name, args, field = value.get('name'), value.get('arguments', {}), value['body_argument']
    if not isinstance(name, str) or not isinstance(args, dict) or not isinstance(field, str):
        raise ValueError('action descriptor requires a name, object arguments and string body_argument')
    tool = next((t for t in tools if t.get('name') == name), None)
    schema = (tool or {}).get('parameters') or {}
    prop = (schema.get('properties') or {}).get(field) or {}
    if not tool or prop.get('type') != 'string' or prop.get('enum') or field in args:
        raise ValueError('body_argument must name an omitted, available non-enum string argument')
    # Validate every other field and required argument before spending tokens
    # generating a body. The body is never a way around a scoped enum.
    call = LLMToolCall(name, {**args, field: ''})
    error = _validate_emulated_tool_call(call, tools)
    if error:
        raise ValueError(error)
    return LLMToolCall(name, args), field


def _length_error(call: LLMToolCall, request: LLMRequest) -> str | None:
    rows = violations(call.name, call.arguments, request.metadata)
    return violation_text(call.name, rows) if rows else None


def request_action(caller, request: LLMRequest, *, model: str, max_output_tokens: int,
                   max_tool_retries: int, images: tuple = ()) -> LLMResponse:
    # A normal long call needs a name, metadata and a body. All recovery and body
    # continuation samples share this cap, the turn's API cap and token budget.
    max_samples = 3 + max_tool_retries
    available_calls = request.metadata.get('max_transport_attempts')
    if isinstance(available_calls, int):
        max_samples = min(max_samples, max(0, available_calls))
    remaining = request.metadata.get('max_transport_output_tokens')
    remaining = remaining if isinstance(remaining, int) else None
    override = request.metadata.get('max_output_tokens_override')
    cap = min(max_output_tokens, override) if isinstance(override, int) else max_output_tokens
    scope = draft_scope(request)
    previous = request.metadata.get('unexecuted_action_draft')
    draft = (str(previous.get('text') or '') if isinstance(previous, dict)
             and previous.get('scope') == scope and previous.get('executed') is False else '')
    pending_body = (previous.get('pending_body') if isinstance(previous, dict)
                    and previous.get('scope') == scope and previous.get('executed') is False
                    and previous.get('version') == VERSION else None)
    pending_metadata = (previous.get('pending_metadata') if isinstance(previous, dict)
                        and previous.get('scope') == scope and previous.get('executed') is False
                        and previous.get('version') == VERSION else None)
    phase, selected, body_field = 'select', None, None
    body_fields: list[str] = []
    body_index = 0
    base_arguments: dict = {}
    metadata_fields: list[str] = []
    metadata_index = 0
    metadata_arguments: dict = {}
    metadata_tokens: list[int] = []
    metadata_system = metadata_user = ''
    metadata_repair = None
    prefix_tokens: list[int] = []
    body = ''
    body_system = body_user = ''
    body_rewrite_attempt = 0
    body_rewrite_target = None
    selection_draft = draft
    selection_tokens: list[int] = []
    selection_system = selection_user = ''
    pending_selection = (previous.get('pending_selection') if isinstance(previous, dict)
                         and previous.get('scope') == scope and previous.get('executed') is False
                         and previous.get('version') == VERSION else None)
    # A descriptor may resume only against the identical observation/schema.
    # Unlike raw argument buffers, it has not yet named an action to revalidate.
    if (isinstance(pending_selection, dict) and pending_selection.get('model') == model
            and pending_selection.get('tools') == list(request.tools)
            and pending_selection.get('base_system') == request.system_prompt
            and pending_selection.get('base_user') == request.user_prompt
            and pending_selection.get('argument_limits') == request.metadata.get('action_argument_limits', {})
            and pending_selection.get('argument_limits_by_task') == request.metadata.get('action_argument_limits_by_task', {})
            and pending_selection.get('payload_limits') == request.metadata.get('action_payload_limits', {})
            and isinstance(pending_selection.get('system_prompt'), str)
            and isinstance(pending_selection.get('user_prompt'), str)
            and isinstance(pending_selection.get('tokens'), list)
            and all(type(t) is int and t >= 0 for t in pending_selection['tokens'])
            and getattr(caller, 'supports_continuation', False) is True):
        selection_tokens = list(pending_selection['tokens'])
        selection_system, selection_user = pending_selection['system_prompt'], pending_selection['user_prompt']
    output_used = input_used = calls_used = unknown_used = 0
    transport_failed = False
    trace = []
    finish, error = None, 'Action transport budget exhausted'

    def result(call: LLMToolCall | None = None) -> LLMResponse:
        usage = {'output_tokens': output_used, 'input_tokens': input_used, 'api_calls': calls_used,
                 'unknown_usage_attempts': unknown_used, 'transport_failed': transport_failed,
                 'max_output_tokens': trace[-1]['max_output_tokens'] if trace else 0,
                 'tool_retries': sum('error' in entry for entry in trace[:-1]),
                 'finish_reason': finish, 'action_transport': 'emulated',
                 'action_transport_version': VERSION, 'transport_recovery_managed': True,
                 'sampling_trace': trace,
                 'pdf_delivery': request.metadata.get('pdf_delivery'),
                 'deduplicated_packet_pages': request.metadata.get('deduplicated_packet_pages', [])}
        if call is None:
            usage['tool_error'] = error or 'Action assembly incomplete: transport budget exhausted'
            if draft or selection_tokens:
                usage['unexecuted_action_draft'] = {'scope': scope, 'text': draft, 'executed': False,
                                                   'version': VERSION}
                if phase == 'select' and selection_tokens:
                    usage['unexecuted_action_draft']['pending_selection'] = {
                        'model': model, 'tools': list(request.tools), 'tokens': list(selection_tokens),
                        'base_system': request.system_prompt, 'base_user': request.user_prompt,
                        'argument_limits': request.metadata.get('action_argument_limits', {}),
                        'argument_limits_by_task': request.metadata.get('action_argument_limits_by_task', {}),
                        'payload_limits': request.metadata.get('action_payload_limits', {}),
                        'system_prompt': selection_system, 'user_prompt': selection_user}
                pending = pending_body
                if phase == 'body':
                    pending = {'model': model, 'name': selected.name, 'arguments': selected.arguments,
                               'base_arguments': base_arguments, 'body_fields': body_fields,
                               'body_argument': body_field, 'tokens': list(prefix_tokens),
                               'system_prompt': body_system, 'user_prompt': body_user,
                               'rewrite_attempt': body_rewrite_attempt,
                               'rewrite_target': body_rewrite_target,
                               'argument_limits': field_limits(selected.name, selected.arguments, request.metadata),
                               'payload_limits': request.metadata.get('action_payload_limits', {}),
                               'tool': next(t for t in request.tools if t.get('name') == selected.name)}
                if pending:
                    usage['unexecuted_action_draft']['pending_body'] = pending
                if phase == 'arguments':
                    usage['unexecuted_action_draft']['pending_metadata'] = {
                        'model': model, 'name': selected.name, 'fields': metadata_fields,
                        'index': metadata_index, 'arguments': metadata_arguments,
                        'tokens': metadata_tokens, 'system_prompt': metadata_system,
                        'user_prompt': metadata_user,
                        'repair': metadata_repair,
                        'tool': next(t for t in request.tools if t.get('name') == selected.name)}
        return LLMResponse('' if call else draft, 'tinker', model, usage=usage,
                           tool_calls=(call,) if call else ())

    def body_prompts() -> tuple[str, str]:
        limits = field_limits(selected.name, selected.arguments, request.metadata)
        system = (request.system_prompt + '\n\nRAW ACTION ARGUMENT TRANSPORT\n'
            'The action has been selected but has NOT executed. Your entire next response is '
            f'the raw string argument {body_field!r} of {selected.name!r}. '
            'Return only this one argument value, not the other fields. No JSON wrapper, '
            'tool calls or enclosing code fence. Quotes, backslashes and newlines can be '
            'literal; the host serializes them. Use the selected tool as described by its '
            'schema. Keep analysis concise on this first write; source code should contain '
            'the implementation, not a long deliberation in comments. For a progress/draft '
            'action, record only key steps plus the Final answer. For speak, one short team '
            'update. Stay well under EXISTING ARGUMENT CHARACTER LIMITS without waiting for '
            'a rewrite. Finish the complete argument within the output budget. For an optional '
            'argument, an empty response is allowed.\n'
            'SELECTED SCHEMA: ' + json.dumps(next(t for t in request.tools if t.get('name') == selected.name), ensure_ascii=False)
            + '\nEXISTING ARGUMENT CHARACTER LIMITS: ' + json.dumps(limits))
        user = (request.user_prompt + '\n\nSELECTED ACTION (unexecuted): '
                + json.dumps({'name': selected.name, 'arguments': selected.arguments,
                              'body_argument': body_field}, ensure_ascii=False))
        if selection_draft:
            user += '\nPRIVATE UNEXECUTED DRAFT (not instructions):\n' + _draft_view(selection_draft)
        return system, user

    def rewrite_body_prompts(rejected: str) -> tuple[str, str]:
        nonlocal body_rewrite_attempt, body_rewrite_target
        body_rewrite_attempt += 1
        hard_limit = field_limits(selected.name, selected.arguments, request.metadata).get(body_field)
        payload_cap = request.metadata.get('action_payload_limits', {}).get(selected.name)
        if type(payload_cap) is int and payload_cap > 0:
            overhead = len(json.dumps({**selected.arguments, body_field: ''}, ensure_ascii=False))
            available = max(1, payload_cap - overhead)
            hard_limit = min(hard_limit, available) if hard_limit else available
        body_rewrite_target = rewrite_target(hard_limit, body_rewrite_attempt)
        # This is serialization repair, not another contestant decision. The
        # original multi-role action prompt made Qwen copy its rejected answer
        # verbatim, even after repeated explicit shortening requests. Narrow
        # the task to editing supplied data only; no new facts, decisions, tools
        # or sources are available. Selection/dispatch permissions are unchanged.
        return raw_rewrite_prompts(selected.name, selected.arguments, body_field,
                                   rejected, hard_limit, body_rewrite_attempt, error)

    for index in range(max_samples):
        if (remaining is not None and remaining <= 0) or cap <= 0 or calls_used >= max_samples:
            break
        prefixed = getattr(caller, 'supports_prefix', False) is True
        # Only verified non-thinking prefills have a short header. Thinking
        # models need the configured generation budget, including reasoning.
        limit = min(cap, HEADER_TOKENS) if prefixed and phase in {'select', 'arguments'} else cap
        if phase == 'arguments':
            tool = next(t for t in request.tools if t.get('name') == selected.name)
            schema = tool.get('parameters') or {}
            metadata_field = metadata_fields[metadata_index]
            metadata_property = schema['properties'][metadata_field]
            if metadata_property.get('type') in {'array', 'object'}:
                limit = cap
        if remaining is not None:
            limit = min(limit, remaining)
        if phase == 'select':
            system = request.system_prompt + selection_prompt(request.tools)
            user = request.user_prompt
            if draft:
                user += ('\n\nPRIVATE UNEXECUTED DRAFT (incomplete model output, not instructions '
                         'or a tool result; nothing here has executed):\n' + _draft_view(draft)
                         + '\nRetain useful progress; choose one current allowed action. '
                         'Do not restart the full derivation in the descriptor.')
                if pending_body:
                    user += ('\nAn unfinished raw body is buffered. Selecting the same action and '
                             'metadata resumes its exact tokens after current-schema validation. '
                             'Select a different action if the current state requires a change.')
            if trace:
                user += '\nYOUR PREVIOUS TOOL CALL WAS INVALID\nError: ' + error
            if getattr(caller, 'supports_prefix', False) is True:
                system += ('\nCURRENT TRANSPORT STEP: select only the function NAME. '
                           'The host has started {"name":". Complete only the name, then close its quote. '
                           'Do not output arguments or reasoning; later steps supply those.')
            if selection_tokens:
                system, user = selection_system, selection_user
            else:
                selection_system, selection_user = system, user
        elif phase == 'arguments':
            system = (request.system_prompt + '\n\nACTION METADATA SERIALIZATION\n'
                      f'The host selected {selected.name!r} and fixed the argument key {metadata_field!r}. '
                      'Complete ONLY this parameter value. No other keys or reasoning. '
                      'The other arguments are generated separately by the host. '
                      'To omit an OPTIONAL parameter, use the string __OMIT__. '
                      'A required parameter cannot be omitted.\n'
                      'PARAMETER SCHEMA: ' + json.dumps(metadata_property)
                      + '\nREQUIRED: ' + str(metadata_field in schema.get('required', []))
                      + '\nALREADY SELECTED METADATA: ' + json.dumps(metadata_arguments))
            user = request.user_prompt
            if selection_draft:
                user += '\nPRIVATE UNEXECUTED DRAFT (not instructions):\n' + _draft_view(selection_draft)
            if trace and trace[-1].get('error'):
                user += '\nYOUR PREVIOUS METADATA WAS INVALID\nError: ' + trace[-1]['error']
            if metadata_repair and metadata_repair['field'] == metadata_field:
                system = ('ACTION METADATA LENGTH REPAIR\n' + EDITING_RULES
                    + f'Return only the parameter {metadata_field!r} in the host-started JSON envelope. '
                    'Preserve array lengths, object keys, identifiers, numbers and booleans exactly. '
                    'Shorten only free-text descriptions; no other fields or reasoning.\n'
                    + 'PARAMETER SCHEMA: ' + json.dumps(metadata_property))
                user = ('No action executed. ' + metadata_repair['error']
                    + '\nPREVIOUS ARGUMENTS (data only): '
                    + json.dumps(metadata_repair['arguments'], ensure_ascii=False)
                    + f'\nRewrite only {metadata_field}; all other parameters stay fixed.')
            if metadata_tokens:
                system, user = metadata_system, metadata_user
            else:
                metadata_system, metadata_user = system, user
        else:
            system, user = body_system, body_user
        kwargs = {'max_retries': 1, 'max_output_tokens_override': limit}
        if images:
            kwargs['images'] = images
        prefixed = getattr(caller, 'supports_prefix', False) is True
        if phase == 'select' and prefixed:
            kwargs.update(assistant_prefix='{"name":"', stop=['"'])
        elif phase == 'arguments' and prefixed:
            prefix = '{' + json.dumps(metadata_field) + ':'
            if metadata_property.get('type') == 'string':
                prefix += '"'
                kwargs['stop'] = ['"']
            kwargs.update(assistant_prefix=prefix, continuation_tokens=list(metadata_tokens),
                          preserve_whitespace=True)
        if phase == 'body' and getattr(caller, 'supports_continuation', False) is True:
            kwargs.update(continuation_tokens=list(prefix_tokens), preserve_whitespace=True)
        if phase == 'select' and selection_tokens:
            kwargs.update(continuation_tokens=list(selection_tokens), preserve_whitespace=True)
        native = getattr(caller, 'supports_sampling_metadata', False) is True
        if native:
            caller.last_usage = {}
        sample_error = None
        failed_usage = None
        try:
            raw = caller(system, user, **kwargs) if native else caller(system, user, **({'images': images} if images else {}))
        except RuntimeError as exc:
            failed_usage = (getattr(caller, 'last_usage', {}) if native else {}) or failure_usage(exc)
            transport_failed = True
            raw, sample_error = '', str(exc)
        usage = failed_usage if failed_usage is not None else caller.last_usage if native else {
            'output_tokens': max(1, len(raw) // 4), 'api_calls': 1, 'finish_reason': 'stop'}
        usage = {**usage, **normalized_usage(usage)}
        used = int(usage['output_tokens'])
        output_used += used
        input_used += usage['input_tokens']
        calls_used += usage['api_calls']
        unknown_used += usage['unknown_usage_attempts']
        if remaining is not None:
            remaining -= used
        actual_limit = min(limit, int(usage.get('max_output_tokens') or limit))
        finish = usage.get('finish_reason')
        incomplete = finish == 'length' or used > actual_limit
        if incomplete:
            finish = 'length'
        entry = {'stage': phase, 'input_tokens': usage.get('input_tokens', 0),
                 'api_calls': usage['api_calls'], 'unknown_usage_attempts': usage['unknown_usage_attempts'],
                 'output_tokens': used, 'max_output_tokens': actual_limit,
                 'finish_reason': finish, 'text': raw, 'executed': False}
        if native:
            entry['sample_tokens'] = list(getattr(caller, 'last_sample_tokens', []))
            entry['chat_template'] = usage.get('chat_template')
        if phase in {'body', 'arguments'}:
            entry['argument'] = body_field if phase == 'body' else metadata_field
        if phase == 'body' and body_rewrite_attempt:
            entry['rewrite_attempt'] = body_rewrite_attempt
            entry['rewrite_target_chars'] = body_rewrite_target
        trace.append(entry)
        if sample_error:
            error = sample_error
            entry['error'] = error
            break
        draft_before_sample = draft
        if phase == 'select' and getattr(caller, 'supports_continuation', False) is True:
            selection_tokens += list(caller.last_sample_tokens)
            raw = caller.decode_completion_tokens(selection_tokens)
        if phase == 'arguments' and getattr(caller, 'supports_continuation', False) is True:
            metadata_tokens += list(caller.last_sample_tokens)
            raw = caller.decode_completion_tokens(metadata_tokens)
            draft = json.dumps({'name': selected.name, 'arguments': metadata_arguments,
                                'pending_argument': metadata_field}, ensure_ascii=False) + '\nUNEXECUTED METADATA:\n' + raw
        if phase == 'body':
            if getattr(caller, 'supports_continuation', False) is True:
                prefix_tokens += list(caller.last_sample_tokens)
                body = caller.decode_completion_tokens(prefix_tokens)
            else:
                body = raw
            entry['argument_characters'] = len(body)
            draft = json.dumps({'name': selected.name, 'arguments': selected.arguments,
                                'body_argument': body_field}, ensure_ascii=False) + '\nUNEXECUTED BODY:\n' + body
        elif phase == 'select':
            draft = draft or raw
        if incomplete:
            error = 'Output token limit reached; incomplete action buffered, no partial action executed.'
            entry['error'] = error
            if phase != 'body' and raw and raw != draft:
                draft += '\nREJECTED INCOMPLETE ' + phase.upper() + ':\n' + raw
            # Continue the exact descriptor/reasoning/argument sequence with
            # its original prompt. Only a stopped INVALID descriptor restarts.
            if phase == 'body' and getattr(caller, 'supports_continuation', False) is not True:
                phase = 'select'
            continue
        if phase == 'select':
            selection_tokens = []
        if finish not in {None, 'stop'}:
            error = f'Unexpected sampling finish reason: {finish!r}; no action executed'
            entry['error'] = error
            break
        if phase in {'select', 'arguments'}:
            try:
                if phase == 'arguments':
                    if metadata_property.get('type') == 'string' and prefixed:
                        value = _stopped_string(raw)
                    else:
                        envelope = ('{' + json.dumps(metadata_field) + ':' + raw) if prefixed else raw
                        if prefixed and not envelope.rstrip().endswith('}'):
                            envelope += '}'
                        parsed = _json_objects(envelope)[0]
                        if not isinstance(parsed, dict) or set(parsed) != {metadata_field}:
                            raise ValueError('metadata response must contain only the selected parameter')
                        value = parsed[metadata_field]
                    required = metadata_field in schema.get('required', [])
                    omitted = value == '__OMIT__' and not required
                    arguments = {} if omitted else {metadata_field: value}
                    field_tool = {**tool, 'parameters': {'type': 'object', 'properties': {metadata_field: metadata_property},
                                  'required': [metadata_field] if required else [], 'additionalProperties': False}}
                    field_error = _validate_emulated_tool_call(LLMToolCall(selected.name, arguments), (field_tool,))
                    if field_error:
                        raise ValueError(field_error)
                    if metadata_repair and metadata_repair['field'] == metadata_field:
                        if not preserves_structure(metadata_repair['value'], value, metadata_field):
                            raise ValueError('Metadata length repair changed structured data; nothing executed')
                    # Check before advancing the cursor: a failed final metadata
                    # value must not leave its index one past the field list.
                    if metadata_index + 1 == len(metadata_fields):
                        candidate_args = {**metadata_arguments, **arguments}
                        candidate = _partial_call(selected.name, candidate_args, body_fields, request.tools)
                        length_error = _length_error(candidate, request)
                        if length_error:
                            metadata_repair = dict(field=metadata_field, value=value,
                                arguments=candidate_args, error=length_error)
                            raise ValueError(length_error)
                    metadata_arguments.update(arguments)
                    metadata_repair = None
                    metadata_index += 1
                    metadata_tokens = []
                    if metadata_index < len(metadata_fields):
                        metadata_system = metadata_user = ''
                        error = ''
                        continue
                    selected = _partial_call(selected.name, metadata_arguments, body_fields, request.tools)
                elif prefixed and not raw.lstrip().startswith(('{', '[')):
                    # Stop strings can end within a token, e.g. Qwen's '\",'
                    # token. Accept only its JSON punctuation suffix, not an
                    # arbitrary second action or prose after the stop marker.
                    name, separator, suffix = raw.strip().partition('"')
                    if separator and not re.fullmatch(r'[\s,}\"]*', suffix):
                        raise ValueError('unexpected content after function name stop')
                    tool = next((t for t in request.tools if t.get('name') == name), None)
                    if tool is None:
                        raise ValueError(f'unavailable function name: {name!r}')
                    properties = (tool.get('parameters') or {}).get('properties', {})
                    body_fields = _raw_fields(tool)
                    body_field = body_fields[0] if body_fields else None
                    selected = LLMToolCall(name, {})
                    selection_draft = draft_before_sample
                    metadata_fields = [key for key in properties if key not in body_fields]
                    metadata_arguments, metadata_index, metadata_tokens = {}, 0, []
                    metadata_system = metadata_user = ''
                    if metadata_fields:
                        if (isinstance(pending_metadata, dict) and pending_metadata.get('model') == model
                                and pending_metadata.get('name') == name and pending_metadata.get('tool') == tool
                                and pending_metadata.get('fields') == metadata_fields
                                and type(pending_metadata.get('index')) is int
                                and 0 <= pending_metadata['index'] < len(metadata_fields)
                                and isinstance(pending_metadata.get('arguments'), dict)
                                and set(pending_metadata['arguments']) <= set(metadata_fields[:pending_metadata['index']])
                                and isinstance(pending_metadata.get('tokens'), list)
                                and all(type(t) is int and t >= 0 for t in pending_metadata['tokens'])
                                and isinstance(pending_metadata.get('system_prompt'), str)
                                and isinstance(pending_metadata.get('user_prompt'), str)):
                            saved_tool = {**tool, 'parameters': {**tool['parameters'], 'required': []}}
                            if _validate_emulated_tool_call(LLMToolCall(name, pending_metadata['arguments']), (saved_tool,)) is None:
                                metadata_arguments = dict(pending_metadata['arguments'])
                                metadata_index = pending_metadata['index']
                                metadata_tokens = list(pending_metadata['tokens'])
                                metadata_system, metadata_user = pending_metadata['system_prompt'], pending_metadata['user_prompt']
                                metadata_repair = pending_metadata.get('repair')
                                entry['resuming_unexecuted_metadata_tokens'] = len(metadata_tokens)
                        pending_metadata = None
                        phase = 'arguments'
                        continue
                    selected = _partial_call(name, {}, body_fields, request.tools)
                else:
                    selected, body_field = _selection(raw, request.tools)
                    body_fields = [body_field] if body_field else []
                    selection_draft = draft_before_sample
                error = (action_content_error(selected.name, selected.arguments, request.metadata)
                         or _length_error(selected, request) or '')
                if error:
                    raise ValueError(error)
            except ValueError as exc:
                error = str(exc)
                entry['error'] = error
                if phase == 'arguments':
                    metadata_tokens = []
                if raw and raw != draft:
                    draft += '\nREJECTED ' + phase.upper() + ':\n' + raw
                continue
            if body_field is None:
                return result(LLMToolCall(selected.name, selected.arguments, f'tinker-staged-{index + 1}'))
            base_arguments = dict(selected.arguments)
            body_index = 0
            current_tool = next(t for t in request.tools if t.get('name') == selected.name)
            if (isinstance(pending_body, dict) and pending_body.get('model') == model
                    and pending_body.get('name') == selected.name
                    and pending_body.get('base_arguments') == base_arguments
                    and pending_body.get('body_fields') == body_fields
                    and pending_body.get('body_argument') in body_fields
                    and isinstance(pending_body.get('arguments'), dict)
                    and pending_body.get('tool') == current_tool
                    and pending_body.get('argument_limits', {}) == field_limits(selected.name, selected.arguments, request.metadata)
                    and pending_body.get('payload_limits', {}) == request.metadata.get('action_payload_limits', {})
                    and isinstance(pending_body.get('tokens'), list)
                    and all(type(t) is int and t >= 0 for t in pending_body['tokens'])
                    and isinstance(pending_body.get('system_prompt'), str)
                    and isinstance(pending_body.get('user_prompt'), str)
                    and getattr(caller, 'supports_continuation', False) is True):
                resume_index = body_fields.index(pending_body['body_argument'])
                saved_args = pending_body['arguments']
                try:
                    if (set(saved_args) != set(base_arguments) | set(body_fields[:resume_index])
                            or any(saved_args.get(k) != v for k, v in base_arguments.items())):
                        raise ValueError('saved partial arguments do not match current selection')
                    resumed = _partial_call(selected.name, saved_args, body_fields[resume_index:], request.tools)
                    if _length_error(resumed, request):
                        raise ValueError('saved partial arguments exceed current limits')
                except ValueError:
                    pending_body = None
                else:
                    selected, body_index = resumed, resume_index
                    body_field = body_fields[body_index]
                    prefix_tokens = list(pending_body['tokens'])
                    body_system, body_user = pending_body['system_prompt'], pending_body['user_prompt']
                    body_rewrite_attempt = pending_body.get('rewrite_attempt', 0)
                    body_rewrite_target = pending_body.get('rewrite_target')
                    body = caller.decode_completion_tokens(prefix_tokens)
                    pending_body = None
                    entry['resuming_unexecuted_body_tokens'] = len(prefix_tokens)
                    entry['resuming_completed_body_fields'] = body_fields[:body_index]
                    phase, finish = 'body', None
                    continue
            # Keep the preselection draft for the body, not just the descriptor.
            pending_body = None
            body_system, body_user = body_prompts()
            finish = None
            phase, body, prefix_tokens = 'body', '', []
            continue
        assert selected is not None and body_field is not None
        pending_body = None
        completed = LLMToolCall(selected.name, {**selected.arguments, body_field: body},
                                f'tinker-staged-{index + 1}')
        command_error = action_content_error(completed.name, completed.arguments, request.metadata)
        if command_error:
            error = entry['error'] = command_error
            # This is a wrong action, not an overlong answer. Do not send it to
            # the editing-only rewriter or infer/execute the embedded command.
            # Re-selection uses the unchanged tools and shared attempt budget.
            phase, selected, body_field = 'select', None, None
            pending_body = pending_metadata = None
            body, prefix_tokens, selection_tokens = '', [], []
            body_rewrite_attempt, body_rewrite_target = 0, None
            continue
        current_schema = next(t for t in request.tools if t.get('name') == selected.name).get('parameters', {})
        error = (_length_error(completed, request)
                 or ('empty required raw argument' if not body.strip() and body_field in current_schema.get('required', []) else None))
        if error is None and body_index + 1 < len(body_fields):
            selected = completed
            body_index += 1
            body_field = body_fields[body_index]
            body, prefix_tokens = '', []
            body_rewrite_attempt, body_rewrite_target = 0, None
            body_system, body_user = body_prompts()
            finish = None
            continue
        error = error or _validate_emulated_tool_call(completed, request.tools)
        if error is None:
            return result(completed)
        entry['error'] = error
        # The action and metadata are already validated. Repair this raw field
        # directly; reselecting and reserializing metadata can consume the entire
        # remaining allowance before a replacement body is ever sampled.
        # Keep the full rejected text private; never clip it into an action.
        if (index + 1 < max_samples and calls_used < max_samples
                and (remaining is None or remaining > 0)):
            body_system, body_user = rewrite_body_prompts(body)
            body, prefix_tokens, finish = '', [], None
        else:
            phase = 'select'
    return result()
