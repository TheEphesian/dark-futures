import pytest
from src.game.state import GameState
from src.game.country import COUNTRY_PRESETS
from src.systems.nuclear import NuclearSystem


def make_state() -> GameState:
    gs = GameState(seed=99)
    gs.countries = {k: v for k, v in COUNTRY_PRESETS.items()}
    gs.player_country = "USA"
    gs.countries["USA"].is_player = True
    return gs


def test_icbm_requires_warheads():
    gs = make_state()
    nuke = NuclearSystem(gs)
    usa = gs.countries["USA"]
    usa.icbms = 0
    usa.warheads = 0
    result = nuke.launch_icbm_strike(usa, "RUS", ["cities"], 10, 1.0)
    assert result["success"] is False


def test_icbm_sets_defcon_1():
    gs = make_state()
    nuke = NuclearSystem(gs)
    usa = gs.countries["USA"]
    result = nuke.launch_icbm_strike(usa, "RUS", ["cities"], 5, 1.0)
    if result["success"]:
        assert gs.defcon == 1
        assert gs.global_tension == 100.0


def test_slbm_requires_slbms():
    gs = make_state()
    nuke = NuclearSystem(gs)
    usa = gs.countries["USA"]
    usa.slbms = 0
    result = nuke.slbm_strike(usa, "RUS", 5)
    assert result["success"] is False


def test_nuclear_reduces_target_population():
    gs = make_state()
    nuke = NuclearSystem(gs)
    usa = gs.countries["USA"]
    rus = gs.countries["RUS"]
    initial_pop = rus.population
    nuke.launch_icbm_strike(usa, "RUS", ["cities"], 20, 1.0)
    assert rus.population <= initial_pop
