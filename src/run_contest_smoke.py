"""Deterministic matched-pair smoke runs for contest-session plumbing."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from contest_adapters import grade_contest_result
from contest_manifest import ContestManifest, load_contest_manifest
from contest_runner import ContestRunConfig, run_contest
from run_competition_batch import _write_json_atomic

REPO_ROOT = Path(__file__).resolve().parent.parent


class DeterministicContestAgent:
    """Protocol exerciser that never reads gold or hidden judge data."""

    def __init__(self, manifest: ContestManifest, variant: str) -> None:
        self.manifest = manifest
        self.variant = variant
        self.candidates: dict[str, str] = {}
        self.authors: dict[str, str] = {}
        self.evidence_done: set[str] = set()
        self.revisions: dict[str, int] = {}

    @staticmethod
    def _agent(system: str) -> str:
        match = re.search(r"You are (Agent_\d+)", system)
        return match.group(1) if match else "Agent_1"

    @staticmethod
    def _status(user: str) -> list[dict[str, Any]]:
        match = re.search(r"TASK STATUS (.+?)\nBUDGET", user, re.DOTALL)
        return json.loads(match.group(1)) if match else []

    @staticmethod
    def _active(user: str) -> str | None:
        match = re.search(r"ACTIVE TASK ([^\n]+)", user)
        return match.group(1).strip() if match else None

    @staticmethod
    def _review_history(user: str) -> dict[str, list[dict[str, Any]]]:
        match = re.search(
            r"SHARED ANSWER REVIEW HISTORY\n(.+?)\n\nYOUR ELIGIBLE PENDING REVIEWS",
            user,
            re.DOTALL,
        )
        return json.loads(match.group(1)) if match else {}

    @staticmethod
    def _action(name: str, **arguments: Any) -> str:
        return json.dumps({"action": name, "arguments": arguments})

    def __call__(self, system: str, user: str) -> str:
        agent = self._agent(system)
        status = self._status(user)
        active_id = self._active(user)
        review_history = self._review_history(user)
        task_map = {task.task_id: task for task in self.manifest.tasks}
        if "FINAL REVIEW PHASE:" in user and active_id is not None:
            version = review_history[active_id][-1]
            if version.get("author") == agent:
                return self._action("rest", reason="await independent final review")
            return self._action(
                "review_answer",
                problem_id=active_id,
                version_hash=version["version_hash"],
                decision="approve",
                content="deterministic final review check",
            )
        if self.variant == "strategic" and active_id is None:
            reviewable = next(
                (
                    row
                    for row in status
                    if row.get("has_draft")
                    and not row.get("independent_approval")
                    and row.get("latest_author") != agent
                    and review_history.get(row["task_id"])
                ),
                None,
            )
            if reviewable is not None:
                task_id = reviewable["task_id"]
                version = review_history[task_id][-1]
                return self._action(
                    "review_answer",
                    problem_id=task_id,
                    version_hash=version["version_hash"],
                    decision="approve",
                    content="deterministic smoke protocol check",
                )
        if active_id is None:
            candidate = next(
                (
                    row["task_id"]
                    for row in status
                    if row["state"] not in {"solved", "blocked"}
                ),
                None,
            )
            return (
                self._action("select_problem", problem_id=candidate)
                if candidate
                else self._action("finish_contest", reason="no eligible tasks")
            )

        row = next(item for item in status if item["task_id"] == active_id)
        task = task_map[active_id]
        if row["state"] == "solved":
            candidate = next(
                (
                    item["task_id"]
                    for item in status
                    if item["task_id"] != active_id
                    and item["state"] not in {"solved", "blocked"}
                ),
                None,
            )
            return (
                self._action("select_problem", problem_id=candidate)
                if candidate
                else self._action("finish_contest", reason="all reachable tasks done")
            )
        if row["state"] in {"active", "submitted"}:
            revision = self.revisions.get(active_id, 0) + 1
            self.revisions[active_id] = revision
            candidate = (
                f"# deterministic smoke candidate {active_id} v{revision}\nprint(0)"
                if task.programming
                else f"candidate-{active_id}-v{revision}"
            )
            self.candidates[active_id] = candidate
            self.authors[active_id] = agent
            self.evidence_done.discard(active_id)
            return self._action("work", content=candidate)
        if row["state"] == "candidate":
            candidate = self.candidates[active_id]
            if self.variant == "vanilla":
                action = "submit_code" if task.programming else "submit"
                key = "code" if task.programming else "answer"
                return self._action(action, **{key: candidate})
            if task.programming and active_id not in self.evidence_done:
                self.evidence_done.add(active_id)
                return self._action("execute_code", code=candidate)
            if agent != self.authors.get(active_id):
                versions = review_history.get(active_id)
                if not versions:
                    return self._action(
                        "rest",
                        reason="await shared version history",
                    )
                version = versions[-1]
                return self._action(
                    "review_answer",
                    problem_id=active_id,
                    version_hash=version["version_hash"],
                    decision="approve",
                    content="deterministic smoke protocol check",
                )
            return self._action("speak", content="Please review this exact version.")
        if row["state"] == "review":
            if not task.programming:
                next_task = next(
                    (
                        item["task_id"]
                        for item in status
                        if not item.get("has_draft")
                    ),
                    None,
                )
                if next_task is not None:
                    return self._action("select_problem", problem_id=next_task)
                return self._action("submit")
            candidate = self.candidates[active_id]
            action = "submit_code" if task.programming else "submit"
            key = "code" if task.programming else "answer"
            return self._action(action, **{key: candidate})
        return self._action("rest", reason=f"state={row['state']}")


class MockProgrammingJudge:
    def __init__(self, first_task_id: str) -> None:
        self.first_task_id = first_task_id
        self.attempts: dict[str, int] = {}

    def __call__(
        self,
        task,
        action: str,
        _arguments: dict[str, Any],
    ) -> dict[str, Any]:
        if action == "execute_code":
            return {"valid": True, "result": "local sample evidence"}
        self.attempts[task.task_id] = self.attempts.get(task.task_id, 0) + 1
        attempt = self.attempts[task.task_id]
        verdict = "WA" if task.task_id == self.first_task_id else "AC"
        return {"valid": True, "verdict": verdict}


def run_pair(
    manifest: ContestManifest,
    *,
    max_turns: int,
    max_api_calls: int,
    max_tokens: int,
) -> dict[str, Any]:
    outputs = {}
    # Legacy pair names: vanilla -> decentralized, strategic -> open_table_coach.
    for variant in ("vanilla", "strategic"):
        agent = DeterministicContestAgent(manifest, variant)
        executor = (
            MockProgrammingJudge(manifest.tasks[0].task_id)
            if any(task.programming for task in manifest.tasks)
            else None
        )
        result = run_contest(
            manifest,
            agent,
            ContestRunConfig(
                system_variant=variant,
                team_size=3,
                max_turns=max_turns,
                max_api_calls=max_api_calls,
                max_tokens=max_tokens,
                max_simulated_minutes=300,
                minutes_per_turn=0,
                start_seat=0,
            ),
            coach_query_fn=lambda _system, _user: (
                "Triage tasks by apparent difficulty, follow the shared active-task "
                "cursor, route every draft to a non-author reviewer, and reserve a "
                "final answer-sheet audit."
            ),
            task_action_executor=executor,
        )
        result["grade"] = grade_contest_result(manifest, result)
        result["metrics"]["task_utility"] = result["grade"]["task_utility"]
        outputs[f"{variant}_team"] = result
    return {
        "manifest": manifest.session_id,
        "matched_constraints": {
            "team_size": 3,
            "max_turns": max_turns,
            "max_api_calls": max_api_calls,
            "max_tokens": max_tokens,
            "start_seat": 0,
            # Baselines differ only by optional bundles (desk / private
            # channel); the core contest actions must be identical.
            "action_sets_equal": (
                set(outputs["vanilla_team"]["action_names"])
                == set(outputs["strategic_team"]["action_names"])
                - {"inspect_problem", "triage_problem", "direct_message"}
            ),
        },
        "results": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "contest_matched_smoke",
    )
    args = parser.parse_args()
    root = REPO_ROOT / "data" / "benchmarks"
    manifests = {
        "arml": load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "arml_local_2009.json",
            benchmark_root=root,
        ),
        "icpc": load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "icpc_wf_2012_5.json",
            benchmark_root=root,
        ),
    }
    payload = {
        "protocol": "deterministic_mock_matched_pair_v1",
        "gold_visible_to_agent": False,
        "pairs": {
            "arml": run_pair(
                manifests["arml"],
                max_turns=12,
                max_api_calls=36,
                max_tokens=12000,
            ),
            "icpc": run_pair(
                manifests["icpc"],
                max_turns=18,
                max_api_calls=54,
                max_tokens=18000,
            ),
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(args.output / "matched_pair.json", payload)
    print(f"Saved: {args.output / 'matched_pair.json'}")


if __name__ == "__main__":
    main()
