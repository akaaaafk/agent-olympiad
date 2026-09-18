"""Resolve displayed simulation budgets without changing source rule bundles."""
from dataclasses import replace


def bind_runtime_budget(card, config):
    simulation = dict(card.simulation, max_turns=config.max_turns,
        turn_budget_basis='Actual run configuration; official timing is recorded separately.',
        minutes_per_turn=config.minutes_per_turn,
        max_api_calls=config.max_api_calls, max_tokens=config.max_tokens)
    return replace(card, max_turns=config.max_turns, simulation=simulation)
