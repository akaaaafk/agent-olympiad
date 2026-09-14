"""Conversation memory works even when the agent never chooses recall."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from action_modules.memory import agent_context
from contest_memory import ContestMemory
from contest_runner import run_contest
from llm import LLMResponse, LLMToolCall
from test_checkpoint_cursor import manifest, config
import automatic_memory
from contest_budget import estimate_tokens
from contest_engine import _ContestEngine
from unittest.mock import Mock


class AutomaticMemoryTests(unittest.TestCase):
    def memory(self):
        return ContestMemory(run_id="auto", session_id="test", competition_id="arml_local")

    def append(self, memory, text, *, task="q1", actor="Agent_1", kind="speak",
               visibility="public", recipients=()):
        return memory.append(task_id=task, question_id=None, actor=actor,
                             kind=kind, visibility=visibility, recipients=recipients,
                             payload={"content": text, "gold_answer": "GOLD_CANARY"}, turn=1)

    def test_visible_dialogue_exact_candidate_and_task_history_survive_restore(self):
        memory = self.memory()
        first = self.append(memory, "Public useful premise")
        work = self.append(memory, "A derivation.\nFinal answer: 25/42", kind="work")
        self.append(memory, "Other question", task="q2")
        automatic_memory.sync(memory, viewer="Agent_2", turn=1)
        context = automatic_memory.context(memory, viewer="Agent_2", current_task_id="q1")
        self.assertEqual(context["current_task"]["candidate_claim"]["value"], "25/42")
        self.assertIn(first.event_id, json.dumps(context))
        self.assertIn(work.event_id, json.dumps(context))
        self.assertEqual(context["recent_other_tasks"][0]["task_id"], "q2")
        before = memory.to_checkpoint_json()
        restored = ContestMemory.from_checkpoint_json(before)
        automatic_memory.sync(restored, viewer="Agent_2", turn=1)
        self.assertEqual(before, restored.to_checkpoint_json())
        self.assertEqual(context, automatic_memory.context(restored, viewer="Agent_2", current_task_id="q1"))
        self.append(restored, "Corrected derivation.\nFinal answer: 26/42", kind="work")
        automatic_memory.sync(restored, viewer="Agent_2", turn=2)
        self.assertEqual(automatic_memory.context(restored, viewer="Agent_2", current_task_id="q1")
                         ["current_task"]["candidate_claim"]["value"], "26/42")
        self.assertEqual(automatic_memory.context(restored, viewer="Agent_2", current_task_id="q2")
                         ["current_task"]["task_id"], "q2")

    def test_no_private_or_judge_leak_and_memory_off_hides_automatic_records(self):
        memory = self.memory()
        self.append(memory, "PUBLIC_CANARY")
        self.append(memory, "DM_CANARY", kind="direct_message", visibility="private", recipients=("Agent_2",))
        self.append(memory, "THINK_CANARY", kind="think", visibility="private")
        self.append(memory, "JUDGE_CANARY", visibility="judge")
        for viewer in ("Agent_1", "Agent_2", "Agent_3"):
            automatic_memory.sync(memory, viewer=viewer, turn=1)
        contexts = {v: json.dumps(automatic_memory.context(memory, viewer=v, current_task_id="q1"))
                    for v in ("Agent_1", "Agent_2", "Agent_3")}
        for text in contexts.values():
            self.assertIn("PUBLIC_CANARY", text)
            self.assertNotIn("GOLD_CANARY", text)
            self.assertNotIn("JUDGE_CANARY", text)
        self.assertIn("DM_CANARY", contexts["Agent_2"])
        self.assertNotIn("THINK_CANARY", contexts["Agent_2"])
        self.assertNotIn("DM_CANARY", contexts["Agent_3"])
        self.assertNotIn("THINK_CANARY", contexts["Agent_3"])
        restored = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
        disabled = agent_context(restored, viewer="Agent_1", enabled=False, current_task_id="q1")
        self.assertNotIn("automatic_memory", json.dumps(disabled))
        self.assertNotIn("THINK_CANARY", json.dumps(disabled))

    def test_summary_fallback_is_bounded_and_preserves_sources(self):
        memory = self.memory()
        for i in range(60):
            self.append(memory, f"message {i}: " + "x" * 1000)
        automatic_memory.sync(memory, viewer="Agent_2", turn=1)
        context = automatic_memory.context(memory, viewer="Agent_2", current_task_id="q1", max_chars=3000)
        self.assertLessEqual(len(json.dumps(context, ensure_ascii=False)), 3000)
        self.assertIn("message 59:", json.dumps(context))
        self.assertIsNone(context["current_task"]["essence"])
        self.assertEqual(len([e for e in memory.view("Agent_2") if e.kind == "speak"]), 60)
        self.assertEqual(memory.view("Agent_2")[-1].payload["source_event_count"], 60)
        for block in ('<memory_update>bad json</memory_update>', '<memory_update>{',
                      '<memory_update>{"takeaways":"x"}</memory_update>'):
            thought, essence = automatic_memory.split_think("Check this.\n" + block)
            self.assertEqual(thought, "Check this.")
            self.assertIsNone(essence)

    def test_old_memory_runtime_is_rejected_before_any_new_model_call(self):
        engine = _ContestEngine(manifest(), Mock(), config())
        checkpoint = engine._checkpoint()
        checkpoint["engine_state"]["settings"].pop("automatic_memory_version")
        query = Mock(side_effect=AssertionError("must not call model"))
        with self.assertRaisesRegex(ValueError, "runtime version/settings mismatch"):
            run_contest(manifest(), query, config(), session_checkpoint=checkpoint,
                        memory_checkpoint=engine.memory.to_checkpoint_json())
        query.assert_not_called()

    def test_engine_carries_dialogue_and_summary_without_optional_memory_actions(self):
        captures = []
        query_outputs = []

        def query(system, user):
            if "<memory_update>" in system:
                response = ('Consider the unfinished check.\n<memory_update>'
                        '{"task_id":"q1","team_progress":"",'
                        '"takeaways":"Pairing trick retained",'
                        '"open_questions":"Endpoint unverified",'
                        '"next_step":"Check the endpoint"}</memory_update>')
            else:
                response = "Divide the work."
            query_outputs.append(response)
            return response

        def request(req):
            captures.append(req)
            if req.metadata["agent"] == "Agent_1":
                name, args = "speak", {"content": "DIALOGUE_CANARY: endpoint needs checking."}
            else:
                name, args = "rest", {"reason": "Waiting"}
            return LLMResponse("", "mock", "automatic-memory", tool_calls=(LLMToolCall(name, args),),
                               usage={"api_calls": 1, "output_tokens": 1})

        result = run_contest(manifest(), query, config(max_turns=2),
                             action_request_fn=request, coach_query_fn=query)
        events = result["memory"]["events"]
        self.assertFalse(any(e["kind"] in {"recall", "note", "memory_auxiliary_call"} for e in events))
        automatic = [e for e in events if e["kind"] == "automatic_memory"]
        self.assertTrue(automatic, "No automatic memory was written without explicit tool calls")
        self.assertTrue(any("Pairing trick retained" in json.dumps(e) for e in automatic))
        second = next(r for r in captures if r.metadata["agent"] == "Agent_2")
        self.assertIn("automatic_memory", second.user_prompt)
        self.assertIn("DIALOGUE_CANARY", second.user_prompt)
        self.assertIn("Pairing trick retained", second.user_prompt)
        self.assertEqual(result["budget"]["api_calls_used"], 25)  # coach + 12 think + 12 action
        self.assertEqual(result["budget"]["tokens_used"], sum(map(estimate_tokens, query_outputs)) + 12)
        self.assertEqual(result["memory_action_policy"]["semantic_updates"], 12)
        self.assertTrue(all("<memory_update>" not in e["payload"]["content"]
                            and "<memory_update>" in e["payload"]["raw_content"]
                            for e in events if e["kind"] == "think"))


if __name__ == "__main__":
    unittest.main()
