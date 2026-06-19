#!/usr/bin/env python3
"""Generate benchmark slots per test-based olympiad — one full problem per year/contest, no splitting."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLYMP_DIR = os.path.join(ROOT, "data", "olympiads")

# Each slot is (year_or_id, title). One entry = one complete published team task.
SLOTS = {
    "iol_team": [
        # 2003 had three separate team problems; all other years have one team contest each → 24 total
        ("2003", "Team — Tocharian"),
        ("2003", "Team — Subscripts"),
        ("2003", "Team — Verbs"),
        ("2004", "Team — Armenian"),
        ("2005", "Team — Figuig"),
        ("2006", "Team — American Sign Language"),
        ("2007", "Team — Hawaiian"),
        ("2008", "Team — Fanqie"),
        ("2009", "Team — Vietnamese"),
        ("2010", "Team — Mongolian"),
        ("2011", "Team — Sanskrit Poetry"),
        ("2012", "Team — Lao"),
        ("2013", "Team — Georgian"),
        ("2014", "Team — Armenian"),
        ("2015", "Team — Northern Sotho"),
        ("2016", "Team — Taa"),
        ("2017", "Team — Emoji/Indonesian"),
        ("2018", "Team — Mẽbêngôkre, Xavante and Krĩkatí"),
        ("2019", "Team — Rhythmic Gymnastics"),
        ("2021", "Team — Garífuna, Lokono and Kari'ña"),
        ("2022", "Team — Manchu"),
        ("2023", "Team — Murrinh-patha"),
        ("2024", "Team — Lexicostatistics"),
        ("2025", "Team — Camling and Bantawa"),
    ],
    "arml_power": [
        (f"{1994 + i // 2}", f"Power Round {'Spring' if i % 2 else 'Fall'}")
        for i in range(30)
    ],
    "ioaa_group": [
        (str(y), f"Group Competition {y}") for y in range(2007, 2025)
    ],
    "ijso_practical": [
        (str(2004 + i), f"Team Practical {2004 + i}") for i in range(30)
    ],
}

META = {
    "iol_team": ("International Linguistics Olympiad", "team_contest", 4, "https://ioling.org/problems/{year}/"),
    "arml_power": ("ARML Power Contest", "team_power", None, "https://www.arml.com/"),
    "ioaa_group": ("IOAA Group Competition", "team_contest", 5, "https://ioaastrophysics.org/"),
    "ijso_practical": ("IJSO Practical", "team_practical", 3, "https://ijsoweb.org/"),
}

TARGET = 30


def slug(s):
    return s.lower().replace(" ", "_").replace("/", "_").replace("'", "").replace("(", "").replace(")", "")[:60]


def make_entry(oid, year, title):
    comp, task_type, team_size, url_tpl = META[oid]
    pid = f"{oid}_{year}_{slug(title)}"
    url = url_tpl.format(year=year) if "{year}" in url_tpl else url_tpl
    y = int(year) if str(year).isdigit() else None
    return {
        "problem_id": pid,
        "competition": comp,
        "year": y,
        "topic": title,
        "task_type": task_type,
        "team_size": team_size,
        "source_url": url,
        "source_file": None,
        "total_points": None,
        "problem_description": "",
        "gold_label": {
            "expected_answer": None,
            "grading_rubric": None,
            "human_baseline": None,
        },
        "status": "placeholder",
    }


def main():
    for oid, slots in SLOTS.items():
        entries = [make_entry(oid, y, t) for y, t in slots[:TARGET]]
        path = os.path.join(OLYMP_DIR, oid, "benchmark.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)
        filled = sum(1 for e in entries if e.get("problem_description"))
        print(f"{oid}: wrote {len(entries)} full-problem slots ({filled} filled) → {path}")

    index_path = os.path.join(OLYMP_DIR, "index.json")
    with open(index_path) as f:
        index = json.load(f)
    for o in index["olympiads"]:
        if o["id"] in SLOTS:
            o["problems_collected"] = 0
            o["slots_scaffolded"] = len(SLOTS[o["id"]])
            o["target"] = min(TARGET, len(SLOTS[o["id"]]))
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"Updated {index_path}")


if __name__ == "__main__":
    main()
