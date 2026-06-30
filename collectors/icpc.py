#!/usr/bin/env python3
"""Download ICPC World Finals problem sets.

Sources tried in order:
  1. https://icpc.kattis.com  (official Kattis mirror, open problem PDFs)
  2. https://problems.icpc.io  (community archive)
  3. Direct ICPC site problem statements

Run:  python3 collectors/icpc.py
"""

import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "icpc")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "icpc", "benchmark.json")

KATTIS_BASE = "https://icpc.kattis.com"
PROBLEMS_IO_BASE = "https://problems.icpc.io"

# World Finals years to collect (1976 onwards; we focus on modern era 2000+)
TARGET_YEARS = list(range(2000, 2026))

# Known Kattis contest slugs for World Finals: icpc-[year]-[location] or icpcwf[year]
# Only the well-known ones; others discovered by scraping
KATTIS_CONTEST_SLUGS = {
    2024: "icpc2024",
    2023: "icpc2023",
    2022: "icpc2022-wf",
    2021: "icpc2021-wf",
    2020: "icpc2020-wf",
    2019: "icpc2019",
    2018: "icpc2018",
    2017: "icpc2017",
    2016: "icpc2016",
    2015: "icpc2015",
    2014: "icpc2014",
    2013: "icpc2013",
    2012: "icpc2012",
    2011: "icpc2011",
    2010: "icpc2010",
}

# Fallback: direct PDF URLs from ICPC official site / Kattis open archive
def direct_pdf_candidates(year):
    return [
        f"https://icpc.kattis.com/contests/icpcwf{year}/problems.pdf",
        f"https://icpc.kattis.com/contests/icpc{year}/problems.pdf",
        f"https://icpc.kattis.com/contests/icpc{year}-wf/problems.pdf",
        f"{PROBLEMS_IO_BASE}/icpc/world/{year}/problems.pdf",
        f"https://judge.icpc.global/problems/{year}-world-finals.pdf",
        f"https://icpc.global/newcms/wp-content/uploads/{year}/05/icpc{year}worldfinals_problems.pdf",
    ]


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


def count_problems(text):
    """Estimate number of problems from problem statement text."""
    # ICPC problems are labeled A, B, C, ... typically up to 12-13
    letters = set(re.findall(r'(?m)^(?:Problem\s+)?([A-M])[:\.\s]', text))
    return len(letters) if letters else None


def scrape_problems_io(year):
    """Try to get a PDF link from problems.icpc.io for a given year."""
    url = f"{PROBLEMS_IO_BASE}/icpc/world/{year}/"
    html = curl_html(url)
    if not html:
        return None
    pdfs = re.findall(r'href="([^"]+\.pdf)"', html, re.I)
    for href in pdfs:
        if "problem" in href.lower() or "statement" in href.lower() or re.search(r'\d{4}', href):
            return href if href.startswith("http") else f"{PROBLEMS_IO_BASE}{href}"
    return pdfs[0] if pdfs else None


def download_year(year):
    """Download problem PDF for a given World Finals year. Returns (dest, url) or (None, None)."""
    dest = os.path.join(RAW_DIR, str(year), f"icpc_wf_{year}_problems.pdf")
    if os.path.exists(dest) and is_pdf(dest):
        return dest, "(cached)"

    # Try direct candidate URLs
    for url in direct_pdf_candidates(year):
        if curl(url, dest) and is_pdf(dest):
            return dest, url

    # Try problems.icpc.io page scrape
    scraped_url = scrape_problems_io(year)
    if scraped_url and curl(scraped_url, dest) and is_pdf(dest):
        return dest, scraped_url

    return None, None


def collect_year(year):
    dest, used_url = download_year(year)
    if not dest:
        print(f"  {year}: not found — try manual download from icpc.global or icpc.kattis.com")
        return None

    text = pdf_text(dest)
    n_problems = count_problems(text)
    print(f"  {year}: ok — {len(text)} chars, ~{n_problems} problems ({used_url})")

    return {
        "problem_id": f"icpc_wf_{year}",
        "competition": "ICPC World Finals",
        "year": year,
        "topic": f"ICPC World Finals {year}",
        "task_type": "algorithmic_programming",
        "team_size": 3,
        "source_url": used_url or f"https://icpc.global/",
        "source_file": dest.replace(ROOT + os.sep, ""),
        "solution_file": None,
        "total_points": n_problems,
        "problem_description": text,
        "gold_label": {
            "expected_answer": None,
            "grading_rubric": (
                "ICPC scoring: ranked by number of problems solved (descending), then by total "
                "time penalty (ascending). Each accepted problem earns 1 point; wrong submissions "
                "add 20-minute penalty. Solutions verified by automated judge."
            ),
            "human_baseline": None,
        },
        "status": "collected" if len(text) > 500 else "partial",
    }


def main():
    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                existing[e["year"]] = e

    for year in TARGET_YEARS:
        if year in existing and existing[year].get("status") == "collected":
            print(f"  {year}: already collected — skipping")
            continue
        print(f"Collecting ICPC WF {year}...")
        entry = collect_year(year)
        if entry:
            existing[year] = entry
        time.sleep(0.4)

    entries = [existing[y] for y in sorted(existing)]
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    # Update index.json
    index_path = os.path.join(ROOT, "data", "benchmarks", "index.json")
    with open(index_path) as f:
        index = json.load(f)
    for o in index["olympiads"]:
        if o["id"] == "icpc":
            o["problems_collected"] = len(entries)
            o["status"] = "collected" if entries else "not_started"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nWrote {len(entries)} problems → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
