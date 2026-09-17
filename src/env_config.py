"""Load repository .env without overwriting existing shell variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_run_provider(provider: str, judge_provider: str | None = None) -> str:
    """A run uses one service for contestants, planning and all judges."""
    aliases = {'pplx': 'perplexity', 'oai': 'openai', 'tml': 'tinker'}
    provider = aliases.get(provider, provider)
    judge_provider = aliases.get(judge_provider, judge_provider)
    if not provider:
        raise ValueError('A run provider is required')
    if judge_provider and judge_provider != provider:
        raise ValueError(
            f'Solver and judges must use the same provider: --provider {provider} '
            f'conflicts with --judge-provider {judge_provider}. '
            'Set --provider to the intended service and omit --judge-provider.'
        )
    return provider


def provider_config(provider: str) -> dict[str, Any]:
    """Load a provider profile and apply its non-secret environment overrides."""
    if not provider or not provider.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"Invalid provider profile name: {provider!r}")
    path = REPO_ROOT / "configs" / "providers" / f"{provider}.json"
    if not path.is_file():
        raise ValueError(f"Unknown provider profile: {provider}")
    profile = json.loads(path.read_text(encoding="utf-8"))
    resolved = {
        **profile,
        "model": os.environ.get(profile["model_env"]) or profile["model"],
    }
    if "base_url" in profile:
        endpoint = os.environ.get(profile["base_url_env"]) or profile["base_url"]
        parsed = urlsplit(endpoint)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError(
                f"{provider} base URL must be an HTTP(S) endpoint without credentials, query or fragment"
            )
        resolved["base_url"] = endpoint
    return resolved


def openagents_config() -> dict[str, Any]:
    """Resolve the dedicated gateway profile without reading another provider's key."""
    profile = provider_config("openagents")
    if profile["api"] != "chat_completions":
        raise ValueError("OpenAgents profile requires api=chat_completions")
    return profile


def tinker_config() -> dict[str, Any]:
    """Resolve the Tinker sampling profile and its selected model."""
    profile = provider_config("tinker")
    if profile["api"] != "tinker_sampling":
        raise ValueError("Tinker profile requires api=tinker_sampling")
    return profile


def load_repo_dotenv(path: Path | None = None) -> None:
    env_path = path or (REPO_ROOT / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


RUN_API_KEY_ENV = {
    'perplexity': 'PERPLEXITY_API_KEY', 'openai': 'OPENAI_API_KEY',
    'openagents': 'OPENAGENTS_API_KEY', 'tinker': 'TINKER_API_KEY',
    'vectorengine': 'VECTORENGINE_API_KEY',
}


def require_explicit_model(model):
    if not isinstance(model, str) or not model.strip():
        raise ValueError('An explicit --model is required; no default model is selected')
    return model.strip()


def add_run_credentials(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--api-key', help='API key for the selected provider; never persisted')
    group.add_argument('--api-key-env', help='Read the API key from this environment variable')


def consume_run_credentials(args):
    """Install a runtime key for SDKs/child processes, then discard CLI fields."""
    mapping = args if isinstance(args, dict) else vars(args)
    key = mapping.pop('api_key', None)
    variable = mapping.pop('api_key_env', None)
    if variable is not None:
        key = os.environ.get(variable)
        if not key:
            raise ValueError('The --api-key-env variable is unset or empty')
    if key is not None:
        if not key.strip():
            raise ValueError('--api-key must be nonempty')
        provider = resolve_run_provider(mapping['provider'])
        target = RUN_API_KEY_ENV.get(provider)
        if target is None:
            raise ValueError('Unsupported provider for --api-key')
        os.environ[target] = key.strip()
