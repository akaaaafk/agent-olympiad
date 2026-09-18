"""Model-specific serialization and continuation policy for native sampling."""
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class ModelPolicy:
    template: str
    renderer: str | None = None
    disable_thinking_kwarg: bool = False
    supports_prefix: bool = False
    context_window: int | None = None


@lru_cache(maxsize=128)
def model_policy(model: str) -> ModelPolicy:
    base = model.split(':', 1)[0]
    from tinker_cookbook.model_info import get_model_attributes
    from tinker_cookbook.exceptions import ConfigurationError
    try:
        attrs=get_model_attributes(base)
    except (KeyError, ValueError, ConfigurationError):
        # Unknown models must supply their own tokenizer chat template. No
        # guessed Qwen template, reasoning switch or JSON assistant prefill.
        return ModelPolicy('model_tokenizer_chat_template')
    if not attrs.is_chat:
        raise ValueError(f'{base} is a base model, not a supported instruction/tool model')
    names=attrs.recommended_renderers
    # Only catalog-verified switchable templates get the HF thinking keyword.
    # A family-name match alone is not evidence: base/instruct/thinking-only
    # variants can have entirely different generation suffixes.
    if (base.startswith(('Qwen/Qwen3-', 'Qwen/Qwen3.5-', 'Qwen/Qwen3.6-'))
            and any(n in {'qwen3_disable_thinking', 'qwen3_5_disable_thinking'} for n in names)):
        return ModelPolicy('model_tokenizer_chat_template', disable_thinking_kwarg=True,
                           supports_prefix=True,
                           context_window=65536 if base=='Qwen/Qwen3.6-35B-A3B' and ':' not in model else None)
    name=next((n for n in names if 'disable_thinking' in n),
              next((n for n in names if 'low_reasoning' in n), names[0]))
    if name=='gpt_oss_no_sysprompt':
        name='gpt_oss_low_reasoning'
    prefix=(name.endswith('disable_thinking') or name in {'llama3','deepseekv3', 'qwen3_instruct', 'qwen3_vl_instruct'})
    return ModelPolicy(name, renderer=name, supports_prefix=prefix)


def make_text_renderer(policy, tokenizer):
    from tinker_cookbook.renderers import get_renderer
    return get_renderer(policy.renderer, tokenizer)


def context_limit(policy, tokenizer):
    if policy.context_window is not None:
        return policy.context_window
    limit=getattr(tokenizer,'model_max_length',None)
    # HF uses huge sentinel integers when no context maximum is known.
    return limit if isinstance(limit,int) and not isinstance(limit,bool) and 0 < limit < 10_000_000 else None


def stop_sequences(tokenizer, renderer=None, explicit=None):
    if renderer is not None:
        defaults=renderer.get_stop_sequences()
        defaults=[tokenizer.decode([x],skip_special_tokens=False) if isinstance(x,int) else x for x in defaults]
    else:
        eos=getattr(tokenizer,'eos_token',None)
        defaults=[eos] if isinstance(eos,str) and eos else []
    return list(dict.fromkeys([*(explicit or []),*defaults])) or None


def decode_response(tokenizer, renderer, tokens):
    """Decode the visible channel, never a reasoning block as an action.

    Sampling may exclude its EOS token. Supply it to the *parser only* so
    renderers which require a terminator still separate channels. This does
    not modify saved tokens or the provider finish reason: length-stopped
    output remains ineligible for execution, even if its JSON looks complete.
    """
    if renderer is None:
        return tokenizer.decode(tokens, skip_special_tokens=True)
    from tinker_cookbook.renderers.base import get_text_content
    raw = tokenizer.decode(tokens, skip_special_tokens=False)
    name = type(renderer).__name__
    # GLM's prompt owns <think>, so until </think> is sampled ALL output is
    # reasoning. The SDK parser otherwise treats an unclosed prefill as text.
    if name.startswith('Glm5_3') and '</think>' not in raw:
        return ''
    if raw.lstrip().startswith('<think>') and '</think>' not in raw:
        return ''
    if name.startswith('GptOss') and '<|message|>' not in raw:
        return ''  # Incomplete Harmony header, not visible text.
    parsed_tokens = list(tokens)
    stops = renderer.get_stop_sequences()
    if stops and not any((stop in parsed_tokens if isinstance(stop, int) else stop in raw)
                         for stop in stops):
        stop = stops[0]
        parsed_tokens += ([stop] if isinstance(stop, int)
                          else tokenizer.encode(stop, add_special_tokens=False))
    message, termination = renderer.parse_response(parsed_tokens)
    if not termination.is_clean:
        return ''  # A renderer's malformed raw-text fallback is not a final channel.
    # This is a JSON-emulated transport, not a native-tool conversation. Do
    # not silently lose unparsed calls or extract the first of several calls.
    if message.get('unparsed_tool_calls') or message.get('tool_calls'):
        raise ValueError('unexpected native tool block in JSON transport; no action executed')
    return get_text_content(message)
