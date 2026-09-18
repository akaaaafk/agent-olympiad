"""NYU CTF flags are checked on submit; Cybench keeps a single final answer."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contest_adapters import grade_contest_result
from contest_config import ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import run_contest
from llm import LLMResponse, LLMToolCall

FLAG = "flag{real}"


def manifest(competition):
    row = {"problem_id": "ctf_1", "gold_label": {"expected_answer": FLAG},
           "evaluation": {"status": "ready_with_limitations", "evaluator_id": "gold_answer_v1"}}
    task = ManifestTask("ctf_1", "ctf_1", None, "Recover the flag.", "ctf", 1, False, row)
    return ContestManifest("ctf-session", competition, (task,))


def run(competition, answers):
    pending = list(answers)

    def agent(request):
        names = {tool["name"] for tool in request.tools}
        if "select_problem" in names and not agent.selected:
            agent.selected = True
            return LLMResponse("", "mock", "ctf", tool_calls=(LLMToolCall("select_problem", {"problem_id": "ctf_1"}),))
        if pending and "submit" in names:
            return LLMResponse("", "mock", "ctf", tool_calls=(LLMToolCall("submit", {"answer": pending.pop(0)}),))
        return LLMResponse("", "mock", "ctf", tool_calls=(LLMToolCall("rest", {}),))

    agent.selected = False
    config = ContestRunConfig("single_agent", 1, 8, minutes_per_turn=0)
    return run_contest(manifest(competition), lambda *_: "x", config, action_request_fn=agent,
                       action_transport="native", coach_query_fn=lambda *_: "x",
                       task_action_executor=Mock())


def checks(result):
    return [e["payload"] for e in result["memory"]["events"] if e["kind"] == "flag_check_result"]


class FlagCheckTests(unittest.TestCase):
    def test_nyu_wrong_flag_is_reported_and_challenge_stays_open(self):
        result = run("nyu_ctf_bench", ["flag{guess}", FLAG])
        self.assertEqual(checks(result), [{"correct": False, "attempts": 1},
                                          {"correct": True, "attempts": 2}])
        self.assertEqual(result["submissions"]["ctf_1"], FLAG)
        self.assertEqual(grade_contest_result(manifest("nyu_ctf_bench"), result)["score"], 1.0)

    def test_nyu_only_wrong_flags_score_zero(self):
        result = run("nyu_ctf_bench", ["flag{a}", "flag{b}"])
        self.assertEqual([c["correct"] for c in checks(result)], [False, False])
        self.assertEqual(grade_contest_result(manifest("nyu_ctf_bench"), result)["score"], 0.0)

    def test_cybench_first_answer_is_final_without_feedback(self):
        result = run("cybench", ["flag{guess}", FLAG])
        self.assertEqual(checks(result), [])
        self.assertEqual(result["submissions"]["ctf_1"], "flag{guess}")
        self.assertEqual(grade_contest_result(manifest("cybench"), result)["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
