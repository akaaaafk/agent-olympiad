#!/usr/bin/env python3
"""Download EUSO team experiment PDFs into data/olympiads/euso/benchmark.json."""

import json
import os
import re
import subprocess
import time

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "euso")
BENCHMARK_PATH = os.path.join(ROOT, "data", "olympiads", "euso", "benchmark.json")

# (year, experiment_num, title, [(url, filename), ...])
ENTRIES = [
    (2003, 1, "Photosynthesis", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2003_TaskA.pdf", "task.pdf"),
    ]),
    (2003, 2, "Properties of Proteins", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2003_TaskB.pdf", "task.pdf"),
    ]),
    (2004, 1, "Hexokinase Assay", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2004_TaskA.pdf", "task.pdf"),
    ]),
    (2004, 2, "Luminescence and Plastic LDSs", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2004_TaskB.pdf", "task.pdf"),
    ]),
    (2005, 1, "Water Quality", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2005_TaskA.pdf", "task.pdf"),
    ]),
    (2005, 2, "Salinity and Mussel Physiology", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2005_TaskB.pdf", "task.pdf"),
    ]),
    (2007, 1, "All About the Potato", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2007_TaskA.pdf", "task.pdf"),
    ]),
    (2007, 2, "All about Starch", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2007_TaskB.pdf", "task.pdf"),
    ]),
    (2008, 1, "Energy from Light", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2008_TaskA.pdf", "task.pdf"),
    ]),
    (2008, 2, "Light Energy", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2008_TaskB.pdf", "task.pdf"),
    ]),
    (2009, 1, "Fibres", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2009_TaskA.pdf", "task.pdf"),
    ]),
    (2009, 2, "Fruit, Juices and Food", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2009_TaskB.pdf", "task.pdf"),
    ]),
    (2010, 1, "Water", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2010_TaskA.pdf", "task.pdf"),
    ]),
    (2010, 2, "CSI Sweden", [
        ("http://euso.eu/wp-content/uploads/EUSO_I_2010_TaskB.pdf", "task.pdf"),
    ]),
    (2006, 1, "CSI Brussels", [
        ("http://www.vob-ond.be/Olympiades/EUSO2006/TEST1.pdf", "task.pdf"),
    ]),
    (2006, 2, "Respiration and Boyle's Law", [
        ("http://www.vob-ond.be/Olympiades/EUSO2006/TEST2%20final%20version%20English.pdf", "task.pdf"),
    ]),
    (2011, 1, "All about Beer", [
        ("http://black-hole.cz/euso2011/P1Tasks.pdf", "task.pdf"),
    ]),
    (2011, 2, "Lenses including Contact Lenses", [
        ("http://black-hole.cz/euso2011/P2Tasks.pdf", "task.pdf"),
    ]),
    (2012, 1, "Amber", [
        ("https://www.euso2012.lt/wp-content/uploads/2012/05/EUSO2012-experiment-no-1.pdf", "task.pdf"),
        ("https://www.euso2012.lt/wp-content/uploads/2012/05/EUSO2012-task1-key.pdf", "key.pdf"),
    ]),
    (2012, 2, "Space Exploration", [
        ("https://www.euso2012.lt/wp-content/uploads/2012/05/EUSO-2012-experiment-2-tasks.pdf", "task.pdf"),
    ]),
    (2013, 1, "Silicon From Nature to Hi-Tec", [
        ("https://www.euso2013.lu/resources/site1/General/EUSO%202013%20_%20TEST%201_TASK.pdf", "task.pdf"),
    ]),
    (2013, 2, "Renewable Energy", [
        ("https://www.euso2013.lu/resources/site1/General/EUSO%202013%20TEST%202%20TASK%202.pdf", "task.pdf"),
    ]),
    (2014, 1, "Olive Oil", [
        ("https://www.euso2014.eu/downloads/euso2014_Task_A.pdf", "task.pdf"),
    ]),
    (2014, 2, "Sea Water", [
        ("https://www.euso2014.eu/downloads/euso2014_Task_B.pdf", "task.pdf"),
    ]),
    (2015, 1, "Blowing in the Wind", [
        ("http://euso.eu/wp-content/uploads/ExpBlowingintheWind.pdf", "task.pdf"),
    ]),
    (2015, 2, "Art Forgery", [
        ("http://www.euso.at/euso/uploads/tasks/tasksheet2.pdf", "task.pdf"),
    ]),
    (2016, 1, "Milk Day", [
        ("http://www.euso.at/euso/uploads/tasks/tasksheet1.pdf", "task.pdf"),
    ]),
    (2016, 2, "Battery Day", [
        ("http://www.euso.at/euso/uploads/tasks/additionalfileschallenge1.pdf", "task2.pdf"),
    ]),
    (2017, 1, "ICE", [
        ("http://euso.eu/wp-content/uploads/Task_1_ICE.pdf", "task.pdf"),
    ]),
    (2017, 2, "OCEAN", [
        ("http://euso.eu/wp-content/uploads/Task_2_OCEAN.pdf", "task.pdf"),
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
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            text = re.sub(r"\s+", " ", text).strip()
            pages.append(text)
        return "\n\n".join(pages)
    except Exception:
        return None


def main():
    existing = {}
    if os.path.exists(BENCHMARK_PATH):
        for e in json.load(open(BENCHMARK_PATH)):
            existing[e["problem_id"]] = e

    for year, exp_num, title, files in ENTRIES:
        pid = f"euso_{year}_experiment_{exp_num}"
        print(f"EUSO {year} exp {exp_num} — {title}...")
        year_dir = os.path.join(RAW_DIR, str(year), f"exp{exp_num}")
        prob_parts, sol_parts = [], []
        for url, name in files:
            dest = os.path.join(year_dir, name)
            if not download(url, dest):
                print(f"  failed download: {name}")
                continue
            text = extract_pdf_text(dest)
            if not text:
                continue
            if "key" in name or "sol" in name or "marking" in name:
                sol_parts.append(text)
            else:
                prob_parts.append(text)
        if not prob_parts:
            print("  skip — no problem text")
            continue
        entry = existing.get(pid) or {
            "problem_id": pid,
            "competition": "European Union Science Olympiad",
            "year": year,
            "topic": f"Experiment {exp_num} — {title}",
            "task_type": "team_practical",
            "team_size": 3,
            "source_url": "http://euso.eu/about/experiments/",
            "total_points": 100,
            "gold_label": {
                "expected_answer": None,
                "grading_rubric": "Official EUSO marking scheme / model answers. Human scores reported as percentage.",
                "human_baseline": None,
            },
            "status": "placeholder",
        }
        entry["problem_description"] = "\n\n---\n\n".join(prob_parts)
        entry["source_file"] = year_dir.replace(ROOT + os.sep, "")
        if sol_parts:
            entry["gold_label"]["expected_answer"] = "\n\n---\n\n".join(sol_parts)
        entry["status"] = "collected"
        existing[pid] = entry
        plen = len(entry["problem_description"])
        slen = len(entry["gold_label"].get("expected_answer") or "")
        print(f"  ok — prob={plen} sol={slen}")

    entries = sorted(existing.values(), key=lambda e: (e.get("year") or 0, e["problem_id"]))
    os.makedirs(os.path.dirname(BENCHMARK_PATH), exist_ok=True)
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    filled = sum(1 for e in entries if e.get("problem_description"))
    gold = sum(1 for e in entries if e.get("gold_label", {}).get("expected_answer"))
    print(f"\nWrote {len(entries)} entries ({filled} with text, {gold} with gold) → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
