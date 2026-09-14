"""Export full contest transcripts for every baseline without rewriting results."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contest_transcript import communication_markdown, communication_sidecar


OTC_VARIANTS = {"otc", "vallina_otc", "strategic_team", "open_table_coach"}


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def export_one(session_path: Path) -> tuple[Path, int] | None:
    data = json.loads(session_path.read_text(encoding="utf-8"))
    sidecar = communication_sidecar(data, source=session_path.name)
    json_path = session_path.with_name("chat.json")
    md_path = session_path.with_name("chat.md")
    _atomic_text(json_path, json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n")
    _atomic_text(md_path, communication_markdown(sidecar))
    if data.get("system_variant") in OTC_VARIANTS:
        _atomic_text(session_path.with_name("otc_chat.json"),
                     json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n")
        _atomic_text(session_path.with_name("otc_chat.md"), communication_markdown(sidecar))
    return json_path, sidecar["event_count"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="A contest_session.json or a directory to scan")
    args = parser.parse_args()
    paths = [args.path] if args.path.is_file() else sorted(args.path.rglob("contest_session.json"))
    exported = []
    for path in paths:
        result = export_one(path)
        if result is not None:
            exported.append(result)
            print(f"{result[0]} ({result[1]} communication events)")
    print(f"Exported {len(exported)} full contest transcript pair(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
