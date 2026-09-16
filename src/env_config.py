"""Load repository .env without overwriting existing shell variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent


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
