"""Contract of the independent one-edition mini dataset (verified_one_edition_v2)."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MINI = DATA / "mini_data"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def relocated(path):
    return "data/mini_data/" + path[len("data/"):] if path.startswith("data/") else path


class MiniDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = read(MINI / "benchmarks/index.json")["olympiads"]
        cls.tracks = {t["competition_id"]: t for t in read(MINI / "selection_manifest.json")["tracks"]}
        cls.rows = {e["id"]: read(ROOT / e["benchmark_path"]) for e in cls.index}

    def test_index_matches_selection_manifest(self):
        self.assertEqual({e["id"] for e in self.index}, set(self.tracks))
        for entry in self.index:
            self.assertTrue(entry["benchmark_path"].startswith("data/mini_data/benchmarks/"))
            rows, track = self.rows[entry["id"]], self.tracks[entry["id"]]
            self.assertEqual([r["problem_id"] for r in rows], track["selected_record_ids"], entry["id"])
            self.assertEqual(len(rows), track["selected_records"], entry["id"])
            self.assertEqual(entry["problems_collected"], len(rows), entry["id"])

    def test_one_edition_per_track(self):
        for name, rows in self.rows.items():
            years = {r.get("year") for r in rows}
            self.assertEqual(len(years), 1, name)
            self.assertEqual(years, set(self.tracks[name]["selected_years"]), name)

    def test_yearless_tracks_keep_one_whole_session(self):
        # A partial packet cannot run: WSC writing needs all three prompts.
        for name, rows in self.rows.items():
            if rows[0].get("year") is not None or not rows[0].get("parent_session_id"):
                continue
            sessions = {r.get("parent_session_id") for r in rows}
            self.assertEqual(len(sessions), 1, name)
            source = read(DATA / "benchmarks" / name / "benchmark.json")
            expected = [r["problem_id"] for r in source if r.get("parent_session_id") in sessions]
            self.assertEqual(sorted(r["problem_id"] for r in rows), sorted(expected), name)

    def test_declared_assets_are_local_and_keep_roles(self):
        for name, rows in self.rows.items():
            source_path = DATA / "benchmarks" / name / "benchmark.json"
            source = {r["problem_id"]: r for r in read(source_path)} if source_path.is_file() else {}
            for row in rows:
                assets = row.get("assets") or row.get("provenance", {}).get("assets", [])
                for asset in assets:
                    self.assertTrue(asset["path"].startswith("data/mini_data/"), asset["path"])
                    self.assertTrue((ROOT / asset["path"]).is_file(), asset["path"])
                original = source.get(row["problem_id"])
                if original is None:
                    continue
                original_assets = original.get("assets") or original.get("provenance", {}).get("assets", [])
                # Mini-specific repairs may add assets (see test_mini_pattern_recognition),
                # but must never drop or reclassify an inherited one.
                roles = {a["path"]: a.get("role") for a in assets}
                for a in original_assets:
                    self.assertEqual(roles.get(relocated(a["path"]), "<missing>"), a.get("role"),
                                     (row["problem_id"], a["path"]))


if __name__ == "__main__":
    unittest.main()
