#!/usr/bin/env python3
"""Download ICPC World Finals problem statements.

Scrapes individual problem pages from open.kattis.com where problem text
is embedded in the HTML. PDFs are not reliably publicly accessible.

Run:  python3 collectors/icpc.py
"""

import html
import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "icpc")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "icpc", "benchmark.json")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Kattis contest slugs for ICPC World Finals
# Verified by checking open.kattis.com/problem-sources/ICPC World Finals
CONTEST_SLUGS = {
    2024: "icpc2024",
    2023: "icpc2023",
    2022: "icpc2022",
    2021: "icpc2021",
    2020: "icpc2020",
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

TARGET_YEARS = sorted(CONTEST_SLUGS.keys())


def curl_html(url):
    r = subprocess.run(
        ["curl", "-sL", "-A", UA, "--max-time", "20", url],
        capture_output=True,
    )
    return r.stdout.decode("utf-8", "ignore") if r.returncode == 0 else ""


def scrape_problem_list(year, slug):
    """Return list of (problem_id, title) from a Kattis contest page."""
    url = f"https://open.kattis.com/problem-sources/ICPC%20World%20Finals%20{year}"
    html_src = curl_html(url)
    if not html_src:
        # Fallback: try contest page directly
        url = f"https://open.kattis.com/contests/{slug}/problems"
        html_src = curl_html(url)
    if not html_src:
        return []

    problems = []
    # Match problem links like /problems/adjoin
    for m in re.finditer(r'href="/problems/([a-z0-9]+)"[^>]*>([^<]+)</a>', html_src, re.I):
        pid = m.group(1)
        title = html.unescape(m.group(2)).strip()
        if pid and title:
            problems.append((pid, title))
    # Deduplicate preserving order
    seen = set()
    unique = []
    for pid, title in problems:
        if pid not in seen:
            seen.add(pid)
            unique.append((pid, title))
    return unique


def scrape_problem_text(problem_id):
    """Scrape problem statement HTML from open.kattis.com/problems/<id>."""
    url = f"https://open.kattis.com/problems/{problem_id}"
    html_src = curl_html(url)
    if not html_src:
        return "", url

    # Extract the problem statement div
    m = re.search(
        r'<div[^>]+class="[^"]*problem-statement[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html_src, re.S | re.I
    )
    if not m:
        # Broader fallback: everything between <article> tags
        m = re.search(r'<article[^>]*>(.*?)</article>', html_src, re.S | re.I)
    if not m:
        return "", url

    raw = m.group(1)
    # Strip HTML tags and decode entities
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    return text, url


def collect_year(year, slug):
    print(f"Collecting ICPC WF {year} (slug={slug})...")

    problems = scrape_problem_list(year, slug)
    if not problems:
        print(f"  {year}: could not find problem list")
        return []

    print(f"  {year}: found {len(problems)} problems")
    entries = []
    year_dir = os.path.join(RAW_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)

    for pid, title in problems:
        text, src_url = scrape_problem_text(pid)
        txt_path = os.path.join(year_dir, f"{pid}.txt")
        if text:
            with open(txt_path, "w") as f:
                f.write(text)

        entry = {
            "problem_id": f"icpc_wf_{year}_{pid}",
            "competition": "ICPC World Finals",
            "year": year,
            "kattis_id": pid,
            "title": title,
            "task_type": "algorithmic_programming",
            "team_size": 3,
            "source_url": src_url,
            "source_file": txt_path.replace(ROOT + os.sep, "") if text else None,
            "problem_description": text,
            "gold_label": {
                "expected_answer": None,
                "grading_rubric": (
                    "ICPC scoring: ranked by number of problems solved (descending), "
                    "then by total time penalty (ascending). Each accepted problem earns "
                    "1 point; wrong submissions add 20-minute penalty. Solutions verified "
                    "by automated judge."
                ),
                "human_baseline": None,
            },
            "status": "collected" if len(text) > 200 else "partial",
        }
        entries.append(entry)
        time.sleep(0.3)

    ok = sum(1 for e in entries if e["status"] == "collected")
    print(f"  {year}: {ok}/{len(entries)} problems with text")
    return entries


def main():
    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                existing[e["problem_id"]] = e

    all_entries = list(existing.values())

    for year in TARGET_YEARS:
        # Skip year if already collected (check by year prefix)
        already = [e for e in all_entries if e.get("year") == year and e.get("status") == "collected"]
        if already:
            print(f"  {year}: {len(already)} problems already collected — skipping")
            continue

        entries = collect_year(year, CONTEST_SLUGS[year])
        # Replace any partial entries for this year
        all_entries = [e for e in all_entries if e.get("year") != year]
        all_entries.extend(entries)
        time.sleep(0.5)

    all_entries.sort(key=lambda e: (e.get("year", 0), e.get("kattis_id", "")))
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(all_entries, f, indent=2)

    # Update index.json
    index_path = os.path.join(ROOT, "data", "benchmarks", "index.json")
    with open(index_path) as f:
        index = json.load(f)
    collected = sum(1 for e in all_entries if e.get("status") == "collected")
    for o in index["olympiads"]:
        if o["id"] == "icpc":
            o["problems_collected"] = len(all_entries)
            o["status"] = "collected" if collected > 0 else "not_started"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nWrote {len(all_entries)} problems → {BENCHMARK_PATH}")
    print(f"({collected} with full text)")


if __name__ == "__main__":
    main()
