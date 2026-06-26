#!/usr/bin/env python3
"""Download ARML National Meet PDFs → team round + power round benchmarks."""

import json
import os
import re
import subprocess
import time

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "arml_national")
BOOK_PATH = os.path.join(RAW, "ARML_2009_2014.pdf")
BOOK_URL = "https://www.arml.com/ARML/arml_2019/public_contest_files/2009_2014_book/ARML_2009_2014.pdf"

NATIONAL_PDFS = {
    2016: "2016_Contest_Final_Version.pdf",
    2017: "2017_Contest_Final_Version.pdf",
    2018: "2018_Contest_Final_Version.pdf",
    2019: "2019_Contest_Final_Version.pdf",
    2023: "ARML_2023Contest.pdf",
}

TEAM_BENCH = os.path.join(ROOT, "data", "benchmarks", "arml_national_team", "benchmark.json")
POWER_BENCH = os.path.join(ROOT, "data", "benchmarks", "arml_national_power", "benchmark.json")


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sLf", "-o", dest, url], capture_output=True)
    return r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 5000


def pdf_pages(path):
    return [re.sub(r"\s+", " ", (p.extract_text() or "")).strip() for p in PdfReader(path).pages]


def pdf_text(path):
    return "\n\n".join(pdf_pages(path))


def count_team_questions(text):
    t = set(int(m) for m in re.findall(r"Problem\s+(\d{1,2})\.", text, re.I))
    u = set(int(m) for m in re.findall(r"T-(\d{1,2})\.", text, re.I))
    nums = t | u
    return max(nums) if nums else None


def count_power_questions(text):
    pts = re.findall(r"\[(\d+)\s*pts?\.?\]", text, re.I)
    if pts:
        return len(pts)
    return len(set(int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})[a-z]?[\.\)]", text))) or None


def join_pages(pages, start, end):
    return "\n\n".join(pages[start:end]).strip()


def extract_book_national(pages, year):
    team_start = next((i for i, p in enumerate(pages) if f"{year} Team Problems" in p), None)
    team_sol_start = next((i for i, p in enumerate(pages) if f"{year} Team Solutions" in p), None)
    power_start = next((i for i, p in enumerate(pages) if f"Power Question {year}" in p), None)
    power_sol_start = next((i for i, p in enumerate(pages) if f"Solutions to {year} Power Question" in p), None)
    relay_start = next((i for i, p in enumerate(pages) if i > (power_start or 0) and re.search(rf"{year} Relay|Relay Problems", p)), None)
    indiv_start = next((i for i, p in enumerate(pages) if i > (team_start or 0) and f"{year} Individual" in p), None)

    team_p = join_pages(pages, team_start, team_sol_start or power_start or indiv_start) if team_start is not None else ""
    team_s = join_pages(pages, team_sol_start, power_start or indiv_start) if team_sol_start is not None else ""
    power_p = join_pages(pages, power_start, power_sol_start or relay_start or indiv_start) if power_start is not None else ""
    power_s = join_pages(pages, power_sol_start, relay_start or indiv_start) if power_sol_start is not None else ""
    return team_p, team_s, power_p, power_s


def split_national_pdf(text):
    team_m = re.search(
        r"(?:Team\s+(?:Problems|Round)\b)(.*?)(?=Answers\s+to\s+Team|Solutions\s+to\s+Team|Power\s+(?:Question|Round))",
        text,
        re.I | re.S,
    )
    team_sol_m = re.search(
        r"Solutions?\s+to\s+Team\s+(?:Problems|Round)\b(.*?)(?=Power\s+(?:Question|Round))",
        text,
        re.I | re.S,
    )
    power_m = re.search(
        r"Power\s+(?:Question|Round)\b[^\n]*(.*?)(?=Solutions?\s+to\s+Power|Individual\s+Round|Relay)",
        text,
        re.I | re.S,
    )
    power_sol_m = re.search(
        r"Solutions?\s+to\s+Power\s+(?:Question|Round)\b(.*?)(?=Individual\s+Round|Relay|$)",
        text,
        re.I | re.S,
    )
    return (
        team_m.group(1).strip() if team_m else "",
        team_sol_m.group(1).strip() if team_sol_m else "",
        power_m.group(1).strip() if power_m else "",
        power_sol_m.group(1).strip() if power_sol_m else "",
    )


def make_entry(pid, competition, year, topic, task_type, team_size, source_file, source_url, prob, sol, total_points):
    if not prob or len(prob) < 300:
        return None
    return {
        "problem_id": pid,
        "competition": competition,
        "year": year,
        "topic": topic,
        "task_type": task_type,
        "team_size": team_size,
        "source_url": source_url,
        "source_file": source_file.replace(ROOT + os.sep, ""),
        "total_points": total_points,
        "problem_description": prob,
        "gold_label": {
            "expected_answer": sol if sol and len(sol) > 100 else None,
            "grading_rubric": None,
            "human_baseline": None,
        },
        "status": "collected",
    }


def main():
    team_entries = {}
    power_entries = {}

    if download(BOOK_URL, BOOK_PATH):
        print(f"Downloaded book → {BOOK_PATH}")
        pages = pdf_pages(BOOK_PATH)
        rel = BOOK_PATH.replace(ROOT + os.sep, "")
        for year in range(2009, 2015):
            team_p, team_s, power_p, power_s = extract_book_national(pages, year)
            te = make_entry(
                f"arml_national_team_{year}",
                "ARML National Meet — Team Round",
                year,
                f"Team Round — {year}",
                "team_contest",
                15,
                rel,
                BOOK_URL,
                team_p,
                team_s,
                50,
            )
            pe = make_entry(
                f"arml_national_power_{year}",
                "ARML National Meet — Power Round",
                year,
                f"Power Round — {year}",
                "team_power",
                15,
                rel,
                BOOK_URL,
                power_p,
                power_s,
                50,
            )
            if te:
                team_entries[te["problem_id"]] = te
                print(f"  book {year} team: {count_team_questions(team_p)} q, {len(team_p)} chars")
            if pe:
                power_entries[pe["problem_id"]] = pe
                print(f"  book {year} power: {count_power_questions(power_p)} q, {len(power_p)} chars")

    base = "https://www.arml.com/ARML/arml_2019/public_contest_files"
    for year, fname in NATIONAL_PDFS.items():
        dest = os.path.join(RAW, str(year), fname)
        url = f"{base}/{year}_contest_file/{fname}"
        print(f"Trying {year}...")
        if not download(url, dest):
            print("  skip — download failed")
            continue
        team_p, team_s, power_p, power_s = split_national_pdf(pdf_text(dest))
        rel = dest.replace(ROOT + os.sep, "")
        te = make_entry(
            f"arml_national_team_{year}",
            "ARML National Meet — Team Round",
            year,
            f"Team Round — {year}",
            "team_contest",
            15,
            rel,
            url,
            team_p,
            team_s,
            50,
        )
        pe = make_entry(
            f"arml_national_power_{year}",
            "ARML National Meet — Power Round",
            year,
            f"Power Round — {year}",
            "team_power",
            15,
            rel,
            url,
            power_p,
            power_s,
            50,
        )
        if te:
            team_entries[te["problem_id"]] = te
            print(f"  team ok — {count_team_questions(team_p)} q")
        if pe:
            power_entries[pe["problem_id"]] = pe
            print(f"  power ok — {count_power_questions(power_p)} q")
        time.sleep(0.2)

    for path, entries in [(TEAM_BENCH, team_entries), (POWER_BENCH, power_entries)]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out = sorted(entries.values(), key=lambda e: e["year"])
        with open(path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\nWrote {len(out)} → {path}")


if __name__ == "__main__":
    main()
