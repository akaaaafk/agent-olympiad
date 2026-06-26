#!/usr/bin/env python3
"""Fill gold_label.human_baseline from published competition results."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLYMP = os.path.join(ROOT, "data", "benchmarks")

# IOL team contest gold trophy scores — https://ioling.org/results/{year}/
IOL_GOLD = {
    2008: "85 team pts (USA 2, gold; ioling.org/results/2008/)",
    2009: "2261 team pts (USA Red, gold; different scale that year)",
    2010: "96 team pts (Latvia, gold)",
    2011: "85 team pts (USA Red, gold)",
    2014: "29 team pts (USA Red, gold)",
    2016: "57 team pts (Sweden, gold)",
    2018: "84.83 team pts (USA Blue, gold)",
    2019: "113 team pts (Slovenia, gold)",
    2021: "56.8 team pts (Ukraine, gold)",
    2022: "68.1 team pts (Korea Mal, gold)",
    2023: "256 team pts (United Kingdom, gold)",
    2024: "85.5 team pts (Czechia, gold)",
    2025: "200.0/200 team pts (Taiwan Blue Magpie, gold)",
}

# ARML Power top team score per round — arml.com finalscores pages
ARML_GOLD = {
    "arml_power_fall_2018": "40/40 (Thomas Jefferson HS, 2018-19 Round 1)",
    "arml_power_fall_2019": "40/40 (Bergen County Academies, 2019-20 Round 1)",
    "arml_power_spring_2019": "39/40 (Thomas Jefferson HS, 2018-19 Round 2)",
    "arml_power_fall_2020": "40/40 (Bergen County Academies, 2019-20 Round 1)",
    "arml_power_spring_2020": "38/40 (Thomas Jefferson HS, 2019-20 Round 2)",
    "arml_power_fall_2021": "40/40 (Montgomery Blair HS, 2020-21 Round 1)",
    "arml_power_spring_2021": "38/40 (Thomas Jefferson HS, 2020-21 Round 2)",
    "arml_power_fall_2024": "37/40 (AlphaStar & SFBA ARML Erdos, 2023-24 Round 1)",
    "arml_power_fall_2025": "40/40 (State College Area HS, 2024-25 Round 1)",
}

# IJSO experimental (practical) team gold — ijsoweb.org past-results (sparse)
IJSO_GOLD = {
    "ijso_practical_2006_team_practical_2006": "40/40 (Thailand, experimental gold, 3rd IJSO 2006)",
    "ijso_practical_2007_team_practical_2007": "39.4/40 (Russia, experimental gold, 4th IJSO 2007)",
}


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def set_baseline(entries, key_fn, mapping):
    n = 0
    for e in entries:
        key = key_fn(e)
        if key not in mapping:
            continue
        gl = e.setdefault("gold_label", {})
        if gl.get("expected_answer") or e.get("problem_description", "").strip():
            gl["human_baseline"] = mapping[key]
            n += 1
    return n


def main():
    iol = load(os.path.join(OLYMP, "iol_team", "benchmark.json"))
    n_iol = set_baseline(iol, lambda e: e.get("year"), IOL_GOLD)

    arml = load(os.path.join(OLYMP, "arml_power", "benchmark.json"))
    n_arml = set_baseline(arml, lambda e: e["problem_id"], ARML_GOLD)

    ijso = load(os.path.join(OLYMP, "ijso_practical", "benchmark.json"))
    n_ijso = set_baseline(ijso, lambda e: e["problem_id"], IJSO_GOLD)

    save(os.path.join(OLYMP, "iol_team", "benchmark.json"), iol)
    save(os.path.join(OLYMP, "arml_power", "benchmark.json"), arml)
    save(os.path.join(OLYMP, "ijso_practical", "benchmark.json"), ijso)

    print(f"IOL: {n_iol} human baselines")
    print(f"ARML: {n_arml} human baselines")
    print(f"IJSO: {n_ijso} human baselines")


if __name__ == "__main__":
    main()
