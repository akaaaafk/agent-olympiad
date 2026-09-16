import json
from pathlib import Path
import random
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MINI = DATA / "mini_data"


class MiniDataTests(unittest.TestCase):
    def test_seed_920_selection_replays_exactly(self):
        source_index = json.loads((DATA / "benchmarks/index.json").read_text(encoding="utf-8"))
        manifest = json.loads((MINI / "selection_manifest.json").read_text(encoding="utf-8"))
        by_id = {row["competition_id"]: row for row in manifest["tracks"]}
        rng = random.Random(920)
        self.assertEqual(len(by_id), len(source_index["olympiads"]))
        for track in source_index["olympiads"]:
            rows = json.loads((ROOT / track["benchmark_path"]).read_text(encoding="utf-8"))
            years = sorted({int(r["year"]) for r in rows if str(r.get("year", "")).isdigit()})
            if len(years) >= 2:
                selected_years = rng.sample(years, 1)
                selected = [r for r in rows if str(r.get("year", "")).isdigit()
                            and int(r["year"]) in selected_years]
            elif years:
                selected_years = years
                selected = [r for r in rows if str(r.get("year", "")).isdigit()
                            and int(r["year"]) in selected_years]
            else:
                selected_years = []
                ids = {r["problem_id"] for r in rng.sample(
                    sorted(rows, key=lambda r: r["problem_id"]), min(1, len(rows)))}
                selected = [r for r in rows if r["problem_id"] in ids]
            actual = json.loads((MINI / f"benchmarks/{track['id']}/benchmark.json").read_text(encoding="utf-8"))
            self.assertEqual(actual, selected, track["id"])
            self.assertEqual(by_id[track["id"]]["selected_years"], selected_years)
            self.assertEqual(by_id[track["id"]]["selected_record_ids"],
                             [r["problem_id"] for r in selected])

    def test_counts_and_paths(self):
        manifest = json.loads((MINI / "selection_manifest.json").read_text(encoding="utf-8"))
        index = json.loads((MINI / "benchmarks/index.json").read_text(encoding="utf-8"))
        totals = manifest['totals']
        self.assertEqual(totals['records'], sum(t['selected_records'] for t in manifest['tracks']))
        self.assertEqual(totals['question_or_task_units'], totals['explicit_question_units'] + totals['whole_task_fallback_units'])
        self.assertEqual(index["total_records"], totals['records'])
        self.assertEqual(len(index["olympiads"]), totals['competitions'])
        for track in index["olympiads"]:
            self.assertTrue(track["benchmark_path"].startswith("data/mini_data/benchmarks/"))
            self.assertTrue((ROOT / track["benchmark_path"]).is_file())

    def test_visibility_roles_are_unchanged(self):
        for path in (MINI / "benchmarks").glob("*/benchmark.json"):
            source = DATA / "benchmarks" / path.parent.name / "benchmark.json"
            source_rows = {r["problem_id"]: r for r in json.loads(source.read_text(encoding="utf-8"))}
            for row in json.loads(path.read_text(encoding="utf-8")):
                self.assertEqual(row.get("assets", []), source_rows[row["problem_id"]].get("assets", []))


if __name__ == "__main__":
    unittest.main()
