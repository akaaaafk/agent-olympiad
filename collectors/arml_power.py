#!/usr/bin/env python3
"""Download ARML Power Contest PDFs and populate data/benchmarks/arml_power/benchmark.json."""

import json
import os
import re
import subprocess
import sys
import time

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "arml")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "arml_power", "benchmark.json")
BASE = "https://www.arml.com/ARML/arml_2019/public_power_contest/contest_archive"

# Fall + Spring seasons to try (public archive)
SEASONS = []
for y in range(2018, 2026):
    SEASONS.append((f"Fall_{y}", f"Fall {y}"))
for y in range(2019, 2026):
    SEASONS.append((f"Spring_{y}", f"Spring {y}"))


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return os.path.getsize(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sLf", "-o", dest, url], capture_output=True)
    if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) < 500:
        if os.path.exists(dest):
            os.remove(dest)
        return 0
    time.sleep(0.2)
    return os.path.getsize(dest)


def extract_pdf_text(path):
    if not path or not os.path.exists(path):
        return None
    try:
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            text = re.sub(r"\s+", " ", text).strip()
            pages.append(text)
        return "\n\n".join(pages)
    except Exception:
        return None


def season_files(folder):
    prob = os.path.join(RAW_DIR, folder, f"ARMLPower_{folder.replace('_', '_')}.pdf")
    # folder like Fall_2024 -> ARMLPower_Fall_2024.pdf
    parts = folder.split("_")
    tag = f"{parts[0]}_{parts[1]}"
    prob_name = f"ARMLPower_{tag}.pdf"
    sol_name = f"ARMLPower_{tag.replace('Fall', 'Fall').replace('Spring', 'Spring')}_Solution_{parts[1]}.pdf"
    # Actual pattern: ARMLPower_Fall_2024.pdf, ARMLPower_Fall_Solution_2024.pdf
    year = parts[1]
    kind = parts[0]
    prob_name = f"ARMLPower_{kind}_{year}.pdf"
    sol_name = f"ARMLPower_{kind}_Solution_{year}.pdf"
    prob = os.path.join(RAW_DIR, folder, prob_name)
    sol = os.path.join(RAW_DIR, folder, sol_name)
    prob_url = f"{BASE}/{folder}/{prob_name}"
    sol_url = f"{BASE}/{folder}/{sol_name}"
    return prob_url, sol_url, prob, sol, prob_name, sol_name


def collect_season(folder, label):
    prob_url, sol_url, prob_path, sol_path, prob_name, sol_name = season_files(folder)
    if not download(prob_url, prob_path):
        return None
    download(sol_url, sol_path)
    prob_text = extract_pdf_text(prob_path)
    sol_text = extract_pdf_text(sol_path) if os.path.exists(sol_path) else None
    if not prob_text or len(prob_text) < 300:
        return None
    year = int(folder.split("_")[1])
    pid = f"arml_power_{folder.lower()}"
    return {
        "problem_id": pid,
        "competition": "ARML Power Contest",
        "year": year,
        "topic": f"Power Round — {label}",
        "task_type": "team_power",
        "team_size": None,
        "source_url": prob_url,
        "source_file": prob_path.replace(ROOT + os.sep, ""),
        "solution_file": sol_path.replace(ROOT + os.sep, "") if os.path.exists(sol_path) else None,
        "total_points": 40,
        "problem_description": prob_text,
        "gold_label": {
            "expected_answer": sol_text,
            "grading_rubric": "Official ARML Power solution packet. 40 points total per contest.",
            "human_baseline": None,
        },
        "status": "collected",
    }


def main():
    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH) as f:
            for e in json.load(f):
                if e.get("problem_id"):
                    existing[e["problem_id"]] = e

    for folder, label in SEASONS:
        print(f"Trying {label}...")
        entry = collect_season(folder, label)
        if entry:
            existing[entry["problem_id"]] = entry
            sol_len = len(entry["gold_label"].get("expected_answer") or "")
            print(f"  ok — prob={len(entry['problem_description'])} sol={sol_len}")

    entries = sorted(existing.values(), key=lambda e: (e.get("year", 0), e.get("topic", "")))
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    gold = sum(1 for e in entries if e.get("gold_label", {}).get("expected_answer"))
    print(f"\nWrote {len(entries)} seasons ({gold} with solutions) → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
