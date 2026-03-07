import pytest
from src.game.state import GameState
from src.game.country import COUNTRY_PRESETS


def make_state() -> GameState:
    gs = GameState()
    gs.countries = {k: v for k, v in COUNTRY_PRESETS.items()}
    gs.player_country = "USA"
    gs.countries["USA"].is_player = True
    return gs


def test_initial_defcon():
    gs = make_state()
    assert gs.defcon == 5


def test_advance_turn():
    gs = make_state()
    gs.global_tension = 20.0
    gs.advance_turn()
    assert gs.turn == 1
    assert gs.phase == "intel"
    assert gs.global_tension == 18.0


def test_log_event():
    gs = make_state()
    gs.log_event("Test event", "info")
    assert len(gs.events) == 1
    assert gs.events[0]["event"] == "Test event"


def test_to_dict_keys():
    gs = make_state()
    d = gs.to_dict()
    for key in ("turn", "phase", "player_country", "defcon", "global_tension", "countries", "events"):
        assert key in d


def test_tension_clamp():
    gs = make_state()
    gs.global_tension = 1.0
    gs.advance_turn()
    assert gs.global_tension == 0.0  # clamped at 0
