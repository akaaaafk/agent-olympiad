#!/usr/bin/env python3
"""Download IIOT (International Informatics Olympiad in Teams) task PDFs.

Tasks are published at https://iio.team/competition/tasks per edition.
Run:  python3 collectors/iiot.py
"""

import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "iiot")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "iiot", "benchmark.json")

TASKS_URL = "https://iio.team/competition/tasks"
IIOT_BASE = "https://iio.team"

# Known international round PDFs (edition number → year mapping based on iio.team)
# Edition 1 started ~2019; international rounds usually held late in the academic year
KNOWN_EDITIONS = {
    # edition: (year, tasks_pdf_url, solutions_pdf_url)
    # Fill in as discovered from the site; None means try to scrape
}


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


def scrape_task_links():
    """Scrape iio.team/competition/tasks for all PDF links."""
    print("  scraping iio.team/competition/tasks ...")
    html = curl_html(TASKS_URL)
    if not html:
        print("  warning: could not fetch IIOT tasks page")
        return []

    links = []
    # Find all PDF hrefs
    for href in re.findall(r'href="([^"]+\.pdf)"', html, re.I):
        url = href if href.startswith("http") else IIOT_BASE + ("" if href.startswith("/") else "/") + href
        links.append(url)

    # Also look for links to sub-pages like /competition/tasks/1 etc.
    sub_pages = re.findall(r'href="(/competition/tasks/\d+[^"]*)"', html)
    for sub in set(sub_pages):
        sub_url = IIOT_BASE + sub
        sub_html = curl_html(sub_url)
        for href in re.findall(r'href="([^"]+\.pdf)"', sub_html, re.I):
            url = href if href.startswith("http") else IIOT_BASE + ("" if href.startswith("/") else "/") + href
            links.append(url)
        time.sleep(0.2)

    return list(set(links))


def classify_link(url):
    """Return (edition, kind) where kind is 'tasks' or 'solutions' or None."""
    lower = url.lower()
    # Extract edition/year from URL
    m = re.search(r'edition[_\-]?(\d+)|round[_\-]?(\d+)|(\d{4})', lower)
    edition = int(m.group(1) or m.group(2) or m.group(3)) if m else None
    if "sol" in lower or "answer" in lower:
        kind = "solutions"
    elif "task" in lower or "prob" in lower or "statement" in lower:
        kind = "tasks"
    else:
        kind = "tasks"  # default assumption
    return edition, kind


def collect_from_links(links):
    entries = {}
    for url in sorted(links):
        edition, kind = classify_link(url)
        if edition is None:
            continue
        year_dir = os.path.join(RAW_DIR, str(edition))
        fname = os.path.basename(url.split("?")[0]) or f"iiot_{edition}_{kind}.pdf"
        if not fname.endswith(".pdf"):
            fname += ".pdf"
        dest = os.path.join(year_dir, fname)

        if not curl(url, dest):
            print(f"  edition {edition} {kind}: download failed — {url}")
            continue
        if not is_pdf(dest):
            print(f"  edition {edition} {kind}: not a PDF — skipping")
            os.remove(dest)
            continue

        text = pdf_text(dest)
        print(f"  edition {edition} {kind}: ok — {len(text)} chars ({os.path.basename(dest)})")

        if edition not in entries:
            entries[edition] = {
                "problem_id": f"iiot_{edition}",
                "competition": "International Informatics Olympiad in Teams (IIOT)",
                "year": edition,
                "topic": f"IIOT Edition {edition} — International Round",
                "task_type": "algorithmic_programming",
                "team_size": 4,
                "source_url": TASKS_URL,
                "source_file": None,
                "solution_file": None,
                "total_points": None,
                "problem_description": "",
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": (
                        "Automated judge: solution is accepted if it produces correct output for all "
                        "test cases within time and memory limits. Partial credit awarded per test case "
                        "in some editions."
                    ),
                    "human_baseline": None,
                },
                "status": "partial",
            }

        if kind == "tasks":
            entries[edition]["source_file"] = dest.replace(ROOT + os.sep, "")
            entries[edition]["problem_description"] = text
            if len(text) > 300:
                entries[edition]["status"] = "collected"
        elif kind == "solutions":
            entries[edition]["solution_file"] = dest.replace(ROOT + os.sep, "")
            entries[edition]["gold_label"]["expected_answer"] = text

        time.sleep(0.3)

    return entries


def main():
    links = scrape_task_links()
    print(f"  found {len(links)} PDF link(s)")

    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                existing[e["year"]] = e

    new_entries = collect_from_links(links)
    existing.update(new_entries)

    entries = [existing[y] for y in sorted(existing)]
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    # Update index.json
    index_path = os.path.join(ROOT, "data", "benchmarks", "index.json")
    with open(index_path) as f:
        index = json.load(f)
    for o in index["olympiads"]:
        if o["id"] == "iiot":
            o["problems_collected"] = len(entries)
            o["status"] = "collected" if entries else "not_started"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nWrote {len(entries)} problems → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
