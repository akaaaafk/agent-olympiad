"""Memory retrieval and public handoffs through the real contest boundaries."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

import otc_runtime
from action_modules.memory import agent_context
from contest_actions import _apply_action
from contest_config import ContestRunConfig
from contest_memory import ContestMemory
from contest_runner import run_contest
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card
from strategy import StrategicPolicy
from test_otc_rulecard import arml_manifest


class MemoryAuditRegressions(unittest.TestCase):
    def setUp(self):
        self.manifest = arml_manifest()
        self.card = copy.deepcopy(load_rule_card("arml_local", required=True))
        self.config = ContestRunConfig("otc", 6, 12, rule_card=self.card)
        self.memory = ContestMemory(run_id="audit", session_id="arml_test",
                                    competition_id="arml_local")
        self.session = ContestSession([TaskUnit("q1"), TaskUnit("q2")],
                                      ContestBudgetState(max_turns=12))
        self.session.select_task("q1")

    def call(self, action, **arguments):
        return _apply_action(action=action, arguments=arguments, agent="Agent_1",
            manifest=self.manifest, session=self.session, memory=self.memory,
            config=self.config, strategic_policy=StrategicPolicy(),
            task_action_executor=Mock(side_effect=AssertionError("No external tools")))

    def remember(self, content, task_id="q1"):
        self.call("remember", content=content, problem_id=task_id)
        return self.memory.view("Agent_1")[-1].event_id

    def test_identical_notes_on_different_tasks_remain_retrievable(self):
        first = self.remember("The diagram is missing; inspect the source PDF.", "q1")
        second = self.remember("The diagram is missing; inspect the source PDF.", "q2")
        notes = self.memory.recall("Agent_1")
        self.assertEqual({n["note_id"] for n in notes}, {first, second})
        status = self.memory.recall_status("Agent_1", current_task_id="q1")
        self.assertEqual(status["visible_note_count"], 2)
        self.assertEqual(status["current_task_note_count"], 1)
        restored = ContestMemory.from_checkpoint_json(self.memory.to_checkpoint_json())
        self.assertEqual(restored.recall_status("Agent_1", current_task_id="q1"), status)

    def test_keyword_punctuation_does_not_hide_a_saved_fact(self):
        note_id = self.remember("The parity shortcut fails for odd n.")
        for query in ("parity,", '"parity"', "(parity)"):
            with self.subTest(query=query):
                self.assertEqual([n["note_id"] for n in self.memory.recall(
                    "Agent_1", query=query)], [note_id])
        self.assertEqual(self.memory.recall("Agent_1", query="network flow"), [])
        self.assertEqual(self.memory.recall("Agent_1", query="..."), [])

    def test_public_share_obeys_message_cap_and_preserves_private_note(self):
        original = "A compact result with supporting evidence. " * 50
        note_id = self.remember(original)
        self.call("share_note", note_id=note_id)
        shared = [e for e in self.memory.view("Agent_2") if e.kind == "note_shared"]
        self.assertEqual(len(shared), 1)
        limit = min(self.config.otc_policy.char_limit("share_note"),
                    self.config.otc_policy.communication["max_message_chars"])
        self.assertLessEqual(len(shared[0].payload["content"]), limit)
        own_notes = {n["note_id"]: n for n in self.memory.recall("Agent_1", problem_id="q1")}
        self.assertEqual(own_notes[note_id]["content"], original)
        self.assertNotIn(original, json.dumps(agent_context(self.memory,
            viewer="Agent_2", enabled=True, current_task_id="q1")))
        self.assertEqual(otc_runtime.communication_budget(
            self.memory, self.config.otc_policy).team_used, 1)

    def test_public_share_counts_as_a_report(self):
        self.call("work", content="An unfinished derivation.")
        note_id = self.remember("Failed symmetry shortcut; check the odd case.")
        self.call("share_note", note_id=note_id)
        self.assertTrue(otc_runtime.reported_after_last_work(self.memory, "Agent_1"))
        self.assertEqual(otc_runtime.silent_work_streak(self.memory, "Agent_1"), 0)

    def test_private_side_call_does_not_reset_silent_work_streak(self):
        for turn in (0, 1):
            self.call("work", content=f"Partial derivation, stage {turn}.")
            self.session.consume_budget(turns=1)
        self.remember("Keep the unfinished odd case private.")
        self.assertEqual(otc_runtime.silent_work_streak(self.memory, "Agent_1"), 2)
        self.assertFalse(otc_runtime.reported_after_last_work(self.memory, "Agent_1"))

    def test_new_work_after_same_turn_share_still_needs_its_own_report(self):
        note_id = self.remember("Earlier odd-case counterexample.")
        self.call("share_note", note_id=note_id)
        self.call("work", content="New result after the earlier handoff.")
        self.assertFalse(otc_runtime.reported_after_last_work(self.memory, "Agent_1"))

    def test_failed_or_duplicate_share_does_not_publish_or_spend_message_budget(self):
        note_id = self.remember("Verified small-case counterexample.")
        self.call("share_note", note_id=note_id)
        before = self.memory.to_checkpoint_json()
        for bad_id in ("missing-note", note_id):
            with self.subTest(note_id=bad_id), self.assertRaises(ValueError):
                self.call("share_note", note_id=bad_id)
            self.assertEqual(self.memory.to_checkpoint_json(), before)
        self.assertEqual(otc_runtime.communication_budget(
            self.memory, self.config.otc_policy).team_used, 1)

    def test_shared_report_unlocks_work_in_the_same_seat_turn(self):
        self.run_handoff_scenario()

    def test_private_side_call_cannot_unlock_same_turn_work(self):
        self.run_handoff_scenario(private=True)

    def test_handoff_checkpoint_resumes_without_repeating_share_or_think(self):
        uninterrupted = self.run_handoff_scenario()
        resumed = self.run_handoff_scenario(interrupt=True)
        from test_checkpoint_cursor import comparable
        self.assertEqual(comparable(uninterrupted), comparable(resumed))

    def run_handoff_scenario(self, *, private=False, interrupt=False):
        # Two silent ordinary actions trigger discussion on turn three.
        # A successful auxiliary share must satisfy it without a second report.
        counts = Counter()
        note_ids = {}
        observations = []
        self.card.simulation["max_turns"] = 3
        self.card.simulation["open_table_coach"]["min_turns"] = 3
        config = ContestRunConfig("otc", 6, 3, rule_card=self.card,
            max_api_calls=100, max_tokens=100000, deadline_submit=False)

        def query(system, user):
            return "Check the unresolved case and continue."

        def request(req):
            agent = req.metadata["agent"]
            stage = counts[agent]
            counts[agent] += 1
            offered = {t["name"] for t in req.tools}
            if stage == 0:
                name, args = "remember", {"content": f"{agent}: odd-case counterexample.",
                                           "problem_id": req.metadata["task_id"]}
            elif stage == 1:
                receipts = json.loads(req.user_prompt.rsplit(
                    "MEMORY TOOL RESULTS (same turn, private to you)\n", 1)[1])
                note_ids[agent] = next(e["event_id"] for e in receipts if e["kind"] == "note")
                name, args = "work", {"content": f"{agent} unfinished branch 1."}
            elif stage == 2:
                name, args = "work", {"content": f"{agent} unfinished branch 2."}
            elif stage == 3:
                self.assertNotIn("work", offered)
                name, args = ("remember", {"content": "Private clarification of the odd case."}) if private else (
                    "share_note", {"note_id": note_ids[agent]})
            else:
                self.assertEqual(stage, 4)
                observations.append((agent, offered))
                name, args = ("work", {"content": f"{agent} unfinished branch 3."}) if "work" in offered else (
                    "rest", {"reason": "Work incorrectly still hidden after public report."})
            return LLMResponse("", "mock", "memory-audit",
                tool_calls=(LLMToolCall(name, args),), usage={"api_calls": 1, "output_tokens": 1})

        saved = []
        class InterruptedHandoff(BaseException):
            pass

        def checkpoint(session, memory):
            events = json.loads(memory)["events"]
            if interrupt and not saved and any(e["kind"] == "memory_auxiliary_call"
                and e["payload"].get("action") == "share_note" for e in events):
                saved.extend([copy.deepcopy(session), memory])
                raise InterruptedHandoff()

        try:
            result = run_contest(self.manifest, query, config, action_request_fn=request,
                action_transport="native", coach_query_fn=query, checkpoint_callback=checkpoint)
        except InterruptedHandoff:
            result = run_contest(self.manifest, query, config, action_request_fn=request,
                action_transport="native", coach_query_fn=query,
                session_checkpoint=saved[0], memory_checkpoint=saved[1])
        if interrupt:
            self.assertEqual(len(saved), 2)
        self.assertEqual(len(observations), 6)
        self.assertTrue(all(("work" in offered) == (not private)
                            for _, offered in observations), observations)
        kinds = Counter(e["kind"] for e in result["memory"]["events"])
        self.assertEqual(kinds["action_error"], 0)
        self.assertEqual(kinds["note_shared"], 0 if private else 6)
        self.assertEqual(kinds["work"], 12 if private else 18)
        self.assertEqual(kinds["think"], 18)
        self.assertEqual(result["budget"]["turns_used"], 3)
        self.assertEqual(result["budget"]["simulated_minutes_used"], 15)
        return result


if __name__ == "__main__":
    unittest.main()
