from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from contest_transcript import communication_history, communication_sidecar, communication_markdown
from export_otc_chat import export_one


class ContestTranscriptTests(unittest.TestCase):
    def test_all_baselines_export_generic_files(self):
        from run_competition_batch import _write_otc_chat_sidecars
        for competition in ("arml_local", "icpc"):
            for variant in ("single_agent", "centralized", "decentralized", "vallina_otc", "otc"):
                with self.subTest(competition=competition, variant=variant), tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "contest_session.json"
                    source = {"session_id": "s", "competition_id": competition,
                              "system_variant": variant, "memory": {"events": [
                                  {"turn": 1, "kind": "think", "actor": "Agent_1",
                                   "visibility": "private", "payload": {"content": "saved thought"}}]}}
                    original = json.dumps(source)
                    path.write_text(original, encoding="utf-8")
                    _write_otc_chat_sidecars(path.parent, source)
                    live = (path.parent / "chat.json").read_text(encoding="utf-8")
                    export_one(path)
                    self.assertEqual(json.loads(live), json.loads((path.parent / "chat.json").read_text(encoding="utf-8")))
                    self.assertIn("saved thought", (path.parent / "chat.md").read_text(encoding="utf-8"))
                    self.assertEqual(path.read_text(encoding="utf-8"), original)
                    self.assertEqual((path.parent / "otc_chat.json").exists(), variant in ("otc", "vallina_otc"))

    def test_coach_opening_is_preserved_before_agent_chat(self):
        for chat in ([], [{"sender": "Agent_1", "message": "saved", "turn": 1}]):
            source = {"precontest_coach_guidance": "Opening advice.\n\nCheck answers.",
                      "chat_history": chat}
            sidecar = communication_sidecar(source)
            rendered = communication_markdown(sidecar)
            self.assertEqual(sidecar["precontest_coach_guidance"], source["precontest_coach_guidance"])
            self.assertIn(source["precontest_coach_guidance"], rendered)
            self.assertEqual(sidecar["chat_history"], chat)
            if chat:
                self.assertLess(rendered.index("Turn 0 - Coach"), rendered.index("### Agent_1"))

    def test_full_archive_includes_private_events_and_missing_turns(self):
        events = [
            {"event_id": "1", "turn": 1, "actor": "Agent_1", "kind": "think",
             "visibility": "private", "payload": {"content": "short", "raw_content": "full thought"}},
            {"event_id": "2", "turn": 3, "actor": "Tool", "kind": "tool_result",
             "visibility": "private", "payload": {"value": 42}},
            {"event_id": "3", "turn": 3, "actor": "Agent_2", "kind": "automatic_memory",
             "visibility": "private", "payload": {"exchanges": ["saved"]}},
        ]
        source = {"memory": {"events": events}, "chat_history": [], "budget": {"turns_used": 4}}
        exported = communication_sidecar(source)
        self.assertEqual(exported["event_count"], 3)
        for event, row in zip(events, exported["chat_history"]):
            for key, value in event.items():
                self.assertEqual(row[key], value)
        self.assertEqual(exported["chat_history"][0]["message"], "full thought")
        self.assertEqual([t["turn"] for t in exported["turns"]], [1, 2, 3, 4])
        self.assertEqual(exported["turns"][1]["status"], "no_archived_events")
        self.assertEqual(exported["turns"][2]["chat_history_indices"], [1, 2])
        rendered = communication_markdown(exported)
        for turn in range(1, 5):
            self.assertIn(f"## Turn {turn}\n", rendered)
        self.assertIn("full thought", rendered)

    def test_projects_conversation_and_structured_deliberation_only(self):
        events = [
            {"event_id": "1", "turn": 1, "actor": "Agent_1", "kind": "think",
             "visibility": "private", "payload": {"content": "secret"}},
            {"event_id": "2", "turn": 1, "actor": "Agent_1", "kind": "speak",
             "visibility": "public", "payload": {"content": "hello"}},
            {"event_id": "3", "turn": 2, "actor": "Agent_2", "kind": "decide",
             "payload": {"outcome": "accept", "reason": "checked"}},
        ]
        rows = communication_history(events)
        self.assertEqual([row["action"] for row in rows], ["speak", "decide"])
        self.assertEqual(rows[0]["message"], "hello")
        self.assertEqual(rows[1]["message"], "accept | checked")

    def test_sidecars_do_not_rewrite_contest_session(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contest_session.json"
            source = {"session_id": "s", "competition_id": "c", "system_variant": "otc",
                      "memory": {"events": [{"event_id": "e", "turn": 1,
                          "actor": "Agent_1", "kind": "review_answer",
                          "payload": {"content": "approve"}}]}}
            original = json.dumps(source)
            path.write_text(original, encoding="utf-8")
            result = export_one(path)
            self.assertIsNotNone(result)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            exported = json.loads((path.parent / "otc_chat.json").read_text(encoding="utf-8"))
            self.assertEqual(exported["event_count"], 1)
            self.assertIn("approve", (path.parent / "otc_chat.md").read_text(encoding="utf-8"))

    def test_sidecar_reuses_persisted_chat_history(self):
        source = {"session_id": "s", "system_variant": "otc", "memory": {"events": []},
                  "chat_history": [{"sender": "Agent_1", "message": "saved"}]}
        sidecar = communication_sidecar(source)
        self.assertEqual(sidecar["event_count"], 1)
        self.assertEqual(sidecar["chat_history"][0]["message"], "saved")


if __name__ == "__main__":
    unittest.main()
