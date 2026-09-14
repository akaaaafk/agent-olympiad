"""Exercise dispatch, visibility, scoring and real engine resume for both pilots."""
import copy
from contextlib import redirect_stdout
from dataclasses import replace
import json
import io
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from action_modules.competition_flow import ACTION_NAMES
from action_modules.task_specific import resolve_contest_interface
from competition_flow import bind_competition_flow
from contest_actions import _apply_action
from contest_adapters import grade_contest_result
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_engine import _ContestEngine
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_policy import _actions_for_agent, _resolved_actions
from contest_prompts import _user_prompt
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card
from strategy import StrategicPolicy
from tool_registry import actions_for_runtime


def fixture(competition="hmmt_guts", season="nov", pairs=2):
    count = (3 if season == "nov" else 4) * 2 if competition == "hmmt_guts" else pairs * 2
    tasks = []
    for i in range(count):
        tid = f"PILOT_SECRET_TASK_{i+1}"
        role = "toss_up" if i % 2 == 0 else "bonus"
        row = dict(season=season, parent_session_id="packet", source_file="packet.pdf",
                   question_number=i // 2 + 1, tossup_or_bonus=role,
                   gold_label={"parts": [{"id": str(i+1), "expected": "synthetic correct",
                                           "points": 5 if competition == "hmmt_guts" else 1}]})
        tasks.append(ManifestTask(tid, "packet", str(i+1), f"Only prompt {i+1}.",
                                  "team_contest" if competition == "hmmt_guts" else "science_bowl",
                                  5 if competition == "hmmt_guts" else 1, False, row))
    flow = "guts_sets_v1" if competition == "hmmt_guts" else "science_bowl_buzzer_v1"
    return ContestManifest("flow_test", competition, tuple(tasks), {"competition_flow": flow})


def config_for(manifest, variant="decentralized"):
    size = (6 if manifest.tasks[0].benchmark.get("season") == "nov" else 8) if manifest.competition_id == "hmmt_guts" else 4
    return ContestRunConfig(variant, 1 if variant == "single_agent" else size, 24,
                            max_api_calls=240, max_tokens=60000,
                            rule_card=load_rule_card(manifest.competition_id)
                            if variant in {"otc", "vallina_otc"} else None)


class FlowTests(unittest.TestCase):
    def setup_flow(self, competition="hmmt_guts", variant="decentralized", **kw):
        self.manifest = fixture(competition, **kw)
        self.config = config_for(self.manifest, variant)
        self.session = ContestSession([TaskUnit(t.task_id, kind="non_programming") for t in self.manifest.tasks],
                                      ContestBudgetState(max_turns=24))
        self.memory = ContestMemory(run_id="flow_test", session_id="flow_test", competition_id=competition)
        self.flow = bind_competition_flow(self.manifest, self.session, self.config)
        self.session.select_task(self.flow.current_ids[0])
        self.executor = Mock(side_effect=AssertionError("flow must not invoke arbitrary external tools"))

    def apply(self, action, arguments=None, agent="Agent_1"):
        return _apply_action(action=action, arguments=arguments or {}, agent=agent,
                             manifest=self.manifest, session=self.session, memory=self.memory,
                             config=self.config, strategic_policy=StrategicPolicy(),
                             task_action_executor=self.executor)

    def offered(self, agent="Agent_1"):
        return _actions_for_agent(_resolved_actions(self.manifest, self.config), self.session,
                                  self.config, agent, memory=self.memory)

    def test_opt_in_and_runtime_scope(self):
        for competition in ("hmmt_guts", "science_bowl"):
            manifest = fixture(competition)
            ordinary = replace(manifest, metadata={})
            self.assertFalse({s.name for s in resolve_contest_interface(ordinary).actions} & ACTION_NAMES)
            self.assertTrue({s.name for s in resolve_contest_interface(manifest).actions} & ACTION_NAMES)
        self.assertFalse(actions_for_runtime("env") & ACTION_NAMES)
        self.assertTrue(ACTION_NAMES <= actions_for_runtime("session"))

    def test_guts_seasons_lock_submit_and_release(self):
        for season, size in (("nov", 3), ("feb", 4)):
            self.setup_flow(season=season)
            current = self.flow.current_ids
            self.assertEqual(len(current), size)
            for tid in current:
                self.apply("select_problem", {"problem_id": tid})
                self.apply("work", {"content": "synthetic correct"})
            self.apply("submit_set")
            self.assertEqual(self.flow.state["phase"], "awaiting_set")
            self.assertEqual(sum(t.score for t in self.session.tasks), size * 5)
            self.assertTrue(all(self.session.task(tid).locked for tid in current))
            before = self.session.checkpoint()
            with self.assertRaises(ValueError):
                self.apply("submit_set")
            self.assertEqual(before, self.session.checkpoint())
            self.apply("collect_next_set")
            self.assertEqual(len(self.flow.current_ids), size)
            self.assertFalse(set(current) & set(self.flow.current_ids))
            with self.assertRaises(RuntimeError):
                self.session.select_task(current[0])

    def test_hidden_tasks_absent_from_prompt_schemas_scoreboard_and_direct_calls(self):
        self.setup_flow(variant="otc")
        hidden = self.manifest.tasks[3].task_id
        prompt = _user_prompt(self.manifest, self.session, self.memory, self.config, "Agent_1")
        self.assertNotIn(hidden, prompt)
        self.assertNotIn("automatically hands in", prompt)
        self.assertNotIn(hidden, json.dumps([dict(s.argument_schema) for s in self.offered()]))
        from contest_lifecycle import _record_scoreboard
        _record_scoreboard(self.memory, self.session)
        self.assertNotIn(hidden, self.memory.to_checkpoint_json())
        for action, args in (("inspect_problem", {"problem_id": hidden}),
                             ("work", {"problem_id": hidden, "content": "x"}),
                             ("recall", {"problem_id": hidden}),
                             ("remember", {"problem_id": hidden, "content": "x"}),
                             ("select_problem", {"problem_id": hidden})):
            before = (self.session.checkpoint(), self.memory.to_checkpoint_json())
            with self.assertRaises(ValueError):
                self.apply(action, args)
            self.assertEqual(before, (self.session.checkpoint(), self.memory.to_checkpoint_json()))
        with self.assertRaises(ValueError):
            self.session.select_task(hidden)

    def test_generic_submit_cannot_bypass_flow(self):
        self.setup_flow()
        self.apply("work", {"content": "synthetic correct"})
        for action in ("submit", "finish_contest", "answer_bonus"):
            with self.assertRaises(ValueError):
                self.apply(action, {"answer": "synthetic correct"} if action == "answer_bonus" else {})
        with self.assertRaises(ValueError):
            self.session.submit("AC", score=100)

    def test_atomic_set_judge_failure(self):
        self.setup_flow()
        before = (self.session.checkpoint(), self.memory.to_checkpoint_json())
        with patch.object(self.flow, "_grade", side_effect=[(0, 5), RuntimeError("judge unavailable")]):
            with self.assertRaises(RuntimeError):
                self.apply("submit_set")
        self.assertEqual(before, (self.session.checkpoint(), self.memory.to_checkpoint_json()))

    def test_science_recognition_first_answer_and_captain(self):
        self.setup_flow("science_bowl")
        tossup = self.flow.current_ids[0]
        bonus = self.manifest.tasks[1].task_id
        with self.assertRaises(ValueError):
            self.apply("answer_tossup", {"answer": "synthetic correct"})
        self.apply("buzz", agent="Agent_2")
        for agent in ("Agent_1", "Agent_3"):
            self.assertNotIn("answer_tossup", {s.name for s in self.offered(agent)})
            with self.assertRaises(ValueError):
                self.apply("answer_tossup", {"answer": "synthetic correct"}, agent)
        with self.assertRaises(ValueError):
            self.apply("buzz", agent="Agent_3")
        self.apply("answer_tossup", {"answer": "synthetic correct"}, "Agent_2")
        self.assertEqual(self.flow.current_ids, (bonus,))
        self.assertTrue(self.session.task(tossup).locked)
        self.assertEqual(self.session.task(tossup).score, 4)
        with self.assertRaises(ValueError):
            self.apply("answer_bonus", {"answer": "synthetic correct"}, "Agent_2")
        self.apply("answer_bonus", {"answer": "synthetic correct"})
        self.assertEqual(self.session.task(bonus).score, 10)
        self.assertEqual(self.flow.state["phase"], "tossup_open")

    def test_tossup_conferral_blocked_for_every_baseline(self):
        for variant in BASELINE_NAMES:
            self.setup_flow("science_bowl", variant)
            forbidden = {"work", "speak", "direct_message", "share_note", "propose", "review_answer"}
            self.assertFalse(forbidden & {s.name for s in self.offered()})
            for name in forbidden:
                with self.assertRaises(ValueError):
                    self.apply(name, {"content": "teammate hint"})
            with self.assertRaises(ValueError):
                self.session.create_answer("teammate draft")

    def test_wrong_tossup_skips_unearned_bonus_and_cannot_retry(self):
        self.setup_flow("science_bowl")
        bonus = self.manifest.tasks[1].task_id
        self.apply("buzz")
        self.apply("answer_tossup", {"answer": "wrong"})
        self.assertEqual(self.flow.state["cursor"], 1)
        self.assertFalse(self.flow.is_visible(bonus))
        self.assertFalse(self.session.task(bonus).submissions)
        with self.assertRaises(ValueError):
            self.apply("answer_bonus", {"answer": "synthetic correct"})

    def test_checkpoint_resume_preserves_recognized_speaker(self):
        self.setup_flow("science_bowl")
        self.apply("buzz", agent="Agent_2")
        checkpoint = self.session.checkpoint()
        self.session = ContestSession.from_checkpoint(checkpoint)
        self.flow = bind_competition_flow(self.manifest, self.session, self.config)
        self.assertEqual(self.session.checkpoint(), checkpoint)
        with self.assertRaises(ValueError):
            self.apply("answer_tossup", {"answer": "synthetic correct"}, "Agent_1")
        self.apply("answer_tossup", {"answer": "synthetic correct"}, "Agent_2")
        self.assertEqual(self.flow.state["phase"], "bonus_open")

    def test_resume_rejects_mismatched_flow_and_hidden_unlock(self):
        self.setup_flow()
        checkpoint = self.session.checkpoint()
        for kind in ("disabled", "tampered"):
            saved = copy.deepcopy(checkpoint)
            manifest = self.manifest
            if kind == "disabled":
                manifest = replace(manifest, metadata={})
            else:
                saved["tasks"][-1]["locked"] = False
            restored = ContestSession.from_checkpoint(saved)
            with self.assertRaises(ValueError):
                bind_competition_flow(manifest, restored, self.config)

    def test_missing_pairs_season_or_grading_rejected_before_run(self):
        for manifest in (replace(fixture("science_bowl"), tasks=fixture("science_bowl").tasks[:1]),
                         replace(fixture(), tasks=fixture().tasks[:2])):
            with self.assertRaises(ValueError):
                _ContestEngine(manifest, lambda *_: "", config_for(manifest))
        manifest = fixture()
        bad = replace(manifest.tasks[0], benchmark={**manifest.tasks[0].benchmark, "gold_label": {}})
        with self.assertRaises(Exception):
            _ContestEngine(replace(manifest, tasks=(bad, *manifest.tasks[1:])), lambda *_: "", config_for(manifest))

    def test_role_review_and_permission_gates_cannot_be_bypassed(self):
        self.setup_flow(variant="centralized")
        with self.assertRaises(ValueError):
            self.apply("submit_set", agent="Agent_2")
        self.setup_flow(variant="otc")
        self.apply("work", {"content": "synthetic correct"})
        self.assertNotIn("submit_set", {s.name for s in self.offered()})
        with self.assertRaises(ValueError):
            self.apply("submit_set")
        task = self.session.active_task
        self.apply("review_answer", {"problem_id": task.task_id, "version_hash": task.versions[-1].version_hash,
                                      "decision": "approve", "content": "Synthetic fixture checked."}, "Agent_2")
        self.assertIn("submit_set", {s.name for s in self.offered()})
        with patch("tool_registry.competition_permissions", return_value=set()):
            with self.assertRaises(ValueError):
                self.apply("submit_set")

    def test_cli_result_and_completed_resume_use_existing_pipeline_contract(self):
        import run_competition_batch as cli
        for competition in ("hmmt_guts", "science_bowl"):
            manifest = fixture(competition, pairs=1)
            actions = ([('submit_set', {}), ('collect_next_set', {}), ('submit_set', {})]
                       if competition == "hmmt_guts" else
                       [('buzz', {}), ('answer_tossup', {'answer': 'synthetic correct'}),
                        ('answer_bonus', {'answer': 'synthetic correct'})])
            query = Mock(side_effect=[json.dumps(dict(action=name, arguments=args)) for name, args in actions])
            with tempfile.TemporaryDirectory() as directory:
                argv = ["batch", "--contest-manifest", "fixture.json", "--system-variant", "single_agent",
                        "--max-turns", "6", "--output", directory, "--no-judge-collab", "--no-judge-cce"]
                with patch.object(cli, "load_contest_manifest", return_value=manifest), \
                     patch.object(cli, "resolve_query_fn", return_value=query), redirect_stdout(io.StringIO()):
                    with patch.object(sys, "argv", argv):
                        cli.main()
                    count = query.call_count
                    with patch.object(sys, "argv", argv + ["--resume"]):
                        cli.main()
                result = json.loads((Path(directory) / "contest_session.json").read_text(encoding="utf-8"))
                self.assertEqual(result["competition_flow"]["phase"], "complete")
                self.assertTrue(result["grade"]["graded"])
                self.assertEqual(count, len(actions))
                self.assertEqual(query.call_count, count)

    def test_deadline_never_hands_in_unsubmitted_drafts(self):
        for competition in ("hmmt_guts", "science_bowl"):
            manifest = fixture(competition)
            engine = _ContestEngine(manifest, lambda *_: "", config_for(manifest))
            engine.session.select_task(engine.competition_flow.current_ids[0])
            if competition == "hmmt_guts":
                engine.session.create_answer("synthetic correct", author="Agent_1")
            engine._collect_deadline()
            self.assertFalse(any(t.submissions for t in engine.session.tasks))
            self.assertTrue(all(t.locked for t in engine.session.tasks))
            self.assertTrue(engine.competition_flow.state["closed"])

    def test_centralized_opening_plan_does_not_expose_unreleased_questions_or_tossup(self):
        for competition in ("hmmt_guts", "science_bowl"):
            manifest = fixture(competition)
            query = Mock(return_value='{}')
            engine = _ContestEngine(manifest, query, config_for(manifest, "centralized"))
            engine._prepare_coach()
            text = json.dumps(query.call_args.args)
            self.assertNotIn(manifest.tasks[-1].task_id, text)
            if competition == "science_bowl":
                self.assertNotIn(manifest.tasks[0].task_id, text)
                self.assertNotIn(manifest.tasks[0].prompt, text)

    def test_native_engine_both_flows_all_baselines_and_mid_action_resume(self):
        for competition in ("hmmt_guts", "science_bowl"):
            manifest = fixture(competition)
            for variant in BASELINE_NAMES:
                with self.subTest(competition=competition, variant=variant):
                    config = config_for(manifest, variant)
                    snapshots = []
                    requests = []
                    def request(req):
                        requests.append(req)
                        offered = {tool["name"] for tool in req.tools}
                        action = next((name for name in ("collect_next_set", "buzz", "answer_tossup", "answer_bonus", "submit_set")
                                       if name in offered), "rest")
                        args = {"answer": "synthetic correct"} if action.startswith("answer_") else {}
                        return LLMResponse("", "mock", "flow-test", tool_calls=(LLMToolCall(action, args),))
                    def callback(session, memory):
                        snapshots.append((copy.deepcopy(session), memory))
                        state = session["competition_flow"]
                        if state["phase"] in {"awaiting_set", "tossup_buzzed"} and not state["closed"]:
                            raise RuntimeError("simulated interruption")
                    engine = _ContestEngine(manifest, lambda *_: "Follow the public phase.", config,
                                            action_request_fn=request, checkpoint_callback=callback)
                    with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                        engine.run()
                    checkpoint, memory = snapshots[-1]
                    resumed = _ContestEngine(manifest, lambda *_: "Follow the public phase.", config,
                                             action_request_fn=request, session_checkpoint=checkpoint,
                                             memory_checkpoint=memory)
                    result = resumed.run()
                    self.assertEqual(result["competition_flow"]["phase"], "complete")
                    self.assertEqual(result["deadline_policy"], "explicit_handins_only")
                    self.assertFalse(result["diagnostics"]["deadline_submission"])
                    self.assertFalse([e for e in result["memory"]["events"] if e["kind"] == "action_error"])
                    grade = grade_contest_result(manifest, result)
                    self.assertTrue(grade["graded"])
                    self.assertEqual(grade["score"], 28 if competition == "science_bowl" else 0)
                    self.assertEqual(grade["max_score"], 28 if competition == "science_bowl" else 30)
                    for task in result["session_checkpoint"]["tasks"]:
                        self.assertEqual(len(task["submissions"]), 1)
                    first = requests[0]
                    self.assertNotIn(manifest.tasks[-1].task_id, first.user_prompt + json.dumps(first.tools))


if __name__ == "__main__":
    unittest.main()
