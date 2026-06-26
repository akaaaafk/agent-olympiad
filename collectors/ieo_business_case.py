#!/usr/bin/env python3
"""Populate data/benchmarks/ieo_business_case/benchmark.json from IEO PDFs in data/raw/business_case/."""

import json
import os
import re

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "business_case")
BENCHMARK = os.path.join(ROOT, "data", "benchmarks", "ieo_business_case", "benchmark.json")

CASES = [
    (2021, "2021_case.pdf", "Business Case — Rebirth and Evolution of JDL"),
    (2022, "2022_case.pdf", "Business Case — JDL Improvements"),
    (2023, "2023_case.pdf", "Business Case — IEO 2023 Task"),
    (2024, "2024.pdf", "Business Case — Housing Challenges in Hong Kong"),
    (2025, "2025.pdf", "Business Case — The Caspian Connector"),
]

RUBRIC = """Evaluated on 4 dimensions (total 50 points):

1. ANALYTICAL: Problem and goal identification; information synthesis; scope and depth of analysis.
2. CONCEPTUAL: Model relevancy and structure clarity; validity of assumptions; solution completeness and feasibility.
3. QUANTITATIVE: Convincing predictions and calculations.
4. COMMUNICATION: Professional communication; teamwork and timing.

Source: data/raw/business_case/2023_criteria.pdf (same rubric format used across IEO years)"""


def extract(path):
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        pages.append(text)
    return "\n\n".join(pages)


def main():
    criteria_path = os.path.join(RAW, "2023_criteria.pdf")
    if os.path.exists(criteria_path):
        rubric = extract(criteria_path) or RUBRIC
    else:
        rubric = RUBRIC

    entries = []
    for year, filename, topic in CASES:
        path = os.path.join(RAW, filename)
        if not os.path.exists(path):
            print(f"skip {year}: missing {filename}")
            continue
        text = extract(path)
        if len(text) < 500:
            print(f"skip {year}: text too short ({len(text)} chars)")
            continue
        human = "Canada 92.5/100 overall raw (2025 winner)" if year == 2025 else None
        entries.append({
            "problem_id": f"ieo_business_case_{year}",
            "competition": "International Economics Olympiad",
            "year": year,
            "topic": topic,
            "task_type": "business_case",
            "team_size": 5,
            "source_url": "https://ieo-official.org/prepare",
            "source_file": path.replace(ROOT + os.sep, ""),
            "total_points": 50,
            "problem_description": text,
            "gold_label": {
                "expected_answer": None,
                "grading_rubric": rubric,
                "human_baseline": human,
            },
            "status": "collected",
        })
        print(f"{year}: ok — {len(text)} chars")

    os.makedirs(os.path.dirname(BENCHMARK), exist_ok=True)
    with open(BENCHMARK, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"\nWrote {len(entries)} → {BENCHMARK}")


if __name__ == "__main__":
    main()
