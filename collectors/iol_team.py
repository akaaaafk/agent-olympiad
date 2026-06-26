#!/usr/bin/env python3
"""Download IOL team contest PDFs and populate data/benchmarks/iol_team/benchmark.json."""

import json
import os
import re
import subprocess
import sys
import time

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "iol")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "iol_team", "benchmark.json")
BASE = "https://ioling.org/booklets"

# One full team contest PDF per year (2003 has 3 named tasks inside one booklet)
YEARS = [y for y in range(2003, 2026) if y != 2020]

# Display names from ioling.org (for topic field)
TOPICS = {
    2003: "Team Contest — Tocharian, Subscripts, Verbs",
    2004: "Team Contest — Armenian",
    2005: "Team Contest — Figuig",
    2006: "Team Contest — American Sign Language",
    2007: "Team Contest — Hawaiian",
    2008: "Team Contest — Fanqie",
    2009: "Team Contest — Vietnamese",
    2010: "Team Contest — Mongolian",
    2011: "Team Contest — Sanskrit Poetry",
    2012: "Team Contest — Lao",
    2013: "Team Contest — Georgian",
    2014: "Team Contest — Armenian",
    2015: "Team Contest — Northern Sotho",
    2016: "Team Contest — Taa",
    2017: "Team Contest — Emoji/Indonesian",
    2018: "Team Contest — Mẽbêngôkre, Xavante and Krĩkatí",
    2019: "Team Contest — Rhythmic Gymnastics",
    2021: "Team Contest — Garífuna, Lokono and Kari'ña",
    2022: "Team Contest — Manchu",
    2023: "Team Contest — Murrinh-patha",
    2024: "Team Contest — Lexicostatistics",
    2025: "Team Contest — Camling and Bantawa",
}


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"  downloading {os.path.basename(dest)}...")
    subprocess.run(["curl", "-sL", "-o", dest, url], check=True)
    time.sleep(0.2)


def is_pdf(path):
    with open(path, "rb") as f:
        return f.read(5) == b"%PDF-"


def extract_pdf_text(path):
    if not path or not os.path.exists(path) or not is_pdf(path):
        return None
    try:
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            text = re.sub(r"(\w)([A-Z])", r"\1 \2", text)
            text = re.sub(r"\s+", " ", text).strip()
            pages.append(text)
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  warning: could not read {os.path.basename(path)}: {e}")
        return None


def collect_year(year):
    prob_url = f"{BASE}/iol-{year}-team-prob.en.pdf"
    sol_url = f"{BASE}/iol-{year}-team-sol.en.pdf"
    prob_file = os.path.join(RAW_DIR, f"iol-{year}-team-prob.en.pdf")
    sol_file = os.path.join(RAW_DIR, f"iol-{year}-team-sol.en.pdf")

    try:
        download(prob_url, prob_file)
    except Exception as e:
        print(f"  skip {year} problem: {e}")
        return None

    try:
        download(sol_url, sol_file)
    except Exception as e:
        print(f"  warning {year} solution: {e}")
        sol_file = None

    prob_text = extract_pdf_text(prob_file)
    sol_text = extract_pdf_text(sol_file) if sol_file else None

    if not prob_text or len(prob_text) < 500:
        print(f"  skip {year}: problem text missing or too short ({len(prob_text or '')} chars)")
        return None

    return {
        "problem_id": f"iol_team_{year}",
        "competition": "International Linguistics Olympiad",
        "year": year,
        "topic": TOPICS.get(year, f"Team Contest {year}"),
        "task_type": "team_contest",
        "team_size": 4,
        "source_url": f"https://ioling.org/problems/{year}/",
        "source_file": prob_file.replace(ROOT + os.sep, ""),
        "solution_file": sol_file.replace(ROOT + os.sep, "") if sol_file else None,
        "total_points": None,
        "problem_description": prob_text,
        "gold_label": {
            "expected_answer": sol_text,
            "grading_rubric": "Official IOL team contest solution booklet. Score each sub-part against the published answers.",
            "human_baseline": None,
        },
        "status": "collected",
    }


def main():
    years = YEARS
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]

    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                existing[e["year"]] = e

    for year in years:
        print(f"Collecting IOL {year}...")
        entry = collect_year(year)
        if entry:
            existing[year] = entry
            print(f"  ok — {len(entry['problem_description'])} chars problem, "
                  f"{len(entry['gold_label']['expected_answer'] or '')} chars solution")

    entries = [existing[y] for y in sorted(existing)]
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    index_path = os.path.join(ROOT, "data", "benchmarks", "index.json")
    with open(index_path) as f:
        index = json.load(f)
    for o in index["olympiads"]:
        if o["id"] == "iol_team":
            o["problems_collected"] = len(entries)
            o["target"] = len(entries)
            o["status"] = "collected" if entries else "scaffolded"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nWrote {len(entries)} problems → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
