"""Load repository .env without overwriting existing shell variables."""

from __future__ import annotations

import os
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def openagents_config() -> dict[str, str]:
    """Resolve the dedicated gateway profile without reading another provider's key."""
    profile = json.loads((REPO_ROOT / "configs/providers/openagents.json").read_text(encoding="utf-8"))
    if profile["api"] != "chat_completions":
        raise ValueError("OpenAgents profile requires api=chat_completions")
    from urllib.parse import urlsplit
    endpoint = os.environ.get(profile["base_url_env"]) or profile["base_url"]
    parsed = urlsplit(endpoint)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("OpenAgents base URL must be an HTTP(S) endpoint without credentials, query or fragment")
    return {
        **profile,
        "base_url": endpoint,
        "model": os.environ.get(profile["model_env"]) or profile["model"],
    }


def load_repo_dotenv(path: Path | None = None) -> None:
    env_path = path or (REPO_ROOT / ".env")
    if not env_path.exists():
        return
    values = {}
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            values[key] = value
            os.environ.setdefault(key, value)
    # Compatibility with the original repo-local OpenAgents gateway block.
    # Never borrow an inherited OPENAI_API_KEY (it may belong to another service).
    if (not os.environ.get("OPENAGENTS_API_KEY")
            and values.get("OPENAI_BASE_URL", "").rstrip("/") == "https://api-gateway.openagents.org/v1"):
        for suffix in ("API_KEY", "BASE_URL", "MODEL"):
            if values.get("OPENAI_" + suffix):
                os.environ.setdefault("OPENAGENTS_" + suffix, values["OPENAI_" + suffix])
