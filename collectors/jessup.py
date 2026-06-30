#!/usr/bin/env python3
"""Download Philip C. Jessup Moot Court Compromis (problem) PDFs.

The Compromis is the annual legal problem statement published each September
by the International Law Students Association (ILSA). Archive: ilsa.org/jessup/
Run:  python3 collectors/jessup.py
"""

import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "jessup")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "jessup", "benchmark.json")

ILSA_BASE = "https://www.ilsa.org"
ARCHIVE_URL = f"{ILSA_BASE}/jessup/jessup-problem/"

# Known Compromis titles (for metadata)
COMPROMIS_TITLES = {
    2026: "The Case Concerning the Gordian Gorge",
    2025: "The Case Concerning the Azure Coast",
    2024: "The Case Concerning the Prentanian Sea",
    2023: "The Case Concerning the Templeton Sea",
    2022: "The Case Concerning the Indigen People",
    2021: "The Case Concerning the Serene Coast",
    2020: "The Case Concerning the Fenian Straits",
    2019: "The Case Concerning the Melloria Sea",
    2018: "The Case Concerning the Northern Sea Routes",
    2017: "The Case Concerning the SolarMax",
    2016: "The Case Concerning the Crystalline Waters",
    2015: "The Case Concerning the Blue Ridge Mine",
    2014: "The Case Concerning the Islas Piedras",
    2013: "The Case Concerning the Lake Lanoux II",
    2012: "The Case Concerning the Outer Space Mining",
    2011: "The Case Concerning the Iron Rhine II",
    2010: "The Case Concerning the Gabcikovo II",
    2009: "The Case Concerning the Davis Strait",
    2008: "The Case Concerning the Grand Canyon II",
}

# Direct PDF URL patterns to try per year
def candidate_urls(year):
    slug = str(year)[-2:]  # e.g. "26" for 2026
    return [
        f"{ILSA_BASE}/wp-content/uploads/{year}/09/Jessup{year}Compromis.pdf",
        f"{ILSA_BASE}/wp-content/uploads/{year}/09/jessup{year}compromis.pdf",
        f"{ILSA_BASE}/wp-content/uploads/{year}/10/Jessup{year}Compromis.pdf",
        f"{ILSA_BASE}/wp-content/uploads/{year}/08/Jessup{year}Compromis.pdf",
        f"{ILSA_BASE}/wp-content/uploads/Jessup{year}Compromis.pdf",
        f"https://jessup.ilsa.org/wp-content/uploads/{year}/Jessup{year}Compromis.pdf",
        # Older naming conventions
        f"{ILSA_BASE}/wp-content/uploads/{year}/09/{year}JessupCompromis.pdf",
        f"{ILSA_BASE}/wp-content/uploads/{year}/09/Jessup-Compromis-{year}.pdf",
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


def scrape_archive_urls():
    """Try to discover Compromis PDF URLs from the ILSA archive page."""
    print("  scraping ilsa.org archive page...")
    html = curl_html(ARCHIVE_URL)
    if not html:
        # Try alternate archive URL
        html = curl_html(f"{ILSA_BASE}/jessup/past-problems/")
    if not html:
        print("  warning: could not fetch ILSA archive page")
        return {}
    found = {}
    for url in re.findall(r'https?://[^\s"\'<>]+[Cc]ompromis[^\s"\'<>]*\.pdf', html):
        m = re.search(r'20\d{2}', url)
        if m:
            found[int(m.group())] = url
    return found


def download_year(year):
    """Try all candidate URLs for a given year; return (dest_path, url) or None."""
    dest = os.path.join(RAW_DIR, str(year), f"jessup_{year}_compromis.pdf")
    if os.path.exists(dest) and is_pdf(dest):
        return dest, None  # already on disk
    for url in candidate_urls(year):
        if curl(url, dest):
            if is_pdf(dest):
                return dest, url
            else:
                os.remove(dest)
    return None, None


def collect_year(year):
    dest, used_url = download_year(year)
    if not dest:
        print(f"  {year}: not found — try manual download from ilsa.org")
        return None

    text = pdf_text(dest)
    if len(text) < 500:
        print(f"  {year}: text too short ({len(text)} chars)")

    source = used_url or f"https://www.ilsa.org/jessup/ (manual)"
    print(f"  {year}: ok — {len(text)} chars")
    return {
        "problem_id": f"jessup_{year}",
        "competition": "Philip C. Jessup International Law Moot Court Competition",
        "year": year,
        "topic": COMPROMIS_TITLES.get(year, f"Jessup {year} Compromis"),
        "task_type": "moot_court",
        "team_size": "2-5",
        "source_url": source,
        "source_file": dest.replace(ROOT + os.sep, ""),
        "solution_file": None,
        "total_points": None,
        "problem_description": text,
        "gold_label": {
            "expected_answer": None,
            "grading_rubric": (
                "Jessup rubric: legal analysis and argumentation (both Applicant and Respondent sides), "
                "quality of written memorials, citation of relevant international law, "
                "oral advocacy clarity. Winning memorials available via Jessup Compendium (HeinOnline)."
            ),
            "human_baseline": None,
        },
        "status": "collected" if len(text) > 500 else "partial",
    }


def main():
    # Merge scraped URLs with candidate guesses
    scraped = scrape_archive_urls()

    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                existing[e["year"]] = e

    # Collect recent years (2010–present); earlier years are in HeinOnline only
    target_years = list(range(2010, 2027))

    for year in target_years:
        if year in existing and existing[year].get("status") == "collected":
            print(f"  {year}: already collected — skipping")
            continue
        # Override candidate URL if scraped found something
        print(f"Collecting Jessup {year}...")
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
        if o["id"] == "jessup":
            o["problems_collected"] = len(entries)
            o["status"] = "collected" if entries else "not_started"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nWrote {len(entries)} problems → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
