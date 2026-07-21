from dataclasses import dataclass
from typing import Callable, Literal

from actions import apply_agent_response, build_action_instructions, extract_final_answer_from_text, parse_agent_response

SchemaName = Literal["round_table", "centralized", "decentralized"]
QueryFn = Callable[[str, str], str]


@dataclass
class CollabConfig:
  rounds: int = 2
  decentralized_events: int = 3
  synthesize: bool = True
  progress: Callable[[str], None] | None = None


def _system_prompt(env, role: str) -> str:
    meta = env.get_metadata()
    tools = build_action_instructions(env.get_available_tools())
    return (
        f"You are {role} on a {meta['competition_id']} team of {meta['team_size']} agents.\n"
        f"Problem: {meta.get('title') or meta['problem_id']} ({meta.get('year', 'n/a')})\n"
        f"Allowed tools: {meta['allowed_tools'] or 'none'}\n\n"
        f"{tools}"
    )


def _discussion_history(env) -> str:
    if not env.chat_history:
        return "(no messages yet)"
    lines = []
    for entry in env.chat_history:
        lines.append(f"[{entry['sender']}]: {entry['message']}")
    return "\n".join(lines)


def _agent_user_prompt(env, agent_name: str, schema_note: str, extra: str = "") -> str:
    state = env.get_state()
    scratchpad = state["shared_workspace"].get("scratchpad") or "(empty)"
    return f"""=== SCHEMA ===
{schema_note}

=== PROBLEM ===
{state['problem_statement']}

=== TEAM DISCUSSION ===
{_discussion_history(env)}

=== SHARED SCRATCHPAD ===
{scratchpad}

=== YOUR TURN ===
You are {agent_name}.
Turn budget: {state['turn_status']}
Submitted: {state['submitted']}
{extra}
What is your contribution?"""


def _count_numbered_parts(text: str) -> int:
    import re
    return len(re.findall(r"(?:^|\n)\s*\d+\s*[\.\)]", text))


def _synthesis_system_prompt(env, synthesizer: str) -> str:
    meta = env.get_metadata()
    return (
        f"You are {synthesizer}, writing the team's official final answer sheet for "
        f"{meta['competition_id']} ({meta.get('year', 'n/a')}).\n"
        "Output ONLY the numbered answer sheet. No ACTION lines, no commentary."
    )


def _final_answer_instructions(env) -> str:
    task_type = env.problem_data.get("task_type", "")
    total_pts = env.problem_data.get("total_points")
    if task_type in {"team_contest", "team_power", "team_practical"}:
        points_line = f" ({int(total_pts)} points total)" if total_pts else ""
        return f"""Write the team's COMPLETE final answer sheet{points_line}.

CRITICAL:
- Include EVERY numbered problem from the problem statement (1. through 10.).
- Format exactly:
1. [answer]
2. [answer]
...
10. [answer]
- Compile the best answers from the full discussion and scratchpad above.
- Output plain text only (no ACTION: lines)."""
    return "Synthesize the team's complete final answer as plain text."


def _submit_synthesis_response(env, synthesizer: str, response: str) -> int:
    """Submit synthesis output; prefer full response over truncated ACTION payloads."""
    text = response.strip()
    if not text:
        return 0

    for action_type, payload in parse_agent_response(response):
        if action_type == "submit_final":
            text = payload.strip()
            break

    parts = _count_numbered_parts(text)
    if parts < 3:
        stripped = response.strip()
        if _count_numbered_parts(stripped) > parts:
            text = stripped
            parts = _count_numbered_parts(text)

    env.execute_action(synthesizer, "submit_final", text)
    return parts


def _synthesis_prompt(env, schema_note: str) -> str:
    state = env.get_state()
    instructions = _final_answer_instructions(env)
    return f"""=== SCHEMA ===
{schema_note}

=== PROBLEM ===
{state['problem_statement']}

=== FULL TEAM DISCUSSION ===
{_discussion_history(env)}

=== SHARED SCRATCHPAD ===
{state['shared_workspace'].get('scratchpad') or '(empty)'}

=== FINAL TEAM ANSWER ===
{instructions}"""


def _run_synthesis(
    env,
    query_llm_fn: QueryFn,
    schema_note: str,
    synthesizer: str,
    *,
    submitters: set[str] | None = None,
    progress: Callable[[str], None] | None = None,
) -> None:
    if env.submitted:
        return

    def _log(msg: str) -> None:
        if progress:
            progress(msg)

    best_answer = ""
    best_parts = 0

    for attempt in range(2):
        _log(f"{synthesizer} synthesizing final answer (attempt {attempt + 1})...")
        system = _synthesis_system_prompt(env, synthesizer)
        user = _synthesis_prompt(env, schema_note)
        if attempt > 0:
            user += (
                "\n\nREMINDER: Your previous submission was incomplete. "
                "You MUST include ALL numbered problems (1. through 10.)."
            )
        response = query_llm_fn(system, user)
        if env.submitted:
            env.workspace["final_answer"] = ""
            env.submitted = False
            env.submitted_by = None

        parts = _submit_synthesis_response(env, synthesizer, response)
        answer = env.workspace.get("final_answer", "")
        if parts > best_parts:
            best_parts = parts
            best_answer = answer

        if parts >= 5:
            break
        _log(f"  submission has only {parts} numbered parts — retrying synthesis")

    if best_answer and not env.submitted:
        env.execute_action(synthesizer, "submit_final", best_answer)
    elif best_answer and _count_numbered_parts(env.workspace.get("final_answer", "")) < best_parts:
        env.workspace["final_answer"] = best_answer
        env.submitted = True
        env.submitted_by = synthesizer


def run_round_table(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema A: Round Table — every agent sees the full conversation, takes turns.
    """
    config = config or CollabConfig()
    schema_note = "Round Table: all agents see full history; strict turn order."
    agents = [f"Agent_{i + 1}" for i in range(env.team_size)]

    for _round in range(config.rounds):
        for agent in agents:
            if env.submitted:
                break
            if config.progress:
                config.progress(f"Round {_round + 1}/{config.rounds} — {agent} thinking...")
            system = _system_prompt(env, agent)
            user = _agent_user_prompt(
                env,
                agent,
                schema_note,
                extra=f"Round {_round + 1} of {config.rounds}.",
            )
            response = query_llm_fn(system, user)
            apply_agent_response(env, agent, response)

    if config.synthesize:
        _run_synthesis(env, query_llm_fn, schema_note, "Agent_1", progress=config.progress)

    return _result(env, "round_table")


def run_centralized(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema B: Centralized — coordinator delegates, aggregates, and submits.
    """
    config = config or CollabConfig()
    schema_note = "Centralized: Group_Leader delegates; only leader submits final answer."
    leader = "Group_Leader"

    state = env.get_state()
    system = _system_prompt(env, leader)
    user = (
        f"=== PROBLEM ===\n{state['problem_statement']}\n\n"
        "You are the Group Leader. Assign sub-tasks to Agent_2 .. "
        f"Agent_{env.team_size}. Output your delegation plan."
    )
    if config.progress:
        config.progress("Group_Leader planning delegation...")
    plan = query_llm_fn(system, user)
    env.execute_action(leader, "speak", f"Delegation plan: {plan}")

    for i in range(1, env.team_size):
        if env.submitted:
            break
        peer = f"Agent_{i + 1}"
        if config.progress:
            config.progress(f"{peer} working on assigned slice...")
        system = _system_prompt(env, peer)
        user = _agent_user_prompt(
            env,
            peer,
            schema_note,
            extra=f"Leader's plan:\n{plan}\n\nComplete your assigned slice. You may use allowed tools.",
        )
        response = query_llm_fn(system, user)
        apply_agent_response(env, peer, response, submitters=set())

    if config.synthesize and not env.submitted:
        _run_synthesis(
            env,
            query_llm_fn,
            schema_note,
            leader,
            submitters={"Group_Leader"},
            progress=config.progress,
        )

    return _result(env, "centralized")


def run_decentralized(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema C: Decentralized — agents work independently, coordinate via shared state.
    """
    config = config or CollabConfig()
    schema_note = "Decentralized: no leader; peers update scratchpad/tools directly."
    agents = [f"Agent_{i + 1}" for i in range(env.team_size)]

    for _event in range(config.decentralized_events):
        for agent in agents:
            if env.submitted:
                break
            if config.progress:
                config.progress(f"Event {_event + 1}/{config.decentralized_events} — {agent} thinking...")
            system = _system_prompt(env, agent)
            user = _agent_user_prompt(
                env,
                agent,
                schema_note,
                extra="Coordinate directly with peers. No manager.",
            )
            response = query_llm_fn(system, user)
            apply_agent_response(env, agent, response)

    if config.synthesize and not env.submitted:
        _run_synthesis(env, query_llm_fn, schema_note, agents[0], progress=config.progress)

    return _result(env, "decentralized")


def _result(env, schema: str) -> dict:
    return {
        "schema": schema,
        "problem_id": env.problem_id,
        "competition_id": env.competition_id,
        "submitted": env.submitted,
        "submitted_by": env.submitted_by,
        "turns_used": env.current_turn,
        "chat_messages": len(env.chat_history),
        "final_answer": env.workspace.get("final_answer", ""),
        "grade": env.grade_submission(),
    }


SCHEMAS: dict[SchemaName, Callable] = {
    "round_table": run_round_table,
    "centralized": run_centralized,
    "decentralized": run_decentralized,
}


def run_collaboration(
    schema: SchemaName,
    env,
    query_llm_fn: QueryFn,
    config: CollabConfig | None = None,
) -> dict:
    if schema not in SCHEMAS:
        raise ValueError(f"Unknown schema '{schema}'. Choose from: {list(SCHEMAS)}")
    return SCHEMAS[schema](env, query_llm_fn, config)
