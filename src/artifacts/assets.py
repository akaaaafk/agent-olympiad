"""Typed benchmark assets with role and integrity validation."""

from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

AssetRole = Literal["agent_visible", "judge_only"]


class AssetError(ValueError):
    """Raised when benchmark artifact metadata is unsafe or invalid."""


@dataclass(frozen=True)
class Asset:
    path: Path
    mime_type: str
    role: AssetRole
    page_start: int | None = None
    page_end: int | None = None
    sha256: str | None = None

    def as_metadata(self, root: Path) -> dict:
        return {
            "path": str(self.path.relative_to(root)),
            "mime_type": self.mime_type,
            "role": self.role,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "sha256": self.sha256 or file_sha256(self.path),
        }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_inside(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise AssetError(f"Asset escapes repository root: {relative_path}") from exc
    return candidate


def _load_asset(raw: dict, root: Path) -> Asset:
    role = raw.get("role")
    if role not in {"agent_visible", "judge_only"}:
        raise AssetError(f"Invalid asset role: {role!r}")

    path = _resolve_inside(root, str(raw.get("path", "")))
    if not path.is_file():
        raise AssetError(f"Missing asset: {path}")

    mime_type = raw.get("mime_type") or mimetypes.guess_type(path.name)[0]
    if not mime_type:
        raise AssetError(f"Unknown MIME type for asset: {path}")

    page_start = raw.get("page_start")
    page_end = raw.get("page_end")
    if (page_start is None) != (page_end is None):
        raise AssetError(f"Asset must specify both page_start and page_end: {path}")
    if page_start is not None and (
        not isinstance(page_start, int)
        or not isinstance(page_end, int)
        or page_start < 1
        or page_end < page_start
    ):
        raise AssetError(f"Invalid page range {page_start}-{page_end}: {path}")

    expected_sha = raw.get("sha256")
    if expected_sha:
        actual_sha = file_sha256(path)
        if actual_sha != expected_sha:
            raise AssetError(
                f"Checksum mismatch for {path}: expected {expected_sha}, got {actual_sha}"
            )

    return Asset(
        path=path,
        mime_type=mime_type,
        role=role,
        page_start=page_start,
        page_end=page_end,
        sha256=expected_sha,
    )


def load_assets(
    problem: dict,
    root: str | Path,
    *,
    roles: Iterable[AssetRole] | None = None,
) -> list[Asset]:
    """Resolve and validate problem assets, filtered by visibility role."""
    root_path = Path(root).resolve()
    selected_roles = set(roles or ("agent_visible", "judge_only"))
    assets = [_load_asset(raw, root_path) for raw in problem.get("assets", [])]
    return [asset for asset in assets if asset.role in selected_roles]
