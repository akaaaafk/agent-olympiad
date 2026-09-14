"""Per-competition time / API / token budgets.

The turn budget is derived from the official contest clock: one turn always
stands for five minutes. The result is clamped to ``[10, 90]``: a 45-minute
ARML round therefore runs for 10 turns, a 5-hour ICPC runs for 60 turns, and
multi-day or duration-unknown events run for 90 turns. Production entrypoints
enforce that floor; low-level explicit overrides remain available for bounded
deterministic diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

MAX_TURNS_CAP = 90
DEFAULT_MINUTES_PER_TURN = 5.0
MIN_TURNS = 10
# Backward-compatible name retained for callers; this is now enforced by all
# production contest entrypoints rather than merely advisory.
MIN_RECOMMENDED_TURNS = MIN_TURNS


def turns_for_duration(
    duration_minutes: int | float | None,
    minutes_per_turn: float = DEFAULT_MINUTES_PER_TURN,
    *,
    cap: int = MAX_TURNS_CAP,
) -> int:
    """Convert an official contest duration into a turn budget.

    ``duration / minutes_per_turn`` rounded up to a whole turn, then
    clamped to ``[10, cap]``. ``None`` or a non-positive step falls back to
    the cap.
    """
    if duration_minutes is None or minutes_per_turn <= 0:
        return cap
    turns = int(math.ceil(duration_minutes / minutes_per_turn))
    return max(MIN_TURNS, min(cap, turns))


@dataclass(frozen=True)
class ContestBudget:
    """Budget knobs for one competition run."""

    duration_minutes: int | None = None
    minutes_per_turn: float = DEFAULT_MINUTES_PER_TURN
    max_turns: int = MAX_TURNS_CAP
    max_api_calls: int | None = None
    max_output_tokens_per_call: int | None = None
    max_total_tokens: int | None = None
    # ICPC-style: each turn advances simulated contest clock by this many minutes
    # (defaults to minutes_per_turn).
    clock_minutes_per_turn: float | None = None

    def simulated_minutes_for_turns(self, turns: int) -> float:
        step = self.clock_minutes_per_turn or self.minutes_per_turn
        return turns * step


def _budget(
    *,
    duration_minutes: int,
    minutes_per_turn: float = DEFAULT_MINUTES_PER_TURN,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> ContestBudget:
    return ContestBudget(
        duration_minutes=duration_minutes,
        minutes_per_turn=minutes_per_turn,
        max_turns=turns_for_duration(duration_minutes, minutes_per_turn),
        max_api_calls=max_api_calls,
        max_output_tokens_per_call=max_output_tokens_per_call,
        max_total_tokens=max_total_tokens,
        clock_minutes_per_turn=minutes_per_turn,
    )


# Without a verified clock, use the bounded long-event budget.
DEFAULT_CONTEST_BUDGET = ContestBudget(duration_minutes=None, max_turns=MAX_TURNS_CAP)

# Durations from docs/DATA_COLLECTION.md (official contest clocks).
# Turn counts in the comments assume the default 5 min/turn unless a
# different minutes_per_turn is given; everything is capped at 90.
COMPETITION_BUDGET_REGISTRY: dict[str, ContestBudget] = {
    "arml_local": _budget(duration_minutes=45),  # 9 clock units → floor 10
    "arml_national_team": _budget(duration_minutes=20),  # 4 clock units → floor 10
    "arml_national_power": _budget(duration_minutes=60),  # → 12
    "arml_power": ContestBudget(duration_minutes=None, max_turns=MAX_TURNS_CAP),
    "icpc": _budget(duration_minutes=300, max_output_tokens_per_call=4096),  # 5h → 60
    "iiot": _budget(duration_minutes=180, max_output_tokens_per_call=4096),  # 3h → 36
    "ieo_business_case": _budget(duration_minutes=24 * 60),  # multi-day → cap 90
    "iol_team": _budget(duration_minutes=240),  # 4h → 48
    "ioaa_group": _budget(duration_minutes=90),  # 90m → 18
    "ijso_practical": _budget(duration_minutes=180),  # → 36
    "wsc_writing": _budget(duration_minutes=75),  # → 15
    "jessup": _budget(duration_minutes=30 * 24 * 60),  # multi-day → cap 90
    "iypt": _budget(duration_minutes=12 * 60),  # → cap 90
    "hmmt_team": _budget(duration_minutes=60),  # → 12
    "hmmt_guts": _budget(duration_minutes=80),  # → 16
    "mcm": _budget(duration_minutes=99 * 60),  # → cap 90
    "icm": _budget(duration_minutes=99 * 60),  # → cap 90
    "fyziklani": _budget(duration_minutes=180),  # → 36
    "purple_comet": _budget(duration_minutes=90),  # HS 90m → 18
    "itym": _budget(duration_minutes=12 * 60),  # → cap 90
}


def resolve_contest_budget(
    competition_id: str,
    *,
    max_turns: int | None = None,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> ContestBudget:
    """Merge registry defaults with explicit run-time overrides.

    ``max_turns`` defaults to the duration-derived value and an explicit
    override is clamped to ``[1, MAX_TURNS_CAP]``. Production entrypoints apply
    ``MIN_TURNS`` before calling this function; the lower range exists only for
    tests and deliberately short diagnostics.
    """
    base = COMPETITION_BUDGET_REGISTRY.get(competition_id, DEFAULT_CONTEST_BUDGET)
    overrides: dict[str, int | float | None] = {}
    if max_turns is not None:
        overrides["max_turns"] = max(1, min(MAX_TURNS_CAP, int(max_turns)))
    if max_api_calls is not None:
        overrides["max_api_calls"] = max_api_calls
    if max_output_tokens_per_call is not None:
        overrides["max_output_tokens_per_call"] = max_output_tokens_per_call
    if max_total_tokens is not None:
        overrides["max_total_tokens"] = max_total_tokens
    return replace(base, **overrides) if overrides else base


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token). Good enough for budget caps."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    if estimate_tokens(text) <= max_tokens:
        return text

    suffix = "\n\n[truncated: output token budget reached]"
    suffix_tokens = estimate_tokens(suffix)
    body_budget = max_tokens - suffix_tokens
    if body_budget <= 0:
        return suffix[: max_tokens * 4]

    clipped = text[: body_budget * 4].rstrip()
    while clipped and estimate_tokens(clipped + suffix) > max_tokens:
        clipped = clipped[:-4]
    return (clipped + suffix) if clipped else suffix[: max_tokens * 4]
