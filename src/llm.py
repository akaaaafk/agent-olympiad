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
    # Tinker 0.26 exposes plain sampling but no tools/JSON-schema parameter.
    # Its adapter therefore renders the same schemas into the prompt, validates
    # the sampled call, and performs bounded repair attempts.
    "tinker": ProviderCapabilities(emulated_tools=True, pdf_text=True),
    "tml": ProviderCapabilities(emulated_tools=True, pdf_text=True),
}


def provider_capabilities(provider: str) -> ProviderCapabilities:
    """Return explicit capabilities instead of branching on provider names."""
    return _PROVIDER_CAPABILITIES.get(
        provider.lower().strip(),
        ProviderCapabilities(),
    )


def provider_action_transport(provider: str) -> ActionTransport:
    return provider_capabilities(provider).action_transport


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
    return str(data)


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

    client = OpenAI(api_key=api_key)

    def call(request: LLMRequest) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "instructions": request.system_prompt,
            "max_output_tokens": request.metadata.get("max_output_tokens_override", max_output_tokens),
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
        usage = {}
        if getattr(response, "usage", None):
            raw_usage = response.usage
            usage = raw_usage.model_dump() if hasattr(raw_usage, "model_dump") else {}
        return LLMResponse(
            text=response.output_text,
            provider="openai",
            model=model,
            usage=usage,
            tool_calls=parse_response_tool_calls(response.model_dump()),
        )

    return call


def make_perplexity_responses_caller(
    model: str = "openai/gpt-5.4",
    *,
    max_output_tokens: int = 16000,
    temperature: float = 0.2,
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
        content = _openai_style_content(request)
        payload = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": request.metadata.get("max_output_tokens_override", max_output_tokens),
            "temperature": temperature,
        }
        if request.system_prompt.strip():
            payload["instructions"] = request.system_prompt
        if request.tools:
            payload["tools"] = [{**tool, "name": "contest_web_search" if tool.get("name") == "web_search" else tool.get("name")} for tool in request.tools]
            payload["tool_choice"] = request.tool_choice
            if request.parallel_tool_calls is not None:
                payload["parallel_tool_calls"] = request.parallel_tool_calls
        last_error: Exception | None = None
        for attempt in range(max_retries):
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
                return LLMResponse(
                    text=_response_output_text(data),
                    provider="perplexity",
                    model=model,
                    usage={**usage, "max_output_tokens": payload["max_output_tokens"]},
                    tool_calls=tuple(LLMToolCall("web_search" if call.name == "contest_web_search" else call.name, call.arguments, call.call_id) for call in parse_response_tool_calls(data)),
                )
            except requests.exceptions.SSLError as exc:
                last_error = RuntimeError(
                    "TLS failed talking to api.perplexity.ai (often a huge image "
                    "payload). Re-render pages as smaller JPEGs, or retry with "
                    "--pages 1-1. Original error: "
                    f"{exc}"
                )
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise last_error from exc
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(15 * (attempt + 1))
                else:
                    raise
        raise RuntimeError(f"Perplexity multimodal call failed: {last_error}")

    return call


def _json_objects(text: str) -> list[Any]:
    """Decode JSON values embedded in fences or provider-specific tags."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.replace("<tool_call>", "").replace("</tool_call>", "")
    decoder = json.JSONDecoder()
    values: list[Any] = []
    for index, char in enumerate(cleaned):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        values.append(value)
    return values


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
        "strict: copy one exactly as shown.\n"
        f"FUNCTION SCHEMAS:\n{json.dumps(compact_tools, ensure_ascii=False)}"
    )


def pdf_text_request(request: LLMRequest) -> LLMRequest:
    """Convert host-selected PDF pages to text without forwarding binary files.

    LLMRequest still enforces contestant/judge separation before conversion.
    Empty scanned pages fail explicitly; this route does not claim OCR/vision.
    """
    if not request.attachments:
        return request
    from artifacts.pdf_ingest import extract_pdf_text
    sections = [request.user_prompt,
                "PDF TEXT DELIVERY: extracted text only; diagrams and layout may be lost."]
    for index, attachment in enumerate(request.attachments, 1):
        if attachment.mime_type != "application/pdf":
            raise ValueError("Tinker PDF text delivery accepts PDFs only, not page images.")
        text, _, warnings = extract_pdf_text(attachment.path,
            page_start=attachment.page_start, page_end=attachment.page_end)
        if warnings:
            raise ValueError("PDF text delivery failed: " + "; ".join(warnings))
        sections.append(f"PDF {index} ({attachment.role}) TEXT:\n{text}")
    user = "\n\n".join(sections)
    if len(user) > 600000:
        raise ValueError("PDF text request exceeds 600000 characters; select fewer pages.")
    return replace(request, user_prompt=user, attachments=(),
                   metadata={**request.metadata, "pdf_delivery": "extracted_text_v1"})


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
    caller = make_tinker_caller(
        model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )

    def call(request: LLMRequest) -> LLMResponse:
        request = pdf_text_request(request)
        if not request.tools or request.tool_choice == "none":
            text = caller(request.system_prompt, request.user_prompt)
            return LLMResponse(
                text=text,
                provider="tinker",
                model=model,
                usage={
                    "output_tokens": max(1, len(text) // 4),
                    "api_calls": 1,
                    "action_transport": "prompt_json",
                },
            )

        system = request.system_prompt + _tinker_tool_prompt(request.tools)
        user = request.user_prompt
        output_tokens = 0
        last_text = ""
        last_error = "unknown tool-call error"
        requested_attempts = request.metadata.get("max_transport_attempts")
        attempts = max_tool_retries + 1
        if isinstance(requested_attempts, int):
            attempts = max(1, min(attempts, requested_attempts))
        for attempt in range(attempts):
            last_text = caller(system, user)
            output_tokens += max(1, len(last_text) // 4)
            try:
                tool_call = _coerce_emulated_tool_call(last_text)
                error = _validate_emulated_tool_call(tool_call, request.tools)
                if error:
                    raise ValueError(error)
            except ValueError as exc:
                last_error = str(exc)
                if attempt >= max_tool_retries:
                    break
                user = (
                    f"{request.user_prompt}\n\n"
                    "YOUR PREVIOUS TOOL CALL WAS INVALID\n"
                    f"Error: {last_error}\n"
                    f"Invalid output: {last_text[:1200]}\n"
                    "Return one corrected JSON tool-call object only."
                )
                continue
            return LLMResponse(
                text="",
                provider="tinker",
                model=model,
                usage={
                    "output_tokens": output_tokens,
                    "api_calls": attempt + 1,
                    "tool_retries": attempt,
                    "action_transport": "emulated",
                },
                tool_calls=(
                    LLMToolCall(
                        name=tool_call.name,
                        arguments=tool_call.arguments,
                        call_id=f"tinker-emulated-{attempt + 1}",
                    ),
                ),
            )
        return LLMResponse(
            text=last_text,
            provider="tinker",
            model=model,
            usage={
                "output_tokens": output_tokens,
                "api_calls": attempts,
                "tool_retries": attempts - 1,
                "tool_error": last_error,
                "action_transport": "emulated",
            },
        )

    call.supports_attachments = False
    call.supports_pdf_text = True
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
            raise ValueError('VectorEngine attachment support has not been verified.')
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

    def call(request: LLMRequest) -> LLMResponse:
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
        output_limit = request.metadata.get("max_output_tokens_override", max_output_tokens)
        if not isinstance(output_limit, int) or isinstance(output_limit, bool) or output_limit <= 0:
            raise ValueError("max_output_tokens must be a positive integer")
        if provider in {"openagents", "vectorengine"}:
            output_limit = min(output_limit, max_output_tokens)
        kwargs: dict[str, Any] = {
            "model": model, "max_tokens": output_limit, "temperature": temperature,
            "messages": [{"role": "system", "content": request.system_prompt},
                         {"role": "user", "content": content}],
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
        choices = response.get("choices") or []
        if not choices:
            raise ValueError(f"{provider} returned no completion choices.")
        choice = choices[0]
        message = choice["message"]
        incomplete = choice.get("finish_reason") in {"length", "content_filter"}
        deliberation_truncated = (
            choice.get("finish_reason") == "length"
            and request.purpose == "contest_deliberation"
            and not request.tools
            and bool(message.get("content"))
        )
        calls = parse_response_tool_calls({"output": [
            {"type": "function_call", "call_id": item.get("id", ""), **item["function"]}
            for item in ([] if incomplete else message.get("tool_calls") or [])
        ]})
        usage = response.get("usage") or {}
        return LLMResponse("" if incomplete and not deliberation_truncated else message.get("content") or "", provider, model, {
            **usage, "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "finish_reason": choice.get("finish_reason"), "max_output_tokens": output_limit,
            "reasoning_chars": len(message.get("reasoning_content") or ""),
            **({"api_calls": len(gateway_attempts), "gateway_attempts": gateway_attempts,
                "unknown_usage_attempts": sum(a["usage_unknown"] for a in gateway_attempts)}
               if gateway_attempts else {}),
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

    def call(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        sampling_client, sampling_tokenizer = resources()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            encoded = sampling_tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            input_ids = encoded["input_ids"] if hasattr(encoded, "keys") else encoded
            prompt = tinker.ModelInput.from_ints(input_ids)
            sampling_params = tinker.SamplingParams(
                max_tokens=max_output_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Tinker prompt preparation failed: {_safe_api_error(exc)}"
            ) from exc

        last_error: Exception | None = None
        for attempt in range(max_retries):
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
                raise RuntimeError(
                    f"Tinker sampling failed: {_safe_api_error(exc)}"
                ) from exc
        else:
            raise RuntimeError(
                f"Tinker sampling failed after {max_retries} attempts: "
                f"{_safe_api_error(last_error or RuntimeError('unknown error'))}"
            ) from last_error

        if not response.sequences:
            raise RuntimeError("Tinker returned no sampled sequences.")
        sequence = response.sequences[0]
        try:
            text = sampling_tokenizer.decode(
                sequence.tokens, skip_special_tokens=True
            ).strip()
        except Exception as exc:
            raise RuntimeError(
                f"Tinker decode failed: {_safe_api_error(exc)}"
            ) from exc
        if not isinstance(text, str) or not text.strip():
            stop_reason = getattr(sequence, "stop_reason", None)
            raise RuntimeError(
                f"Tinker returned an empty decoded completion "
                f"(stop_reason={stop_reason!r})."
            )
        return text

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
