"""Read-only catalog audit; never promote PDF candidates automatically."""
from pathlib import Path
import sys
import json
import hashlib
import re
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from problem_pdf import approved_assets


def audit():
    import pymupdf
    rows = []
    snapshot = {}
    index = json.loads((ROOT / "data/benchmarks/index.json").read_text(encoding="utf-8-sig"))
    for path in sorted(ROOT / track["benchmark_path"] for track in index["olympiads"]):
        snapshot[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.extend((path.parent.name, row) for row in json.loads(path.read_text(encoding="utf-8-sig")))
    judge_hashes = {a.get("sha256") for _, r in rows for a in r.get("assets", [])
                    if a.get("role") == "judge_only" and a.get("sha256")}
    records = []
    for cid, row in rows:
        record = {"competition": cid, "problem_id": row["problem_id"],
                  "evaluation_status": (row.get("evaluation") or {}).get("status", "unknown"),
                  "limitations": (row.get("evaluation") or {}).get("limitations"),
                  "pdfs": [], "issues": []}
        statement = row.get("problem_description") or row.get("description") or row.get("prompt") or ""
        if len(statement.strip()) < 80:
            record["issues"].append("short_or_missing_json_statement")
        approved = {a["path"] for a in approved_assets(row)}
        for asset in row.get("assets", []):
            if asset.get("role") != "agent_visible" or asset.get("mime_type") != "application/pdf":
                continue
            item = {"path": asset["path"], "approved": asset["path"] in approved, "issues": []}
            path = (ROOT / asset["path"]).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                item["issues"].append("missing_or_outside_root")
            else:
                sha = hashlib.sha256(path.read_bytes()).hexdigest()
                if sha != asset.get("sha256"):
                    item["issues"].append("hash_mismatch_or_missing")
                if sha in judge_hashes:
                    item["issues"].append("also_declared_judge_only")
                try:
                    with pymupdf.open(path) as pdf:
                        start = asset.get("page_start") or 1
                        end = asset.get("page_end") or len(pdf)
                        item["pages"] = [start, end]
                        if not 1 <= start <= end <= len(pdf):
                            raise ValueError("invalid range")
                        suspicious, scans = [], []
                        for n in range(start, end + 1):
                            text = pdf[n-1].get_text()
                            if len(text.strip()) < 40:
                                scans.append(n)
                            # A flag is a review lead, not proof of leakage. Official
                            # prompts can legitimately ask for a solution/answer.
                            if re.search(r"(?im)^\s*(?:(?:official|suggested|sample|team|power|relay)\s+)?(?:solutions?|answer\s*key|answers|marking\s+scheme|scoring\s+guide)\b", text):
                                suspicious.append(n)
                        item["answer_heading_candidate_pages"] = suspicious
                        item["image_or_low_text_pages"] = scans
                        if suspicious:
                            item["issues"].append("answer_heading_needs_review")
                except Exception as exc:
                    item["issues"].append("pdf_parse_or_range_error:" + type(exc).__name__)
            if not item["approved"]:
                item["issues"].append("not_in_reviewed_allowlist")
            record["pdfs"].append(item)
        if not record["pdfs"] and "short_or_missing_json_statement" in record["issues"]:
            record["issues"].append("no_pdf_fallback_for_short_statement")
        if record["evaluation_status"] == "not_ready":
            record["issues"].append("evaluation_not_ready")
        records.append(record)
    summary = {"tracks": len(snapshot), "records": len(records),
               "evaluation_status": dict(Counter(r["evaluation_status"] for r in records)),
               "records_with_pdf": sum(bool(r["pdfs"]) for r in records),
               "records_without_pdf": sum(not r["pdfs"] for r in records),
               "records_with_approved_pdf": sum(any(a["approved"] for a in r["pdfs"]) for r in records),
               "pdf_assets": sum(len(r["pdfs"]) for r in records),
               "pdf_issue_counts": dict(Counter(i for r in records for a in r["pdfs"] for i in a["issues"])),
               "record_issue_counts": dict(Counter(i for r in records for i in r["issues"]))}
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "summary": summary,
              "scope": "Local asset/hash/page/text screening. Heading flags are not verdicts; no network or evaluator execution. PDF access requires explicit visual/content review.",
              "catalog_snapshot": snapshot, "records": records}
    out = ROOT / "output/problem_pdf_audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Problem PDF access audit", "", result["scope"], "", "```json", json.dumps(summary, indent=2), "```", "", "## Remaining records", "", "| Competition | Problem | Evaluation | PDF access | Issues / limitations |", "|---|---|---|---|---|"]
    for r in records:
        issues = r["issues"] + sorted({i for a in r["pdfs"] for i in a["issues"]})
        if issues:
            detail = "; ".join(issues) + "; " + str(r["limitations"] or "")
            lines.append(f"| {r['competition']} | {r['problem_id']} | {r['evaluation_status']} | {'approved' if any(a['approved'] for a in r['pdfs']) else 'unavailable'} | {detail.replace('|', '/').replace(chr(10), ' ')} |")
    (out / "audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    audit()
