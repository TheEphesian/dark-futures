import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import GameState


EVENT_POOL = [
    {
        "name": "Economic Recession",
        "severity": "warning",
        "effect": lambda state, rng: _apply_gdp_hit(state, rng),
        "message": "Global markets contract. GDP reduced across all nations.",
    },
    {
        "name": "Cyber Incident",
        "severity": "warning",
        "effect": lambda state, rng: _apply_cyber_incident(state, rng),
        "message": "Unattributed cyber attack hits critical infrastructure.",
    },
    {
        "name": "Diplomatic Crisis",
        "severity": "critical",
        "effect": lambda state, rng: _apply_tension_spike(state, rng),
        "message": "Diplomatic incident escalates global tension.",
    },
    {
        "name": "Military Exercise",
        "severity": "info",
        "effect": lambda state, rng: _apply_tension_rise(state, rng),
        "message": "Large-scale military exercises raise regional tensions.",
    },
    {
        "name": "Humanitarian Crisis",
        "severity": "warning",
        "effect": lambda state, rng: _apply_morale_hit(state, rng),
        "message": "Humanitarian crisis strains public morale.",
    },
]


def trigger_random_events(state: "GameState"):
    """Trigger random events at end of turn"""
    rng = state.rng

    # 40% chance of a random event per turn
    if rng.random() < 0.4:
        event = EVENT_POOL[rng.integers(0, len(EVENT_POOL))]
        event["effect"](state, rng)
        state.log_event(f"[EVENT] {event['name']}: {event['message']}", event["severity"])


def _apply_gdp_hit(state, rng):
    for country in state.countries.values():
        country.gdp *= rng.uniform(0.92, 0.98)


def _apply_cyber_incident(state, rng):
    target_code = rng.choice(list(state.countries.keys()))
    target = state.countries[target_code]
    target.infrastructure -= int(rng.integers(5, 15))
    target.infrastructure = max(0, target.infrastructure)


def _apply_tension_spike(state, rng):
    state.global_tension = min(100.0, state.global_tension + rng.uniform(10, 20))


def _apply_tension_rise(state, rng):
    state.global_tension = min(100.0, state.global_tension + rng.uniform(3, 8))


def _apply_morale_hit(state, rng):
    for country in state.countries.values():
        country.morale -= int(rng.integers(3, 10))
        country.morale = max(0, country.morale)
