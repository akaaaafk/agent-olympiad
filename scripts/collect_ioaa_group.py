#!/usr/bin/env python3
"""Download IOAA group/team competition PDFs into data/olympiads/ioaa_group/benchmark.json."""

import json
import os
import re
import subprocess
import time

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "ioaa")
BENCHMARK_PATH = os.path.join(ROOT, "data", "olympiads", "ioaa_group", "benchmark.json")

# (year, label, [(url, local_name), ...]) — multiple PDFs merged into one problem for 2013
ENTRIES = [
    (2025, "Group Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/18th%20IOAA%202025/Group-Questions.pdf", "group-prob.pdf"),
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/18th%20IOAA%202025/Group-Solutions.pdf", "group-sol.pdf"),
    ]),
    (2023, "Group Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/16th%20IOAA%202023/Group%20Competition%202023%20IOAA.pdf", "group.pdf"),
    ]),
    (2021, "Team Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/14th%20IOAA%202021/Team%20Competition%202021%20IOAA.pdf", "group-prob.pdf"),
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/14th%20IOAA%202021/Team%20Competition%20Solutions%202021%20IOAA.pdf", "group-sol.pdf"),
    ]),
    (2016, "Group Examination", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/10th%20IOAA%202016/Group_Examination_problem_2016_IOAA.pdf", "group-prob.pdf"),
    ]),
    (2015, "Team Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/9th%20IOAA%202015/Team_Competition_problem_2015_IOAA.pdf", "group-prob.pdf"),
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/9th%20IOAA%202015/Team_Competition_solution_2015_IOAA.pdf", "group-sol.pdf"),
    ]),
    (2014, "Team Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/8th%20IOAA%202014/Team_Competition_problem_2014_IOAA.pdf", "group-prob.pdf"),
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/8th%20IOAA%202014/Team_Competition_solution_2014.pdf", "group-sol.pdf"),
    ]),
    (2013, "Team Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/7th%20IOAA%202013/Team%20competition%20Horizontal%20questions%202013%20IOAA.pdf", "horizontal.pdf"),
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/7th%20IOAA%202013/Team%20competition%20Vertical%20questions%202013%20IOAA.pdf", "vertical.pdf"),
    ]),
    (2012, "Team Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/6th%20IOAA%202012/Team%20Competition_problem_2012.pdf", "group-prob.pdf"),
    ]),
    (2011, "Group Competition", [
        ("https://cdn.ioaastrophysics.org/assets/IOAA%20problems/5th%20IOAA%202011/Group%20Competition%20Problem%202011%20IOAA.pdf", "group-prob.pdf"),
    ]),
]


def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        return True
    r = subprocess.run(["curl", "-sLf", "-o", dest, url], capture_output=True)
    time.sleep(0.2)
    return r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 500


def extract_pdf_text(path):
    try:
        reader = PdfReader(path)
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except Exception:
        return None


def main():
    results = []
    for year, label, files in ENTRIES:
        print(f"IOAA {year}...")
        year_dir = os.path.join(RAW_DIR, str(year))
        prob_parts, sol_parts = [], []
        for url, name in files:
            dest = os.path.join(year_dir, name)
            if not download(url, dest):
                print(f"  failed: {name}")
                continue
            text = extract_pdf_text(dest)
            if not text:
                continue
            if "sol" in name or "Solution" in url:
                sol_parts.append(text)
            else:
                prob_parts.append(text)
        if not prob_parts:
            print(f"  skip — no problem text")
            continue
        entry = {
            "problem_id": f"ioaa_group_{year}",
            "competition": "International Olympiad on Astronomy and Astrophysics",
            "year": year,
            "topic": f"{label} {year}",
            "task_type": "team_contest",
            "team_size": 5,
            "source_url": "https://ioaastrophysics.org/resources/problems-from-past-ioaa",
            "source_file": year_dir.replace(ROOT + os.sep, ""),
            "total_points": None,
            "problem_description": "\n\n---\n\n".join(prob_parts),
            "gold_label": {
                "expected_answer": "\n\n---\n\n".join(sol_parts) if sol_parts else None,
                "grading_rubric": "Official IOAA group competition marking scheme / solutions.",
                "human_baseline": None,
            },
            "status": "collected",
        }
        results.append(entry)
        print(f"  ok — prob={len(entry['problem_description'])} sol={len(entry['gold_label']['expected_answer'] or '')}")

    with open(BENCHMARK_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {len(results)} → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
