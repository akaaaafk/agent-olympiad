"""Mechanics exposed by live runs; no reference answers enter action policy."""
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from contest_actions import _apply_action
from contest_memory import ContestMemory
from contest_policy import _actions_for_agent, _resolved_actions
from contest_session import ContestSession
from contest_runner import run_contest
from llm import LLMResponse, LLMToolCall
from test_answer_binding_regression import state as binding_state, BASELINES


def state(*args, **kwargs):
    manifest, session, memory, config = binding_state(*args, **kwargs)
    # Mirror engine initialization: these are numerical answer-sheet tasks,
    # whereas the low-level TaskUnit constructor defaults to programming.
    for task in session.tasks:
        task.kind = "non_programming"
    # These formatting tests revise an already selected task. Cross-task
    # binding has separate regressions, including atomic labelled writes.
    session.select_task(session.tasks[-1].task_id)
    return manifest, session, memory, config


class LiveFailureRegressions(unittest.TestCase):
    def test_native_work_retains_canonical_final_answer_contract_for_every_baseline(self):
        for baseline in BASELINES:
            with self.subTest(baseline=baseline):
                manifest, session, memory, config = state(baseline)
                offered = _actions_for_agent(_resolved_actions(manifest, config), session,
                    config, "Agent_1", answer_sheet_contest=True, memory=memory)
                work = next(spec for spec in offered if spec.name == "work")
                self.assertIn("Final answer: <value>", work.description)
                self.assertIn("different problem's answer", work.description)

    def make_memory(self):
        memory = ContestMemory(run_id="live-repro", session_id="test", competition_id="arml_local")
        memory.append(task_id="q6", question_id=None, actor="Agent_1", kind="note", visibility="private",
            payload={"content": "Unfold the path for the first hit. Need an independent geometric check."}, turn=1)
        return memory

    def test_explicit_problem_filter_never_returns_another_task_even_on_keyword_match(self):
        memory = self.make_memory()
        for query in ("", "path", "P7 verified result or handoff note"):
            with self.subTest(query=query):
                self.assertEqual(memory.recall("Agent_1", problem_id="q7", query=query), [])
        self.assertEqual(len(memory.recall("Agent_1", problem_id="q6", query="path")), 1)
        self.assertEqual(len(memory.recall("Agent_1", query="path")), 1)

    def test_keyword_substrings_and_stop_words_do_not_create_relevance(self):
        memory = self.make_memory()
        for query in ("or", "P7 verified result or handoff note", "fold", "geomet"):
            with self.subTest(query=query):
                self.assertEqual(memory.recall("Agent_1", query=query), [])
        self.assertEqual(len(memory.recall("Agent_1", query='"geometric"')), 1)

    def apply(self, manifest, session, memory, config, content, target):
        return _apply_action(action="work", arguments={"content": content, "problem_id": target},
            agent="Agent_1", manifest=manifest, session=session, memory=memory, config=config,
            strategic_policy=None, task_action_executor=Mock())

    def test_progress_note_cannot_atomically_replace_a_formatted_answer_including_resume(self):
        for baseline in BASELINES:
            for restored in (False, True):
                with self.subTest(baseline=baseline, restored=restored):
                    manifest, session, memory, config = state(baseline, initial="Final answer: 42.")
                    if restored:
                        session = ContestSession.from_checkpoint(session.checkpoint())
                    before = session.checkpoint(), memory.to_checkpoint_json()
                    with self.assertRaisesRegex(ValueError, "Final answer"):
                        self.apply(manifest, session, memory, config,
                            "No change needed; recording this as a verification note for handoff.",
                            "arml_local_2009:7")
                    self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)

    def test_explicit_revisions_and_withdrawals_replace_prior_answers_without_gold(self):
        for content in ("Final answer: 43.", "Final answer: withdrawn; previous candidate was wrong."):
            manifest, session, memory, config = state("decentralized", initial="Final answer: 42.")
            self.apply(manifest, session, memory, config, content, "arml_local_2009:7")
            self.assertEqual(session.active_task.versions[-1].content, content)

    def test_unfinished_work_can_be_recorded_and_revised(self):
        manifest, session, memory, config = state("decentralized", initial="Unfinished branch.")
        self.apply(manifest, session, memory, config, "A new partial derivation.", "arml_local_2009:7")
        self.assertEqual(session.active_task.versions[-1].content, "A new partial derivation.")

    def test_character_cap_cannot_silently_remove_or_change_final_answer(self):
        for baseline in ("vallina_otc", "otc"):
            manifest, session, memory, config = state(baseline, initial="Final answer: 42.")
            limit = config.otc_policy.char_limit("work")
            content = "Derivation. " * limit + "\nFinal answer: 43."
            before = session.checkpoint(), memory.to_checkpoint_json()
            with self.subTest(baseline=baseline), self.assertRaisesRegex(ValueError, "shorten|limit"):
                self.apply(manifest, session, memory, config, content, "arml_local_2009:7")
            self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)

    def test_engine_feedback_and_deadline_preserve_answer_after_rejected_note(self):
        for baseline in BASELINES:
            with self.subTest(baseline=baseline):
                manifest, _, _, config = state(baseline)
                requests = []
                plan = {"work_assignments": {f"Agent_{i}": [t.task_id for t in manifest.tasks]
                    for i in range(1, config.team_size + 1)}}

                def query(system, user):
                    return json.dumps(plan) if user.startswith("OPENING LEADER PLAN") else "NEXT ACTION: rest"

                def request(req):
                    name, args = "rest", {"reason": "waiting"}
                    if req.metadata["agent"] == "Agent_1":
                        requests.append(req)
                        stage = len(requests)
                        if stage in (1, 3):
                            work = next(tool for tool in req.tools if tool["name"] == "work")
                            self.assertIn("Final answer: <value>", work["description"])
                            name, args = "work", {"problem_id": "arml_local_2009:7", "content":
                                "Problem 7: Final answer: 42." if stage == 1 else "Problem 7: No revision; this is a progress note."}
                        elif stage == 2:
                            name, args = "speak", {"content": "The candidate is available for review."}
                    return LLMResponse("", "mock", "format-contract", tool_calls=(LLMToolCall(name, args),),
                        usage={"api_calls": 1, "output_tokens": 1})

                result = run_contest(manifest, query, config, action_request_fn=request, coach_query_fn=query)
                errors = [e for e in result["memory"]["events"] if e["kind"] == "action_error"]
                self.assertEqual(len(errors), 1, errors)
                self.assertEqual(any("Final answer" in req.user_prompt for req in requests[3:]),
                                 not config.current_turn_only)
                self.assertEqual(result["submissions"]["arml_local_2009:7"], "Problem 7: Final answer: 42.")


if __name__ == "__main__":
    unittest.main()
