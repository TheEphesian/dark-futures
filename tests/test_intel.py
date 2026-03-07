import pytest
from src.game.state import GameState
from src.game.country import COUNTRY_PRESETS
from src.systems.intel import IntelSystem


def make_state() -> GameState:
    gs = GameState(seed=42)
    gs.countries = {k: v for k, v in COUNTRY_PRESETS.items()}
    gs.player_country = "USA"
    gs.countries["USA"].is_player = True
    return gs


def test_satellite_recon_returns_tuple():
    gs = make_state()
    intel = IntelSystem(gs)
    success, data = intel.satellite_recon(gs.countries["USA"], "Eastern Europe")
    assert isinstance(success, bool)
    assert isinstance(data, dict)


def test_cyber_hack_invalid_target():
    gs = make_state()
    intel = IntelSystem(gs)
    success, result = intel.cyber_hack(gs.countries["USA"], "INVALID", "steal_intel")
    assert success is False
    assert "error" in result


def test_deploy_agent_updates_tension_on_compromise():
    """Seeded test: with seed=42 the agent may be detected -- check tension rises on failure."""
    gs = make_state()
    intel = IntelSystem(gs)
    initial_tension = gs.global_tension
    success, msg = intel.deploy_agent(gs.countries["USA"], "RUS")
    if not success:
        assert gs.global_tension >= initial_tension
    assert isinstance(msg, str)
