"""Strategic multi-agent contest runner with the pre-contest Open Coach."""

from __future__ import annotations

from typing import Any, Literal

from contest_manifest import ContestManifest
from contest_runner import (
    CheckpointCallback,
    ContestRunConfig,
    QueryFn,
    TaskActionExecutor,
    _run_contest_engine,
)
from llm import RequestFn


def run_strategic_contest(
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
    """Run the Coach-planned workflow with strategic gates and recovery."""
    if config.features.coach == "none":
        raise ValueError(
            "run_strategic_contest requires a coach or leader baseline"
        )
    return _run_contest_engine(
        manifest,
        query_llm_fn,
        config,
        action_request_fn=action_request_fn,
        action_transport=action_transport,
        coach_query_fn=coach_query_fn,
        task_action_executor=task_action_executor,
        session_checkpoint=session_checkpoint,
        memory_checkpoint=memory_checkpoint,
        checkpoint_callback=checkpoint_callback,
    )
