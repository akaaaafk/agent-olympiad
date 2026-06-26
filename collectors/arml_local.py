#!/usr/bin/env python3
"""Download ARML Local contest PDFs → benchmark (6-student team round)."""

import json
import os
import re
import subprocess

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "arml_local")
BOOK_PATH = os.path.join(RAW, "ARML_2009_2014.pdf")
BOOK_URL = "https://www.arml.com/ARML/arml_2019/public_contest_files/2009_2014_book/ARML_2009_2014.pdf"
BENCHMARK = os.path.join(ROOT, "data", "benchmarks", "arml_local", "benchmark.json")


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sLf", "-o", dest, url], capture_output=True)
    return r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 5000


def pdf_pages(path):
    return [re.sub(r"\s+", " ", (p.extract_text() or "")).strip() for p in PdfReader(path).pages]


def count_team_questions(text, year):
    nums = set(int(m) for m in re.findall(r"(?:Problem|T)-(\d{1,2})\.", text, re.I))
    if nums:
        return max(nums)
    return 15 if year >= 2014 else 10


def extract_local_year(pages, year):
    # TOC pages also mention "ARML Local 2009"; use the section header with "Contents".
    candidates = [
        i for i, p in enumerate(pages) if re.search(rf"ARML Local\s+{year}\s+Contents", p)
    ]
    header = candidates[-1] if candidates else None
    if header is None:
        return "", ""
    team_prob = next(
        (
            i
            for i in range(header, min(header + 20, len(pages)))
            if (p := pages[i]).startswith("Team Problems") or p.startswith("Team Round")
        ),
        None,
    )
    team_sol = next(
        (
            i
            for i in range(team_prob + 1, min(team_prob + 12, len(pages)))
            if pages[i].startswith("Team Solutions")
        ),
        None,
    )
    theme = next(
        (
            i
            for i in range(team_prob + 1, min(team_prob + 20, len(pages)))
            if pages[i].startswith("Theme Problems") or pages[i].startswith("Individual Round")
        ),
        None,
    )
    if team_prob is None:
        return "", ""
    prob = "\n\n".join(pages[team_prob : team_sol or theme or team_prob + 2]).strip()
    sol = ""
    if team_sol is not None:
        sol = "\n\n".join(pages[team_sol : theme or team_sol + 6]).strip()
    return prob, sol


def main():
    if not download(BOOK_URL, BOOK_PATH):
        print("Failed to download ARML 2009-2014 book")
        return
    print(f"Downloaded → {BOOK_PATH}")
    pages = pdf_pages(BOOK_PATH)
    entries = {}
    rel = BOOK_PATH.replace(ROOT + os.sep, "")

    for year in range(2009, 2015):
        prob, sol = extract_local_year(pages, year)
        if not prob or len(prob) < 300:
            print(f"  {year}: skip (no text, {len(prob)} chars)")
            continue
        n_q = count_team_questions(prob, year)
        entries[f"arml_local_{year}"] = {
            "problem_id": f"arml_local_{year}",
            "competition": "ARML Local",
            "year": year,
            "topic": f"Team Round — {year}",
            "task_type": "team_contest",
            "team_size": 6,
            "source_url": BOOK_URL,
            "source_file": rel,
            "total_points": n_q * 4,
            "problem_description": prob,
            "gold_label": {
                "expected_answer": sol if sol and len(sol) > 100 else None,
                "grading_rubric": "ARML Local Team Round — numerical answers, 4 points each.",
                "human_baseline": None,
            },
            "status": "collected",
        }
        print(f"  {year}: ok — {n_q} questions, {len(prob)} chars")

    os.makedirs(os.path.dirname(BENCHMARK), exist_ok=True)
    out = sorted(entries.values(), key=lambda e: e["year"])
    with open(BENCHMARK, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {len(out)} → {BENCHMARK}")


if __name__ == "__main__":
    main()
