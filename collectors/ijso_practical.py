#!/usr/bin/env python3
"""Download IJSO team practical PDFs into data/benchmarks/ijso_practical/benchmark.json."""

import json
import os
import re
import subprocess
import time

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "ijso")
BENCHMARK_PATH = os.path.join(ROOT, "data", "benchmarks", "ijso_practical", "benchmark.json")

# One full team practical per year: (year, prob_url, prob_name, sol_urls...)
ENTRIES = [
    (2007, "https://ijsoweb.org/qna/expt-2007.pdf", "questions.pdf", []),
    (2008, "https://ijsoweb.org/qna/expt-2008.pdf", "questions.pdf", []),
    (2009, "https://ijsoweb.org/qna/expt-2009.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna/expt-2009-soln.pdf", "solutions.pdf")]),
    (2010, "https://ijsoweb.org/qna/expt-2010.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna/expt-2010-soln.pdf", "solutions.pdf")]),
    (2011, "https://ijsoweb.org/qna/expt-2011-bio.pdf", "bio.pdf",
     [("https://ijsoweb.org/qna/expt-2011-bio-soln.pdf", "bio-sol.pdf"),
      ("https://ijsoweb.org/qna/expt-2011-chem-soln.pdf", "chem-sol.pdf")]),
    (2013, "https://ijsoweb.org/qna/IJSO_2013_Experiment_TaskA_Questions.pdf", "taskA-q.pdf",
     [("https://ijsoweb.org/qna/IJSO_2013_Experiment_TaskA_Solutions.pdf", "taskA-sol.pdf"),
      ("https://ijsoweb.org/qna/IJSO_2013_Experiment_TaskB_Questions.pdf", "taskB-q.pdf"),
      ("https://ijsoweb.org/qna/IJSO_2013_Experiment_TaskB_Solutions.pdf", "taskB-sol.pdf"),
      ("https://ijsoweb.org/qna/IJSO_2013_Experiment_TaskC_Questions.pdf", "taskC-q.pdf"),
      ("https://ijsoweb.org/qna/IJSO_2013_Experiment_TaskC_Solutions.pdf", "taskC-sol.pdf")]),
    (2014, "https://ijsoweb.org/qna2014/ijso2014_experimental_questions.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna2014/experiment-answers-2014.pdf", "solutions.pdf")]),
    (2015, "https://ijsoweb.org/qna2015/IJSO2015-Experiment-Questions.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna2015/IJSO2015-Experiment-Solutions.pdf", "solutions.pdf")]),
    (2016, "https://ijsoweb.org/qna2016/Experiment/Exam_Sheet_Experimental_Final_INDIA.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna2016/Experiment/Grading_Experiment_Biology.pdf", "bio-grade.pdf"),
      ("https://ijsoweb.org/qna2016/Experiment/Grading_Experiment_Chemistry.pdf", "chem-grade.pdf"),
      ("https://ijsoweb.org/qna2016/Experiment/Grading_Experiment_Physics.pdf", "phy-grade.pdf")]),
    (2017, "https://ijsoweb.org/qna2017/Experiment-questions.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna2017/Practical_test_marking_scheme_final_English_version.pdf", "marking.pdf")]),
    (2018, "https://ijsoweb.org/qna2018/IJSO_2018_LAB_Q.pdf", "questions.pdf",
     [("https://ijsoweb.org/qna2018/IJSO_2018_LAB_Marking.pdf", "marking.pdf")]),
    (2019, "https://ijsoweb.org/event/2019/qna/IJSO_2019_PRACTICAL_Question.pdf", "questions.pdf",
     [("https://ijsoweb.org/event/2019/qna/IJSO_2019_PRACTICAL_Answer.pdf", "answers.pdf"),
      ("https://ijsoweb.org/event/2019/qna/IJSO_2019_PRACTICAL_Marking_Scheme.pdf", "marking.pdf")]),
    (2021, "https://ijsoweb.org/event/2021/qna/IJSO-2021-Experiment-Question-Paper.pdf", "questions.pdf",
     [("https://ijsoweb.org/event/2021/qna/IJSO-2021-Experiment-Solution.pdf", "solutions.pdf")]),
    (2022, "https://ijsoweb.org/event/2022/qna/IJSO2022-Experiment-Questions.pdf", "questions.pdf",
     [("https://ijsoweb.org/event/2022/qna/IJSO2022-Experiment-Solution.pdf", "solutions.pdf"),
      ("https://ijsoweb.org/event/2022/qna/IJSO2022-Experiment-marking-scheme.pdf", "marking.pdf")]),
    (2023, "https://ijsoweb.org/event/2023/qna/Experiment2023-question-sheet.pdf", "questions.pdf",
     [("https://ijsoweb.org/event/2023/qna/Experiment2023-answer-key.pdf", "answers.pdf")]),
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

    for year, prob_url, prob_name, sol_files in ENTRIES:
        pid = f"ijso_practical_{year}_team_practical_{year}"
        print(f"IJSO {year} practical...")
        year_dir = os.path.join(RAW_DIR, str(year))
        prob_path = os.path.join(year_dir, prob_name)
        prob_parts, sol_parts = [], []

        if download(prob_url, prob_path):
            t = extract_pdf_text(prob_path)
            if t:
                prob_parts.append(t)

        for url, name in sol_files:
            dest = os.path.join(year_dir, name)
            if not download(url, dest):
                continue
            t = extract_pdf_text(dest)
            if not t:
                continue
            if "sol" in name or "marking" in name or "grade" in name or "answer" in name:
                sol_parts.append(t)
            elif "question" in name or "task" in name.lower():
                prob_parts.append(t)
            else:
                sol_parts.append(t)

        if not prob_parts:
            print("  skip — no problem text")
            continue

        entry = existing.get(pid) or {
            "problem_id": pid,
            "competition": "International Junior Science Olympiad — Practical",
            "year": year,
            "topic": f"Team Practical {year}",
            "task_type": "team_practical",
            "team_size": 3,
            "source_url": "https://ijsoweb.org/downloads",
            "total_points": 40,
            "gold_label": {
                "expected_answer": None,
                "grading_rubric": "Official IJSO practical marking scheme. Max 40 points.",
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
        print(f"  ok — prob={len(entry['problem_description'])} sol={len(entry['gold_label'].get('expected_answer') or '')}")

    entries = sorted(existing.values(), key=lambda e: (e.get("year") or 0, e["problem_id"]))
    entries = [e for e in entries if (e.get("year") or 0) <= 2025]
    with open(BENCHMARK_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    filled = sum(1 for e in entries if e.get("problem_description"))
    gold = sum(1 for e in entries if e.get("gold_label", {}).get("expected_answer"))
    print(f"\nWrote {len(entries)} entries ({filled} with text, {gold} with gold) → {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
