import base64
import io
import json
import os
import re
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from pypdf import PdfReader, PdfWriter
from llm_usage import local_preflight

QueryFn = Callable[[str, str], str]


@dataclass(frozen=True)
class LLMAttachment:
    path: Path
    mime_type: str
    role: str = "agent_visible"
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True)
class LLMToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str = ""


@dataclass(frozen=True)
class LLMRequest:
    system_prompt: str
    user_prompt: str
    attachments: tuple[LLMAttachment, ...] = ()
    purpose: str = "generation"
    metadata: dict[str, Any] = field(default_factory=dict)
    tools: tuple[dict[str, Any], ...] = ()
    tool_choice: Literal["auto", "required", "none"] = "auto"
    parallel_tool_calls: bool | None = None

    def __post_init__(self):
        # Judge assets are opt-in only for explicit evaluator purposes. This
        # applies to every provider and also to contest_action/coach requests.
        if self.purpose not in {"evaluation", "grading", "judge"}:
            if any(a.role != "agent_visible" for a in self.attachments):
                raise ValueError("Judge-only attachments cannot be sent to contestants.")


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)
    tool_calls: tuple[LLMToolCall, ...] = ()


RequestFn = Callable[[LLMRequest], LLMResponse]

ActionTransport = Literal["native", "emulated", "prompt_json"]


@dataclass(frozen=True)
class ProviderCapabilities:
    """Provider features that affect how agent actions are transported."""

    native_tools: bool = False
    emulated_tools: bool = False
    json_schema: bool = False
    token_usage: bool = False
    attachments: bool = False
    pdf_text: bool = False

    @property
    def action_transport(self) -> ActionTransport:
        if self.native_tools:
            return "native"
        if self.emulated_tools:
            return "emulated"
        return "prompt_json"


_PROVIDER_CAPABILITIES: dict[str, ProviderCapabilities] = {
    "perplexity": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "pplx": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "openai": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "oai": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "openagents": ProviderCapabilities(native_tools=True, token_usage=True, attachments=True),
    "vectorengine": ProviderCapabilities(native_tools=True, token_usage=True, attachments=False),
    # Tinker exposes sampling (including vision) but no native tool parameter.
    # Its adapter therefore renders the same schemas into the prompt, validates
    # the sampled call, and performs bounded repair attempts.
    "tinker": ProviderCapabilities(emulated_tools=True, attachments=True, token_usage=True),
    "tml": ProviderCapabilities(emulated_tools=True, attachments=True, token_usage=True),
    "anthropic": ProviderCapabilities(native_tools=True, token_usage=True, attachments=True),
    "gemini": ProviderCapabilities(native_tools=True, token_usage=True, attachments=True),
    "deepseek": ProviderCapabilities(native_tools=True, token_usage=True, pdf_text=True),
    "openai_compatible": ProviderCapabilities(native_tools=True, token_usage=True, pdf_text=True),
}


def provider_capabilities(provider: str, model: str | None = None) -> ProviderCapabilities:
    """Return explicit capabilities instead of branching on provider names."""
    if provider.lower().strip() in {'tinker', 'tml'} and model is not None:
        from tinker_vision import renderer_name
        vision = renderer_name(model) is not None
        return ProviderCapabilities(emulated_tools=True, token_usage=True,
                                    attachments=vision, pdf_text=not vision)
    return _PROVIDER_CAPABILITIES.get(
        provider.lower().strip(),
        ProviderCapabilities(),
    )


def provider_action_transport(provider: str) -> ActionTransport:
    return provider_capabilities(provider).action_transport


@local_preflight
def _attachment_bytes(attachment: LLMAttachment) -> bytes:
    if not attachment.path.is_file():
        raise ValueError(f"Missing LLM attachment: {attachment.path}")
    if attachment.mime_type != "application/pdf" or attachment.page_start is None:
        return attachment.path.read_bytes()

    reader = PdfReader(str(attachment.path))
    start = attachment.page_start
    end = attachment.page_end
    if end is None or start < 1 or end < start or end > len(reader.pages):
        raise ValueError(
            f"Invalid PDF page range {start}-{end} for {attachment.path} "
            f"({len(reader.pages)} pages)"
        )
    writer = PdfWriter()
    for page_index in range(start - 1, end):
        writer.add_page(reader.pages[page_index])
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@local_preflight
def _openai_style_content(request: LLMRequest) -> list[dict[str, str]]:
    content: list[dict[str, str]] = [{"type": "input_text", "text": request.user_prompt}]
    for attachment in request.attachments:
        encoded = base64.b64encode(_attachment_bytes(attachment)).decode("ascii")
        if attachment.mime_type == "application/pdf":
            content.append(
                {
                    "type": "input_file",
                    "filename": attachment.path.name,
                    "file_data": f"data:application/pdf;base64,{encoded}",
                }
            )
        elif attachment.mime_type.startswith("image/"):
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{attachment.mime_type};base64,{encoded}",
                }
            )
        else:
            raise ValueError(f"Unsupported attachment MIME type: {attachment.mime_type}")
    return content


def _response_output_text(data: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(str(content["text"]))
    if chunks:
        return "\n".join(chunks)
    if any(item.get("type") == "function_call" for item in data.get("output", [])):
        return ""
    return ''


def parse_response_tool_calls(data: dict[str, Any]) -> tuple[LLMToolCall, ...]:
    """Parse provider responses using the OpenAI Responses function-call shape."""
    calls: list[LLMToolCall] = []
    for item in data.get("output", []):
        if item.get("type") != "function_call":
            continue
        raw_arguments = item.get("arguments", {})
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Function-call arguments are not valid JSON.") from exc
        else:
            arguments = raw_arguments
        if not isinstance(arguments, dict):
            raise ValueError("Function-call arguments must decode to an object.")
        name = str(item.get("name") or "").strip()
        if not name:
            raise ValueError("Function call is missing its name.")
        calls.append(
            LLMToolCall(
                name=name,
                arguments=arguments,
                call_id=str(item.get("call_id") or item.get("id") or ""),
            )
        )
    return tuple(calls)


@local_preflight
def _request_output_limit(request, configured, *, allow_expansion=False):
    limit = request.metadata.get('max_output_tokens_override')
    limit = configured if limit is None else limit
    if type(limit) is not int or limit <= 0:
        raise ValueError('max_output_tokens must be a positive integer')
    if not allow_expansion:
        limit = min(limit, configured)
    attempts = request.metadata.get('max_transport_attempts')
    if attempts is not None and attempts <= 0:
        return 0
    remaining = request.metadata.get('max_transport_output_tokens')
    return max(0, min(limit, remaining)) if remaining is not None else limit


def _native_response(data, *, provider, model, usage, text=None):
    """Responses-shaped payloads are validated before any consumer sees output."""
    usage = dict(usage)
    status = data.get('status')
    if status is not None:
        usage['provider_status'] = status
    if status not in {None, 'completed'} or data.get('error'):
        details = data.get('incomplete_details') or {}
        reason = details.get('reason') if isinstance(details, dict) else None
        usage.update(finish_reason='length' if reason == 'max_output_tokens' else reason or status or 'failed',
                     provider_finish_reason=reason or status,
                     tool_error='Incomplete or rejected native response; no partial output accepted')
        return LLMResponse('', provider, model, usage=usage)
    try:
        calls = parse_response_tool_calls(data)
        visible = _response_output_text(data) if text is None else text
        if not isinstance(visible, str):
            raise ValueError('Invalid response text')
    except (ValueError, TypeError, KeyError, AttributeError):
        return LLMResponse('', provider, model, usage={**usage,
            'tool_error': 'Malformed native function-call response; no action executed'})
    if not calls and not visible.strip():
        return LLMResponse('', provider, model, usage={**usage, 'tool_error': 'Empty native response'})
    return LLMResponse(visible, provider, model, usage=usage, tool_calls=calls)


def make_openai_responses_caller(model: str = "gpt-4.1", *, max_output_tokens: int = 8192,
                                 temperature: float = 0.2) -> RequestFn:
    """Create a file-capable OpenAI Responses API caller (PDF + images)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY to use direct PDF/image inputs.")
    if model.lower().startswith("glm-"):
        return _make_chat_completions_caller(
            model, provider="openai", api_key=api_key,
            base_url=os.environ.get("OPENAI_BASE_URL"),
            max_output_tokens=max_output_tokens, temperature=temperature,
        )

    from openai import OpenAI

    # Count each transport attempt ourselves; SDK retries bypass shared budgets.
    client = OpenAI(api_key=api_key, max_retries=0)

    def call(request: LLMRequest) -> LLMResponse:
        limit = _request_output_limit(request, max_output_tokens, allow_expansion=True)
        if limit == 0:
            return LLMResponse('', 'openai', model, usage={'api_calls': 0, 'output_tokens': 0,
                                                         'tool_error': 'No remaining transport budget'})
        kwargs: dict[str, Any] = {
            "model": model,
            "instructions": request.system_prompt,
            "max_output_tokens": limit,
            "temperature": temperature,
            "input": [{"role": "user", "content": _openai_style_content(request)}],
        }
        if request.tools:
            kwargs["tools"] = list(request.tools)
            kwargs["tool_choice"] = request.tool_choice
            if request.parallel_tool_calls is not None:
                kwargs["parallel_tool_calls"] = request.parallel_tool_calls
        response = client.responses.create(
            **kwargs,
        )
        data = response.model_dump()
        usage = data.get('usage') or {}
        if getattr(response, "usage", None):
            raw_usage = response.usage
            usage = raw_usage.model_dump() if hasattr(raw_usage, "model_dump") else {}
        return _native_response(data, text=response.output_text, provider='openai', model=model,
                                usage={**usage, 'api_calls': 1, 'max_output_tokens': limit})

    return call


def make_perplexity_responses_caller(
    model: str = "openai/gpt-5.4",
    *,
    max_output_tokens: int = 16000,
    temperature: float | None = 0.2,
) -> RequestFn:
    """Perplexity Agent API caller with multi-image (and optional PDF) attachments.

    Prefer page images for vision models. Native PDF `input_file` support varies by
    backend; rasterize with artifacts.pdf_ingest when in doubt.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("Set PERPLEXITY_API_KEY to use Perplexity multimodal calls.")

    import requests

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def call(request: LLMRequest, max_retries: int = 5) -> LLMResponse:
        attempt_limit = request.metadata.get('max_transport_attempts')
        attempts = min(max_retries, max_retries if attempt_limit is None else attempt_limit)
        output_limit = _request_output_limit(request, max_output_tokens)
        if attempts <= 0 or output_limit <= 0:
            return LLMResponse('', 'perplexity', model, usage={
                'api_calls': 0, 'output_tokens': 0, 'tool_error': 'No remaining transport budget'})
        content = _openai_style_content(request)
        payload = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": output_limit,
            **({'temperature': temperature} if temperature is not None else {}),
        }
        if request.system_prompt.strip():
            payload["instructions"] = request.system_prompt
        if request.tools:
            payload["tools"] = [{**tool, "name": "contest_web_search" if tool.get("name") == "web_search" else tool.get("name")} for tool in request.tools]
            payload["tool_choice"] = request.tool_choice
            if request.parallel_tool_calls is not None:
                payload["parallel_tool_calls"] = request.parallel_tool_calls
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                resp = requests.post(
                    "https://api.perplexity.ai/v1/agent",
                    headers=headers,
                    json=payload,
                    timeout=300,
                )
                if not resp.ok:
                    detail = resp.text[:800]
                    raise requests.exceptions.HTTPError(
                        f"{resp.status_code} {resp.reason}: {detail}",
                        response=resp,
                    )
                data = resp.json()
                usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                response = _native_response(data, provider='perplexity', model=model,
                    usage={**usage, 'api_calls': attempt + 1, 'unknown_usage_attempts': attempt,
                           'max_output_tokens': output_limit})
                return replace(response, tool_calls=tuple(LLMToolCall(
                    'web_search' if call.name == 'contest_web_search' else call.name,
                    call.arguments, call.call_id) for call in response.tool_calls))
            except requests.exceptions.SSLError as exc:
                last_error = RuntimeError(
                    "TLS failed talking to api.perplexity.ai (often a huge image "
                    "payload). Re-render pages as smaller JPEGs, or retry with "
                    "--pages 1-1. Original error: "
                    f"{exc}"
                )
                if attempt < attempts - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    last_error.usage = {'api_calls': attempt + 1, 'unknown_usage_attempts': attempt + 1}
                    raise last_error from exc
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(15 * (attempt + 1))
                else:
                    exc.usage = {'api_calls': attempt + 1, 'unknown_usage_attempts': attempt + 1}
                    raise
        raise RuntimeError(f"Perplexity multimodal call failed: {last_error}")

    return call


def _json_objects(text: str) -> list[Any]:
    """Decode the whole action envelope; never salvage an inner JSON fragment."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    if cleaned.startswith('<tool_call>') and cleaned.endswith('</tool_call>'):
        cleaned = cleaned[len('<tool_call>'):-len('</tool_call>')].strip()
    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f'duplicate JSON key: {key}')
            value[key] = item
        return value
    def invalid_constant(value):
        raise ValueError(f'invalid JSON constant: {value}')
    if not cleaned.startswith(('{', '[')):
        raise ValueError('response contains no JSON tool-call object at its start')
    try:
        return [json.loads(cleaned, object_pairs_hook=unique_keys, parse_constant=invalid_constant)]
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid action JSON at line {exc.lineno}, column {exc.colno}, '
                         f'char {exc.pos}: {exc.msg}') from exc


def _coerce_emulated_tool_call(text: str) -> LLMToolCall:
    """Parse common JSON tool-call shapes emitted by open-weight models."""
    values = _json_objects(text)
    if not values:
        raise ValueError("response contains no JSON tool-call object")
    value = values[0]
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError("response must contain exactly one tool call")
        value = value[0]
    if not isinstance(value, dict):
        raise ValueError("tool call must be a JSON object")
    function = value.get("function")
    if isinstance(function, dict):
        value = function
    name = value.get("name", value.get("action"))
    arguments = value.get("arguments", value.get("parameters"))
    if arguments is None:
        # Open-weight models often omit arguments for no-argument tools.
        arguments = {}
    if not isinstance(name, str) or not name.strip():
        raise ValueError("tool call is missing a string name")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError("tool-call arguments are not valid JSON") from exc
    if not isinstance(arguments, dict):
        raise ValueError("tool-call arguments must be a JSON object")
    return LLMToolCall(name=name.strip(), arguments=arguments)


_JSON_TYPES: dict[str, type[Any] | tuple[type[Any], ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _validate_emulated_tool_call(
    call: LLMToolCall,
    tools: tuple[dict[str, Any], ...],
) -> str | None:
    """Validate one emulated call against the provider-neutral tool schemas."""
    by_name = {str(tool.get("name") or ""): tool for tool in tools}
    tool = by_name.get(call.name)
    if tool is None:
        return (
            f"tool {call.name!r} is unavailable; choose exactly one of "
            f"{sorted(name for name in by_name if name)}"
        )
    schema = tool.get("parameters") or {}
    properties = schema.get("properties") or {}
    required = set(schema.get("required") or ())
    missing = sorted(required - set(call.arguments))
    if missing:
        return f"tool {call.name!r} is missing required arguments {missing}"
    if schema.get("additionalProperties") is False:
        extras = sorted(set(call.arguments) - set(properties))
        if extras:
            return f"tool {call.name!r} has unknown arguments {extras}"
    for name, value in call.arguments.items():
        field = properties.get(name)
        if not isinstance(field, dict):
            continue
        expected = _JSON_TYPES.get(str(field.get("type") or ""))
        if expected is not None and (
            not isinstance(value, expected)
            or field.get("type") == "integer"
            and isinstance(value, bool)
        ):
            return (
                f"argument {name!r} for tool {call.name!r} must be "
                f"{field.get('type')}"
            )
        enum = field.get("enum")
        if isinstance(enum, list) and enum and value not in enum:
            return f"argument {name!r} must be one of {enum}"
        items = field.get("items")
        if field.get("type") == "array" and isinstance(items, dict):
            if not value:
                return f"argument {name!r} must contain at least one item"
            item_enum = items.get("enum")
            if isinstance(item_enum, list) and item_enum and any(
                item not in item_enum for item in value
            ):
                return f"argument {name!r} items must be one of {item_enum}"
    return None


def _tinker_tool_prompt(tools: tuple[dict[str, Any], ...]) -> str:
    compact_tools = [
        {
            "name": tool.get("name"),
            "description": tool.get("description"),
            "parameters": tool.get("parameters"),
        }
        for tool in tools
    ]
    return (
        "\n\nTOOL-CALL TRANSPORT CONTRACT\n"
        "Choose exactly one function from the schemas below. Return only one "
        'JSON object shaped as {"name":"function_name","arguments":{...}}. '
        "Do not use Markdown, prose, XML, or additional calls. Enum values are "
        "strict: copy one exactly as shown. Start directly with the JSON object. "
        "Keep reasoning concise inside the applicable argument on the first attempt; "
        "never prepend a solution or write a long essay before the JSON. "
        "Use the exact argument fields in the selected schema (for example code for submit_code).\n"
        f"FUNCTION SCHEMAS:\n{json.dumps(compact_tools, ensure_ascii=False)}"
    )


@local_preflight
def pdf_text_request(request: LLMRequest) -> LLMRequest:
    """Convert host-selected PDF pages to text without forwarding binary files.

    LLMRequest still enforces contestant/judge separation before conversion.
    Unreviewed scanned pages fail explicitly; this route does not claim OCR/vision.
    """
    if not request.attachments:
        return request
    from artifacts.pdf_ingest import extract_pdf_text
    from artifacts.reviewed_pdf_text import prepare_judge_pdf_text
    request = prepare_judge_pdf_text(request)
    sections = [request.user_prompt,
                "PDF TEXT DELIVERY: extracted text only; diagrams and layout may be lost."]
    for index, attachment in enumerate(request.attachments, 1):
        if attachment.mime_type != "application/pdf":
            raise ValueError("Tinker PDF text delivery accepts PDFs only, not page images.")
        text, _, warnings = extract_pdf_text(attachment.path,
            page_start=attachment.page_start, page_end=attachment.page_end)
        if warnings:
            raise ValueError("PDF text delivery failed: " + "; ".join(warnings))
        if index - 1 in request.metadata.get('compact_pdf_attachment_indices', []):
            text = re.sub(r'\s+', ' ', text)
        sections.append(f"PDF {index} ({attachment.role}) TEXT:\n{text}")
    user = "\n\n".join(sections)
    if len(user) > 600000:
        raise ValueError("PDF text request exceeds 600000 characters; select fewer pages.")
    return replace(request, user_prompt=user, attachments=(),
                   metadata={**request.metadata, "pdf_delivery": "reviewed_text_v2"})


def make_tinker_request_fn(
    model: str,
    *,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
    max_tool_retries: int = 2,
) -> RequestFn:
    """Adapt Tinker sampling to the provider-neutral request/tool interface."""
    if max_tool_retries < 0:
        raise ValueError("max_tool_retries must be non-negative")
    caller = make_tinker_caller(model, max_output_tokens=max_output_tokens, temperature=temperature)
    from tinker_vision import renderer_name, request_images
    vision = renderer_name(model) is not None

    def call(request: LLMRequest) -> LLMResponse:
        images = request_images(request) if vision else ()
        if not vision:
            request = pdf_text_request(request)
        elif images:
            request = replace(request, metadata={**request.metadata, 'pdf_delivery': 'vision_images_v1'})
        if request.tools and request.tool_choice != "none":
            from tinker_action import request_action
            return request_action(caller, request, model=model,
                                  max_output_tokens=max_output_tokens,
                                  max_tool_retries=max_tool_retries, images=images)
        from tinker_completion import complete
        return complete(caller, request, model, max_output_tokens, max_tool_retries, images)

    call.supports_attachments = vision
    call.supports_pdf_text = not vision
    return call


def make_tinker_query_fn(
    model: str,
    *,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
    max_retries: int = 2,
) -> QueryFn:
    """Return a text-only Tinker caller with the same truncation contract as requests.

    Contest deliberation and Coach planning use ``QueryFn`` rather than the
    request/tool interface.  They must still resume a length-stopped native
    sample exactly, and reject it if the shared turn budget cannot finish it.
    """
    caller = make_tinker_caller(
        model, max_output_tokens=max_output_tokens, temperature=temperature,
    )

    def request(request):
        from tinker_completion import complete
        return complete(caller, request, model, max_output_tokens, max_retries)

    def call(system_prompt: str, user_prompt: str) -> str:
        response = request(LLMRequest(system_prompt, user_prompt, purpose='contest_deliberation'))
        if response.usage.get("tool_error"):
            raise RuntimeError(response.usage["tool_error"])
        return response.text

    call.supports_sampling_metadata = True
    call.request = request
    call.supports_budgeted_requests = True
    call.max_output_tokens = max_output_tokens
    return call


def make_vectorengine_caller(model=None, *, max_output_tokens=8192, temperature=0.2):
    from env_config import provider_config
    profile = provider_config('vectorengine')
    key = os.environ.get(profile['api_key_env'])
    if not key:
        raise ValueError('Set VECTORENGINE_API_KEY to use VectorEngine.')
    caller = _make_chat_completions_caller(
        model or profile['model'], provider='vectorengine', api_key=key,
        base_url=profile['base_url'], max_output_tokens=max_output_tokens,
        temperature=temperature)
    def call(request):
        if request.attachments:
            error = ValueError('VectorEngine attachment support has not been verified.')
            error.usage = {'api_calls': 0, 'output_tokens': 0, 'unknown_usage_attempts': 0}
            raise error
        return caller(request)
    call.supports_attachments = False
    return call


def make_openagents_caller(
    model: str | None = None, *, max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> RequestFn:
    """Adapt canonical requests to the gateway's Chat Completions endpoint."""
    from env_config import openagents_config
    profile = openagents_config()
    key = os.environ.get(profile["api_key_env"])
    if not key:
        raise ValueError("Set OPENAGENTS_API_KEY to use the OpenAgents gateway.")
    return _make_chat_completions_caller(
        model or profile["model"], provider="openagents", api_key=key,
        base_url=profile["base_url"], max_output_tokens=max_output_tokens,
        temperature=temperature,
    )


def _make_chat_completions_caller(model: str, *, provider: str, api_key: str,
                                  base_url: str | None, max_output_tokens: int,
                                  temperature: float) -> RequestFn:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=180.0, max_retries=0)

    @local_preflight
    def prepare_content(request: LLMRequest):
        content: list[dict[str, Any]] = [{"type": "text", "text": request.user_prompt}]
        for attachment in request.attachments:
            if attachment.role != "agent_visible" and request.purpose == "generation":
                raise ValueError("Judge-only attachments cannot be sent to contestants.")
            if attachment.mime_type == "application/pdf":
                # Chat gateways do not consistently accept Responses input_file.
                # Render the selected pages, preserving diagrams and page bounds.
                import pymupdf
                with pymupdf.open(stream=_attachment_bytes(attachment), filetype="pdf") as document:
                    for page in document:
                        encoded = base64.b64encode(page.get_pixmap(dpi=110).tobytes("png")).decode("ascii")
                        content.append({"type": "image_url", "image_url": {
                            "url": "data:image/png;base64," + encoded}})
            elif attachment.mime_type.startswith("image/"):
                encoded = base64.b64encode(_attachment_bytes(attachment)).decode("ascii")
                content.append({"type": "image_url", "image_url": {
                    "url": f"data:{attachment.mime_type};base64,{encoded}"}})
            else:
                raise ValueError(f"Unsupported attachment MIME type: {attachment.mime_type}")
        return content

    def call(request: LLMRequest) -> LLMResponse:
        output_limit = _request_output_limit(request, max_output_tokens, allow_expansion=provider == 'openai')
        if output_limit == 0:
            return LLMResponse('', provider, model, usage={'api_calls': 0, 'output_tokens': 0,
                                                         'tool_error': 'No remaining transport budget'})
        kwargs: dict[str, Any] = {
            "model": model, "max_tokens": output_limit, "temperature": temperature,
            "messages": [{"role": "system", "content": request.system_prompt},
                         {"role": "user", "content": prepare_content(request)}],
        }
        if model.lower().startswith("glm-"):
            kwargs["reasoning_effort"] = "medium"
        disable_reasoning = request.metadata.get("disable_reasoning") or (
            model.lower().startswith("deepseek-")
            and request.purpose == "contest_action"
        )
        if disable_reasoning:
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        if request.tools:
            kwargs["tools"] = [{"type": "function", "function": {
                key: value for key, value in tool.items() if key != "type"
            }} for tool in request.tools]
            kwargs["tool_choice"] = request.tool_choice
            if request.parallel_tool_calls is not None:
                kwargs["parallel_tool_calls"] = request.parallel_tool_calls
        gateway_attempts = []
        if provider == "openagents":
            from gateway_retry import create_with_retry
            attempt_budget = request.metadata.get("max_transport_attempts")
            max_attempts = min(3, max(1, attempt_budget)) if isinstance(attempt_budget, int) else 3
            response, gateway_attempts = create_with_retry(
                client.chat.completions.create, kwargs, max_attempts=max_attempts,
                observe=request.metadata.get("gateway_observe"), sleep=time.sleep,
            )
        else:
            response = client.chat.completions.create(**kwargs).model_dump()
        raw_usage = response.get('usage') or {}
        usage = {**raw_usage, 'max_output_tokens': output_limit,
                 'api_calls': len(gateway_attempts) if gateway_attempts else 1}
        if 'prompt_tokens' in raw_usage:
            usage['input_tokens'] = raw_usage['prompt_tokens']
        if 'completion_tokens' in raw_usage:
            usage['output_tokens'] = raw_usage['completion_tokens']
        if gateway_attempts:
            usage.update(gateway_attempts=gateway_attempts,
                         unknown_usage_attempts=sum(a['usage_unknown'] for a in gateway_attempts))
        choices = response.get("choices") or []
        if not choices:
            return LLMResponse('', provider, model, usage={**usage, 'tool_error': 'No completion choices'})
        choice = choices[0]
        message = choice.get('message') or {}
        usage.update(finish_reason=choice.get('finish_reason'),
                     reasoning_chars=len(message.get('reasoning_content') or ''))
        incomplete = choice.get("finish_reason") in {"length", "content_filter"}
        deliberation_truncated = (
            choice.get("finish_reason") == "length"
            and request.purpose == "contest_deliberation"
            and not request.tools
            and bool(message.get("content"))
        )
        try:
            calls = parse_response_tool_calls({"output": [
                {"type": "function_call", "call_id": item.get("id", ""), **item["function"]}
                for item in ([] if incomplete else message.get("tool_calls") or [])
            ]})
        except (ValueError, TypeError, KeyError, AttributeError):
            return LLMResponse('', provider, model, usage={**usage,
                'tool_error': 'Malformed native function-call response; no action executed'})
        return LLMResponse("" if incomplete and not deliberation_truncated else message.get("content") or "", provider, model, {
            **usage,
            **({"deliberation_truncated": True} if deliberation_truncated else {}),
            **({"tool_error": "Incomplete or filtered completion; no action executed."}
               if incomplete and not deliberation_truncated else {}),
        }, calls)

    return call


def resolve_request_fn(
    provider: str = "perplexity",
    model: str | None = None,
    *,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> RequestFn:
    """Factory for multimodal judges/agents."""
    provider = provider.lower().strip()
    from env_config import PUBLIC_PROFILE_PROVIDERS
    if provider in PUBLIC_PROFILE_PROVIDERS:
        from public_providers import make_public_caller
        return make_public_caller(provider, model, max_output_tokens=max_output_tokens,
                                  temperature=temperature)
    if provider == "vectorengine":
        return make_vectorengine_caller(model, max_output_tokens=max_output_tokens, temperature=temperature)
    if provider == "openagents":
        return make_openagents_caller(model, max_output_tokens=max_output_tokens, temperature=temperature)
    if provider in {"perplexity", "pplx"}:
        return make_perplexity_responses_caller(
            model=model or "openai/gpt-5.4",
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
    if provider in {"openai", "oai"}:
        return make_openai_responses_caller(model=model or "gpt-4.1", max_output_tokens=max_output_tokens,
                                             temperature=temperature)
    if provider in {"tinker", "tml"}:
        from env_config import tinker_config
        resolved_model = (
            model or tinker_config()["model"]
        )
        return make_tinker_request_fn(
            resolved_model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
    raise ValueError(f"Unknown multimodal provider: {provider}")


def bind_attachments(
    request_fn: RequestFn,
    attachments: list[LLMAttachment] | tuple[LLMAttachment, ...],
    *,
    purpose: str = "generation",
) -> QueryFn:
    """Adapt a request-based multimodal caller to existing collaboration code."""
    frozen_attachments = tuple(attachments)

    def call(system_prompt: str, user_prompt: str) -> str:
        return request_fn(
            LLMRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                attachments=frozen_attachments,
                purpose=purpose,
            )
        ).text

    return call


def mock_agent_llm(system_prompt: str, user_prompt: str) -> str:
    """Deterministic mock for offline diagnostics."""
    combined = f"{system_prompt}\n{user_prompt}"

    if "you are coach" in system_prompt.lower() and "pre-contest brief" in system_prompt.lower():
        return (
            "ACTION: speak | PAYLOAD: Triage first, assign independent checks, "
            "and reserve the final quarter for integration and verification."
        )

    if "you are coach" in system_prompt.lower() and "opening discussion" in system_prompt.lower():
        return (
            "ACTION: speak | PAYLOAD: Follow the opening assignments, publish "
            "checkpoints, and escalate disagreements early. I am now exiting."
        )

    if "synthesize" in combined.lower() or "final team answer" in combined.lower():
        return (
            "ACTION: submit | PAYLOAD: "
            "1. (-6, 13)  2. slope -21  3. $52  4. 5√11  5. 49√3/2"
        )

    if "group leader" in combined.lower() and "compile" in combined.lower():
        return (
            "ACTION: work | PAYLOAD: Compiled team work: problems 1-5 solved.\n"
            "ACTION: submit | PAYLOAD: Team answer sheet: 1.(-6,13) 2.-21 3.52 4.5√11 5.49√3/2"
        )

    if "group leader" in combined.lower() and "assign" in combined.lower():
        return "Agent_2 handles problems 1-3. Agent_3 handles problems 4-6. I will synthesize."

    if "your assigned slice" in combined.lower():
        return "ACTION: speak | PAYLOAD: My slice is complete. Key results attached in scratchpad notes."

    if "icpc" in combined.lower() and "allowed_tools" in combined.lower():
        return (
            "ACTION: execute_code | PAYLOAD: print(sum(range(10)))\n"
            "ACTION: speak | PAYLOAD: Code confirms sum 0..9 = 45."
        )

    if (
        "codeforces" in combined.lower()
        or "cf_4a" in combined.lower()
        or (
            "algorithmic_programming" in combined.lower()
            and "submit_code" in combined.lower()
        )
    ):
        solution = (
            "n = int(input())\n"
            'print("YES" if n % 2 == 0 and n > 2 else "NO")\n'
        )
        return (
            "ACTION: execute_code | PAYLOAD: "
            + solution
            + "ACTION: submit_code | PAYLOAD: "
            + solution
            + "ACTION: submit | PAYLOAD: "
            + solution
        )

    if "round table" in combined.lower():
        return "ACTION: speak | PAYLOAD: I propose we divide by sub-problem and cross-check arithmetic."

    if "decentralized" in combined.lower():
        return (
            "ACTION: work | PAYLOAD: Node patch: verified approach for problem 7.\n"
            "ACTION: speak | PAYLOAD: Updated scratchpad with probability calculation."
        )

    return "ACTION: speak | PAYLOAD: Let's align on a unified solution approach."


def make_perplexity_caller(
    model: str = "openai/gpt-5.4-mini",
    api: str = "agent",
    max_output_tokens: int = 16000,
    *, temperature: float | None = None,
) -> QueryFn:
    """Build a real LLM caller using PERPLEXITY_API_KEY. Raises if key missing."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("Set PERPLEXITY_API_KEY to use a live LLM caller.")

    import requests

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def call_agent(system_prompt: str, user_prompt: str, max_retries: int = 5) -> str:
        full_input = f"{system_prompt}\n\n{user_prompt}"
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    "https://api.perplexity.ai/v1/agent",
                    headers=headers,
                    json={"model": model, "input": full_input, "max_output_tokens": max_output_tokens,
                          **({"temperature": temperature} if temperature is not None else {})},
                    timeout=300,
                )
                if not resp.ok:
                    detail = resp.text[:500]
                    raise requests.exceptions.HTTPError(
                        f"{resp.status_code} {resp.reason}: {detail}",
                        response=resp,
                    )
                data = resp.json()
                for item in data.get("output", []):
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            return content["text"]
                return str(data)
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(15 * (attempt + 1))
                else:
                    raise

    def call_sonar(system_prompt: str, user_prompt: str, max_retries: int = 5) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        for attempt in range(max_retries):
            try:
                r = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return r.choices[0].message.content
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(10 * (attempt + 1))
                else:
                    raise

    if api == "agent":
        call_agent.request = make_perplexity_responses_caller(
            model, max_output_tokens=max_output_tokens, temperature=temperature)
        call_agent.supports_budgeted_requests = True
        call_agent.max_output_tokens = max_output_tokens
        return call_agent
    return call_sonar


def _safe_api_error(exc: Exception) -> str:
    message = str(exc)
    for name in ("TINKER_API_KEY", "PERPLEXITY_API_KEY", "OPENAI_API_KEY", "OPENAGENTS_API_KEY", "VECTORENGINE_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(
        r"(?i)(authorization[\"']?\s*[:=]\s*[\"']?bearer\s+)\S+",
        r"\1[REDACTED]",
        message,
    )
    return f"{type(exc).__name__}: {message}"


def _normalize_tinker_api_key(raw: str) -> str:
    """Accept bare ``tml-...`` keys or ``tinker:tml-...`` credential files."""
    key = str(raw or "").strip()
    if key.lower().startswith("tinker:"):
        key = key.split(":", 1)[1].strip()
    match = re.search(r"(tml-[A-Za-z0-9_-]+)", key)
    if match:
        return match.group(1)
    return key


def make_tinker_caller(
    model: str,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> QueryFn:
    """Build a native Tinker sampling caller with lazy per-caller resources."""
    api_key = _normalize_tinker_api_key(os.environ.get("TINKER_API_KEY", ""))
    if not api_key:
        raise ValueError("Set TINKER_API_KEY to use the Tinker provider.")
    os.environ["TINKER_API_KEY"] = api_key
    if not model or not model.strip():
        raise ValueError("Set --model or TINKER_MODEL to select a Tinker model.")
    if max_output_tokens <= 0:
        raise ValueError("max_output_tokens must be positive.")
    if temperature < 0:
        raise ValueError("temperature must be non-negative.")

    try:
        import tinker
    except ImportError as exc:
        raise RuntimeError(
            "The Tinker SDK is unavailable. Install the 'tinker' package."
        ) from exc

    client = None
    tokenizer = None
    vision_renderer = None
    text_renderer = None
    from tinker_model_policy import model_policy, make_text_renderer, context_limit, stop_sequences
    policy = model_policy(model)
    transient_errors = tuple(
        error_type
        for name in (
            "APIConnectionError",
            "APITimeoutError",
            "RateLimitError",
            "InternalServerError",
            "RequestFailedError",
            "SidecarDiedError",
        )
        if isinstance((error_type := getattr(tinker, name, None)), type)
    )

    def resources():
        nonlocal client, tokenizer
        if client is None or tokenizer is None:
            try:
                new_client = tinker.ServiceClient().create_sampling_client(
                    base_model=model
                )
                new_tokenizer = new_client.get_tokenizer()
            except Exception as exc:
                raise RuntimeError(
                    f"Tinker client initialization failed: {_safe_api_error(exc)}"
                ) from exc
            client, tokenizer = new_client, new_tokenizer
        return client, tokenizer

    def call(system_prompt: str, user_prompt: str, max_retries: int = 3,
             *, max_output_tokens_override: int | None = None,
             continuation_tokens: list[int] | None = None,
             preserve_whitespace: bool = False,
             assistant_prefix: str = '', stop: list[str] | None = None,
             images: tuple = ()) -> str:
        nonlocal vision_renderer, text_renderer
        call.last_sample_tokens = []
        call.last_usage = {'api_calls': 0, 'input_tokens': 0, 'output_tokens': 0,
                           'unknown_usage_attempts': 0}
        def failure(message):
            error = RuntimeError(message)
            error.usage = dict(call.last_usage)
            return error
        output_limit = max_output_tokens
        if max_output_tokens_override is not None:
            output_limit = min(output_limit, max_output_tokens_override)
        if output_limit <= 0 or max_retries <= 0:
            raise ValueError("Tinker sampling budget is exhausted")
        try:
            sampling_client, sampling_tokenizer = resources()
        except RuntimeError as exc:
            exc.usage = dict(call.last_usage)
            raise
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            if images:
                from tinker_vision import make_renderer, generation_input
                if vision_renderer is None:
                    vision_renderer = make_renderer(model, sampling_tokenizer)
                prompt = generation_input(vision_renderer, sampling_tokenizer, system_prompt,
                                          user_prompt, images, assistant_prefix, continuation_tokens)
                input_length = prompt.length
            elif policy.renderer:
                from tinker_vision import generation_input
                if text_renderer is None:
                    text_renderer = make_text_renderer(policy, sampling_tokenizer)
                prompt = generation_input(text_renderer, sampling_tokenizer, system_prompt,
                                          user_prompt, (), assistant_prefix, continuation_tokens)
                input_length = prompt.length
            else:
                encoded = sampling_tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    **({'enable_thinking': False} if policy.disable_thinking_kwarg else {}),
                )
                input_ids = encoded["input_ids"] if hasattr(encoded, "keys") else encoded
                if assistant_prefix:
                    input_ids = list(input_ids) + list(sampling_tokenizer.encode(assistant_prefix, add_special_tokens=False))
                if continuation_tokens:
                    input_ids = list(input_ids) + list(continuation_tokens)
                input_length = len(input_ids)
                prompt = tinker.ModelInput.from_ints(input_ids)
            # Use the verified deployment override when present; otherwise use
            # this model's tokenizer limit. Never truncate evidence to fit.
            context_window = context_limit(policy, sampling_tokenizer)
            if context_window is not None:
                available = context_window - input_length - 256
                if available < min(output_limit, 1024):
                    raise ValueError('Tinker context window has insufficient output space: '
                                     f'{input_length} input tokens, {context_window} context limit')
                output_limit = min(output_limit, available)
            active_renderer = vision_renderer if images else text_renderer
            effective_stop = stop_sequences(sampling_tokenizer, active_renderer, stop)
            sampling_params = tinker.SamplingParams(
                max_tokens=output_limit,
                temperature=temperature,
                **({'stop': effective_stop} if effective_stop is not None else {}),
            )
        except Exception as exc:
            raise failure(
                f"Tinker prompt preparation failed: {_safe_api_error(exc)}"
            ) from exc

        last_error: Exception | None = None
        for attempt in range(max_retries):
            # Until a sequence arrives, the attempted request has unknown token
            # usage. Preserve that attempt even if sampling or decoding fails.
            call.last_usage = {'api_calls': attempt + 1, 'input_tokens': 0,
                               'output_tokens': 0, 'unknown_usage_attempts': attempt + 1}
            try:
                response = sampling_client.sample(
                    prompt,
                    num_samples=1,
                    sampling_params=sampling_params,
                ).result()
                break
            except transient_errors as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
            except Exception as exc:
                raise failure(
                    f"Tinker sampling failed: {_safe_api_error(exc)}"
                ) from exc
        else:
            raise failure(
                f"Tinker sampling failed after {max_retries} attempts: "
                f"{_safe_api_error(last_error or RuntimeError('unknown error'))}"
            ) from last_error

        if not response.sequences:
            raise failure("Tinker returned no sampled sequences.")
        sequence = response.sequences[0]
        call.last_sample_tokens = list(sequence.tokens)
        reason = str(getattr(sequence, "stop_reason", "stop")).lower()
        call.last_usage = {"input_tokens": input_length,
                           "chat_template": (getattr(vision_renderer, '_renderer_name', policy.template)
                                             if images else policy.template),
                           "chat_template_model": model,
                           "max_output_tokens": output_limit,
                           "output_tokens": len(sequence.tokens),
                           "api_calls": attempt + 1,
                           "unknown_usage_attempts": attempt,
                           "finish_reason": "length" if reason in {"length", "max_tokens", "max_length"} else reason}
        try:
            # Continuation chunks can begin mid-thought/mid-special-token.
            # Decode the full sampled prefix through the model's renderer.
            from tinker_model_policy import decode_response
            decoder = active_renderer if not policy.supports_prefix else None
            text = decode_response(sampling_tokenizer, decoder,
                                   list(continuation_tokens or []) + list(sequence.tokens))
            if not preserve_whitespace:
                text = text.strip()
        except Exception as exc:
            raise failure(
                f"Tinker decode failed: {_safe_api_error(exc)}"
            ) from exc
        if not isinstance(text, str) or (not text.strip() and not preserve_whitespace
                                        and not (decoder is not None and call.last_usage['finish_reason'] == 'length')):
            stop_reason = getattr(sequence, "stop_reason", None)
            raise failure(
                f"Tinker returned an empty decoded completion "
                f"(stop_reason={stop_reason!r})."
            )
        return text

    call.supports_sampling_metadata = True
    call.supports_continuation = True
    call.supports_prefix = policy.supports_prefix
    def decode_completion_tokens(tokens):
        from tinker_model_policy import decode_response
        return decode_response(resources()[1],
                               (vision_renderer or text_renderer) if not policy.supports_prefix else None,
                               tokens)
    call.decode_completion_tokens = decode_completion_tokens
    return call


def resolve_query_fn(
    use_mock: bool = True,
    model: Optional[str] = None,
) -> QueryFn:
    if use_mock:
        return mock_agent_llm
    return make_perplexity_caller(model=model or "openai/gpt-5.4-mini")


_AGENT_ROLE_RE = re.compile(r"^You are ([A-Za-z0-9_]+)\b", re.MULTILINE)


def make_roster_caller(
    models_by_agent: dict[str, str],
    *,
    default_model: str,
    api: str = "agent",
    max_output_tokens: int = 16000,
) -> QueryFn:
    """Route each agent call to a model based on the system-prompt role line.

    Collaboration prompts start with ``You are Agent_1 ...`` / ``You are Solo ...``.
    Missing agents fall back to ``default_model``.
    """
    callers: dict[str, QueryFn] = {}
    models = {**models_by_agent}
    models.setdefault("__default__", default_model)

    def _caller_for(model: str) -> QueryFn:
        if model not in callers:
            callers[model] = make_perplexity_caller(
                model=model, api=api, max_output_tokens=max_output_tokens
            )
        return callers[model]

    def call(system_prompt: str, user_prompt: str) -> str:
        match = _AGENT_ROLE_RE.search(system_prompt or "")
        agent = match.group(1) if match else None
        model = models.get(agent) if agent else None
        model = model or models["__default__"]
        return _caller_for(model)(system_prompt, user_prompt)

    return call
