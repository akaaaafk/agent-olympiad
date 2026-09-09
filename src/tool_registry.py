"""Typed action registry and capability resolver.

This module is deliberately independent of environment and agent-system
implementations.  Both vanilla and strategic systems can consume the same
resolved action specs and adapt their legacy action names at the boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Iterable, Literal, Mapping

Visibility = Literal["private", "team", "contest"]
JsonType = Literal["string", "integer", "number", "boolean", "object", "array"]


@dataclass(frozen=True)
class ArgumentSpec:
    """One JSON-compatible action argument."""

    name: str
    type: JsonType = "string"
    description: str = ""
    required: bool = True
    enum: tuple[Any, ...] = ()
    # Element type for ``array`` arguments. ``enum`` then constrains elements.
    items: JsonType | None = None

    def to_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": self.type}
        if self.description:
            schema["description"] = self.description
        if self.type == "array":
            items: dict[str, Any] = {"type": self.items or "string"}
            if self.enum:
                items["enum"] = list(self.enum)
            # Non-emptiness is enforced by validate_action_payload rather than
            # ``minItems`` so provider strict-schema support is never a question.
            schema["items"] = items
        elif self.enum:
            schema["enum"] = list(self.enum)
        return schema


@dataclass(frozen=True)
class BudgetSemantics:
    """Units charged when an action succeeds."""

    turns: int = 1
    tool_calls: int = 0
    submission_attempts: int = 0
    terminal: bool = False


@dataclass(frozen=True)
class ActionSpec:
    """Immutable contract shared by prompts, parsers, and dispatch adapters."""

    name: str
    description: str
    arguments: tuple[ArgumentSpec, ...]
    visibility: Visibility
    pack: str
    budget: BudgetSemantics
    handler_name: str
    handler_callable: bool = True
    evaluator: bool = False
    evaluator_name: str | None = None
    submission: bool = False

    @property
    def handler_marker(self) -> str:
        """Stable marker used to match a registered runtime handler."""

        return self.handler_name

    @property
    def argument_fields(self) -> tuple[str, ...]:
        return tuple(argument.name for argument in self.arguments)

    @property
    def argument_schema(self) -> Mapping[str, Any]:
        required = [
            argument.name for argument in self.arguments if argument.required
        ]
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                argument.name: argument.to_schema() for argument in self.arguments
            },
            "additionalProperties": False,
        }
        if required:
            schema["required"] = required
        return MappingProxyType(schema)


@dataclass(frozen=True)
class Resolution:
    """Resolved specs plus machine-readable reasons for omitted requests."""

    actions: frozenset[ActionSpec]
    unknown_capabilities: frozenset[str] = field(default_factory=frozenset)
    missing_handlers: frozenset[str] = field(default_factory=frozenset)

    @property
    def names(self) -> frozenset[str]:
        return frozenset(spec.name for spec in self.actions)

    @property
    def diagnostics(self) -> tuple[str, ...]:
        messages = [
            f"unknown capability: {name}"
            for name in sorted(self.unknown_capabilities)
        ]
        messages.extend(
            f"missing handler: {name}" for name in sorted(self.missing_handlers)
        )
        return tuple(messages)


_TEXT = ArgumentSpec("content", description="Action content.")
_REASON = ArgumentSpec(
    "reason", description="Optional reason for the action.", required=False
)
_PROBLEM_ID = ArgumentSpec(
    "problem_id", description="Identifier of the problem to select."
)
_RECIPIENTS = ArgumentSpec(
    "recipients",
    type="array",
    items="string",
    description=(
        "Exact teammate names that should privately receive the message; "
        "one name for a point-to-point message, several for a sub-group."
    ),
)
_OPTIONAL_PROBLEM_ID = ArgumentSpec(
    "problem_id",
    description="Problem identifier; defaults to the active problem.",
    required=False,
)


def _action(
    name: str,
    description: str,
    arguments: tuple[ArgumentSpec, ...],
    *,
    visibility: Visibility = "team",
    pack: str = "common",
    tool_calls: int = 0,
    submission_attempts: int = 0,
    terminal: bool = False,
    evaluator: bool = False,
    evaluator_name: str | None = None,
    submission: bool = False,
) -> ActionSpec:
    return ActionSpec(
        name=name,
        description=description,
        arguments=arguments,
        visibility=visibility,
        pack=pack,
        budget=BudgetSemantics(
            turns=1,
            tool_calls=tool_calls,
            submission_attempts=submission_attempts,
            terminal=terminal,
        ),
        handler_name=name,
        evaluator=evaluator,
        evaluator_name=evaluator_name,
        submission=submission,
    )


_SPECS = (
    _action(
        "select_problem",
        "Select a contest problem to work on.",
        (_PROBLEM_ID,),
        visibility="contest",
    ),
    _action("speak", "Broadcast a message to the team.", (_TEXT,)),
    _action(
        "direct_message",
        "Send a private message to one teammate or a named sub-group of teammates.",
        (_RECIPIENTS, _TEXT),
        visibility="private",
    ),
    _action(
        "work",
        "Record durable work for the team.",
        (_TEXT,),
    ),
    # Desk actions: read-only inspection, personal notes, and team triage.
    # They are the contestant's desk, not contest-specific instruments, so
    # every task family and both system variants receive them.
    _action(
        "inspect_problem",
        (
            "Read one problem's statement plus its complete answer-version, "
            "review, and submission history without changing the team's "
            "active problem. Self-verification context only; it never counts "
            "as an independent review."
        ),
        (
            _OPTIONAL_PROBLEM_ID,
            ArgumentSpec(
                "focus",
                description="Optional aspect to re-check, such as edge cases.",
                required=False,
            ),
        ),
        visibility="private",
    ),
    _action(
        "triage_problem",
        (
            "Set the team's working priority for one problem, or mark it "
            "hopeless. Hopeless problems stay on the sheet and their latest "
            "draft is still submitted at the deadline."
        ),
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "priority",
                description="Team priority for this problem.",
                enum=("high", "normal", "low", "hopeless"),
            ),
            _REASON,
        ),
        visibility="team",
    ),
    _action(
        "remember",
        (
            "Store a private note that survives outside the visible transcript, "
            "optionally tagged to one problem. Use work for candidate answers, "
            "remember for intermediate results, dead ends, and reminders."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        visibility="private",
    ),
    _action(
        "recall",
        (
            "Search your own notes and notes teammates have shared, ranked by "
            "problem tag, query match, and recency."
        ),
        (
            ArgumentSpec(
                "query",
                description="Optional keywords to match.",
                required=False,
            ),
            ArgumentSpec(
                "problem_id",
                description="Optional problem tag to prioritise.",
                required=False,
            ),
        ),
        visibility="private",
    ),
    _action(
        "share_note",
        "Publish one of your stored notes to the whole team.",
        (
            ArgumentSpec(
                "note_id",
                description="Event id of the note returned by remember or recall.",
            ),
        ),
        visibility="team",
    ),
    _action(
        "request_review",
        "Ask a teammate to review the current active problem; this does not approve it.",
        (
            _TEXT,
            ArgumentSpec(
                "reviewer",
                description="Optional teammate name.",
                required=False,
            ),
        ),
    ),
    _action(
        "review_answer",
        "Independently review another agent's current answer version.",
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "version_hash",
                description="Exact current answer version being reviewed.",
            ),
            ArgumentSpec(
                "decision",
                description="Review outcome.",
                enum=("approve", "reject"),
            ),
            ArgumentSpec("content", description="Review findings and evidence."),
        ),
    ),
    _action(
        "submit",
        "Submit a final answer for evaluation.",
        (ArgumentSpec("answer", description="Complete final answer."),),
        visibility="team",
        submission_attempts=1,
        evaluator=True,
        evaluator_name="task_evaluator",
        submission=True,
    ),
    _action(
        "skip_problem",
        "Skip the current problem.",
        (_REASON,),
        visibility="contest",
    ),
    _action(
        "finish_contest",
        "Finish only after every task has a valid submission and required final review.",
        (_REASON,),
        visibility="contest",
        terminal=True,
    ),
    _action("rest", "Pass the current turn.", (_REASON,), visibility="private"),
    _action(
        "use_calculator",
        "Evaluate a mathematical expression.",
        (ArgumentSpec("expression", description="Arithmetic expression."),),
        visibility="private",
        pack="math",
        tool_calls=1,
    ),
    _action(
        "execute_code",
        (
            "Execute code in the contest sandbox. For programming tasks the same "
            "source is also run on the official sample input and compared with "
            "the expected output; only a sample AC counts as local run evidence."
        ),
        (
            ArgumentSpec("code", description="Source code to execute."),
            ArgumentSpec(
                "language",
                description="Runtime language; defaults to Python.",
                required=False,
            ),
        ),
        visibility="private",
        pack="programming",
        tool_calls=1,
    ),
    _action(
        "verify",
        "Re-open the latest code and its visible version, run, submission, and review history.",
        (
            ArgumentSpec(
                "focus",
                description="Optional aspect to re-check, such as edge cases or complexity.",
                required=False,
            ),
        ),
        visibility="private",
        pack="programming",
    ),
    _action(
        "submit_code",
        "Submit source code to the programming evaluator.",
        (
            ArgumentSpec("code", description="Complete source code."),
            ArgumentSpec(
                "language", description="Submission language.", required=False
            ),
        ),
        pack="programming",
        tool_calls=1,
        submission_attempts=1,
        evaluator=True,
        evaluator_name="programming_judge",
        submission=True,
    ),
    _action(
        "web_search",
        "Search permitted web resources.",
        (ArgumentSpec("query", description="Search query."),),
        visibility="private",
        pack="research",
        tool_calls=1,
    ),
    _action(
        "read_lab_equipment",
        "Read declared laboratory equipment data.",
        (
            ArgumentSpec(
                "resource",
                description="Equipment or reading identifier.",
                required=False,
            ),
        ),
        visibility="private",
        pack="resources",
        tool_calls=1,
    ),
    _action(
        "read_star_chart",
        "Read a declared star-chart resource.",
        (
            ArgumentSpec(
                "resource",
                description="Chart or observation identifier.",
                required=False,
            ),
        ),
        visibility="private",
        pack="resources",
        tool_calls=1,
    ),
)

ACTION_REGISTRY: Mapping[str, ActionSpec] = MappingProxyType(
    {spec.name: spec for spec in _SPECS}
)

COMMON_ACTION_NAMES = frozenset(
    name for name, spec in ACTION_REGISTRY.items() if spec.pack == "common"
)
# Read-only or personal bookkeeping actions that never mutate answers or
# submissions. Contest runners keep these available whenever the agent may
# act at all, regardless of coach assignment or workflow gates.
DESK_ACTION_NAMES = frozenset(
    {"inspect_problem", "triage_problem", "remember", "recall", "share_note"}
)
# Bumped whenever the canonical action surface changes shape; recorded in
# contest results so mixed-version comparisons are visible.
ACTION_SET_VERSION = 2
PACK_ACTION_NAMES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        pack: frozenset(
            name for name, spec in ACTION_REGISTRY.items() if spec.pack == pack
        )
        for pack in ("common", "math", "programming", "research", "resources")
    }
)

# Boundary adapters can translate old environment protocol names without
# polluting the canonical registry.
LEGACY_ACTION_ALIASES: Mapping[str, str] = MappingProxyType(
    {
        "submit_final": "submit",
        "sleep": "rest",
        "write_scratchpad": "work",
    }
)
LEGACY_ENV_ACTIONS = LEGACY_ACTION_ALIASES

COMPETITION_TOOL_REGISTRY: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "purple_comet": ("use_calculator",),
        "fyziklani": ("use_calculator", "web_search"),
        "iiot": ("execute_code", "verify"),
        "icpc": ("execute_code", "verify"),
        "codeforces": ("execute_code", "verify"),
        "mcm": ("execute_code", "verify", "web_search"),
        "icm": ("execute_code", "verify", "web_search"),
        "ieo_business_case": ("web_search",),
        "jessup": ("web_search",),
        "iypt": ("web_search", "execute_code", "verify", "use_calculator"),
        "ijso_practical": ("use_calculator", "read_lab_equipment"),
        "ioaa_group": ("use_calculator", "read_star_chart"),
        "iol_team": (),
        "arml_power": (),
        "arml_national_team": (),
        "arml_national_power": (),
        "arml_local": (),
        "hmmt_team": (),
        "hmmt_guts": (),
        "wsc_writing": (),
    }
)
COMPETITION_ACTION_REGISTRY: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "icpc": ("submit_code",),
        "iiot": ("submit_code",),
        "codeforces": ("submit_code",),
    }
)

_PROGRAMMING_COMPETITIONS = frozenset({"icpc", "iiot", "codeforces"})
_MATH_COMPETITIONS = frozenset(
    {
        "arml_local",
        "arml_national_team",
        "purple_comet",
        "hmmt_guts",
        "hmmt_team",
        "wmtc",
        "fyziklani",
        "ijso_practical",
        "ioaa_group",
        "iypt",
    }
)
_RESEARCH_COMPETITIONS = frozenset(
    {"fyziklani", "mcm", "icm", "ieo_business_case", "jessup", "iypt"}
)
_RESOURCE_ACTIONS = PACK_ACTION_NAMES["resources"]


def _string_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, Mapping):
        return {str(key).strip() for key, enabled in value.items() if enabled}
    try:
        return {str(item).strip() for item in value if str(item).strip()}
    except TypeError:
        text = str(value).strip()
        return {text} if text else set()


def _requirement_tokens(requirements: Any) -> set[str]:
    if not isinstance(requirements, Mapping):
        return _string_set(requirements)
    tokens: set[str] = set()
    for key in (
        "required_packs",
        "packs",
        "required_tools",
        "tools",
        "required_actions",
        "actions",
        "capabilities",
    ):
        tokens.update(_string_set(requirements.get(key)))
    return tokens


def _requested_names(
    competition: str,
    task_type: str | None,
    requirements: Any,
    capabilities: set[str],
) -> tuple[set[str], set[str]]:
    names = set(COMMON_ACTION_NAMES)
    packs: set[str] = set()
    competition_key = (competition or "").strip().lower()
    task_key = (task_type or "").strip().lower()

    if competition_key in _PROGRAMMING_COMPETITIONS or any(
        marker in task_key for marker in ("program", "coding", "algorithm")
    ):
        packs.add("programming")
    if competition_key in _MATH_COMPETITIONS or any(
        marker in task_key for marker in ("math", "proof", "numeric")
    ):
        packs.add("math")
    if competition_key in _RESEARCH_COMPETITIONS or any(
        marker in task_key for marker in ("research", "case_study", "legal")
    ):
        packs.add("research")

    tokens = _requirement_tokens(requirements) | capabilities
    known_packs = set(PACK_ACTION_NAMES) - {"common", "resources"}
    packs.update(tokens & known_packs)
    names.update(tokens & set(ACTION_REGISTRY))
    for pack in packs:
        names.update(PACK_ACTION_NAMES[pack])

    # Use the same contest tool allowlist as the environment. Capabilities may
    # request tools, but must not grant tools forbidden by a known contest.
    from contest_rules import get_contest_rules
    rules = get_contest_rules(competition_key)
    if competition_key in COMPETITION_TOOL_REGISTRY or rules is not None:
        permitted = set(COMPETITION_TOOL_REGISTRY.get(competition_key, ()))
        if not permitted and rules is not None:
            permitted.update(rules.encoded_tools)
        if "execute_code" in permitted:
            permitted.add("verify")
        permitted.update(COMPETITION_ACTION_REGISTRY.get(competition_key, ()))
        names = (names & set(COMMON_ACTION_NAMES)) | (permitted - _RESOURCE_ACTIONS)

    # Physical resources are capabilities, not entitlements inferred from a
    # contest, task type, generic resources pack, or benchmark requirement.
    names.difference_update(_RESOURCE_ACTIONS)
    resources = _RESOURCE_ACTIONS & capabilities
    if competition_key in COMPETITION_TOOL_REGISTRY or rules is not None:
        resources &= permitted
    names.update(resources)
    return names, tokens


def _handler_markers(
    registered_handlers: Mapping[str, Callable[..., Any] | Any]
    | Iterable[str]
    | None,
) -> set[str]:
    if registered_handlers is None:
        return {
            marker
            for spec in ACTION_REGISTRY.values()
            for marker in (spec.name, spec.handler_marker)
        }
    if isinstance(registered_handlers, Mapping):
        return {str(name) for name in registered_handlers}
    return {str(name) for name in registered_handlers}


def resolve_actions_with_diagnostics(
    competition: str | None = None,
    task_type: str | None = None,
    benchmark_requirements: Any = None,
    declared_capabilities: Iterable[str] | Mapping[str, bool] | None = None,
    registered_handlers: Mapping[str, Callable[..., Any] | Any]
    | Iterable[str]
    | None = None,
    *,
    competition_id: str | None = None,
    system_variant: str | None = None,
) -> Resolution:
    """Resolve available actions without depending on agent-system strategy.

    ``system_variant`` is accepted as migration-friendly context but is
    intentionally ignored.  It can therefore never fork the action surface.
    """

    del system_variant
    competition_key = competition if competition is not None else competition_id or ""
    capabilities = _string_set(declared_capabilities)
    requested, tokens = _requested_names(
        competition_key, task_type, benchmark_requirements, capabilities
    )
    known_tokens = set(ACTION_REGISTRY) | set(PACK_ACTION_NAMES)
    unknown = capabilities - known_tokens
    # Unknown benchmark tokens are also useful diagnostics when requirements
    # use one of the supported action/pack fields.
    unknown.update(tokens - known_tokens)

    handler_markers = _handler_markers(registered_handlers)
    available: set[ActionSpec] = set()
    missing: set[str] = set()
    for name in requested:
        spec = ACTION_REGISTRY[name]
        if spec.name in handler_markers or spec.handler_marker in handler_markers:
            available.add(spec)
        else:
            missing.add(name)
    return Resolution(
        actions=frozenset(available),
        unknown_capabilities=frozenset(unknown),
        missing_handlers=frozenset(missing),
    )


def resolve_actions(
    competition: str | None = None,
    task_type: str | None = None,
    benchmark_requirements: Any = None,
    declared_capabilities: Iterable[str] | Mapping[str, bool] | None = None,
    registered_handlers: Mapping[str, Callable[..., Any] | Any]
    | Iterable[str]
    | None = None,
    *,
    competition_id: str | None = None,
    system_variant: str | None = None,
) -> frozenset[ActionSpec]:
    """Return the immutable set of executable action contracts."""

    return resolve_actions_with_diagnostics(
        competition=competition,
        task_type=task_type,
        benchmark_requirements=benchmark_requirements,
        declared_capabilities=declared_capabilities,
        registered_handlers=registered_handlers,
        competition_id=competition_id,
        system_variant=system_variant,
    ).actions


def resolve_action_names(*args: Any, **kwargs: Any) -> frozenset[str]:
    """Convenience adapter for parsers that only need canonical names."""

    return frozenset(spec.name for spec in resolve_actions(*args, **kwargs))


def _coerce_specs(
    actions: Iterable[ActionSpec | str],
) -> tuple[ActionSpec, ...]:
    specs = []
    for action in actions:
        spec = ACTION_REGISTRY[action] if isinstance(action, str) else action
        specs.append(spec)
    return tuple(sorted(specs, key=lambda item: item.name))


def render_action_schema(
    actions: Iterable[ActionSpec | str],
) -> dict[str, Any]:
    """Render a strict tagged-union JSON schema for structured model output."""

    variants = []
    for spec in _coerce_specs(actions):
        variants.append(
            {
                "type": "object",
                "properties": {
                    "action": {"const": spec.name},
                    "arguments": dict(spec.argument_schema),
                },
                "required": ["action", "arguments"],
                "additionalProperties": False,
            }
        )
    return {"type": "object", "oneOf": variants}


def render_function_tools(
    actions: Iterable[ActionSpec | str],
) -> list[dict[str, Any]]:
    """Render provider-native custom function definitions from ActionSpecs."""
    return [
        {
            "type": "function",
            "name": spec.name,
            "description": spec.description,
            "parameters": dict(spec.argument_schema),
            # OpenAI-style strict schemas require every property to be
            # required. Keep optional-argument actions valid by disabling
            # strict mode only for those functions.
            "strict": all(argument.required for argument in spec.arguments),
        }
        for spec in _coerce_specs(actions)
    ]


def render_action_instructions(actions: Iterable[ActionSpec | str]) -> str:
    """Render compact prompt text from the same specs used for validation."""

    lines = ["Available actions:"]
    for spec in _coerce_specs(actions):
        arguments = ", ".join(
            f"{argument.name}{'' if argument.required else '?'}"
            for argument in spec.arguments
        )
        signature = f"{spec.name}({arguments})"
        lines.append(f"- {signature}: {spec.description}")
    return "\n".join(lines)


_PYTHON_TYPES: Mapping[str, type[Any] | tuple[type[Any], ...]] = MappingProxyType(
    {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }
)


def validate_action_payload(
    action: str | ActionSpec,
    payload: Mapping[str, Any] | Any,
) -> tuple[str, ...]:
    """Validate action arguments; return all errors instead of raising."""

    spec = ACTION_REGISTRY.get(action) if isinstance(action, str) else action
    if spec is None:
        return (f"unknown action: {action}",)
    if not isinstance(payload, Mapping):
        return (f"{spec.name} arguments must be an object",)

    errors: list[str] = []
    arguments = {argument.name: argument for argument in spec.arguments}
    for argument in spec.arguments:
        if argument.required and argument.name not in payload:
            errors.append(f"missing required argument: {argument.name}")
    for name, value in payload.items():
        argument = arguments.get(name)
        if argument is None:
            errors.append(f"unexpected argument: {name}")
            continue
        expected = _PYTHON_TYPES[argument.type]
        valid = isinstance(value, expected)
        if argument.type in {"integer", "number"} and isinstance(value, bool):
            valid = False
        if not valid:
            errors.append(
                f"argument {name} must have JSON type {argument.type}"
            )
        elif argument.type == "array":
            if not value:
                errors.append(f"argument {name} must contain at least one item")
            element_type = _PYTHON_TYPES[argument.items or "string"]
            for item in value:
                if not isinstance(item, element_type):
                    errors.append(
                        f"argument {name} items must have JSON type "
                        f"{argument.items or 'string'}"
                    )
                    break
                if argument.enum and item not in argument.enum:
                    errors.append(
                        f"argument {name} items must be one of {list(argument.enum)!r}"
                    )
                    break
        elif argument.enum and value not in argument.enum:
            errors.append(
                f"argument {name} must be one of {list(argument.enum)!r}"
            )
    return tuple(errors)


def validate_registry(
    registry: Mapping[str, ActionSpec] = ACTION_REGISTRY,
) -> tuple[str, ...]:
    """Return registry consistency errors for startup checks and tests."""

    errors: list[str] = []
    seen_handlers: set[str] = set()
    for name, spec in registry.items():
        if name != spec.name:
            errors.append(f"registry key {name!r} does not match {spec.name!r}")
        if not name or not name.replace("_", "").isalnum():
            errors.append(f"invalid action name: {name!r}")
        argument_names = [argument.name for argument in spec.arguments]
        if len(argument_names) != len(set(argument_names)):
            errors.append(f"duplicate argument in action: {name}")
        if not spec.handler_name:
            errors.append(f"missing handler marker: {name}")
        seen_handlers.add(spec.handler_name)
        if spec.evaluator and not spec.evaluator_name:
            errors.append(f"evaluator action lacks evaluator name: {name}")
        if spec.budget.submission_attempts and not spec.submission:
            errors.append(f"submission budget on non-submission action: {name}")
    del seen_handlers
    if {
        name for name, spec in registry.items() if spec.pack == "common"
    } != set(COMMON_ACTION_NAMES):
        errors.append("common pack does not match COMMON_ACTION_NAMES")
    return tuple(errors)


def dispatch_environment_action(
    environment: Any,
    *,
    agent_name: str,
    action_name: str,
    payload: str,
) -> Any:
    """Dispatch canonical task-pack actions against an environment runtime.

    ``NotImplemented`` means the action belongs to the legacy collaboration
    layer rather than this registry.
    """
    if action_name == "submit_code":
        duplicate_error = environment._unchanged_failed_source_error(payload)
        if duplicate_error:
            return duplicate_error
        result = environment._submit_code(payload, agent_name=agent_name)
        environment._record_shared_code_submission(agent_name, payload, result)
        return result
    if action_name == "use_calculator":
        return environment._run_calculator(payload)
    if action_name == "execute_code":
        return environment._run_code(payload)
    if action_name == "verify":
        visible_history = [
            {
                "turn": item.get("turn"),
                "agent": item.get("agent"),
                "action": item.get("action"),
                "payload": item.get("payload"),
                "result": item.get("result"),
            }
            for item in environment.action_log
            if item.get("visibility") != "private"
            or item.get("agent") == agent_name
        ][-20:]
        latest_code = next(
            (
                str(item.get("payload") or "")
                for item in reversed(visible_history)
                if item.get("action")
                in {"execute_code", "submit_code", "submit_final"}
                and str(item.get("payload") or "").strip()
            ),
            str(environment.workspace.get("final_answer") or ""),
        )
        return json.dumps(
            {
                "focus": payload.strip(),
                "latest_code": latest_code,
                "history": visible_history,
                "note": (
                    "Self-verification context only; this does not count as an "
                    "independent review approval."
                ),
            },
            ensure_ascii=False,
        )
    if action_name == "web_search":
        return environment._run_web_search(payload)
    resource_roles = {
        "read_lab_equipment": "lab",
        "read_star_chart": "star",
    }
    role = resource_roles.get(action_name)
    if role is not None:
        loaded = environment._tool_asset_text(role, payload)
        return (
            f"[{action_name}]\n{loaded}"
            if loaded
            else f"[{action_name}] No executable fixture for {payload!r}."
        )
    return NotImplemented


__all__ = [
    "ACTION_REGISTRY",
    "ACTION_SET_VERSION",
    "COMMON_ACTION_NAMES",
    "DESK_ACTION_NAMES",
    "PACK_ACTION_NAMES",
    "LEGACY_ACTION_ALIASES",
    "LEGACY_ENV_ACTIONS",
    "COMPETITION_TOOL_REGISTRY",
    "COMPETITION_ACTION_REGISTRY",
    "ActionSpec",
    "ArgumentSpec",
    "BudgetSemantics",
    "Resolution",
    "render_action_instructions",
    "render_function_tools",
    "render_action_schema",
    "resolve_action_names",
    "resolve_actions",
    "resolve_actions_with_diagnostics",
    "validate_action_payload",
    "validate_registry",
    "dispatch_environment_action",
]
