import pytest
from pathlib import Path
from src.game.state import GameState
from src.game.country import COUNTRY_PRESETS
from src.utils.persistence import save_game, load_game


def make_state() -> GameState:
    gs = GameState(seed=7)
    gs.countries = {k: v for k, v in COUNTRY_PRESETS.items()}
    gs.player_country = "USA"
    gs.countries["USA"].is_player = True
    gs.turn = 5
    gs.defcon = 3
    gs.global_tension = 55.0
    gs.log_event("Test save event", "info")
    return gs


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    """Game state survives a save/load cycle."""
    monkeypatch.chdir(tmp_path)
    gs = make_state()
    save_game(gs, "test_save.db")
    loaded = load_game("test_save.db")

    assert loaded.turn == 5
    assert loaded.defcon == 3
    assert abs(loaded.global_tension - 55.0) < 0.01
    assert "USA" in loaded.countries
    assert "RUS" in loaded.countries
    assert any("Test save event" in e["event"] for e in loaded.events)


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_game("nonexistent_file.db")
