#!/usr/bin/env python3
"""Download World Scholar's Cup Collaborative Writing prompts/rubrics.

Tries the public archives at scholarscup.org and known static asset URLs.
Run:  python3 collectors/wsc_writing.py
"""

import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "wsc_writing")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "wsc_writing", "benchmark.json")

# Known annual themes (used for metadata)
THEMES = {
    2016: "A World on the Margins",
    2017: "The Story of Us",
    2018: "Complexity",
    2019: "A Madman's Dream",
    2020: "Pandemic (cancelled / virtual)",
    2021: "A World in Transition",
    2022: "A World of Uncertainty",
    2023: "A World Rediscovered",
    2024: "A World at the Crossroads",
    2025: "A World Reimagined",
}

# Known direct PDF URLs for Scholar's Guides (contain writing prompts + rubrics).
# Entries left None will be discovered by scraping the archive page.
GUIDE_URLS = {
    2024: "https://scholarscup.org/s/2024-Scholars-Guide.pdf",
    2023: "https://scholarscup.org/s/2023-Scholars-Guide.pdf",
    2022: "https://scholarscup.org/s/2022-Scholars-Guide.pdf",
    2021: "https://scholarscup.org/s/2021-Scholars-Guide.pdf",
}

ARCHIVES_URL = "https://scholarscup.org/archives"


def curl(url, dest, *, silent=True):
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    flags = ["-sLf"] if silent else ["-Lf"]
    r = subprocess.run(["curl"] + flags + ["-o", dest, url], capture_output=True)
    ok = r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 2000
    if not ok and os.path.exists(dest):
        os.remove(dest)
    return ok


def curl_html(url):
    r = subprocess.run(["curl", "-sLf", url], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def is_pdf(path):
    if not os.path.exists(path):
        return False
    with open(path, "rb") as f:
        return f.read(5) == b"%PDF-"


def pdf_text(path):
    if not is_pdf(path):
        return ""
    try:
        from pypdf import PdfReader
        pages = []
        for p in PdfReader(path).pages:
            pages.append(re.sub(r"\s+", " ", p.extract_text() or "").strip())
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  warning: pdf_text failed for {os.path.basename(path)}: {e}")
        return ""


def scrape_archive_guides():
    """Return {year: url} from the WSC archives page."""
    print("  scraping scholarscup.org/archives ...")
    html = curl_html(ARCHIVES_URL)
    if not html:
        print("  warning: could not fetch archives page")
        return {}
    found = {}
    # Match links that look like Scholar's Guide PDFs
    for url in re.findall(r'https?://[^\s"\'<>]+(?:Scholars?[-_]Guide|guide|writing)[^\s"\'<>]*\.pdf', html, re.I):
        m = re.search(r'20\d{2}', url)
        if m:
            found[int(m.group())] = url
    return found


def collect_year(year, guide_url):
    dest = os.path.join(RAW_DIR, str(year), f"wsc_writing_{year}_guide.pdf")
    if not curl(guide_url, dest):
        print(f"  {year}: download failed — {guide_url}")
        return None
    if not is_pdf(dest):
        print(f"  {year}: downloaded file is not a PDF — skipping")
        os.remove(dest)
        return None

    text = pdf_text(dest)
    if len(text) < 300:
        print(f"  {year}: text too short ({len(text)} chars) — may need manual download")

    print(f"  {year}: ok — {len(text)} chars")
    return {
        "problem_id": f"wsc_writing_{year}",
        "competition": "World Scholar's Cup — Collaborative Writing",
        "year": year,
        "topic": THEMES.get(year, f"WSC {year} theme"),
        "task_type": "collaborative_writing",
        "team_size": 3,
        "source_url": guide_url,
        "source_file": dest.replace(ROOT + os.sep, ""),
        "solution_file": None,
        "total_points": None,
        "problem_description": text,
        "gold_label": {
            "expected_answer": None,
            "grading_rubric": (
                "WSC Collaborative Writing rubric: argument quality, use of evidence, "
                "style and clarity, originality. Evaluated against the annual Scholar's Guide."
            ),
            "human_baseline": None,
        },
        "status": "collected" if len(text) > 300 else "partial",
    }


def main():
    # Merge known URLs with anything scraped from the archive page
    all_urls = dict(scrape_archive_guides())
    all_urls.update(GUIDE_URLS)  # known URLs take precedence

    # Also try guessing URLs for years not yet discovered
    for year in range(2021, 2026):
        if year not in all_urls:
            for pattern in [
                f"https://scholarscup.org/s/{year}-Scholars-Guide.pdf",
                f"https://scholarscup.org/s/WSC{year}Guide.pdf",
                f"https://static1.squarespace.com/static/scholars-guide-{year}.pdf",
            ]:
                all_urls.setdefault(year, pattern)

    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                existing[e["year"]] = e

    for year in sorted(all_urls):
        if year in existing and existing[year].get("status") == "collected":
            print(f"  {year}: already collected — skipping")
            continue
        print(f"Collecting WSC Writing {year}...")
        entry = collect_year(year, all_urls[year])
        if entry:
            existing[year] = entry
        time.sleep(0.3)

    entries = [existing[y] for y in sorted(existing)]
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    # Update index.json
    index_path = os.path.join(ROOT, "data", "benchmarks", "index.json")
    with open(index_path) as f:
        index = json.load(f)
    for o in index["olympiads"]:
        if o["id"] == "wsc_writing":
            o["problems_collected"] = len(entries)
            o["status"] = "collected" if entries else "not_started"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nWrote {len(entries)} problems → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
