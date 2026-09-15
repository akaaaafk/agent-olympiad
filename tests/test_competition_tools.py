"""Exercise the actual preparation implementations and both runtime gates."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from action_modules.competition_tools import ACTION_NAMES, BY_COMPETITION, PROFILES
from action_wire import normalize_invocation, render_text_signature
from competition_tool_runtime import execute_preparation_tool, public_context
from contest_actions import _apply_action
from contest_adapters import EnvironmentTaskExecutor
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_policy import _actions_for_agent, _resolved_actions
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from env import OlympiadEnvironment
from rules.loader import DEFAULT_RULES_ROOT, load_rule_card
from rules.storage import iter_rule_card_ids
from tool_registry import ACTION_REGISTRY, render_function_tools, resolve_action_names, resolve_actions_with_diagnostics, validate_action_payload


def sample_arguments(profile):
    """Small, meaningful contestant examples, not a mock preparation backend."""
    by_kind = {
        "answers": dict(problem_ids=["q1"], answers=["2/3"]),
        "integers": dict(problem_ids=["q1"], answers=["17"]),
        "seasonal_answers": dict(problem_ids=["q1"], answers=["17"], justifications=["By the given recurrence."]),
        "guts": dict(problem_ids=["q1", "q2", "q3"], answers=["1", "2", "3"]),
        "event_answers": dict(problem_ids=["q1"], answers=["Mars"]),
        "proofs": dict(part_ids=["a", "b"], claims=["Base case", "Inductive step"], proofs=["Direct substitution.", "Apply part a."], dependencies=["", "a"]),
        "quantities": dict(quantities=["speed"], values=["2.5"], units=["m/s"], required_units=["m/s"]),
        "measurements": dict(quantities=["length"], values=["12.5"], units=["cm"], uncertainties=["0.1"], sources=["provided table 1"]),
        "io_cases": dict(case_ids=["empty", "single"], inputs=["0\n", "1\n5\n"], expected_outputs=["0\n", "5\n"]),
        "linguistics": dict(rule_ids=["plural"], rules=["suffix -ka marks plural"], example_refs=["examples 2, 3"], counterexamples=[""]),
        "observations": dict(objects=["object A"], observations=["RA 12h"], frames_or_units=["equatorial J2000"], sources=["provided star chart"]),
        "short_answer": dict(answer="Marie Curie"),
        "science_answer": dict(answer_type="multiple_choice", answer="W", option_text="electron"),
        "flag": dict(flag="flag{Case_Sensitive}", recovery_evidence="Contestant reports a response from the authorized target."),
        "speeches": dict(roles=["PM", "LO", "DPM", "DLO", "MG", "MO", "GW", "OW"], speeches=["Supplied speech " + str(i) for i in range(8)]),
        "authorities": dict(sides=["applicant" if profile.competition == "jessup" else "claimant"], issues=["jurisdiction"], propositions=["Consent was given"], authorities=["supplied authority paragraph 5"], fact_refs=["problem paragraph 8"]),
        "portfolio": dict(symbols=["AAA", "CASH"], weights_percent=[60, 40], rationales=["thesis", "liquidity"], client_objectives="Preserve liquidity"),
        "extraction": dict(feeder_ids=["one", "two"], answers=["CAT", "DOG"], indices=[2, 2]),
        "robot": dict(steps=["move", "stop"], expected_observations=["line found", "marker reached"], durations_seconds=[20, 30], run_limit_seconds=120),
        "ai_artifacts": dict(artifact_names=["result.png"], media_types=["image/png"], provenance=["contestant-generated from provided asset"]),
        "constraints": dict(constraints=["self-supporting"], solution_elements=["triangular frame"], evidence=["proposed load trial"]),
        "writing": dict(authors=["Agent_1", "Agent_2", "Agent_3"], prompt_ids=["p1", "p2", "p3"], responses=["Essay one", "Essay two", "Essay three"]),
    }
    return ({field: f"Contestant-supplied {field}." for field in profile.fields}
            if profile.kind == "sections" else copy.deepcopy(by_kind[profile.kind]))


def context(competition):
    return public_context(competition, "q1", expected_ids=["q1", "q2", "q3"],
                          task_metadata=dict(season="nov", division="B", event="Solar System", year=2024,
                                             gold={"answer": "SECRET_GOLD"}, judge_token="PRIVATE"))


def manifest_for(competition):
    ctx = context(competition)
    row = {"problem_id": "q1", "task_type": "general", "problem_description": "Public task.",
           **ctx["selectors"], "gold": {"answer": "SECRET_GOLD"}}
    task = ManifestTask("q1", "q1", None, "Public task.", "general", 1, False, row)
    return ContestManifest("preparation-test", competition, (task,))


class CompetitionToolTests(unittest.TestCase):
    def run_tool(self, competition, **changes):
        profile = BY_COMPETITION[competition]
        args = sample_arguments(profile)
        args.update(changes)
        return execute_preparation_tool(profile.name, args, context(competition))

    def test_every_card_has_one_real_scoped_tool(self):
        self.assertEqual(set(BY_COMPETITION), set(iter_rule_card_ids(DEFAULT_RULES_ROOT)))
        self.assertEqual(len(PROFILES), 43)
        for profile in PROFILES:
            with self.subTest(competition=profile.competition):
                for runtime in ("env", "session"):
                    self.assertEqual(resolve_action_names(profile.competition, runtime=runtime) & ACTION_NAMES, {profile.name})
                self.assertIn(profile.name, load_rule_card(profile.competition).allowed_tools)
                self.assertEqual(validate_action_payload(profile.name, sample_arguments(profile)), ())
                result = self.run_tool(profile.competition)
                self.assertTrue(result["format_ok"], result)
                self.assertFalse(result["correctness_checked"])
                self.assertFalse(result["submitted"])
                self.assertNotIn("SECRET_GOLD", json.dumps(result))
                self.assertEqual(render_function_tools([profile.name])[0]["name"], profile.name)

    def test_public_context_allowlists_only_selectors(self):
        value = context("ioai_team")
        self.assertNotIn("SECRET_GOLD", json.dumps(value))
        self.assertNotIn("PRIVATE", json.dumps(value))
        self.assertEqual(value["selectors"]["year"], "2024")

    def test_integer_and_unknown_problem_rejections(self):
        for answer in ("-1", "1.5", "2+3", "", "NaN"):
            self.assertFalse(self.run_tool("purple_comet", answers=[answer])["format_ok"], answer)
        self.assertFalse(self.run_tool("arml_local", problem_ids=["invented"])["format_ok"])
        self.assertFalse(self.run_tool("arml_local", problem_ids=["q1", "q1"], answers=["1", "2"])["format_ok"])

    def test_proof_cycles_missing_dependencies_and_forward_refs(self):
        for deps in (["b", "a"], ["missing", "a"], ["a", "a"]):
            self.assertFalse(self.run_tool("pumac_power", dependencies=deps)["format_ok"])
        good = self.run_tool("pumac_power")
        self.assertEqual(good["data"]["dependency_graph"], {"a": [], "b": ["a"]})

    def test_season_must_come_from_task_and_changes_set_size(self):
        profile = BY_COMPETITION["hmmt_guts"]
        args = sample_arguments(profile)
        missing = public_context("hmmt_guts", "q1")
        self.assertFalse(execute_preparation_tool(profile.name, args, missing)["format_ok"])
        feb = public_context("hmmt_guts", "q1", task_metadata={"season": "feb"})
        self.assertFalse(execute_preparation_tool(profile.name, args, feb)["format_ok"])
        args["problem_ids"].append("q4")
        args["answers"].append("4")
        self.assertTrue(execute_preparation_tool(profile.name, args, feb)["format_ok"])

    def test_measurements_preserve_values_and_reject_bad_uncertainty(self):
        result = self.run_tool("ijso_practical")
        self.assertEqual(result["data"]["rows"][0]["values"], "12.5")
        for values in (["NaN"], ["Infinity"], ["not measured"]):
            self.assertFalse(self.run_tool("ijso_practical", values=values)["format_ok"])
        self.assertFalse(self.run_tool("eoes", uncertainties=["-0.1"])["format_ok"])
        self.assertFalse(self.run_tool("fyziklani", units=["km/s"])["format_ok"])

    def test_testcase_conflicts_are_not_judge_results(self):
        result = self.run_tool("icpc", inputs=["same", "same"])
        self.assertFalse(result["format_ok"])
        self.assertNotIn("verdict", result)
        self.assertNotIn("sample_verdict", result)

    def test_domain_specific_checks(self):
        self.assertEqual(self.run_tool("mystery_hunt")["data"]["extraction"], "AO")
        self.assertFalse(self.run_tool("mystery_hunt", indices=[0, 999])["format_ok"])
        self.assertFalse(self.run_tool("wharton_investment", weights_percent=[60, 50])["format_ok"])
        self.assertEqual(self.run_tool("wharton_investment")["data"]["total_percent"], "100")
        self.assertFalse(self.run_tool("wro", durations_seconds=[120, 30])["format_ok"])
        self.assertFalse(self.run_tool("wsc_writing", authors=["Agent_1"] * 3)["format_ok"])
        self.assertFalse(self.run_tool("wsc_writing", prompt_ids=["p1"] * 3)["format_ok"])
        self.assertFalse(self.run_tool("debatebench", roles=["PM"] * 8)["format_ok"])
        self.assertFalse(self.run_tool("jessup", sides=["claimant"])["format_ok"])
        self.assertEqual(self.run_tool("cybench")["candidate_text"], "flag{Case_Sensitive}")

    def test_bad_shapes_and_nonfinite_numbers_do_not_crash_or_succeed(self):
        self.assertFalse(self.run_tool("iol_team", rules=["a", "b"])["format_ok"])
        self.assertFalse(self.run_tool("wharton_investment", weights_percent=[float("nan"), 1])["format_ok"])
        with self.assertRaises(ValueError):
            self.run_tool("purple_comet", answers=123)
        self.assertFalse(self.run_tool("mystery_hunt", indices=[True, 2])["format_ok"])

    def test_wrong_competition_and_forged_capability_cannot_grant_tool(self):
        profile = BY_COMPETITION["purple_comet"]
        with self.assertRaisesRegex(ValueError, "different competition"):
            execute_preparation_tool(profile.name, sample_arguments(profile), context("icpc"))
        names = resolve_actions_with_diagnostics("icpc", declared_capabilities={profile.name}, permitted_actions={profile.name}).names
        self.assertNotIn(profile.name, names)
        card = replace(load_rule_card("icpc"), allowed_tools=(profile.name,))
        env = OlympiadEnvironment("icpc", "q1", problem_data=manifest_for("icpc").tasks[0].benchmark,
                                  rule_card=card, rules_mode="off")
        self.assertNotIn(profile.name, env.get_available_tools())

    def test_actual_environment_and_adapter_execute_typed_arrays(self):
        for profile in PROFILES:
            with self.subTest(competition=profile.competition):
                manifest = manifest_for(profile.competition)
                env = OlympiadEnvironment(profile.competition, "q1", problem_data=manifest.tasks[0].benchmark, rules_mode="off")
                raw = env.execute_action("Agent_1", profile.name, sample_arguments(profile))
                result = json.loads(raw)
                self.assertTrue(result["valid"])
                self.assertFalse(env.submitted)
                self.assertEqual(env.workspace["final_answer"], "")
                encoded = json.dumps(sample_arguments(profile), ensure_ascii=False)
                invocation = normalize_invocation(profile.name, encoded)
                self.assertTrue(invocation.ok, invocation.errors)
                self.assertEqual(invocation.arguments, sample_arguments(profile))
                self.assertIn("JSON object", render_text_signature(ACTION_REGISTRY[profile.name]))
                text_result = json.loads(env.execute_action("Agent_1", profile.name, encoded))
                self.assertEqual(text_result, result)
                adapter = EnvironmentTaskExecutor(manifest, benchmark_root="unused")
                result = adapter(manifest.tasks[0], profile.name, sample_arguments(profile))
                self.assertTrue(result["valid"])

    def test_all_five_baselines_dispatch_privately_without_answer_mutation(self):
        for profile in PROFILES:
            manifest = manifest_for(profile.competition)
            for baseline in BASELINE_NAMES:
                with self.subTest(competition=profile.competition, baseline=baseline):
                    card = load_rule_card(profile.competition)
                    config = ContestRunConfig(baseline, 1 if baseline == "single_agent" else card.team_size_default, 20,
                                              rule_card=card if baseline in {"otc", "vallina_otc"} else None)
                    self.assertIn(profile.name, {s.name for s in _resolved_actions(manifest, config)})
                    session = ContestSession([TaskUnit("q1", kind="non_programming")], budget=ContestBudgetState(max_turns=20))
                    session.select_task("q1")
                    memory = ContestMemory(run_id="r", session_id="s", competition_id=profile.competition)
                    offered = _actions_for_agent(_resolved_actions(manifest, config), session, config, "Agent_1", memory=memory)
                    self.assertIn(profile.name, {spec.name for spec in offered})
                    external = Mock(side_effect=AssertionError("Preparation must not call external tools or judges"))
                    _apply_action(action=profile.name, arguments=sample_arguments(profile), agent="Agent_1", manifest=manifest,
                                  session=session, memory=memory, config=config, strategic_policy=None, task_action_executor=external)
                    external.assert_not_called()
                    self.assertEqual(session.active_task.versions, [])
                    self.assertEqual(session.active_task.submissions, [])
                    self.assertEqual(len(memory.view("Agent_2")), 0)
                    result = memory.view("Agent_1")[-1].payload
                    self.assertEqual(result["tool"], profile.name)
                    self.assertFalse(result["submitted"])
                    restored = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
                    self.assertEqual(restored.view("Agent_1")[-1].payload, result)

    def test_direct_dispatch_respects_allowlist_lock_and_assignment(self):
        competition = "purple_comet"
        profile = BY_COMPETITION[competition]
        manifest = manifest_for(competition)
        session = ContestSession([TaskUnit("q1", kind="non_programming")], budget=ContestBudgetState(max_turns=20))
        session.select_task("q1")
        store = ContestMemory(run_id="r", session_id="s", competition_id=competition)
        kwargs = dict(action=profile.name, arguments=sample_arguments(profile), agent="Agent_1", manifest=manifest,
                      session=session, memory=store, strategic_policy=None, task_action_executor=Mock())
        empty = replace(load_rule_card(competition), allowed_tools=())
        with self.assertRaisesRegex(ValueError, "not permitted"):
            _apply_action(**kwargs, config=ContestRunConfig("otc", empty.team_size_default, 20, rule_card=empty))
        config = ContestRunConfig("decentralized", 2, 20)
        with self.assertRaisesRegex(ValueError, "assignment"):
            _apply_action(**kwargs, config=config, work_task_ids={"q2"})
        session.active_task.locked = True
        offered = _actions_for_agent(_resolved_actions(manifest, config), session, config, "Agent_1", memory=store)
        self.assertNotIn(profile.name, {spec.name for spec in offered})
        with self.assertRaisesRegex(ValueError, "unlocked"):
            _apply_action(**kwargs, config=config)


if __name__ == "__main__":
    unittest.main()
