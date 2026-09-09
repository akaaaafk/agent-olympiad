"""Matched-budget vanilla and strategic runners for multi-task contests."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from actions import parse_typed_action, validate_action_invocation
from contest_budget import estimate_tokens
from contest_manifest import ContestManifest, ManifestTask, TaskFamily
from contest_memory import ContestMemory
from contest_session import (
    BudgetExceededError,
    ContestBudgetState,
    ContestSession,
    TaskState,
    TaskUnit,
)
from llm import LLMRequest, RequestFn
from programming_workflow import ProgrammingProgress
from programming_candidates import deadline_candidate, execution_key, failed_execution, source_identity
from submission_policy import SubmissionPolicy
from strategy import StrategicPolicy
from tool_registry import (
    ACTION_REGISTRY,
    ACTION_SET_VERSION,
    DESK_ACTION_NAMES,
    DESK_READONLY_ACTION_NAMES,
    LEADER_ACTION_NAMES,
    MEMORY_ACTION_NAMES,
    ActionSpec,
    render_action_instructions,
    render_function_tools,
    resolve_actions,
)

PROTOCOL_VERSION = "contest_session_v4"

QueryFn = Callable[[str, str], str]
TaskActionExecutor = Callable[[ManifestTask, str, dict[str, Any]], dict[str, Any]]
CheckpointCallback = Callable[[dict[str, Any], str], None]


def _is_answer_sheet_contest(manifest: ContestManifest) -> bool:
    return len(manifest.tasks) > 1 and all(
        not task.programming for task in manifest.tasks
    ) and (
        manifest.competition_id.startswith("arml")
        or all(task.task_type == "team_contest" for task in manifest.tasks)
    )


def _required_answer_sheet_task_ids(manifest: ContestManifest) -> set[str]:
    scored = {task.task_id for task in manifest.tasks if task.max_score > 0}
    return scored or {task.task_id for task in manifest.tasks}


CoachMode = Literal["none", "precontest", "leader"]

# The centralized baseline's coordinator seat. It is an ordinary contestant
# with two extra powers: it writes the opening plan and it alone submits.
LEADER_AGENT = "Agent_1"


@dataclass(frozen=True)
class BaselineFeatures:
    """Orthogonal switches that together define one contest baseline.

    Every behavioural difference between baselines lives here; the engine
    never branches on the baseline's name.
    """

    coach: CoachMode
    review_workflow: bool
    memory_actions: bool
    desk_actions: bool
    private_channel: bool
    structured_context: bool
    submission_cooldown: bool
    mechanical_switch: bool
    leader_submits: bool


_NO_COACH = BaselineFeatures(
    coach="none",
    review_workflow=False,
    memory_actions=False,
    desk_actions=False,
    private_channel=False,
    structured_context=False,
    submission_cooldown=False,
    mechanical_switch=True,
    leader_submits=False,
)
_OPEN_TABLE_COACH = BaselineFeatures(
    coach="precontest",
    review_workflow=True,
    memory_actions=False,
    desk_actions=True,
    private_channel=True,
    structured_context=True,
    submission_cooldown=True,
    mechanical_switch=False,
    leader_submits=False,
)
BASELINES: dict[str, BaselineFeatures] = {
    # Same environment as decentralized; team_size is pinned to 1.
    "single_agent": _NO_COACH,
    "decentralized": _NO_COACH,
    "centralized": BaselineFeatures(
        coach="leader",
        review_workflow=False,
        memory_actions=False,
        desk_actions=True,
        private_channel=True,
        structured_context=True,
        submission_cooldown=True,
        mechanical_switch=False,
        leader_submits=True,
    ),
    "open_table_coach": _OPEN_TABLE_COACH,
    "open_table_coach_memory": replace(_OPEN_TABLE_COACH, memory_actions=True),
}
# Pre-v5 names. ``strategic`` predates memory actions, so it maps to the
# memory-less coach baseline.
BASELINE_ALIASES: dict[str, str] = {
    "vanilla": "decentralized",
    "vanilla_team": "decentralized",
    "strategic": "open_table_coach",
    "strategic_team": "open_table_coach",
}
BASELINE_NAMES: tuple[str, ...] = tuple(BASELINES)


def canonical_baseline(name: str) -> str:
    canonical = BASELINE_ALIASES.get(name, name)
    if canonical not in BASELINES:
        raise ValueError(
            f"unknown system_variant {name!r}; expected one of "
            f"{', '.join(BASELINE_NAMES)} or an alias "
            f"{', '.join(BASELINE_ALIASES)}"
        )
    return canonical


@dataclass(frozen=True)
class ContestRunConfig:
    system_variant: str
    team_size: int
    max_turns: int
    max_api_calls: int | None = None
    max_tokens: int | None = None
    max_simulated_minutes: float | None = None
    minutes_per_turn: float = 5.0
    consecutive_non_ac_limit: int = 3
    cooldown_turns: int = 2
    stall_turns: int = 3
    require_review: bool | None = None
    require_final_review: bool | None = None
    start_seat: int = 0
    rule_guidance: str = ""
    programming_deadline_submit: bool = False
    # Filled from ``BASELINES[system_variant]`` unless given explicitly
    # (ablations may override single switches).
    features: BaselineFeatures | None = None

    def __post_init__(self) -> None:
        if self.team_size < 1 or self.max_turns < 1:
            raise ValueError("team_size and max_turns must be positive")
        canonical = canonical_baseline(self.system_variant)
        object.__setattr__(self, "system_variant", canonical)
        if self.features is None:
            object.__setattr__(self, "features", BASELINES[canonical])
        if canonical == "single_agent" and self.team_size != 1:
            raise ValueError("single_agent requires team_size=1")
        if self.features.coach == "leader" and self.team_size < 2:
            raise ValueError("a leader baseline needs at least one worker seat")
        if self.minutes_per_turn < 0 or self.stall_turns < 1:
            raise ValueError("invalid scheduling limits")

    @property
    def review_required(self) -> bool:
        return (
            self.features.review_workflow
            if self.require_review is None
            else self.require_review
        )

    @property
    def final_review_required(self) -> bool:
        return (
            self.features.review_workflow
            if self.require_final_review is None
            else self.require_final_review
        )

    @property
    def leader(self) -> str | None:
        return LEADER_AGENT if self.features.coach == "leader" else None


def _resolved_actions(
    manifest: ContestManifest,
    config: ContestRunConfig | None = None,
) -> frozenset[ActionSpec]:
    """Baseline-level action surface; per-turn gating lives in _actions_for_agent."""
    specs: set[ActionSpec] = set()
    handlers = set(ACTION_REGISTRY)
    for task in manifest.tasks:
        benchmark = task.benchmark
        declared = set(benchmark.get("available_capabilities") or ())
        assets = benchmark.get("assets") or []
        if any("lab" in str(asset).lower() for asset in assets):
            declared.add("read_lab_equipment")
        if any("star" in str(asset).lower() for asset in assets):
            declared.add("read_star_chart")
        requirements = dict(benchmark.get("tool_requirements") or {})
        specs.update(
            resolve_actions(
                competition=manifest.competition_id,
                task_type=task.task_type,
                benchmark_requirements=requirements,
                declared_capabilities=declared,
                registered_handlers=handlers,
            )
        )
    # ``inspect_problem`` covers self-verification for every family; the
    # programming-only ``verify`` remains registered for the legacy stack.
    specs.discard(ACTION_REGISTRY["verify"])
    if _is_answer_sheet_contest(manifest):
        submit = ACTION_REGISTRY["submit"]
        specs.discard(submit)
        specs.discard(ACTION_REGISTRY["request_review"])
        specs.add(
            replace(
                submit,
                description=(
                    "Submit the complete current answer sheet once and end the contest."
                ),
                arguments=(),
            )
        )
    if config is not None:
        specs = _trim_to_baseline(specs, config)
    return frozenset(specs)


def _trim_to_baseline(
    specs: set[ActionSpec],
    config: ContestRunConfig,
) -> set[ActionSpec]:
    """Drop the optional action bundles a baseline does not include."""
    features = config.features
    hidden: set[str] = set()
    if not features.memory_actions:
        hidden |= MEMORY_ACTION_NAMES
    if not features.desk_actions:
        hidden |= DESK_READONLY_ACTION_NAMES
    if not features.private_channel or config.team_size < 2:
        hidden.add("direct_message")
    if not features.leader_submits:
        hidden |= LEADER_ACTION_NAMES
    return {spec for spec in specs if spec.name not in hidden}


def _default_executor(
    _task: ManifestTask,
    action: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    if action == "use_calculator":
        from env import OlympiadEnvironment

        return {
            "result": f"Calculator output: {OlympiadEnvironment._safe_calculate(arguments['expression'])}",
            "valid": True,
        }
    if action == "submit_code":
        return {
            "verdict": "SUBMIT_FAILED",
            "valid": False,
            "error": "No programming judge adapter configured.",
        }
    return {
        "result": f"{action} requires a task action adapter.",
        "valid": False,
    }


def _task_rows(session: ContestSession) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.task_id,
            "state": task.state.value,
            "attempts": len(task.submissions),
            "locked": task.locked,
            "has_draft": bool(task.versions),
            "versions": len(task.versions),
            "latest_author": task.versions[-1].author if task.versions else None,
            "independent_approval": _task_has_independent_approval(task),
            "valid_submission": task.latest_valid_submission is not None,
            "priority": task.priority,
            "hopeless": task.hopeless,
            "triaged_by": task.triaged_by,
        }
        for task in session.tasks
    ]


def _needs_programming_source(task: TaskUnit) -> bool:
    """True for initial implementation and local/official failure repair."""
    if task.kind != "programming" or task.locked:
        return False
    if not task.versions:
        return True
    latest = task.versions[-1]
    return not latest.evidence_refs or any(
        submission.valid and submission.version_hash == latest.version_hash
        for submission in task.submissions
    )


def _actions_for_agent(
    actions: frozenset[ActionSpec],
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    *,
    answer_sheet_contest: bool = False,
    review_targets: list[dict[str, str]] | None = None,
    reported_version_hashes: set[str] | None = None,
    work_task_ids: set[str] | None = None,
    review_task_ids: set[str] | None = None,
    answer_sheet_submit_ready: bool = False,
    required_answer_task_ids: set[str] | None = None,
    programming_source_required: bool = False,
) -> frozenset[ActionSpec]:
    """Per-turn, per-agent gating on top of the baseline action surface."""
    available = _trim_to_baseline(set(actions), config)
    teammates = tuple(
        f"Agent_{index}"
        for index in range(1, config.team_size + 1)
        if f"Agent_{index}" != agent
    )
    direct_message = next(
        (spec for spec in available if spec.name == "direct_message"),
        None,
    )
    if direct_message is not None:
        by_name = {argument.name: argument for argument in direct_message.arguments}
        available.discard(direct_message)
        available.add(
            replace(
                direct_message,
                arguments=(
                    replace(by_name["recipients"], enum=teammates),
                    by_name["content"],
                ),
            )
        )
    # Desk actions that take a problem id get the concrete task list so the
    # model cannot invent identifiers.
    task_ids = tuple(task.task_id for task in session.tasks)
    for name in ("inspect_problem", "triage_problem", "remember", "recall"):
        spec = next((spec for spec in available if spec.name == name), None)
        if spec is None:
            continue
        available.discard(spec)
        available.add(
            replace(
                spec,
                arguments=tuple(
                    replace(argument, enum=task_ids)
                    if argument.name == "problem_id"
                    else argument
                    for argument in spec.arguments
                ),
            )
        )
    leader = config.leader
    if leader is not None:
        assign_spec = next(
            (spec for spec in available if spec.name == "assign_problem"), None
        )
        if assign_spec is not None:
            available.discard(assign_spec)
            if agent == leader and teammates:
                by_name = {arg.name: arg for arg in assign_spec.arguments}
                available.add(
                    replace(
                        assign_spec,
                        arguments=(
                            replace(by_name["agent"], enum=teammates),
                            replace(by_name["problem_ids"], enum=task_ids),
                            by_name["reason"],
                        ),
                    )
                )
        if config.features.leader_submits and agent != leader:
            # Workers draft and report; only the leader hands anything in.
            for name in ("submit", "submit_code", "finish_contest"):
                available = {spec for spec in available if spec.name != name}
    if not config.review_required:
        # Without the review workflow, keeping review actions visible created
        # an accidental rewrite/review loop on one task.
        available.discard(ACTION_REGISTRY["request_review"])
        available.discard(ACTION_REGISTRY["review_answer"])
    if not _contest_complete(session):
        # The handler rejects finish_contest until every task holds a valid
        # submission, so exposing it earlier only burns a turn (both variants).
        available.discard(ACTION_REGISTRY["finish_contest"])
    if answer_sheet_contest:
        available = {
            spec for spec in available if spec.name != "finish_contest"
        }
        missing_drafts = any(
            not task.versions
            for task in session.tasks
            if required_answer_task_ids is None or task.task_id in required_answer_task_ids
        )
        if missing_drafts or (
            config.final_review_required and not answer_sheet_submit_ready
        ):
            available = {
                spec for spec in available if spec.name != "submit"
            }
        elif any(spec.name == "submit" for spec in available):
            # Sheet complete: the submitter's only remaining move is to hand it
            # in. Workers under a leader keep their ordinary desk instead.
            return frozenset(
                spec for spec in available if spec.name == "submit"
            )
    if work_task_ids is not None:
        active = session.active_task
        select_spec = ACTION_REGISTRY["select_problem"]
        available.discard(select_spec)
        # The scheduler already points the shared cursor at the agent's task, so
        # re-selecting the active problem would only burn a turn.
        selectable = tuple(
            task.task_id
            for task in session.tasks
            if task.task_id in work_task_ids
            and not task.locked
            and (active is None or task.task_id != active.task_id)
        )
        if selectable:
            problem_argument = select_spec.arguments[0]
            available.add(
                replace(
                    select_spec,
                    description=(
                        "Switch to a different problem allowed by your coach "
                        "assignment. The active task is already selected."
                    ),
                    arguments=(replace(problem_argument, enum=selectable),),
                )
            )
        if active is None or active.task_id not in work_task_ids:
            unavailable = {
                "work",
                "request_review",
                "skip_problem",
                "submit_code",
            }
            available = {
                spec
                for spec in available
                if spec.name not in unavailable and spec.pack == "common"
            }
        elif _task_has_independent_approval(active):
            available.discard(ACTION_REGISTRY["work"])
    actions = frozenset(available)

    if config.review_required and (
        answer_sheet_contest
        or any(task.kind == "programming" for task in session.tasks)
    ):
        available = set(actions)
        review_spec = next(
            (spec for spec in available if spec.name == "review_answer"),
            None,
        )
        if review_spec is not None:
            available.discard(review_spec)
            targets = (
                review_targets
                if review_targets is not None
                else _pending_review_queue(
                    session,
                    reviewer=agent,
                    reported_version_hashes=reported_version_hashes,
                    allowed_task_ids=review_task_ids,
                )
            )
            if targets:
                by_name = {argument.name: argument for argument in review_spec.arguments}
                available.add(
                    replace(
                        review_spec,
                        description=(
                            "Independently review one currently eligible non-author "
                            "answer version from the shared queue."
                        ),
                        arguments=(
                            replace(
                                by_name["problem_id"],
                                enum=tuple(row["problem_id"] for row in targets),
                            ),
                            replace(
                                by_name["version_hash"],
                                enum=tuple(row["version_hash"] for row in targets),
                            ),
                            by_name["decision"],
                            by_name["content"],
                        ),
                    )
                )
        actions = frozenset(available)
    if answer_sheet_contest:
        return actions
    active = session.active_task
    if active is None or active.kind != "programming":
        return actions
    if not config.review_required:
        if config.features.leader_submits and agent == config.leader:
            # The leader hands in whatever source the team has frozen on the
            # active task; it never pastes code into the submission itself.
            available = set(actions)
            submit_spec = ACTION_REGISTRY["submit_code"]
            available.discard(submit_spec)
            if active.versions and not active.locked:
                available.add(
                    replace(
                        submit_spec,
                        description=(
                            "Submit the active problem's latest recorded source "
                            "version to the remote judge for an official verdict."
                        ),
                        arguments=(),
                    )
                )
            actions = frozenset(available)
        return actions

    available = set(actions)
    latest = active.versions[-1] if active.versions else None
    has_evidence = bool(latest and latest.evidence_refs)
    # In reviewed programming sessions, work is a note, not a source setter.
    # execute_code is the explicit path for creating/revising candidate source.
    work_spec = ACTION_REGISTRY["work"]
    if work_spec in available:
        available.remove(work_spec)
        available.add(replace(work_spec, description=(
            "Record programming analysis notes without replacing candidate source. "
            "Use execute_code for complete source; use speak to report sample AC."
        )))
    # The remote judge is the oracle for programming tasks: a sample-AC version
    # becomes submittable once a different agent has reviewed it, whether that
    # review approved or rejected. A reject is advice to revise, not a veto.
    has_approval = has_evidence and session.has_independent_review()
    latest_attempt = next(
        (
            submission
            for submission in reversed(active.submissions)
            if latest and submission.version_hash == latest.version_hash
        ),
        None,
    )
    attempt_blocks_submit = bool(
        latest_attempt
        and (
            latest_attempt.valid
            or latest_attempt.turn == session.budget.turns_used
        )
    )

    if not has_approval or attempt_blocks_submit:
        available.discard(ACTION_REGISTRY["submit_code"])
    else:
        submit_spec = ACTION_REGISTRY["submit_code"]
        available.discard(submit_spec)
        available.add(
            replace(
                submit_spec,
                description=(
                    "Submit the exact frozen, sample-AC, independently reviewed "
                    "source version to the remote judge for an official verdict."
                ),
                arguments=(),
            )
        )
    # Authors report successful local runs with speak. Reviewers use
    # review_answer directly from the shared queue.
    available.discard(ACTION_REGISTRY["request_review"])
    if (
        programming_source_required
        and _needs_programming_source(active)
        and (work_task_ids is None or active.task_id in work_task_ids)
        and ACTION_REGISTRY["execute_code"] in available
    ):
        # Only the programming implementation/repair stage is artifact-gated.
        # Reporting, independent review and submission retain their own tools.
        return frozenset({ACTION_REGISTRY["execute_code"]})
    return frozenset(available)


def _programming_gate_guidance(
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    reported_version_hashes: set[str] | None = None,
    sample_reports: dict[str, dict[str, Any]] | None = None,
) -> str:
    active = session.active_task
    if (
        not config.review_required
        or active is None
        or active.kind != "programming"
    ):
        return ""

    latest = active.versions[-1] if active.versions else None
    latest_attempt = next(
        (
            submission
            for submission in reversed(active.submissions)
            if latest and submission.version_hash == latest.version_hash
        ),
        None,
    )
    remote_failure = _remote_failure_guidance(active, config)
    sample_failure = _sample_failure_text(
        (sample_reports or {}).get(latest.version_hash) if latest else None
    )
    if latest is None:
        next_step = (
            "Call execute_code with the complete candidate source. work stores "
            "analysis notes only. This creates your first source version: write "
            "the solver in the code argument now, rather than waiting for a "
            "pre-existing program. execute_code feeds the official sample input to "
            "your program and compares the output; only a sample AC counts as "
            "local run evidence."
        )
    elif latest_attempt and latest_attempt.valid:
        next_step = (
            f"The latest frozen version received {latest_attempt.verdict}. "
            "Use execute_code with revised complete source to create a new version."
        )
    elif latest_attempt and latest_attempt.turn == session.budget.turns_used:
        next_step = (
            "A remote submission of this version already failed this round. "
            "Analyze the failure or wait until the next round before retrying."
        )
    elif not latest.evidence_refs:
        next_step = (
            (
                f"The latest version failed the official samples. {sample_failure} "
                "Fix the code and call execute_code again with the complete revised "
                "source; review and submission stay locked until the samples pass."
            )
            if sample_failure
            else (
                "Call execute_code with the exact complete latest source; it must "
                "pass the official sample cases. work and verify do not count as "
                "local run/test evidence."
            )
        )
    elif any(
        not review.stale
        and review.version_hash == latest.version_hash
        and review.decision == "reject"
        for review in active.reviews
    ):
        next_step = (
            "A reviewer rejected this sample-AC version. Do not request another "
            "review of unchanged code. Either (a) fix the named defect and call "
            "execute_code with the new complete source, or (b) if you believe the "
            "code is right, call submit_code with no arguments now: the remote judge "
            "is the final oracle and a WA/TLE verdict costs only a time penalty, "
            "while never submitting scores zero."
        )
    elif latest.version_hash not in (reported_version_hashes or set()):
        if latest.author == agent:
            next_step = (
                "Call speak to report the sample-AC local run and ask a different "
                "agent to review this exact version."
            )
            if remote_failure:
                next_step += (
                    " Because the previous version failed remotely, this speak must "
                    "contain a one-line diagnosis: what was wrong before and what "
                    "changed in this version. The version does not enter the review "
                    "queue until you speak."
                )
        else:
            next_step = "Wait for the author to report the successful local run with speak."
    elif not session.has_independent_review():
        next_step = (
            "Wait for a different agent to review this exact reported version."
            if latest.author == agent
            else (
                "Read the full source and the sample report listed under YOUR "
                "ELIGIBLE PENDING REVIEWS, then call review_answer on this exact "
                "evidence-backed version. Approve if the algorithm, edge cases, and "
                "complexity look sound; reject only with a concrete defect or a "
                "specific failing input. Remember the remote judge decides "
                "correctness; the samples already pass."
            )
        )
    else:
        next_step = (
            "Call submit_code with no source argument; it submits the exact frozen "
            "latest version to the remote judge."
        )
    guidance = f"PROGRAMMING GATE — NEXT REQUIRED: {next_step}\n"
    if remote_failure:
        guidance += f"{remote_failure}\n"
    return guidance + "\n"


def _shared_review_history(
    session: ContestSession,
    *,
    max_versions_per_task: int | None = None,
    max_content_chars: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build shared review history grouped by task and immutable answer version."""
    history: dict[str, list[dict[str, Any]]] = {}
    for task in session.tasks:
        versions = (
            task.versions[-max_versions_per_task:]
            if max_versions_per_task is not None
            else task.versions
        )
        rows = []
        for version in versions:
            content = version.content
            if max_content_chars is not None and len(content) > max_content_chars:
                content = content[:max_content_chars] + "…"
            rows.append(
                {
                    "version_hash": version.version_hash,
                    "parent_hash": version.parent_hash,
                    "author": version.author,
                    "answer": content,
                    "current": bool(
                        task.versions
                        and version.version_hash == task.versions[-1].version_hash
                    ),
                    "reviews": [
                        {
                            "reviewer": review.reviewer,
                            "decision": review.decision,
                            "body": review.body,
                            "stale": review.stale,
                        }
                        for review in task.reviews
                        if review.version_hash == version.version_hash
                    ],
                }
            )
        if rows:
            history[task.task_id] = rows
    return history


def _pending_review_queue(
    session: ContestSession,
    *,
    reviewer: str,
    reported_version_hashes: set[str] | None = None,
    allowed_task_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    reported = reported_version_hashes or set()
    return [
        {
            "problem_id": task.task_id,
            "version_hash": task.versions[-1].version_hash,
            "author": task.versions[-1].author,
        }
        for task in session.tasks
        if task.versions
        and (allowed_task_ids is None or task.task_id in allowed_task_ids)
        and task.versions[-1].author != reviewer
        and (
            task.kind != "programming"
            or task.versions[-1].version_hash in reported
        )
        and not _task_has_independent_approval(task)
        and not any(
            not review.stale
            and review.version_hash == task.versions[-1].version_hash
            and review.decision == "reject"
            for review in task.reviews
        )
    ]


def _reported_version_hashes(memory: ContestMemory) -> set[str]:
    return set(_local_run_reports(memory))


def _local_run_reports(memory: ContestMemory) -> dict[str, str]:
    """Latest author speak report per version hash."""
    reports: dict[str, str] = {}
    for event in memory.archival_snapshot()["events"]:
        payload = event.get("payload", {})
        if event["kind"] == "local_run_report" and payload.get("version_hash"):
            reports[str(payload["version_hash"])] = str(payload.get("report") or "")
    return reports


def _sample_reports(memory: ContestMemory) -> dict[str, dict[str, Any]]:
    """Latest official-sample judge report per version hash."""
    reports: dict[str, dict[str, Any]] = {}
    for event in memory.archival_snapshot()["events"]:
        payload = event.get("payload", {})
        if event["kind"] == "sample_judge_result" and payload.get("version_hash"):
            reports[str(payload["version_hash"])] = {
                "sample_verdict": payload.get("sample_verdict"),
                "sample_summary": payload.get("sample_summary"),
                "sample_cases": payload.get("sample_cases") or [],
            }
    return reports


def _sample_failure_text(report: dict[str, Any] | None) -> str:
    if not report:
        return ""
    verdict = report.get("sample_verdict")
    if verdict is None or str(verdict).upper() == "AC":
        return ""
    failed = [
        case
        for case in report.get("sample_cases") or []
        if str(case.get("verdict")) != "AC"
    ]
    parts = [str(report.get("sample_summary") or f"Sample judge: {verdict}.")]
    for case in failed[:3]:
        line = f"sample case {case.get('name')} -> {case.get('verdict')}"
        if case.get("detail"):
            line += f" ({case['detail']})"
        if case.get("expected") is not None:
            line += f"; expected: {json.dumps(case.get('expected'), ensure_ascii=False)}"
        if case.get("actual") is not None:
            line += f"; got: {json.dumps(case.get('actual'), ensure_ascii=False)}"
        parts.append(line)
    return " ".join(parts)


_VERDICT_CHECKLISTS = {
    "WA": (
        "WA checklist: re-read the output format (case labels, spacing, line "
        "breaks, exact wording), floating-point precision and rounding, edge cases "
        "(zero/empty input, minimum and maximum bounds, ties), integer overflow or "
        "off-by-one in loops, and every branch the samples never exercise. Build "
        "an extra adversarial test and run it with execute_code."
    ),
    "TLE": (
        "TLE checklist: compute the asymptotic complexity against the maximum "
        "input size, replace per-query rescans with precomputation or better data "
        "structures, read all input with sys.stdin.buffer and write with one join, "
        "and avoid Python-level loops over 10^7 or more operations."
    ),
    "RE": (
        "RE checklist: index and recursion bounds, division by zero, exhausted "
        "input reads, memory blow-ups, and unhandled parsing of blank lines."
    ),
    "MLE": (
        "MLE checklist: avoid materializing full input copies or dense tables; "
        "stream input and prefer arrays over lists of objects."
    ),
}


def _remote_failure_guidance(
    active: TaskUnit,
    config: ContestRunConfig,
) -> str:
    """Describe the latest valid non-AC remote verdict with a concrete checklist."""
    attempt = next(
        (submission for submission in reversed(active.submissions) if submission.valid),
        None,
    )
    if attempt is None or attempt.verdict.upper() == "AC":
        return ""
    verdict = attempt.verdict.upper()
    valid_attempts = sum(submission.valid for submission in active.submissions)
    remaining = max(0, config.consecutive_non_ac_limit - active.consecutive_non_ac)
    checklist = _VERDICT_CHECKLISTS.get(
        verdict,
        "Re-derive the algorithm from the statement and test the boundaries.",
    )
    return (
        f"REMOTE VERDICT {verdict} on attempt {valid_attempts}; "
        f"{remaining} more non-AC attempt(s) before this task is forced into cooldown. "
        "The judge gives no failing case, so reason from the statement. "
        f"{checklist} The same source hash cannot be resubmitted; the revised "
        "version must pass the official samples again, be reported with speak, and "
        "be independently re-reviewed."
    )


def _precontest_coach_prompts(
    manifest: ContestManifest,
    config: ContestRunConfig,
) -> tuple[str, str]:
    tasks = [
        {
            "problem_id": task.task_id,
            "type": task.task_type,
            "programming": task.programming,
            "prompt": task.prompt,
        }
        for task in manifest.tasks
    ]
    if config.leader is not None:
        role = (
            f"You are {config.leader}, the team leader, and you stay in the contest "
            "afterwards. Produce a structured opening plan for your teammates. You "
            "may assign one problem per agent, several agents to one problem, or the "
            "whole team to one problem; you may work on any problem yourself and you "
            "alone submit. You can change assignments later with assign_problem. "
        )
        plan_title = "OPENING LEADER PLAN"
    else:
        role = (
            "You are Coach. Produce a structured pre-contest brief for the contestant "
            "agents, then exit. You may assign one problem per agent, several agents to "
            "one problem, or the whole team to one problem. "
        )
        plan_title = "PRE-CONTEST BRIEF"
    system = (
        role
        + "Base the choice on the actual "
        "task set, team size, rules, and budget. Do not solve the problems and do not "
        "call contestant actions. Respect the declared task family: never prescribe "
        "source code, stdin/stdout, sample execution, or code review for a "
        "non-programming family. Return only one JSON object with this schema: "
        '{"summary":"...",'
        '"work_assignments":{"Agent_1":["exact problem_id"]},'
        '"review_assignments":{"Agent_1":["exact problem_id"]},'
        '"task_order":["exact problem_id"],'
        '"switch_conditions":["..."],"final_check":["..."]}.'
    )
    user = (
        f"{plan_title}\nCompetition: {manifest.competition_id}\n"
        f"Task family: {manifest.task_family}\n"
        "Competition format: "
        f"{manifest.metadata.get('competition_description') or 'No additional format description.'}\n"
        f"Team size: {config.team_size}\n"
        f"Budget: turns={config.max_turns}, api_calls={config.max_api_calls}, "
        f"tokens={config.max_tokens}, minutes={config.max_simulated_minutes}\n"
        f"Rules: {config.rule_guidance or 'No additional rule-card guidance.'}\n"
        "Assign every listed task to at least one worker and at least one reviewer. "
        "A task may appear under multiple workers for group collaboration. "
        "Use only the exact Agent_N names and exact problem_id strings shown here. "
        "Work assignments will be enforced by the runtime and copied into each "
        "agent's private memory.\n"
        f"Tasks:\n{json.dumps(tasks, ensure_ascii=False)}"
    )
    return system, user


def _strip_coach_response(response: str) -> str:
    marker = "ACTION: speak | PAYLOAD:"
    stripped = response.strip()
    if stripped.lower().startswith(marker.lower()):
        stripped = stripped[len(marker) :].strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _normalize_task_ids(
    values: Any,
    manifest: ContestManifest,
) -> list[str]:
    known = {task.task_id for task in manifest.tasks}
    suffixes = {
        task.task_id.rsplit(":", 1)[-1]: task.task_id
        for task in manifest.tasks
    }
    normalized: list[str] = []
    for value in values if isinstance(values, list) else []:
        raw = str(value)
        task_id = raw if raw in known else suffixes.get(raw)
        if task_id and task_id not in normalized:
            normalized.append(task_id)
    return normalized


def _default_coach_plan(
    manifest: ContestManifest,
    config: ContestRunConfig,
    *,
    summary: str,
) -> dict[str, Any]:
    agents = [f"Agent_{index}" for index in range(1, config.team_size + 1)]
    scored = [task.task_id for task in manifest.tasks]
    work = {agent: [] for agent in agents}
    review = {agent: [] for agent in agents}
    for index, task_id in enumerate(scored):
        work[agents[index % len(agents)]].append(task_id)
        reviewer_index = (index + 1) % len(agents) if len(agents) > 1 else index
        review[agents[reviewer_index]].append(task_id)
        if len(agents) > 1:
            review[agents[(reviewer_index + 1) % len(agents)]].append(task_id)
    return {
        "summary": summary or "Round-robin fallback allocation.",
        "work_assignments": work,
        "review_assignments": review,
        "task_order": scored,
        "switch_conditions": ["Move on after the latest draft is independently approved."],
        "final_check": ["Audit every latest version before final submission."],
    }


def _set_work_assignment(
    personal_assignments: dict[str, dict[str, Any]],
    agent: str,
    problem_ids: list[str],
) -> None:
    """Replace one seat's enforced work list (leader reassignment)."""
    current = personal_assignments.get(agent) or {
        "agent": agent,
        "work_tasks": [],
        "review_tasks": [],
        "summary": "",
        "switch_conditions": [],
        "final_check": [],
    }
    personal_assignments[agent] = {**current, "work_tasks": list(problem_ids)}


def _normalize_coach_plan(
    response: str,
    manifest: ContestManifest,
    config: ContestRunConfig,
) -> dict[str, Any]:
    stripped = _strip_coach_response(response)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        try:
            parsed = json.loads(stripped[start : end + 1])
        except (json.JSONDecodeError, ValueError):
            return _default_coach_plan(manifest, config, summary=stripped)
    if not isinstance(parsed, dict):
        return _default_coach_plan(manifest, config, summary=stripped)

    agents = [f"Agent_{index}" for index in range(1, config.team_size + 1)]
    work_raw = parsed.get("work_assignments")
    review_raw = parsed.get("review_assignments")
    work = {
        agent: _normalize_task_ids(
            work_raw.get(agent, []) if isinstance(work_raw, dict) else [],
            manifest,
        )
        for agent in agents
    }
    review = {
        agent: _normalize_task_ids(
            review_raw.get(agent, []) if isinstance(review_raw, dict) else [],
            manifest,
        )
        for agent in agents
    }
    scored = [task.task_id for task in manifest.tasks]
    for index, task_id in enumerate(scored):
        if not any(task_id in assignments for assignments in work.values()):
            work[agents[index % len(agents)]].append(task_id)
        if not any(task_id in assignments for assignments in review.values()):
            reviewer_index = (index + 1) % len(agents) if len(agents) > 1 else index
            review[agents[reviewer_index]].append(task_id)
        assigned_reviewers = [
            agent for agent in agents if task_id in review[agent]
        ]
        if len(agents) > 1 and len(assigned_reviewers) < 2:
            backup = next(agent for agent in agents if agent not in assigned_reviewers)
            review[backup].append(task_id)
    switch_conditions = parsed.get("switch_conditions")
    final_check = parsed.get("final_check")
    return {
        "summary": str(parsed.get("summary") or "Coach allocation"),
        "work_assignments": work,
        "review_assignments": review,
        "task_order": _normalize_task_ids(parsed.get("task_order"), manifest)
        or scored,
        "switch_conditions": [
            str(item) for item in switch_conditions
        ]
        if isinstance(switch_conditions, list)
        else [],
        "final_check": [str(item) for item in final_check]
        if isinstance(final_check, list)
        else [],
    }


def _system_prompt(
    config: ContestRunConfig,
    agent: str,
    actions: frozenset[ActionSpec],
    *,
    native_actions: bool = False,
    answer_sheet_contest: bool = False,
    task_family: TaskFamily = "general",
    coach_guidance: str = "",
) -> str:
    if native_actions:
        base = (
            f"You are {agent}, one contestant in a {config.team_size}-agent team.\n"
            "You decide which provided function best advances the contest. "
            "Choose exactly one function and call it once. "
            "Do not emit a text answer instead of the function call."
        )
    else:
        base = (
            f"You are {agent}, one contestant in a {config.team_size}-agent team.\n"
            "Return exactly one JSON object with keys action and arguments. "
            "Do not include Markdown or a second action.\n"
            f"{render_action_instructions(actions)}"
        )
    if any(spec.name in DESK_ACTION_NAMES for spec in actions):
        base += (
            "\nDESK TOOLS: inspect_problem reads any problem's statement and full "
            "version/review/submission history without moving the team's active "
            "problem; use it to check another problem or to self-verify before you "
            "act. remember stores a private note (intermediate result, dead end, "
            "reminder) that survives outside the visible transcript; recall searches "
            "your notes and shared notes; share_note publishes one note to the team. "
            "work is only for a candidate answer, never for notes. triage_problem "
            "sets the team priority of a problem (high/normal/low/hopeless) so the "
            "scheduler reorders remaining work; hopeless problems stay on the sheet "
            "and their latest draft is still submitted at the deadline. Desk tools "
            "consume a turn like any other action, so do not loop on them."
        )
    features = config.features
    if features.coach == "none":
        if config.rule_guidance:
            return base + f"\nCONTEST RULES\n{config.rule_guidance}"
        return base
    reviewed_programming = task_family == "programming" and config.review_required
    if features.coach == "leader":
        leader = config.leader
        if agent == leader:
            strategic = base + (
                f"\nLEADER PROTOCOL: You are {leader}, the team leader. Your opening "
                "plan is enforced: each teammate may only work on the problems in "
                "their work list, and you may change a list at any time with "
                "assign_problem. You may work on any problem yourself. Only you can "
                "submit: teammates draft and report, you check the latest version of "
                "each problem and hand it in. Re-plan when a problem stalls, when a "
                "teammate finishes early, or when the budget is running out. "
            )
        else:
            strategic = base + (
                f"\nLEADER PROTOCOL: {leader} is the team leader. Work only on the "
                "problems in your enforced work list, report results with speak, and "
                f"raise blockers or handoffs with direct_message to {leader}. You "
                "cannot submit; the leader hands in the team's latest version of each "
                "problem, so make sure your best answer is the latest recorded draft. "
            )
        strategic += (
            "The active task is a shared team cursor, not an ownership lock: select "
            "the problem you are assigned before acting on it. Preserve teammates' "
            "drafts and do not overwrite a sound version without a concrete correction. "
        )
    else:
        strategic = base + (
            "\nPRE-CONTEST COACH OPERATING PRINCIPLE: Follow the coach's assignment "
            "and coordination guidance for this contest. The coach may assign one problem "
            "per agent, put a group on one problem, or focus the whole team on one problem. "
            "The active task is a shared team cursor, not an ownership lock: select the "
            "problem assigned by the coach before acting on it. Preserve teammates' drafts "
            "and do not overwrite a sound reviewed version without a concrete correction. "
        )
        if features.private_channel and config.team_size > 1:
            strategic += (
                "Use direct_message when one specific teammate needs a private question, "
                "handoff, or correction; use speak when the whole team should know. "
            )
    strategic += (
        "Use work for programming analysis notes; execute_code records source. "
        if reviewed_programming
        else "Use work only to create a substantive candidate solution or final answer, "
             "never a status update, request for missing work, TODO, or placeholder. "
    )
    if config.review_required:
        strategic += (
            "A different agent uses "
            "review_answer with the exact problem_id and version_hash to approve or "
            "reject it. After repeated failed submissions, move to another unsolved "
            "problem and revisit later. "
            "Inspect task status before acting: prefer review over another rewrite when "
            "a teammate's candidate is ready."
        )
    else:
        strategic += (
            "After repeated failed submissions, move to another unsolved problem and "
            "revisit later. Inspect task status before acting so you do not redo a "
            "teammate's finished work."
        )
    if answer_sheet_contest and config.review_required:
        strategic += (
            "\nANSWER-SHEET COACH PROTOCOL: Never submit an individual problem. "
            "Use work only when you have a complete candidate response for the active "
            "problem: include the explicit final answer and enough derivation to audit "
            "it. Never save setup notes, TODOs, uncertainty, or placeholders as a "
            "candidate answer; use speak to discuss those or move to another assigned "
            "problem. Follow the opening coach's frozen allocation when selecting "
            "problems. Every new candidate automatically enters the shared review "
            "queue. A reviewer must reject any candidate lacking an explicit final "
            "answer or containing unresolved uncertainty; approve only a complete, "
            "checkable answer. After every problem has a "
            "reviewed draft, perform the contest-wide FINAL REVIEW. Only after that "
            "review is complete, call submit once with no arguments to atomically "
            "hand in the whole answer sheet and end the contest. Never call "
            "finish_contest."
        )
    elif answer_sheet_contest:
        strategic += (
            "\nANSWER-SHEET PROTOCOL: Never submit an individual problem. Use work "
            "only when you have a complete candidate response for the active problem "
            "with an explicit final answer. Never save setup notes, TODOs, or "
            "placeholders as a candidate answer. "
            + (
                f"Once every problem has a draft, {config.leader} calls submit once "
                "with no arguments to hand in the whole sheet and end the contest; "
                "nobody else can submit. "
                if features.leader_submits
                else "Once every problem has a draft, call submit once with no "
                "arguments to hand in the whole sheet and end the contest. "
            )
            + "Never call finish_contest."
        )
    elif task_family == "programming" and not config.review_required:
        strategic += (
            "\nPROGRAMMING WORKFLOW: An author calls execute_code with the complete "
            "candidate source that reads stdin and writes stdout; the system runs it "
            "on the official samples and reports expected versus actual output. Fix "
            "the code and re-run until the samples pass, then report with speak. "
            + (
                f"Only {config.leader} submits: after a sample-AC report, the leader "
                "selects that problem and calls submit_code with no arguments to send "
                "the latest recorded source to the remote judge. "
                if features.leader_submits
                else "When the samples pass, call submit_code to send the source to "
                "the remote judge. "
            )
            + "A WA/TLE costs a time penalty, but a sample-AC version that is never "
            "submitted scores zero. Select another unsolved problem after a valid "
            "submission."
        )
    elif task_family == "programming":
        strategic += (
            "\nMANDATORY PROGRAMMING WORKFLOW: (1) An author calls execute_code "
            "with the complete candidate source that reads stdin and writes stdout. "
            "Write the first solver directly in that call; lack of existing source "
            "is not a reason to rest. Do not replace an algorithm with a placeholder "
            "or a hardcoded sample harness when repairing it. "
            "The system runs it on the official sample input and compares the "
            "output; only a sample AC counts as local run evidence, and a sample "
            "failure reports the expected versus actual output so you can fix it. "
            "(2) Only after the samples pass, the author calls speak to report the "
            "sample result (and, after a remote WA/TLE, a one-line diagnosis of what "
            "changed) and asks for review. (3) A different agent reads the FULL "
            "source and sample report shown in YOUR ELIGIBLE PENDING REVIEWS and "
            "calls review_answer on that exact version, approving when the "
            "algorithm, edge cases, and complexity look sound; reject only with a "
            "concrete defect or a specific failing input, never for lack of a formal "
            "proof. Never approve code you have not read in full. "
            "(4) After the independent review, call submit_code with no arguments; "
            "the system re-checks the samples and then submits the frozen reviewed "
            "source to the remote judge. Never rewrite or paste source into "
            "submit_code. The remote judge is the final oracle: a WA/TLE costs a "
            "time penalty, but a sample-AC version that is never submitted scores "
            "zero. If review_answer rejects a version, the author either fixes the "
            "named defect and re-runs execute_code, or submits anyway when the "
            "objection is speculative; never request another review of unchanged "
            "code. After WA/TLE, follow the verdict checklist in the PROGRAMMING "
            "GATE, revise, and repeat all four steps. Select another unsolved "
            "problem after a valid submission. Never call finish_contest while any "
            "task lacks a valid submission or required final approval."
        )
    elif task_family == "mathematics":
        strategic += (
            "\nMATHEMATICS WORKFLOW: This is a mathematics contest, not a programming "
            "task. Never ask for source code, stdin/stdout, executable candidates, or "
            "sample-run evidence. Read the numbered problems in the active prompt and "
            "solve as many as possible. Use work only for an actual candidate answer "
            "sheet containing explicit numbered final answers, with compact derivations "
            "where useful for review. Preserve already-solved entries when revising the "
            "sheet. Use the calculator when available for arithmetic checks. Reviewers "
            "check the mathematics and answer numbering, not code. Submit the best "
            "available answer sheet before the deadline even when some entries remain "
            "blank or unreviewed."
        )
    elif task_family == "short_answer":
        strategic += (
            "\nSHORT-ANSWER WORKFLOW: This is not a programming task. Answer the "
            "questions directly and concisely. For a packet, use work for a numbered "
            "answer sheet such as `Q1: answer`; for one question, give its explicit "
            "final answer. Never save a status update or ask for source code. Reviewers "
            "check factual correctness, aliases, and alignment between question numbers "
            "and answers. Submit the most complete answer set available by the deadline."
        )
    elif task_family == "puzzle":
        strategic += (
            "\nPUZZLE WORKFLOW: This is a puzzle whose deliverable is a final answer "
            "word or phrase, not source code. Infer the puzzle mechanism from the "
            "provided prompt and assets, share concrete deductions with the team, and "
            "use work only when recording a plausible final answer with its supporting "
            "reasoning. Never store a status-only draft. Review extraction, spelling, "
            "and answer format before submission."
        )
    else:
        strategic += (
            "\nGENERAL NON-PROGRAMMING WORKFLOW: Solve the task directly. Use work only "
            "for a substantive candidate response with an explicit final answer. Never "
            "ask for executable source or stdin/stdout unless the active task explicitly "
            "states that programming is required."
        )
    if coach_guidance:
        title = (
            "OPENING LEADER PLAN" if features.coach == "leader"
            else "PRE-CONTEST COACH BRIEF"
        )
        strategic += f"\n{title}\n{coach_guidance}"
    if config.rule_guidance:
        strategic += f"\nCONTEST RULES\n{config.rule_guidance}"
    return strategic


def _user_prompt(
    manifest: ContestManifest,
    session: ContestSession,
    memory: ContestMemory,
    config: ContestRunConfig,
    agent: str,
    *,
    final_review_phase: bool = False,
    personal_assignment: dict[str, Any] | None = None,
    programming_source_required: bool = False,
) -> str:
    active = session.active_task
    allowed_reviews = (
        set(personal_assignment.get("review_tasks", []))
        if personal_assignment
        else None
    )
    task_by_id = {task.task_id: task for task in manifest.tasks}
    active_text = (
        f"ACTIVE TASK {active.task_id}\n"
        "(This task is already selected for you; act on it directly instead of "
        f"calling select_problem again.)\n{task_by_id[active.task_id].prompt}"
        if active is not None
        else "NO ACTIVE TASK. Select one unfinished problem."
    )
    status = json.dumps(_task_rows(session), ensure_ascii=False)
    shared_reviews = json.dumps(
        _shared_review_history(
            session,
            max_versions_per_task=5,
            max_content_chars=800,
        ),
        ensure_ascii=False,
    )
    local_run_reports = _local_run_reports(memory)
    sample_reports = _sample_reports(memory)
    pending_rows = _pending_review_queue(
        session,
        reviewer=agent,
        reported_version_hashes=set(local_run_reports),
        allowed_task_ids=allowed_reviews,
    )
    if final_review_phase and active is not None and active.versions:
        version = active.versions[-1]
        if version.author != agent and (allowed_reviews is None or active.task_id in allowed_reviews):
            if not any(row["problem_id"] == active.task_id for row in pending_rows):
                pending_rows.append({"problem_id": active.task_id, "version_hash": version.version_hash, "author": version.author})
    session_task_by_id = {task.task_id: task for task in session.tasks}
    for row in pending_rows:
        task = session_task_by_id[row["problem_id"]]
        version = next(
            (
                candidate
                for candidate in reversed(task.versions)
                if candidate.version_hash == row["version_hash"]
            ),
            None,
        )
        if version is None:
            continue
        row["prompt"] = task_by_id[task.task_id].prompt
        row["answer"] = version.content
        if task.kind == "programming":
            # Reviewers approve the exact frozen source, so show all of it.
            row["source"] = version.content
            row["sample_report"] = sample_reports.get(version.version_hash)
            row["author_report"] = local_run_reports.get(version.version_hash)
    pending_reviews = json.dumps(pending_rows, ensure_ascii=False)
    budget = json.dumps(
        {
            **asdict(session.budget),
            "blank_tasks": [task.task_id for task in session.tasks if not task.versions],
        },
        ensure_ascii=False,
    )
    if config.features.structured_context and active is not None:
        context: Any = memory.strategic_projection(
            viewer=agent,
            current_task_id=active.task_id,
            max_chars=6000,
        )
    else:
        visible = memory.view(agent)
        context = [
            {
                "turn": event.turn,
                "actor": event.actor,
                "kind": event.kind,
                "payload": event.payload,
            }
            for event in visible[-12:]
        ]
    phase = (
        "FINAL REVIEW PHASE: Audit the active task's latest draft answer. "
        "Call review_answer with its exact problem_id and version_hash. Approve with "
        "concise evidence if correct; reject and explain the defect if wrong.\n\n"
        if final_review_phase
        else ""
    )
    submission_rule = ""
    if _is_answer_sheet_contest(manifest):
        if config.final_review_required:
            submission_rule = (
                "ANSWER-SHEET RULE: work edits per-problem drafts. Do not submit "
                "individual problems. The active problem is shared state, not exclusive "
                "ownership; follow the coach's allocation when selecting which problem "
                "to work on or review. After every draft and the full-sheet review are "
                "complete, call submit once with no arguments; that atomically hands in "
                "the whole sheet and ends the contest. Never use finish_contest.\n\n"
            )
        elif config.features.leader_submits:
            submission_rule = (
                "ANSWER-SHEET RULE: work edits per-problem drafts. Do not submit "
                f"individual problems. Only {config.leader} can call submit (once, "
                "with no arguments) to hand in the whole current answer sheet and end "
                "the contest. Never use finish_contest.\n\n"
            )
        else:
            submission_rule = (
                "ANSWER-SHEET RULE: work edits per-problem drafts. Do not submit "
                "individual problems. Call submit once with no arguments to hand in "
                "the whole current answer sheet and end the contest. Never use "
                "finish_contest.\n\n"
            )
    personal_block = (
        "YOUR ENFORCED PERSONAL COACH MEMORY\n"
        f"{json.dumps(personal_assignment, ensure_ascii=False)}\n\n"
        if personal_assignment is not None
        else ""
    )
    source_block = ""
    if (config.review_required
            and active is not None and active.kind == "programming" and active.versions):
        latest = active.versions[-1]
        source_block = (
            "ACTIVE PROGRAMMING SOURCE (complete, not a preview; repair this version)\n"
            + json.dumps({
                "version_hash": latest.version_hash,
                "author": latest.author,
                "source": latest.content,
                "sample_report": sample_reports.get(latest.version_hash),
                "reviews": [asdict(review) for review in active.reviews
                            if review.version_hash == latest.version_hash and not review.stale],
                "latest_official_submission": (
                    asdict(active.latest_valid_submission) if active.latest_valid_submission else None
                ),
            }, ensure_ascii=False) + "\n\n"
        )
    source_requirement = (
        "SOURCE ACTION REQUIRED: The analysis/rest allowance for this programming "
        "task has been used. Call execute_code now with a complete best-effort "
        "solver reading stdin and writing stdout. Implement or repair the actual "
        "algorithm; do not send an empty/TODO program or a hardcoded sample harness.\n\n"
        if programming_source_required else ""
    )
    return (
        f"CONTEST {manifest.session_id}\n"
        f"TASK FAMILY {manifest.task_family}\n"
        "COMPETITION FORMAT "
        f"{manifest.metadata.get('competition_description') or 'No additional format description.'}\n"
        f"TASK STATUS {status}\n"
        f"BUDGET {budget}\n\n"
        "DEADLINE POLICY: When the session ends, the environment automatically "
        "hands in pending non-programming drafts for both team variants. Missing "
        "answers remain blank. You may use your last action to improve a draft.\n\n"
        f"{personal_block}"
        f"{submission_rule}"
        f"{phase}"
        f"{_programming_gate_guidance(session, config, agent, set(local_run_reports), sample_reports)}"
        f"{active_text}\n\n"
        f"{source_requirement}{source_block}"
        "SHARED ANSWER REVIEW HISTORY (answer previews are truncated to 800 chars; "
        "the complete, untruncated source of every version you may review is given "
        f"under YOUR ELIGIBLE PENDING REVIEWS)\n{shared_reviews}\n\n"
        f"YOUR ELIGIBLE PENDING REVIEWS\n{pending_reviews}\n\n"
        f"VISIBLE MEMORY\n{json.dumps(context, ensure_ascii=False)}"
    )


def _next_task(
    session: ContestSession,
    policy: StrategicPolicy | None = None,
    *,
    exclude_task_id: str | None = None,
) -> TaskUnit | None:
    candidates = [
        task
        for task in session.tasks
        if task.task_id != exclude_task_id
        and not task.locked
        and not _task_complete(task)
        and (
            task.state is not TaskState.BLOCKED
            or (
                policy is not None
                and policy.can_revisit(
                    task,
                    current_turn=session.budget.turns_used,
                )
            )
        )
    ]
    # Team triage reorders within the manifest order; hopeless tasks still
    # qualify, they simply come last.
    candidates.sort(key=lambda task: task.priority_rank)
    unseen = [task for task in candidates if not task.versions and not task.submissions]
    return (unseen or candidates or [None])[0]


def _scheduled_agent_task(
    session: ContestSession,
    *,
    agent: str,
    work_task_ids: list[str],
    review_task_ids: set[str],
    reported_version_hashes: set[str],
) -> TaskUnit | None:
    def schedulable(task: TaskUnit) -> bool:
        return not task.locked and (
            task.state is not TaskState.BLOCKED
            or session.budget.turns_used >= (task.blocked_until_turn or 0)
        )

    # Live triage (triage_problem) outranks the Coach's frozen task_order:
    # stable sort keeps the Coach order inside each priority band and pushes
    # hopeless tasks to the end without dropping them.
    work_task_ids = sorted(
        work_task_ids, key=lambda task_id: session.task(task_id).priority_rank
    )

    # A sample-AC candidate must finish its review/submission pipeline before
    # reviewers or authors are sent back to untouched assignments. Otherwise
    # the shared active-task cursor rotates away from ready code and can consume
    # the entire contest without a remote submission.
    pending_reviews = _pending_review_queue(
        session,
        reviewer=agent,
        reported_version_hashes=reported_version_hashes,
        allowed_task_ids=review_task_ids,
    )
    for row in pending_reviews:
        task = session.task(row["problem_id"])
        if task.kind == "programming" and schedulable(task):
            return task

    for task_id in work_task_ids:
        task = session.task(task_id)
        if not schedulable(task) or task.kind != "programming" or not task.versions:
            continue
        latest = task.versions[-1]
        if (latest.evidence_refs and latest.author == agent
                and latest.version_hash not in reported_version_hashes):
            return task
        latest_submitted = any(
            submission.version_hash == latest.version_hash
            for submission in task.submissions
        )
        if (
            latest.evidence_refs
            and _task_has_independent_review(task)
            and not latest_submitted
        ):
            return task

    # Programming failures and untouched tasks share the same rotation order.
    # An untouched task must not indefinitely suppress repairs of an earlier WA.
    # For other families this remains the original initial-draft pass.
    for task_id in work_task_ids:
        task = session.task(task_id)
        if schedulable(task) and (not task.versions or _needs_programming_source(task)):
            return task

    # Preserve initial parallel drafting, then route review-only assignments
    # for every family. The active cursor determines the full problem context.
    for row in pending_reviews:
        task = session.task(row["problem_id"])
        if schedulable(task):
            return task

    for task_id in work_task_ids:
        task = session.task(task_id)
        if not schedulable(task):
            continue
        latest = task.versions[-1]
        rejected = any(
            not review.stale
            and review.version_hash == latest.version_hash
            and review.decision == "reject"
            for review in task.reviews
        )
        if rejected:
            return task
        if task.kind == "programming" and not task.locked:
            return task
        if not _task_has_independent_approval(task) and latest.author != agent:
            return task
    return None


def _task_complete(task: TaskUnit) -> bool:
    return (
        task.locked
        if task.kind == "programming"
        else task.latest_valid_submission is not None
    )


def _task_has_independent_review(task: TaskUnit) -> bool:
    if not task.versions:
        return False
    version = task.versions[-1]
    return any(
        not review.stale
        and review.version_hash == version.version_hash
        and review.reviewer != version.author
        for review in task.reviews
    )


def _task_has_independent_approval(task: TaskUnit) -> bool:
    if not task.versions:
        return False
    version = task.versions[-1]
    reviews = [
        review
        for review in task.reviews
        if not review.stale and review.version_hash == version.version_hash
    ]
    return not any(review.decision == "reject" for review in reviews) and any(
        review.decision == "approve" and review.reviewer != version.author
        for review in reviews
    )


def _rejected_version_count(task: TaskUnit) -> int:
    """Count distinct candidate versions rejected by another agent."""
    return len(
        {
            review.version_hash
            for review in task.reviews
            if review.decision == "reject"
        }
    )


def _contest_complete(session: ContestSession) -> bool:
    return all(_task_complete(task) for task in session.tasks)


def _append_action_error(
    memory: ContestMemory,
    session: ContestSession,
    agent: str,
    error: str,
) -> None:
    memory.append(
        task_id=session.active_task.task_id if session.active_task else None,
        question_id=None,
        actor=agent,
        visibility="private",
        kind="action_error",
        payload={"error": error},
        turn=session.budget.turns_used,
    )


def _record_scoreboard(
    memory: ContestMemory,
    session: ContestSession,
) -> None:
    memory.append(
        task_id=None,
        question_id=None,
        actor="Contest_Control",
        visibility="public",
        kind="scoreboard",
        payload={"tasks": _task_rows(session)},
        turn=session.budget.turns_used,
    )


def _participation_metrics(
    memory: ContestMemory,
    manifest: ContestManifest,
    team_size: int,
) -> tuple[float, float]:
    substantive = {"speak", "direct_message", "work", "submit", "submit_code"}
    agent_names = [f"Agent_{index + 1}" for index in range(team_size)]
    aar_values: list[float] = []
    balance_values: list[float] = []
    events = memory.archival_snapshot()["events"]
    for task in manifest.tasks:
        counts = [
            sum(
                event["task_id"] == task.task_id
                and event["actor"] == agent
                and event["kind"] in substantive
                for event in events
            )
            for agent in agent_names
        ]
        active = sum(count > 0 for count in counts)
        aar_values.append(active / team_size)
        total = sum(counts)
        if total == 0:
            balance_values.append(0.0)
            continue
        ordered = sorted(counts)
        gini = sum(
            (2 * index - team_size - 1) * value
            for index, value in enumerate(ordered, start=1)
        ) / (team_size * total)
        max_gini = 1.0 - 1.0 / team_size if team_size > 1 else 1.0
        balance_values.append(max(0.0, 1.0 - gini / max_gini))
    return (
        sum(aar_values) / len(aar_values),
        sum(balance_values) / len(balance_values),
    )


_INSPECT_STATEMENT_CHARS = 6000
_INSPECT_VERSION_CHARS = 2000


def _clip(text: str, limit: int) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def _inspect_problem_payload(
    manifest_task: ManifestTask,
    task: TaskUnit,
    memory: ContestMemory,
    *,
    focus: str = "",
) -> dict[str, Any]:
    """Read-only snapshot of one task for ``inspect_problem``."""
    sample_reports = _sample_reports(memory)
    local_reports = _local_run_reports(memory)
    return {
        "problem_id": task.task_id,
        "focus": focus,
        "statement": _clip(manifest_task.prompt, _INSPECT_STATEMENT_CHARS),
        "task_type": manifest_task.task_type,
        "programming": manifest_task.programming,
        "max_score": manifest_task.max_score,
        "state": task.state.value,
        "priority": task.priority,
        "triage_reason": task.triage_reason,
        "locked": task.locked,
        "versions": [
            {
                "version_hash": version.version_hash,
                "parent_hash": version.parent_hash,
                "author": version.author,
                "evidence_refs": list(version.evidence_refs),
                "content": _clip(version.content, _INSPECT_VERSION_CHARS),
                "sample_report": sample_reports.get(version.version_hash),
                "author_report": local_reports.get(version.version_hash),
            }
            for version in task.versions
        ],
        "reviews": [asdict(review) for review in task.reviews],
        "submissions": [asdict(submission) for submission in task.submissions],
        "independent_approval": _task_has_independent_approval(task),
        "note": (
            "Self-verification context only; this does not create or replace "
            "an independent review, and the team's active problem is unchanged."
        ),
    }


def _share_note(
    *,
    memory: ContestMemory,
    session: ContestSession,
    agent: str,
    note_id: str,
) -> tuple[bool, int]:
    """Publish one of the agent's private notes as a public ``note_shared`` event."""
    source = next(
        (
            event
            for event in memory.view(agent)
            if event.event_id == note_id
            and event.kind == "note"
            and event.actor == agent
        ),
        None,
    )
    if source is None:
        raise ValueError(
            f"{note_id} is not one of your notes; use recall to list note ids"
        )
    already = any(
        event.kind == "note_shared"
        and isinstance(event.payload, dict)
        and event.payload.get("source_event_id") == note_id
        for event in memory.view(agent)
    )
    if already:
        raise ValueError(f"{note_id} has already been shared with the team")
    payload = source.payload if isinstance(source.payload, dict) else {}
    memory.append(
        task_id=source.task_id,
        question_id=None,
        actor=agent,
        visibility="public",
        kind="note_shared",
        payload={
            "content": str(payload.get("content") or ""),
            "problem_id": source.task_id,
            "author": agent,
            "source_event_id": note_id,
        },
        turn=session.budget.turns_used,
    )
    return False, 0


def _apply_action(
    *,
    action: str,
    arguments: dict[str, Any],
    agent: str,
    manifest: ContestManifest,
    session: ContestSession,
    memory: ContestMemory,
    config: ContestRunConfig,
    strategic_policy: StrategicPolicy,
    task_action_executor: TaskActionExecutor,
    work_task_ids: set[str] | None = None,
    review_task_ids: set[str] | None = None,
    final_review_complete: bool = True,
    personal_assignments: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, int]:
    task_by_id = {task.task_id: task for task in manifest.tasks}
    active = session.active_task
    if (
        config.features.leader_submits
        and agent != config.leader
        and action in {"submit", "submit_code", "finish_contest"}
    ):
        raise ValueError(f"only {config.leader} may {action} in this baseline")
    visibility: Literal["public", "private"] = (
        "private" if ACTION_REGISTRY[action].visibility == "private" else "public"
    )
    recipients: tuple[str, ...] = ()
    if action == "direct_message":
        raw_recipients = arguments["recipients"]
        if isinstance(raw_recipients, str):
            raw_recipients = [raw_recipients]
        teammates = {
            f"Agent_{index}" for index in range(1, config.team_size + 1)
        }
        ordered: list[str] = []
        for recipient in raw_recipients:
            recipient = str(recipient)
            if recipient not in teammates:
                raise ValueError(f"unknown direct-message recipient: {recipient}")
            if recipient == agent:
                raise ValueError("direct_message recipients must be teammates")
            if recipient not in ordered:
                ordered.append(recipient)
        if not ordered:
            raise ValueError("direct_message needs at least one recipient")
        recipients = tuple(ordered)
        arguments = {**arguments, "recipients": ordered}
    if action in DESK_ACTION_NAMES:
        # Desk actions target an explicit problem or fall back to the shared
        # cursor; they never move it.
        requested = str(arguments.get("problem_id") or "").strip()
        if requested and requested not in task_by_id:
            raise ValueError(f"unknown problem: {requested}")
        event_task_id = requested or (active.task_id if active else None)
    else:
        event_task_id = (
            str(arguments.get("problem_id"))
            if action in {"select_problem", "review_answer"}
            else active.task_id
            if active
            else None
        )
    if action == "share_note":
        return _share_note(
            memory=memory,
            session=session,
            agent=agent,
            note_id=str(arguments["note_id"]),
        )
    if action == "assign_problem":
        if agent != config.leader:
            raise ValueError("only the team leader may reassign problems")
        if personal_assignments is None:
            raise RuntimeError("assign_problem needs the live assignment table")
        target = str(arguments["agent"])
        if target == agent or target not in {
            f"Agent_{index}" for index in range(1, config.team_size + 1)
        }:
            raise ValueError(f"unknown teammate: {target}")
        raw_ids = arguments["problem_ids"]
        if isinstance(raw_ids, str):
            raw_ids = [raw_ids]
        problem_ids: list[str] = []
        for raw in raw_ids:
            task_id = str(raw)
            if task_id not in task_by_id:
                raise ValueError(f"unknown problem: {task_id}")
            if task_id not in problem_ids:
                problem_ids.append(task_id)
        if not problem_ids:
            raise ValueError("assign_problem needs at least one problem")
        _set_work_assignment(personal_assignments, target, problem_ids)
        arguments = {**arguments, "agent": target, "problem_ids": problem_ids}
        event_task_id = None
    memory.append(
        task_id=event_task_id,
        question_id=None,
        actor=agent,
        visibility=visibility,
        # ``remember`` is the note itself; other desk actions log the request
        # and append their result as a private tool event.
        kind="note" if action == "remember" else action,
        payload=(
            {"content": str(arguments["content"]), "problem_id": event_task_id}
            if action == "remember"
            else arguments
        ),
        turn=session.budget.turns_used,
        recipients=recipients,
    )
    if action in {"remember", "assign_problem"}:
        return False, 0
    if action == "recall":
        notes = memory.recall(
            agent,
            query=str(arguments.get("query") or ""),
            problem_id=str(arguments.get("problem_id") or "") or None,
        )
        memory.append(
            task_id=event_task_id,
            question_id=None,
            actor="Tool",
            visibility="private",
            recipients=(agent,),
            kind="recall_result",
            payload={
                "query": str(arguments.get("query") or ""),
                "problem_id": str(arguments.get("problem_id") or "") or None,
                "notes": notes,
                "note": "Empty means no matching note; use remember to store one.",
            },
            turn=session.budget.turns_used,
        )
        return False, 0
    if action == "inspect_problem":
        if event_task_id is None:
            raise RuntimeError("pass problem_id or select a problem before inspect_problem")
        memory.append(
            task_id=event_task_id,
            question_id=None,
            actor="Tool",
            visibility="private",
            recipients=(agent,),
            kind="inspect_problem_result",
            payload=_inspect_problem_payload(
                task_by_id[event_task_id],
                session.task(event_task_id),
                memory,
                focus=str(arguments.get("focus") or ""),
            ),
            turn=session.budget.turns_used,
        )
        return False, 0
    if action == "triage_problem":
        assert event_task_id is not None
        priority = str(arguments["priority"])
        task, previous = session.set_triage(
            event_task_id,
            priority,  # type: ignore[arg-type]
            reason=str(arguments.get("reason") or ""),
            actor=agent,
            turn=session.budget.turns_used,
        )
        memory.append(
            task_id=event_task_id,
            question_id=None,
            actor=agent,
            visibility="public",
            kind="task_triaged",
            payload={
                "problem_id": event_task_id,
                "priority": priority,
                "previous_priority": previous,
                "reason": task.triage_reason,
            },
            turn=session.budget.turns_used,
        )
        return False, 0

    if action == "select_problem":
        task_id = str(arguments["problem_id"])
        if task_id not in task_by_id:
            raise ValueError(f"unknown problem: {task_id}")
        if work_task_ids is not None and task_id not in work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {agent} to work on {task_id}"
            )
        switched = active is not None and active.task_id != task_id
        if switched:
            memory.create_problem_digest(active.task_id, viewer=agent)
        session.select_task(task_id)
        return False, int(switched)
    if action == "speak":
        if (
            active is not None
            and active.versions
            and active.versions[-1].author == agent
            and active.versions[-1].evidence_refs
        ):
            memory.append(
                task_id=active.task_id,
                question_id=None,
                actor=agent,
                visibility="public",
                kind="local_run_report",
                payload={
                    "version_hash": active.versions[-1].version_hash,
                    "report": str(arguments["content"]),
                },
                turn=session.budget.turns_used,
            )
        return False, 0
    if action == "direct_message":
        return False, 0
    if action == "work":
        if active is None:
            raise RuntimeError("select a problem before work")
        if work_task_ids is not None and active.task_id not in work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {agent} to work on {active.task_id}"
            )
        if active.kind == "programming" and config.review_required:
            # The work event above retains the note in team memory. It must not
            # replace executable source or invalidate its exact-version review.
            return False, 0
        if config.review_required and _task_has_independent_approval(active):
            raise ValueError(
                "preserve the independently approved version unless a review rejects it"
            )
        content = str(arguments["content"])
        duplicate = active.find_duplicate_answer(content)
        if duplicate is not None:
            # Same draft already on the sheet: no new version, tell the author
            # where it is and what is still blank instead of failing silently.
            recorded_turn = next(
                (
                    event.turn
                    for event in memory.view(agent, task_id=active.task_id)
                    if event.kind == "work"
                    and isinstance(event.payload, dict)
                    and event.payload.get("content") == content
                ),
                None,
            )
            blank = [task.task_id for task in session.tasks if not task.versions]
            memory.append(
                task_id=active.task_id,
                question_id=None,
                actor="Contest_Control",
                visibility="private",
                recipients=(agent,),
                kind="work_duplicate",
                payload={
                    "version_hash": duplicate.version_hash,
                    "recorded_by": duplicate.author,
                    "recorded_turn": recorded_turn,
                    "is_latest": duplicate is active.versions[-1],
                    "blank_task_ids": blank,
                    "note": (
                        f"This draft is already recorded on {active.task_id}"
                        f" by {duplicate.author or 'a teammate'}"
                        + (f" at turn {recorded_turn}" if recorded_turn is not None else "")
                        + f"; {len(blank)} tasks still have no draft."
                    ),
                },
                turn=session.budget.turns_used,
            )
            return False, 0
        session.create_answer(content, author=agent)
        return False, 0
    if action == "request_review":
        if active is None or not active.versions:
            raise RuntimeError("create a candidate before review")
        if work_task_ids is not None and active.task_id not in work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {agent} to own {active.task_id}"
            )
        memory.append(
            task_id=active.task_id,
            question_id=None,
            actor=agent,
            visibility="public",
            kind="review_requested",
            payload={
                "version_hash": active.versions[-1].version_hash,
                "reviewer": arguments.get("reviewer"),
                "content": str(arguments["content"]),
            },
            turn=session.budget.turns_used,
        )
        return False, 0
    if action == "review_answer":
        task_id = str(arguments["problem_id"])
        if task_id not in task_by_id:
            raise ValueError(f"unknown problem: {task_id}")
        if review_task_ids is not None and task_id not in review_task_ids:
            raise ValueError(
                f"coach assignment does not route {task_id} review to {agent}"
            )
        decision = str(arguments["decision"])
        if decision not in {"approve", "reject"}:
            raise ValueError("review decision must be approve or reject")
        session.record_task_review(
            task_id,
            agent,
            str(arguments["content"]),
            decision=decision,  # type: ignore[arg-type]
            version_hash=str(arguments["version_hash"]),
        )
        return False, 0
    if action == "submit":
        if _is_answer_sheet_contest(manifest):
            required_ids = _required_answer_sheet_task_ids(manifest)
            required_tasks = [
                task for task in session.tasks if task.task_id in required_ids
            ]
            missing = [task for task in required_tasks if not task.versions]
            if missing:
                raise ValueError(
                    "cannot submit answer sheet while "
                    f"{len(missing)} tasks lack drafts"
                )
            if config.review_required:
                unreviewed = [
                    task
                    for task in required_tasks
                    if not _task_has_independent_approval(task)
                ]
                if unreviewed:
                    raise ValueError(
                        "cannot submit answer sheet while "
                        f"{len(unreviewed)} drafts lack independent approval"
                    )
            if config.final_review_required and not final_review_complete:
                raise ValueError(
                    "cannot submit answer sheet before final review completes"
                )
            for task in required_tasks:
                session.select_task(task.task_id)
                session.submit("SUBMITTED", score=0.0, valid=True)
            return True, 0
        if active is None:
            raise RuntimeError("select a problem before submit")
        if work_task_ids is not None and active.task_id not in work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {agent} to submit {active.task_id}"
            )
        if active.kind == "programming":
            raise ValueError("programming tasks must use submit_code")
        answer = str(arguments["answer"])
        if not active.versions or active.versions[-1].content != answer:
            session.create_answer(answer, author=agent)
        if config.review_required and not session.has_independent_approval():
            raise ValueError("strategic submission requires an independent approval")
        session.submit("SUBMITTED", score=0.0, valid=True)
        return _contest_complete(session), 0
    if action == "skip_problem":
        if active is None:
            raise RuntimeError("no active problem to skip")
        if work_task_ids is not None and active.task_id not in work_task_ids:
            raise ValueError(
                f"coach assignment does not allow {agent} to skip {active.task_id}"
            )
        previous_id = active.task_id
        memory.create_problem_digest(active.task_id, viewer=agent)
        session.skip_task()
        memory.append(
            task_id=previous_id,
            question_id=None,
            actor="Contest_Control",
            visibility="public",
            kind="problem_switched",
            payload={
                "from": previous_id,
                "to": None,
                "reason": str(arguments.get("reason") or "manual_skip"),
            },
            turn=session.budget.turns_used,
        )
        return False, 1
    if action == "finish_contest":
        if _is_answer_sheet_contest(manifest):
            raise ValueError(
                "math answer-sheet contests end only through final submit"
            )
        unfinished = [
            task
            for task in session.tasks
            if not (
                task.locked
                if task.kind == "programming"
                else task.latest_valid_submission is not None
            )
        ]
        if unfinished:
            raise ValueError(
                "cannot finish contest while "
                f"{len(unfinished)} tasks lack valid submissions"
            )
        if config.final_review_required and not final_review_complete:
            raise ValueError(
                "cannot finish contest before every task receives final approval"
            )
        return True, 0
    if action == "rest":
        return False, 0
    if active is None:
        raise RuntimeError("select a problem before using task tools")
    if work_task_ids is not None and active.task_id not in work_task_ids:
        raise ValueError(
            f"coach assignment does not allow {agent} to use task tools on "
            f"{active.task_id}"
        )

    if action == "submit_code":
        if config.review_required:
            if not active.versions:
                raise ValueError("strategic code submission requires a candidate")
            code = active.versions[-1].content
            arguments = {**arguments, "code": code}
            if not active.versions[-1].evidence_refs:
                raise ValueError(
                    "strategic code submission requires local run/test evidence"
                )
            if not session.has_independent_review():
                raise ValueError(
                    "strategic code submission requires an independent review"
                )
        elif config.features.leader_submits:
            if agent != config.leader:
                raise ValueError(f"only {config.leader} may submit code")
            if "code" in arguments:
                raise ValueError("the leader submits the latest recorded version; do not paste source")
            if not active.versions:
                raise ValueError("no recorded source version to submit")
            code = active.versions[-1].content
            arguments = {**arguments, "code": code}
        else:
            code = str(arguments["code"])
            if not active.versions or active.versions[-1].content != code:
                session.create_answer(code, author=agent)

    if (action == "execute_code" and active.kind == "programming"
            and config.review_required
            and not str(arguments.get("code") or "").strip()):
        raise ValueError("execute_code requires nonempty candidate source, not an empty placeholder")
    execution_cache_key = None
    if (action == "execute_code" and active.kind == "programming"
            and config.review_required):
        execution_cache_key = execution_key(task_by_id[active.task_id], arguments, task_action_executor)
        reused = failed_execution(memory.archival_snapshot()["events"], active.task_id, execution_cache_key)
        if reused is not None:
            memory.append(task_id=active.task_id, question_id=None, actor="Tool",
                          visibility="private", recipients=(agent,), kind="execute_code_result",
                          payload=reused, turn=session.budget.turns_used)
            return False, 0  # No executor call, source overwrite, or new evidence.
    result = task_action_executor(task_by_id[active.task_id], action, arguments)
    evidence_event = memory.append(
        task_id=active.task_id,
        question_id=None,
        actor="Tool",
        visibility="public" if action == "submit_code" else "private",
        recipients=(agent,) if action != "submit_code" else (),
        kind=f"{action}_result",
        payload=result,
        turn=session.budget.turns_used,
    )
    if action != "submit_code":
        if action == "execute_code":
            code = str(arguments["code"])
            latest = active.versions[-1] if active.versions else None
            # A local run only counts as evidence when the official samples pass
            # (or the task ships no samples and the run itself succeeded).
            sample_verdict = result.get("sample_verdict")
            counts_as_evidence = bool(result.get("valid", True)) and (
                sample_verdict is None or str(sample_verdict).upper() == "AC"
            )
            new_refs = (evidence_event.event_id,) if counts_as_evidence else ()
            if latest is None or latest.content != code:
                version = session.create_answer(
                    code,
                    author=agent,
                    evidence_refs=new_refs,
                )
            else:
                version = session.create_answer(
                    code,
                    author=latest.author or agent,
                    method_summary=latest.method_summary,
                    evidence_refs=(*latest.evidence_refs, *new_refs),
                )
            memory.append(
                task_id=active.task_id, question_id=None, actor="Tool",
                visibility="private", recipients=(agent,),
                kind="programming_source_recorded",
                payload={"version_hash": version.version_hash},
                turn=session.budget.turns_used,
            )
            if "sample_verdict" in result:
                memory.append(
                    task_id=active.task_id,
                    question_id=None,
                    actor="Judge",
                    visibility="public",
                    kind="sample_judge_result",
                    payload={
                        "version_hash": version.version_hash,
                        "author": version.author,
                        "sample_verdict": sample_verdict,
                        "sample_summary": result.get("sample_summary"),
                        "sample_cases": result.get("sample_cases") or [],
                        "evidence": counts_as_evidence,
                        "execution_key": execution_cache_key,
                        "execution_valid": bool(result.get("valid", True)),
                    },
                    turn=session.budget.turns_used,
                )
        return False, 0
    verdict = str(result.get("verdict") or "SUBMIT_FAILED")
    valid = bool(result.get("valid", True))
    session.submit(verdict, valid=valid)
    if valid and verdict.upper() != "AC":
        memory.append(
            task_id=active.task_id,
            question_id=None,
            actor="Judge",
            visibility="public",
            kind="reopen",
            payload={
                "verdict": verdict,
                "version_hash": active.versions[-1].version_hash,
            },
            turn=session.budget.turns_used,
        )
    if valid and verdict.upper() not in {"AC", "SUBMIT_FAILED", "PENDING"}:
        penalty = float(
            task_by_id[active.task_id]
            .benchmark.get("wrong_submission_penalty_minutes", 20)
        )
        session.add_penalty(penalty)
    if active.state is TaskState.BLOCKED:
        previous_id = active.task_id
        memory.create_problem_digest(active.task_id, viewer=agent)
        session.skip_task()
        next_task = _next_task(session, strategic_policy)
        if next_task is not None:
            session.select_task(next_task.task_id)
        memory.append(
            task_id=previous_id,
            question_id=None,
            actor="Contest_Control",
            visibility="public",
            kind="problem_switched",
            payload={
                "from": previous_id,
                "to": next_task.task_id if next_task else None,
                "reason": "three_consecutive_non_ac",
            },
            turn=session.budget.turns_used,
        )
        return False, 1
    return _contest_complete(session), 0


def _collect_programming_deadline(
    manifest: ContestManifest,
    session: ContestSession,
    memory: ContestMemory,
    executor: TaskActionExecutor,
    persist: Callable[[], None],
) -> None:
    """One unattempted candidate per unsolved programming task, without LLM turns.

    Persist intent before external I/O. An interrupted/uncertain attempt is not
    retried automatically on resume, since the judge may already have received it.
    """
    events = memory.archival_snapshot()["events"]
    if not any(e["kind"] == "programming_deadline_started" for e in events):
        memory.append(
            task_id=None, question_id=None, actor="Contest_Control", visibility="public",
            kind="programming_deadline_started",
            payload={"accepted_before": [t.task_id for t in session.tasks if t.kind == "programming" and t.locked],
                     "officially_submitted_before": [t.task_id for t in session.tasks if t.kind == "programming" and t.latest_valid_submission]},
            turn=session.budget.turns_used,
        )
        persist()
    attempted = {e["task_id"] for e in events if e["kind"] == "programming_deadline_submit_started"}
    no_source = {e["task_id"] for e in events if e["kind"] == "programming_deadline_no_source"}
    task_by_id = {t.task_id: t for t in manifest.tasks}
    previous_id = session.active_task.task_id if session.active_task else None
    for task in session.tasks:
        if task.kind != "programming" or task.locked or task.task_id in attempted:
            continue
        source, selection_reason = deadline_candidate(task, events)
        if source is None:
            if selection_reason == "no_recorded_nonempty_source" and task.task_id not in no_source:
                memory.append(
                    task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
                    kind="programming_deadline_no_source", payload={"reason": "no_recorded_nonempty_source"},
                    turn=session.budget.turns_used,
                )
            continue  # Notes and empty drafts are never submitted as code.
        if task.state is TaskState.BLOCKED and session.budget.turns_used < (task.blocked_until_turn or 0):
            memory.append(task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
                          kind="programming_deadline_skipped", payload={"reason": "active_cooldown"},
                          turn=session.budget.turns_used)
            continue
        selected_version_hash = source.version_hash
        session.select_task(task.task_id)
        if source is not task.versions[-1]:
            source = session.create_answer(source.content, author=source.author,
                                           method_summary=source.method_summary, evidence_refs=source.evidence_refs)
        memory.append(
            task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
            kind="programming_deadline_submit_started",
            payload={"version_hash": source.version_hash, "selected_version_hash": selected_version_hash,
                     "source_identity": source_identity(source.content), "selection_reason": selection_reason,
                     "review_gate_waived": True, "sample_gate_waived": True},
            turn=session.budget.turns_used,
        )
        persist()
        try:
            deadline_executor = getattr(executor, "submit_at_deadline", None)
            result = (deadline_executor(task_by_id[task.task_id], source.content)
                      if deadline_executor is not None else
                      executor(task_by_id[task.task_id], "submit_code", {"code": source.content}))
        except Exception as exc:
            result = {"valid": False, "verdict": "SUBMIT_FAILED", "error": str(exc)}
        verdict = str(result.get("verdict") or "SUBMIT_FAILED").upper()
        valid = bool(result.get("valid", False)) and verdict not in {
            "SUBMIT_FAILED", "PENDING", "CHALLENGE", "NEEDS_HUMAN", "JUDGE_ERROR"
        } and not verdict.startswith("SAMPLE_")
        session.submit(verdict, valid=valid)
        if valid and not session.submission_policy.is_accepted(verdict):
            session.add_penalty(float(task_by_id[task.task_id].benchmark.get("wrong_submission_penalty_minutes", 20)))
        memory.append(
            task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
            kind="programming_deadline_submit_result",
            payload={**result, "valid": valid, "verdict": verdict, "version_hash": source.version_hash},
            turn=session.budget.turns_used,
        )
        persist()
    if previous_id is not None and not session.task(previous_id).locked and session.task(previous_id).state is not TaskState.BLOCKED:
        session.select_task(previous_id)
    elif session.active_task is not None:
        session.skip_task()
    persist()


def _run_contest_engine(
    manifest: ContestManifest,
    query_llm_fn: QueryFn,
    config: ContestRunConfig,
    *,
    action_request_fn: RequestFn | None = None,
    action_transport: Literal["native", "emulated", "prompt_json"] | None = None,
    coach_query_fn: QueryFn | None = None,
    task_action_executor: TaskActionExecutor | None = None,
    session_checkpoint: dict[str, Any] | None = None,
    memory_checkpoint: str | None = None,
    checkpoint_callback: CheckpointCallback | None = None,
) -> dict[str, Any]:
    """Shared contest state machine; variant modules own the public interfaces."""
    wall_t0 = time.perf_counter()
    segment_started_at = datetime.now(timezone.utc).isoformat()
    if config.programming_deadline_submit and session_checkpoint and session_checkpoint.get("final_summary") is not None:
        raise ValueError("Cannot force-submit from a finalized checkpoint; start a fresh run")
    session = (
        ContestSession.from_checkpoint(session_checkpoint)
        if session_checkpoint is not None
        else ContestSession(
            [
                TaskUnit(
                    task.task_id,
                    kind="programming" if task.programming else "non_programming",
                )
                for task in manifest.tasks
            ],
            ContestBudgetState(
                max_turns=config.max_turns,
                max_api_calls=config.max_api_calls,
                max_tokens=config.max_tokens,
                max_simulated_minutes=config.max_simulated_minutes,
            ),
            SubmissionPolicy(
                consecutive_non_ac_limit=(
                    config.consecutive_non_ac_limit
                    if config.features.submission_cooldown
                    else (
                        (config.max_api_calls or config.max_turns * config.team_size)
                        + 1
                    )
                ),
                cooldown_turns=config.cooldown_turns,
            ),
        )
    )
    if not session.budget.wall_started_at:
        session.budget.wall_started_at = segment_started_at
    prior_wall_seconds = float(session.budget.wall_seconds_used or 0.0)

    def _persist_checkpoint() -> None:
        session.budget.wall_seconds_used = prior_wall_seconds + (
            time.perf_counter() - wall_t0
        )
        if checkpoint_callback:
            checkpoint_callback(session.checkpoint(), memory.to_checkpoint_json())

    if {task.task_id for task in session.tasks} != {
        task.task_id for task in manifest.tasks
    }:
        raise ValueError("session checkpoint task set does not match manifest")
    memory = (
        ContestMemory.from_checkpoint_json(
            memory_checkpoint,
            expected_run_id=f"{manifest.session_id}:{config.system_variant}",
            expected_session_id=manifest.session_id,
            expected_competition_id=manifest.competition_id,
        )
        if memory_checkpoint is not None
        else ContestMemory(
            run_id=f"{manifest.session_id}:{config.system_variant}",
            session_id=manifest.session_id,
            competition_id=manifest.competition_id,
        )
    )
    actions = _resolved_actions(manifest, config)
    action_transport_log: list[dict[str, Any]] = []
    transport_api_calls = 0
    transport_retries = 0
    transport_failures = 0
    executor = task_action_executor or _default_executor
    strategic_policy = StrategicPolicy(stall_turns=config.stall_turns)
    archived_events = memory.archival_snapshot()["events"]
    final_review_started = any(
        event["kind"] == "final_review_started" for event in archived_events
    )
    final_review_completed = any(
        event["kind"] == "final_review_completed" for event in archived_events
    )
    final_review_approvals = {
        str(event["task_id"]): str(event["payload"]["version_hash"])
        for event in archived_events
        if event["kind"] == "final_review_approved"
        and event.get("task_id")
        and event["payload"].get("version_hash")
    }
    coach_event = next(
        (
            event
            for event in reversed(archived_events)
            if event["kind"] == "precontest_coach_guidance"
        ),
        None,
    )
    coach_plan: dict[str, Any] = (
        dict(coach_event["payload"].get("plan") or {})
        if coach_event is not None
        else {}
    )
    coach_guidance = (
        str(coach_event["payload"].get("guidance") or "")
        if coach_event is not None
        else ""
    )
    coach_budget_exhausted = False
    # Who writes the opening plan: the exiting Coach seat, or the leader who
    # then stays in the contest as an ordinary (submitting) contestant.
    planner: str | None = None
    plan_query: QueryFn | None = None
    if config.features.coach == "precontest" and coach_query_fn is not None:
        planner, plan_query = "Pre_Contest_Coach", coach_query_fn
    elif config.features.coach == "leader":
        planner, plan_query = config.leader, query_llm_fn
    if planner is not None and plan_query is not None and not coach_guidance:
        try:
            session.consume_budget(api_calls=1)
        except BudgetExceededError:
            coach_budget_exhausted = True
        else:
            coach_system, coach_user = _precontest_coach_prompts(manifest, config)
            coach_response = plan_query(coach_system, coach_user)
            coach_tokens = estimate_tokens(coach_response)
            remaining_tokens = (
                None
                if session.budget.max_tokens is None
                else max(
                    0,
                    session.budget.max_tokens - session.budget.tokens_used,
                )
            )
            charged_tokens = (
                coach_tokens
                if remaining_tokens is None
                else min(coach_tokens, remaining_tokens)
            )
            session.consume_budget(tokens=charged_tokens)
            coach_budget_exhausted = charged_tokens < coach_tokens
            coach_plan = _normalize_coach_plan(coach_response, manifest, config)
            if config.leader is not None:
                # The leader may touch every problem; workers keep their lists.
                # No review workflow: review routes would only pull workers
                # onto problems they cannot act on.
                coach_plan["work_assignments"][config.leader] = [
                    task.task_id for task in manifest.tasks
                ]
                if not config.review_required:
                    coach_plan["review_assignments"] = {
                        agent: [] for agent in coach_plan["review_assignments"]
                    }
            coach_guidance = json.dumps(coach_plan, ensure_ascii=False, indent=2)
            memory.append(
                task_id=None,
                question_id=None,
                actor=planner,
                visibility="public",
                kind="precontest_coach_guidance",
                payload={"guidance": coach_guidance, "plan": coach_plan, "author": planner},
                turn=session.budget.turns_used,
            )
            for index in range(1, config.team_size + 1):
                agent = f"Agent_{index}"
                memory.append(
                    task_id=None,
                    question_id=None,
                    actor=planner,
                    visibility="private",
                    recipients=(agent,),
                    kind="coach_personal_assignment",
                    payload={
                        "agent": agent,
                        "work_tasks": list(
                            coach_plan["work_assignments"].get(agent, [])
                        ),
                        "review_tasks": list(
                            coach_plan["review_assignments"].get(agent, [])
                        ),
                        "summary": coach_plan["summary"],
                        "switch_conditions": coach_plan["switch_conditions"],
                        "final_check": coach_plan["final_check"],
                    },
                    turn=session.budget.turns_used,
                )
            _persist_checkpoint()

    personal_assignments: dict[str, dict[str, Any]] = {}
    if coach_plan:
        order = list(coach_plan.get("task_order") or [])
        work_by_agent = coach_plan.get("work_assignments") or {}
        review_by_agent = coach_plan.get("review_assignments") or {}
        for index in range(1, config.team_size + 1):
            agent = f"Agent_{index}"
            assigned_work = list(work_by_agent.get(agent, []))
            ordered_work = [
                task_id for task_id in order if task_id in assigned_work
            ] + [
                task_id for task_id in assigned_work if task_id not in order
            ]
            personal_assignments[agent] = {
                "agent": agent,
                "work_tasks": ordered_work,
                "review_tasks": list(review_by_agent.get(agent, [])),
                "summary": str(coach_plan.get("summary") or ""),
                "switch_conditions": list(
                    coach_plan.get("switch_conditions") or []
                ),
                "final_check": list(coach_plan.get("final_check") or []),
            }
        # Leader reassignments are ordinary public action events; replaying
        # them over the opening plan makes the table resume-safe.
        for event in archived_events:
            if event["kind"] == "assign_problem" and event["actor"] == config.leader:
                _set_work_assignment(
                    personal_assignments,
                    str(event["payload"]["agent"]),
                    [str(task_id) for task_id in event["payload"]["problem_ids"]],
                )

    def final_review_pending() -> list[TaskUnit]:
        required_ids = _required_answer_sheet_task_ids(manifest)
        return [
            task
            for task in session.tasks
            if task.kind != "programming"
            and (
                not _is_answer_sheet_contest(manifest)
                or task.task_id in required_ids
            )
            and task.versions
            and final_review_approvals.get(task.task_id)
            != task.versions[-1].version_hash
        ]

    def answer_sheet_ready_for_final_review() -> bool:
        required_ids = _required_answer_sheet_task_ids(manifest)
        return _is_answer_sheet_contest(manifest) and all(
            task.versions
            and (not config.review_required or _task_has_independent_approval(task))
            for task in session.tasks
            if task.task_id in required_ids
        )

    finished = coach_budget_exhausted
    switches = 0
    stalled_turns = 0
    last_progress_turn: dict[str, int] = {}
    programming_progress = ProgrammingProgress(memory, stall_actions=config.stall_turns)
    deadline_submission_used = False
    baseline_mechanical_switches = 0

    for turn_index in range(config.max_turns):
        if finished:
            break
        switches_at_turn_start = switches
        progress_at_turn_start = sum(
            len(task.versions) + len(task.submissions) for task in session.tasks
        )
        try:
            session.consume_budget(
                turns=1,
                simulated_minutes=config.minutes_per_turn,
            )
        except BudgetExceededError:
            break
        if (
            config.features.submission_cooldown
            and session.active_task is None
            and all(task.versions or task.submissions for task in session.tasks)
        ):
            revisit = _next_task(session, strategic_policy)
            if revisit is not None:
                session.revisit_task(revisit.task_id)
                switches += 1
                memory.append(
                    task_id=revisit.task_id,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="problem_switched",
                    payload={
                        "from": None,
                        "to": revisit.task_id,
                        "reason": "cooldown_revisit",
                    },
                    turn=session.budget.turns_used,
                )
        _record_scoreboard(memory, session)
        start = config.start_seat % config.team_size
        agents = [
            f"Agent_{(start + offset) % config.team_size + 1}"
            for offset in range(config.team_size)
        ]
        if config.leader is not None:
            # The leader opens every round; workers keep the rotating order.
            agents.remove(config.leader)
            agents.insert(0, config.leader)
        for agent_index, agent in enumerate(agents):
            if finished:
                break
            # Both variants retain their last action for useful work. The
            # environment collects pending drafts after the shared loop ends.
            personal_assignment = personal_assignments.get(agent)
            rescue_task_ids = {
                task.task_id
                for task in session.tasks
                if not task.locked
                and task.versions
                and not _task_has_independent_approval(task)
                and _rejected_version_count(task) >= 2
            }
            work_task_ids = (
                set(personal_assignment["work_tasks"]) | rescue_task_ids
                if personal_assignment is not None
                else None
            )
            review_task_ids = (
                set(personal_assignment["review_tasks"]) | rescue_task_ids
                if personal_assignment is not None
                else None
            )
            scheduled_work_ids = (
                [
                    *sorted(rescue_task_ids),
                    *[
                        task_id
                        for task_id in personal_assignment["work_tasks"]
                        if task_id not in rescue_task_ids
                    ],
                ]
                if personal_assignment is not None
                else []
            )
            if config.review_required:
                # Only reorder programming slots; mixed/non-programming tasks
                # retain their original assignment order and workflow.
                code_ids = programming_progress.ordered_tasks(agent, [
                    task_id for task_id in scheduled_work_ids
                    if session.task(task_id).kind == "programming"
                ])
                ordered_code = iter(code_ids)
                scheduled_work_ids = [
                    next(ordered_code) if session.task(task_id).kind == "programming" else task_id
                    for task_id in scheduled_work_ids
                ]
            if (
                personal_assignment is not None
                and not final_review_started
            ):
                scheduled = _scheduled_agent_task(
                    session,
                    agent=agent,
                    work_task_ids=scheduled_work_ids,
                    review_task_ids=review_task_ids or set(),
                    reported_version_hashes=_reported_version_hashes(memory),
                )
                if scheduled is not None and (
                    session.active_task is None
                    or session.active_task.task_id != scheduled.task_id
                ):
                    previous_id = (
                        session.active_task.task_id
                        if session.active_task is not None
                        else None
                    )
                    session.select_task(scheduled.task_id)
                    switches += int(previous_id is not None)
                    memory.append(
                        task_id=scheduled.task_id,
                        question_id=None,
                        actor="Contest_Scheduler",
                        visibility="private",
                        recipients=(agent,),
                        kind="assignment_task_scheduled",
                        payload={
                            "from": previous_id,
                            "to": scheduled.task_id,
                        },
                        turn=session.budget.turns_used,
                    )
            if final_review_started and not final_review_completed:
                pending = final_review_pending()
                if not pending:
                    memory.append(
                        task_id=None,
                        question_id=None,
                        actor="Contest_Control",
                        visibility="public",
                        kind="final_review_completed",
                        payload={"approved_tasks": len(final_review_approvals)},
                        turn=session.budget.turns_used,
                    )
                    final_review_completed = True
                    if not _is_answer_sheet_contest(manifest):
                        finished = True
                        break
                else:
                    eligible = [
                        task
                        for task in pending
                        if not task.versions[-1].author
                        or task.versions[-1].author != agent
                        if (
                            review_task_ids is None
                            or task.task_id in review_task_ids
                        )
                    ]
                    if eligible and (
                        session.active_task is None
                        or session.active_task.task_id != eligible[0].task_id
                    ):
                        session.select_task(eligible[0].task_id)
            programming_source_required = bool(
                config.review_required
                and session.active_task is not None
                and _needs_programming_source(session.active_task)
                and (work_task_ids is None or session.active_task.task_id in work_task_ids)
                and programming_progress.source_required(agent, session.active_task.task_id)
            )
            available_actions = _actions_for_agent(
                actions,
                session,
                config,
                agent,
                answer_sheet_contest=_is_answer_sheet_contest(manifest),
                required_answer_task_ids=_required_answer_sheet_task_ids(manifest),
                reported_version_hashes=_reported_version_hashes(memory),
                work_task_ids=work_task_ids,
                review_task_ids=review_task_ids,
                answer_sheet_submit_ready=(
                    final_review_completed
                    and answer_sheet_ready_for_final_review()
                ),
                programming_source_required=programming_source_required,
                review_targets=(
                    [
                        {
                            "problem_id": task.task_id,
                            "version_hash": task.versions[-1].version_hash,
                            "author": task.versions[-1].author,
                        }
                        for task in final_review_pending()
                        if task.versions[-1].author != agent
                        and (
                            review_task_ids is None
                            or task.task_id in review_task_ids
                        )
                    ]
                    if final_review_started and not final_review_completed
                    else None
                ),
            )
            programming_source_required = programming_source_required and (
                {spec.name for spec in available_actions} == {"execute_code"}
            )
            function_tools = tuple(render_function_tools(available_actions))
            try:
                session.consume_budget(api_calls=1)
            except BudgetExceededError:
                finished = True
                break
            if programming_source_required:
                memory.append(
                    task_id=session.active_task.task_id, question_id=None,
                    actor="Contest_Control", visibility="private", recipients=(agent,),
                    kind="programming_source_required",
                    payload={"agent": agent, "note_action_limit": 2},
                    turn=session.budget.turns_used,
                )
            system_prompt = _system_prompt(
                config,
                agent,
                available_actions,
                native_actions=action_request_fn is not None,
                answer_sheet_contest=_is_answer_sheet_contest(manifest),
                task_family=manifest.task_family,
                coach_guidance=coach_guidance,
            )
            user_prompt = _user_prompt(
                manifest,
                session,
                memory,
                config,
                agent,
                final_review_phase=final_review_started
                and not final_review_completed,
                personal_assignment=personal_assignment,
                programming_source_required=programming_source_required,
            )
            if action_request_fn is not None:
                max_transport_attempts = (
                    None
                    if session.budget.max_api_calls is None
                    else 1
                    + max(
                        0,
                        session.budget.max_api_calls
                        - session.budget.api_calls_used,
                    )
                )
                response = action_request_fn(
                    LLMRequest(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        purpose="contest_action",
                        metadata={
                            "agent": agent,
                            "session_id": manifest.session_id,
                            "task_id": (
                                session.active_task.task_id
                                if session.active_task
                                else None
                            ),
                            "max_transport_attempts": max_transport_attempts,
                        },
                        tools=function_tools,
                        tool_choice="required",
                    )
                )
                reported_api_calls = max(
                    1,
                    int(response.usage.get("api_calls") or 1),
                )
                transport_api_calls += reported_api_calls
                transport_retries += max(
                    0,
                    int(response.usage.get("tool_retries") or 0),
                )
                transport_failures += int(
                    not response.tool_calls
                    and bool(response.usage.get("tool_error"))
                )
                if reported_api_calls > 1:
                    try:
                        session.consume_budget(api_calls=reported_api_calls - 1)
                    except BudgetExceededError:
                        finished = True
                        break
                action_transport_log.extend(
                    {
                        "turn": session.budget.turns_used,
                        "agent": agent,
                        "call_id": call.call_id,
                        "name": call.name,
                        "arguments": call.arguments,
                        "executed": index == 0,
                    }
                    for index, call in enumerate(response.tool_calls)
                )
                serialized_calls = json.dumps(
                    [
                        {
                            "name": call.name,
                            "arguments": call.arguments,
                        }
                        for call in response.tool_calls
                    ],
                    ensure_ascii=False,
                )
                token_count = int(
                    response.usage.get("output_tokens")
                    or response.usage.get("completion_tokens")
                    or estimate_tokens(serialized_calls or response.text)
                )
            else:
                response = query_llm_fn(system_prompt, user_prompt)
                token_count = estimate_tokens(response)
            remaining_tokens = (
                None
                if session.budget.max_tokens is None
                else max(
                    0,
                    session.budget.max_tokens - session.budget.tokens_used,
                )
            )
            charged_tokens = (
                token_count
                if remaining_tokens is None
                else min(token_count, remaining_tokens)
            )
            session.consume_budget(tokens=charged_tokens)
            if charged_tokens < token_count:
                finished = True
                break
            if action_request_fn is not None:
                if not response.tool_calls:
                    action, arguments, error = (
                        None,
                        {},
                        "response must contain at least one native function call",
                    )
                else:
                    call = response.tool_calls[0]
                    if len(response.tool_calls) > 1:
                        memory.append(
                            task_id=(
                                session.active_task.task_id
                                if session.active_task
                                else None
                            ),
                            question_id=None,
                            actor="Contest_Control",
                            visibility="private",
                            recipients=(agent,),
                            kind="extra_function_calls_ignored",
                            payload={
                                "executed_call_id": call.call_id,
                                "ignored_call_ids": [
                                    extra.call_id
                                    for extra in response.tool_calls[1:]
                                ],
                            },
                            turn=session.budget.turns_used,
                        )
                    action, arguments, error = validate_action_invocation(
                        call.name,
                        call.arguments,
                        available_actions,
                    )
            else:
                action, arguments, error = parse_typed_action(
                    response, available_actions
                )
            if error:
                _append_action_error(memory, session, agent, error)
                continue
            assert action is not None
            acted_task = session.active_task
            before_versions = len(acted_task.versions) if acted_task else 0
            before_source = acted_task.versions[-1] if acted_task and acted_task.versions else None
            before_events = len(memory.archival_snapshot()["events"])
            try:
                action_finished, switch_delta = _apply_action(
                    action=action,
                    arguments=arguments,
                    agent=agent,
                    manifest=manifest,
                    session=session,
                    memory=memory,
                    config=config,
                    strategic_policy=strategic_policy,
                    task_action_executor=executor,
                    work_task_ids=work_task_ids,
                    review_task_ids=review_task_ids,
                    final_review_complete=final_review_completed,
                    personal_assignments=personal_assignments,
                )
                switches += switch_delta
            except (KeyError, RuntimeError, ValueError) as exc:
                _append_action_error(memory, session, agent, str(exc))
                _persist_checkpoint()
                continue
            if (
                final_review_started
                and not final_review_completed
                and action == "review_answer"
            ):
                reviewed = session.task(str(arguments["problem_id"]))
                if reviewed is not None and reviewed.reviews:
                    review = reviewed.reviews[-1]
                    review_kind = (
                        "final_review_approved"
                        if review.decision == "approve"
                        else "final_review_rejected"
                    )
                    memory.append(
                        task_id=reviewed.task_id,
                        question_id=None,
                        actor=agent,
                        visibility="public",
                        kind=review_kind,
                        payload={
                            "version_hash": review.version_hash,
                            "body": review.body,
                        },
                        turn=session.budget.turns_used,
                    )
                    if review.decision == "approve":
                        final_review_approvals[reviewed.task_id] = review.version_hash
                    else:
                        final_review_approvals.pop(reviewed.task_id, None)
            if (
                config.final_review_required
                and not final_review_started
                and any(task.kind != "programming" for task in session.tasks)
                and (
                    answer_sheet_ready_for_final_review()
                    or action_finished
                )
            ):
                final_review_started = True
                action_finished = False
                memory.append(
                    task_id=None,
                    question_id=None,
                    actor="Pre_Contest_Coach",
                    visibility="public",
                    kind="final_review_started",
                    payload={
                        "reason": "Initial answer sheet complete; begin reserved final audit."
                    },
                    turn=session.budget.turns_used,
                )
            finished = action_finished
            created_version = bool(
                acted_task is not None and len(acted_task.versions) > before_versions
            )
            programming_visit = bool(
                config.review_required
                and acted_task is not None and acted_task.kind == "programming"
                and (work_task_ids is None or acted_task.task_id in work_task_ids)
                and (
                    action in {"work", "execute_code", "rest", "speak", "submit_code",
                               "select_problem", "skip_problem", "direct_message"}
                    or action in DESK_ACTION_NAMES
                )
            )
            if programming_visit:
                new_events = memory.archival_snapshot()["events"][before_events:]
                latest = acted_task.versions[-1] if acted_task.versions else None
                sample_events = [e for e in new_events if e["kind"] == "sample_judge_result"]
                infrastructure_error = any(
                    e["payload"].get("sample_verdict") == "JUDGE_ERROR"
                    for e in sample_events
                ) or any(
                    e["kind"] == "execute_code_result" and not e["payload"].get("valid", True)
                    for e in new_events
                )
                progressed = bool(
                    latest and latest.evidence_refs and (
                        before_source is None or not before_source.evidence_refs
                        or latest.content != before_source.content
                    )
                ) or any(
                    e["kind"] == "local_run_report"
                    or (e["kind"] == "submit_code_result" and e["payload"].get("valid"))
                    for e in new_events
                )
                if not infrastructure_error:
                    yielded = programming_progress.record(
                        agent, acted_task.task_id, turn=session.budget.turns_used,
                        progressed=progressed,
                        source_attempted=action == "execute_code" and not any(
                            e["kind"] == "execute_code_result" and e["payload"].get("execution_reused")
                            for e in new_events
                        ),
                    )
                    if yielded and personal_assignment is None and not (
                        latest and latest.evidence_refs
                    ):
                        next_task = _next_task(session, strategic_policy, exclude_task_id=acted_task.task_id)
                        if next_task is not None:
                            session.skip_task()
                            session.select_task(next_task.task_id)
                            switches += 1
                if progressed:
                    last_progress_turn[acted_task.task_id] = session.budget.turns_used
            elif created_version and acted_task is not None:
                last_progress_turn[acted_task.task_id] = session.budget.turns_used
            if (
                not finished
                and config.features.mechanical_switch
                and _is_answer_sheet_contest(manifest)
                and action == "work"
                and created_version
                and acted_task is not None
            ):
                next_unseen = next(
                    iter(
                        sorted(
                            (
                                task
                                for task in session.tasks
                                if task.task_id != acted_task.task_id
                                and not task.locked
                                and not task.versions
                                and not task.submissions
                            ),
                            key=lambda task: task.priority_rank,
                        )
                    ),
                    None,
                )
                if next_unseen is not None:
                    memory.create_problem_digest(acted_task.task_id, viewer=agent)
                    session.skip_task()
                    session.select_task(next_unseen.task_id)
                    switches += 1
                    baseline_mechanical_switches += 1
                    memory.append(
                        task_id=next_unseen.task_id,
                        question_id=None,
                        actor="Contest_Control",
                        visibility="public",
                        kind="baseline_next_unseen_scheduled",
                        payload={
                            "from": acted_task.task_id,
                            "to": next_unseen.task_id,
                            "reason": "draft_recorded",
                        },
                        turn=session.budget.turns_used,
                    )
            if (
                config.features.coach == "none"
                and action == "select_problem"
                and session.active_task is not None
            ):
                last_progress_turn.setdefault(
                    session.active_task.task_id,
                    session.budget.turns_used,
                )
            _persist_checkpoint()

        active = session.active_task
        if (
            not finished
            and active is not None
            and not (active.kind == "programming" and config.review_required)
            and switches == switches_at_turn_start
            and strategic_policy.switch_reason(
                active,
                current_turn=session.budget.turns_used,
                last_progress_turn=last_progress_turn.get(active.task_id, 0),
            )
            == "stalled_turns"
        ):
            previous_id = active.task_id
            next_task = _next_task(
                session,
                strategic_policy,
                exclude_task_id=previous_id,
            )
            if next_task is not None:
                memory.create_problem_digest(active.task_id, viewer="Agent_1")
                session.skip_task()
                session.select_task(next_task.task_id)
                switches += 1
                if config.features.mechanical_switch:
                    baseline_mechanical_switches += 1
                memory.append(
                    task_id=previous_id,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="problem_switched",
                    payload={
                        "from": previous_id,
                        "to": next_task.task_id,
                        "reason": "stalled_turns",
                    },
                    turn=session.budget.turns_used,
                )
        _persist_checkpoint()
        progress_at_turn_end = sum(
            len(task.versions) + len(task.submissions) for task in session.tasks
        )
        if progress_at_turn_end == progress_at_turn_start and switches == switches_at_turn_start:
            stalled_turns += 1

    if config.programming_deadline_submit and any(t.programming for t in manifest.tasks):
        _collect_programming_deadline(manifest, session, memory, executor, _persist_checkpoint)

    # Deadline collection is an environment policy shared by both variants.
    if any(task.kind != "programming" for task in session.tasks):
        deadline_active_task_id = (
            session.active_task.task_id if session.active_task is not None else None
        )
        deadline_task_ids = []
        for task in session.tasks:
            if (
                task.kind == "programming"
                or not task.versions
                or task.latest_valid_submission is not None
            ):
                continue
            session.select_task(task.task_id)
            session.submit("SUBMITTED", score=0.0, valid=True)
            deadline_task_ids.append(task.task_id)
        if deadline_task_ids:
            deadline_submission_used = True
            memory.append(
                task_id=None,
                question_id=None,
                actor="Contest_Control",
                visibility="public",
                kind="deadline_drafts_submitted",
                payload={
                    "submitted_task_ids": deadline_task_ids,
                    "review_gate_waived": config.review_required,
                    "final_review_gate_waived": config.final_review_required,
                },
                turn=session.budget.turns_used,
            )
            if deadline_active_task_id is None:
                session.skip_task()
            else:
                session.select_task(deadline_active_task_id)
            _persist_checkpoint()

    deadline_events = memory.archival_snapshot()["events"]
    deadline_attempts = [e for e in deadline_events if e["kind"] == "programming_deadline_submit_started"]
    deadline_results = [e for e in deadline_events if e["kind"] == "programming_deadline_submit_result"]
    deadline_accepted = [e["task_id"] for e in deadline_results if e["payload"].get("valid") and e["payload"].get("verdict") == "AC"]
    deadline_before = next((e["payload"] for e in deadline_events if e["kind"] == "programming_deadline_started"), {})
    deadline_submission_used = deadline_submission_used or bool(deadline_attempts)
    summary = session.finalize()
    submissions = {
        task.task_id: (
            task.latest_submitted_answer.content
            if task.latest_submitted_answer is not None
            else ""
        )
        for task in session.tasks
    }
    submitted = [task for task in session.tasks if task.latest_valid_submission]
    reviewed = [
        task
        for task in submitted
        if any(
            not review.stale
            and review.decision == "approve"
            and task.latest_submitted_answer is not None
            and review.version_hash == task.latest_submitted_answer.version_hash
            and review.reviewer != task.latest_submitted_answer.author
            for review in task.reviews
        )
    ]
    if _is_answer_sheet_contest(manifest):
        required_ids = _required_answer_sheet_task_ids(manifest)
        final_reviewable = [
            task
            for task in session.tasks
            if task.task_id in required_ids and task.versions
        ]
    else:
        final_reviewable = [
            task
            for task in submitted
            if task.kind != "programming"
            and task.latest_submitted_answer is not None
        ]
    final_reviewed = [
        task
        for task in final_reviewable
        if final_review_approvals.get(task.task_id)
        == task.versions[-1].version_hash
    ]
    final_review_coverage = (
        len(final_reviewed) / len(final_reviewable) if final_reviewable else 0.0
    )
    final_review_status = (
        "completed"
        if final_review_started
        and (not final_reviewable or len(final_reviewed) == len(final_reviewable))
        else "in_progress"
        if final_review_started
        else "not_started"
    )
    active_agent_rate, action_balance = _participation_metrics(
        memory, manifest, config.team_size
    )
    attempts_to_ac = {
        task.task_id: next(
            (
                index
                for index, submission in enumerate(task.submissions, start=1)
                if submission.verdict == "AC"
            ),
            None,
        )
        for task in session.tasks
        if task.kind == "programming"
    }
    all_events = memory.archival_snapshot()["events"]
    event_kind_counts: dict[str, int] = {}
    for event in all_events:
        event_kind_counts[event["kind"]] = event_kind_counts.get(event["kind"], 0) + 1
    desk_diagnostics = {
        "inspect_count": event_kind_counts.get("inspect_problem", 0),
        "notes_recorded": event_kind_counts.get("note", 0),
        "notes_shared": event_kind_counts.get("note_shared", 0),
        "recall_count": event_kind_counts.get("recall", 0),
        "triage_changes": event_kind_counts.get("task_triaged", 0),
        "items_hopeless": sum(task.hopeless for task in session.tasks),
        "repeat_draft_attempts": event_kind_counts.get("work_duplicate", 0),
    }
    segment_seconds = time.perf_counter() - wall_t0
    ended_at = datetime.now(timezone.utc).isoformat()
    session.budget.wall_seconds_used = prior_wall_seconds + segment_seconds
    timing = {
        "started_at": session.budget.wall_started_at,
        "ended_at": ended_at,
        "elapsed_seconds": session.budget.wall_seconds_used,
        "segment_seconds": segment_seconds,
        "segment_started_at": segment_started_at,
    }
    return {
        "session_id": manifest.session_id,
        "competition_id": manifest.competition_id,
        "system_variant": config.system_variant,
        "action_calling": action_transport
        or ("native" if action_request_fn is not None else "prompt_json"),
        "manifest": {
            "session_id": manifest.session_id,
            "competition_id": manifest.competition_id,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "parent_problem_id": task.parent_problem_id,
                    "question_id": task.question_id,
                    "task_type": task.task_type,
                    "max_score": task.max_score,
                    "programming": task.programming,
                }
                for task in manifest.tasks
            ],
        },
        "action_names": sorted(spec.name for spec in actions),
        "action_transport_log": action_transport_log,
        "precontest_coach_guidance": coach_guidance,
        "precontest_coach_plan": coach_plan,
        "active_task_id": session.active_task.task_id if session.active_task else None,
        "tasks": summary["tasks"],
        "submissions": submissions,
        "shared_review_history": _shared_review_history(session),
        "budget": asdict(session.budget),
        "protocol_version": PROTOCOL_VERSION,
        "action_set_version": ACTION_SET_VERSION,
        "baseline": asdict(config.features),
        "plan_author": planner,
        "programming_workflow_version": (
            "programming_workflow_v4" if config.review_required and any(task.programming for task in manifest.tasks)
            else None
        ),
        "deadline_policy": ("collect_pending_non_programming_drafts_and_unsubmitted_candidates_v2"
                            if config.programming_deadline_submit else "collect_pending_non_programming_drafts"),
        "programming_deadline_submit": config.programming_deadline_submit,
        "programming_deadline": {
            "enabled": config.programming_deadline_submit,
            **deadline_before,
            "attempted_task_ids": [e["task_id"] for e in deadline_attempts],
            "accepted_task_ids": deadline_accepted,
            "no_source_task_ids": [e["task_id"] for e in deadline_events if e["kind"] == "programming_deadline_no_source"],
            "unconfirmed_task_ids": [e["task_id"] for e in deadline_attempts if not any(r["task_id"] == e["task_id"] and r["payload"].get("valid") for r in deadline_results)],
        },
        "timing": timing,
        "session_checkpoint": session.checkpoint(),
        "memory": memory.archival_snapshot(),
        "diagnostics": {
            "review_coverage": len(reviewed) / len(submitted) if submitted else 0.0,
            "final_review_coverage": final_review_coverage,
            "final_review_status": final_review_status,
            "deadline_submission": deadline_submission_used,
            "programming_deadline_attempts": len(deadline_attempts),
            "programming_deadline_accepted": len(deadline_accepted),
            "switch_count": switches,
            "baseline_mechanical_switches": baseline_mechanical_switches,
            "attempts": sum(len(task.submissions) for task in session.tasks),
            "attempts_to_ac": attempts_to_ac,
            "stalled_turns": stalled_turns,
            "programming_repair_yields": event_kind_counts.get("programming_repair_yield", 0),
            "programming_source_required_actions": event_kind_counts.get(
                "programming_source_required", 0
            ),
            "programming_duplicate_executions_avoided": sum(
                e["kind"] == "execute_code_result" and bool(e["payload"].get("execution_reused"))
                for e in all_events
            ),
            **desk_diagnostics,
            "active_agent_rate": active_agent_rate,
            "action_balance": action_balance,
            "transport_api_calls": transport_api_calls,
            "transport_retries": transport_retries,
            "transport_failures": transport_failures,
            "elapsed_seconds": session.budget.wall_seconds_used,
            "cce": None,
            "cce_status": "not_run",
        },
        "metrics": {
            "task_utility": None,
            "cce": None,
            "active_agent_rate": active_agent_rate,
            "action_balance": action_balance,
            "review_coverage": len(reviewed) / len(submitted) if submitted else 0.0,
            "final_review_coverage": final_review_coverage,
            "elapsed_seconds": session.budget.wall_seconds_used,
        },
    }


def run_contest(
    manifest: ContestManifest,
    query_llm_fn: QueryFn,
    config: ContestRunConfig,
    *,
    action_request_fn: RequestFn | None = None,
    action_transport: Literal["native", "emulated", "prompt_json"] | None = None,
    coach_query_fn: QueryFn | None = None,
    task_action_executor: TaskActionExecutor | None = None,
    session_checkpoint: dict[str, Any] | None = None,
    memory_checkpoint: str | None = None,
    checkpoint_callback: CheckpointCallback | None = None,
) -> dict[str, Any]:
    """Compatibility facade dispatching to one explicit variant module."""
    kwargs = {
        "action_request_fn": action_request_fn,
        "action_transport": action_transport,
        "task_action_executor": task_action_executor,
        "session_checkpoint": session_checkpoint,
        "memory_checkpoint": memory_checkpoint,
        "checkpoint_callback": checkpoint_callback,
    }
    if config.features.coach == "none":
        from vanilla_contest_runner import run_vanilla_contest

        return run_vanilla_contest(manifest, query_llm_fn, config, **kwargs)

    from strategic_contest_runner import run_strategic_contest

    return run_strategic_contest(
        manifest,
        query_llm_fn,
        config,
        coach_query_fn=coach_query_fn,
        **kwargs,
    )
