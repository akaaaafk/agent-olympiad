"""Attribute work progress to its write target, not the old active cursor."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from contest_config import ContestRunConfig
from contest_engine import _AgentTurn, _ContestEngine
from contest_manifest import ContestManifest, ManifestTask
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card


def make_engine(variant="single_agent", *, count=3, request=None, programming=False):
    competition = "icpc" if programming else "arml_local"
    manifest = ContestManifest("work-target-test", competition, tuple(
        ManifestTask(f"q{i}", f"q{i}", None, f"Solve q{i}.",
                     "algorithmic_programming" if programming else "math",
                     1, programming, {})
        for i in range(1, count + 1)
    ))
    config = ContestRunConfig(
        variant, 1 if variant == "single_agent" else (3 if programming else 6), 10,
        rule_card=load_rule_card(competition) if variant in {"otc", "vallina_otc"} else None,
    )
    return _ContestEngine(manifest, lambda *_: "Offline fixture.", config,
                          action_request_fn=request, action_transport="emulated")


def events(engine, kind):
    return [e for e in engine.memory.archival_snapshot()["events"] if e["kind"] == kind]


def work(engine, target, content=None):
    turn = _AgentTurn("Agent_1")
    turn.action = "work"
    turn.arguments = {"problem_id": target,
                      "content": content or f"Problem {target}:\nFinal answer: 42"}
    return engine._apply_agent_action(turn)


@pytest.mark.parametrize("variant", ["single_agent", "decentralized"])
@pytest.mark.parametrize("start", [None, "q1"])
@pytest.mark.parametrize("prior_versions", [0, 2])
def test_explicit_work_records_actual_target_progress_and_switches(variant, start, prior_versions):
    engine = make_engine(variant)
    target = "q2" if start else "q1"
    if start:
        engine.session.select_task(start)
        engine.session.create_answer("Final answer: 11", author="Agent_2")
    if prior_versions:
        engine.session.select_task(target)
        for i in range(prior_versions):
            engine.session.create_answer(f"Final answer: {i}", author="Agent_1")
        if start:
            engine.session.select_task(start)
        else:
            engine.session.skip_task()
    old_versions = tuple(engine.session.task(start).versions) if start else ()
    engine.session.consume_budget(turns=1)

    assert work(engine, target)

    assert len(engine.session.task(target).versions) == prior_versions + 1
    assert engine.last_progress_turn.get(target) == 1
    assert start not in engine.last_progress_turn
    assert engine.session.active_task.task_id == ("q3" if start else "q2")
    switched = events(engine, "baseline_next_unseen_scheduled")
    assert len(switched) == 1
    assert switched[0]["payload"]["from"] == target
    assert engine.baseline_mechanical_switches == 1
    if start:
        assert tuple(engine.session.task(start).versions) == old_versions


@pytest.mark.parametrize("variant,count,rounds", [
    ("single_agent", 10, 10), ("decentralized", 12, 2),
])
def test_real_round_loop_writes_every_task_without_extra_selection_round(variant, count, rounds):
    seen = []

    def request(req):
        target = req.metadata["task_id"] or "q1"
        seen.append((req.metadata["agent"], target))
        return LLMResponse("", "fixture", "fixture", tool_calls=(
            LLMToolCall("work", {"problem_id": target,
                                "content": f"Problem {target}:\nFinal answer: 42"}),
        ), usage={"api_calls": 1, "output_tokens": 20})

    engine = make_engine(variant, count=count, request=request)
    for _ in range(rounds):
        assert engine._run_round()
    engine._collect_deadline()

    assert [target for _, target in seen] == [f"q{i}" for i in range(1, count + 1)]
    assert all(len(t.versions) == 1 and len(t.submissions) == 1 for t in engine.session.tasks)
    assert not events(engine, "action_error")
    assert engine.session.budget.turns_used == rounds
    assert engine.session.budget.api_calls_used == count
    assert engine.session.budget.tokens_used == count * 20
    assert engine.session.budget.simulated_minutes_used == rounds * 5


@pytest.mark.parametrize("variant", ["single_agent", "decentralized"])
def test_duplicate_target_draft_does_not_manufacture_progress_or_switch(variant):
    engine = make_engine(variant)
    content = "Problem q2:\nFinal answer: 42"
    engine.session.select_task("q2")
    original = engine.session.create_answer(content, author="Agent_1")
    engine.session.select_task("q1")
    engine.session.consume_budget(turns=1)

    assert work(engine, "q2", content)

    assert engine.session.task("q2").versions == [original]
    assert not engine.last_progress_turn
    assert engine.session.active_task.task_id == "q2"
    assert not events(engine, "baseline_next_unseen_scheduled")


@pytest.mark.parametrize("variant", ["single_agent", "decentralized"])
@pytest.mark.parametrize("target,content", [
    ("missing", "Final answer: 42"),
    ("q2", "Problem q1:\nFinal answer: 42"),
    ("q2", "x" * 8001),
])
def test_rejected_work_does_not_change_focus_drafts_progress_or_budget(variant, target, content):
    engine = make_engine(variant)
    engine.session.select_task("q1")
    engine.session.create_answer("Final answer: 11", author="Agent_2")
    before = engine.session.checkpoint()

    assert not work(engine, target, content)

    assert engine.session.checkpoint() == before
    assert not engine.last_progress_turn
    assert not events(engine, "baseline_next_unseen_scheduled")
    assert len(events(engine, "action_error")) == 1


@pytest.mark.parametrize("variant", ["single_agent", "decentralized"])
def test_target_snapshot_does_not_bypass_work_assignment_permissions(variant):
    engine = make_engine(variant)
    engine.session.select_task("q1")
    before = engine.session.checkpoint()
    turn = _AgentTurn("Agent_1")
    turn.work_task_ids = {"q1"}
    turn.action = "work"
    turn.arguments = {"problem_id": "q2", "content": "Problem q2:\nFinal answer: 42"}

    assert not engine._apply_agent_action(turn)

    assert engine.session.checkpoint() == before
    assert not engine.last_progress_turn
    assert not events(engine, "baseline_next_unseen_scheduled")
    assert len(events(engine, "action_error")) == 1


@pytest.mark.parametrize("variant", ["centralized", "vallina_otc", "otc"])
def test_nonmechanical_baselines_record_target_progress_without_autoswitch(variant):
    engine = make_engine(variant)
    engine.session.consume_budget(turns=1)
    engine.session.select_task("q1")

    assert work(engine, "q2")

    assert engine.last_progress_turn == {"q2": 1}
    assert engine.session.active_task.task_id == "q2"
    assert not events(engine, "baseline_next_unseen_scheduled")
    assert engine.baseline_mechanical_switches == 0


@pytest.mark.parametrize("variant", ["single_agent", "decentralized"])
def test_implicit_current_task_work_and_selection_keep_existing_semantics(variant):
    engine = make_engine(variant)
    engine.session.consume_budget(turns=1)
    turn = _AgentTurn("Agent_1")
    turn.action, turn.arguments = "select_problem", {"problem_id": "q1"}
    assert engine._apply_agent_action(turn)
    assert engine.session.active_task.task_id == "q1"
    assert not events(engine, "baseline_next_unseen_scheduled")
    engine.session.consume_budget(turns=1)
    turn.action, turn.arguments = "work", {"content": "Final answer: 42"}
    assert engine._apply_agent_action(turn)
    assert engine.last_progress_turn == {"q1": 2}
    assert engine.session.active_task.task_id == "q2"
    assert len(events(engine, "baseline_next_unseen_scheduled")) == 1


def test_otc_programming_note_visit_is_attributed_to_target_without_creating_source():
    engine = make_engine("otc", programming=True)
    engine.session.consume_budget(turns=1)
    engine.session.select_task("q1")
    original = engine.session.create_answer("print(1)", author="Agent_1", evidence_refs=("sample",))

    assert work(engine, "q2", "Inspect the input constraints before coding.")

    assert engine.session.task("q1").versions == [original]
    assert not engine.session.task("q2").versions
    progress = events(engine, "programming_worker_progress")
    assert len(progress) == 1
    assert progress[0]["task_id"] == "q2"
    assert not engine.last_progress_turn
    assert not events(engine, "baseline_next_unseen_scheduled")


def test_restored_engine_retains_target_progress_and_next_task():
    engine = make_engine()
    engine.session.consume_budget(turns=1)
    assert work(engine, "q1")
    restored = _ContestEngine(
        engine.manifest, lambda *_: "Offline fixture.", engine.config,
        action_transport="emulated", session_checkpoint=engine._checkpoint(),
        memory_checkpoint=engine.memory.to_checkpoint_json(),
    )
    assert restored.last_progress_turn == {"q1": 1}
    assert restored.session.active_task.task_id == "q2"
    assert restored.baseline_mechanical_switches == 1
    restored.session.consume_budget(turns=1)
    assert work(restored, "q2")
    assert restored.last_progress_turn == {"q1": 1, "q2": 2}
    assert restored.session.active_task.task_id == "q3"
    assert len(events(restored, "baseline_next_unseen_scheduled")) == 2
