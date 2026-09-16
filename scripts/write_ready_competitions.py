"""Regenerate the active-catalog readiness report."""
from __future__ import annotations

from collections import Counter
from datetime import date
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data/benchmarks/index.json"
OUTPUT = ROOT / "docs/from_zhongzheng/ready-competitions-20260914.md"
READY = {"ready", "ready_with_limitations", "remote_judge_ready"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def status(row: dict) -> str:
    return (row.get("evaluation") or {}).get("status", "not_ready")


def status_text(counts: Counter) -> str:
    return ", ".join(f"`{key}` {counts[key]}" for key in sorted(counts))


def main() -> None:
    index = read_json(INDEX)
    tracks = []
    for entry in index["olympiads"]:
        rows = read_json(ROOT / entry["benchmark_path"])
        counts = Counter(status(row) for row in rows)
        tracks.append((entry["id"], rows, counts))

    ready_rows = [(cid, row) for cid, rows, _ in tracks for row in rows if status(row) in READY]
    not_ready_rows = [(cid, row) for cid, rows, _ in tracks for row in rows if status(row) not in READY]
    fully_not_ready = [cid for cid, rows, _ in tracks if rows and all(status(row) not in READY for row in rows)]
    all_counts = Counter(status(row) for _, rows, _ in tracks for row in rows)
    total = len(ready_rows) + len(not_ready_rows)

    lines = [
        "# All competitions readiness（比赛名_年份）",
        "",
        f"> Updated **{date.today():%Y-%m-%d}** from the active canonical `data/benchmarks/index.json` entries. The historical filename is retained so existing links do not break.",
        "",
        f"- 竞赛种类：**{len(tracks)}**",
        f"- 其中至少一条 ready-ish：**{len(tracks) - len(fully_not_ready)}**",
        f"- 完全 not_ready：**{len(fully_not_ready)}**",
        f"- 记录总数：**{total}**（ready-ish **{len(ready_rows)}** + not_ready **{len(not_ready_rows)}**）",
        "",
        "Status legend: `ready`, `ready_with_limitations`, and `remote_judge_ready` pass the current readiness-label preflight; `not_ready` does not.",
        "",
        "**Important boundary.** A ready-ish label means the record has an enabled evaluation route and evaluator ID. It does not by itself prove that every provider can consume the source assets. PDF/image-dependent records still need a PDF-capable provider or an explicitly approved text-only route.",
        "",
        "**Catalog boundary.** Historical results and frozen experiment snapshots can include archived tracks such as HMMT Guts. They are not active-catalog readiness evidence.",
        "",
        "## Summary by track",
        "",
        "| track | ready-ish | not_ready | total | status counts |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for cid, rows, counts in tracks:
        ready_count = sum(counts[key] for key in READY)
        lines.append(f"| `{cid}` | {ready_count} | {len(rows) - ready_count} | {len(rows)} | {status_text(counts)} |")
    lines.append(f"| **total** | **{len(ready_rows)}** | **{len(not_ready_rows)}** | **{total}** | {status_text(all_counts)} |")

    lines += ["", "## Ready-ish（比赛名_年份）", "", f"共 **{len(ready_rows)}** 条。", ""]
    lines += [f"- `{row['problem_id']}`  `{status(row)}`" for _, row in ready_rows]
    lines += [
        "",
        "## Not ready（比赛名_年份）",
        "",
        f"共 **{len(not_ready_rows)}** 条。",
        "",
        f"### 完全没有 ready 的竞赛（{len(fully_not_ready)}）",
        "",
    ]
    lines += [f"- `{cid}`" for cid in fully_not_ready]
    lines += ["", "### All not_ready records", ""]
    lines += [f"- `{row['problem_id']}`  `{status(row)}`" for _, row in not_ready_rows]
    lines += ["", "## By track", ""]
    for cid, rows, _ in tracks:
        lines += [f"### `{cid}` ({len(rows)})", ""]
        lines += [f"- `{row['problem_id']}`  `{status(row)}`" for row in rows]
        lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    assert len(tracks) == index["active_tracks"]
    assert total == index["total_records"]
    print(f"Readiness report verified: tracks={len(tracks)}, records={total}")


if __name__ == "__main__":
    main()
