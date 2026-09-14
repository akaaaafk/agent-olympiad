"""Offline real-data pipeline smoke for two opt-in competition flows.

No model calls or gold-driven policy. Guts uses a fixed non-answer draft;
Science Bowl passes explicitly. Correct-answer branches are tested with
synthetic fixtures in test_competition_flow.py, not reported as model scores.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_manifest import load_contest_manifest
from contest_runner import run_contest
from contest_adapters import grade_contest_result
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card


class PilotDriver:
    def __init__(self):
        self.calls = Counter()

    def __call__(self, request):
        offered = {tool["name"]: tool for tool in request.tools}
        text = request.user_prompt
        flow = json.loads(re.search(r"COMPETITION FLOW \(enforced for every baseline\): (.+)\n", text)[1])
        rows = json.loads(re.search(r"TASK STATUS (.+)\nBUDGET", text)[1])
        current = set(flow["current_task_ids"])
        blank = next((row for row in rows if row["task_id"] in current and not row["has_draft"]), None)
        action, args = "rest", {}
        if "collect_next_set" in offered:
            action = "collect_next_set"
        elif "buzz" in offered:
            action = "buzz"
        elif "answer_tossup" in offered or "answer_bonus" in offered:
            action = "answer_tossup" if "answer_tossup" in offered else "answer_bonus"
            args = {"answer": ""}  # Explicit pass; never reads benchmark gold.
        elif blank and "work" in offered:
            tid = blank["task_id"]
            action, args = "work", {"problem_id": tid,
                                     "content": f"Problem {tid}:\nFinal answer: OFFLINE_SMOKE_CANDIDATE"}
        elif not blank and "submit_set" in offered:
            action = "submit_set"
        elif "review_answer" in offered:
            match = re.search(r"YOUR ELIGIBLE PENDING REVIEWS\n(.+?)\n\n", text, re.DOTALL)
            reviews = json.loads(match[1]) if match else []
            target = next((row for row in reviews if row["problem_id"] in current), None)
            if target:
                action = "review_answer"
                args = {"problem_id": target["problem_id"], "version_hash": target["version_hash"],
                        "decision": "approve", "content": "Offline test receipt approval; not mathematical correctness."}
        self.calls[action] += 1
        return LLMResponse("", "mock", "competition-flow-smoke",
                           tool_calls=(LLMToolCall(action, args),))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    for name in ("hmmt_guts_2024_first_two_sets", "science_bowl_2020_round10_pair18"):
        path = ROOT / "configs/contest_flows" / (name + ".json")
        manifest = load_contest_manifest(path, benchmark_root=ROOT / "data/benchmarks")
        for variant in BASELINE_NAMES:
            card = load_rule_card(manifest.competition_id)
            size = 1 if variant == "single_agent" else (8 if manifest.competition_id == "hmmt_guts" else 4)
            config = ContestRunConfig(variant, size, 24, max_api_calls=480, max_tokens=120000,
                                      rule_card=card if variant in {"otc", "vallina_otc"} else None)
            driver = PilotDriver()
            result = run_contest(manifest, lambda *_: "Follow the exposed competition phase.", config,
                                 action_request_fn=driver)
            result["grade"] = grade_contest_result(manifest, result)
            errors = [e for e in result["memory"]["events"] if e["kind"] == "action_error"]
            passed = (result["competition_flow"]["phase"] == "complete" and not errors
                      and result["grade"]["graded"] and result["deadline_policy"] == "explicit_handins_only")
            record = dict(competition=manifest.competition_id, setting=variant,
                          status="PASS" if passed else "FAIL", calls=dict(driver.calls),
                          submitted=sum(bool(t["submissions"]) for t in result["session_checkpoint"]["tasks"]),
                          tasks=len(manifest.tasks), errors=errors, result=result)
            (output / f"{manifest.competition_id}_{variant}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            cases.append({k: v for k, v in record.items() if k != "result"})
            print(manifest.competition_id, variant, record["status"], flush=True)
    summary = dict(kind="offline_stateful_pilot_smoke_v1", live_llm=False, live_external_tools=False,
                   policy_reads_gold=False, scoring="existing deterministic evaluator",
                   counts=dict(Counter(case["status"] for case in cases)), cases=cases)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(case["status"] == "PASS" for case in cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
