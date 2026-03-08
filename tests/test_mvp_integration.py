"""End-to-end MVP integration tests for Dark Futures.

Tests the full game loop: engine init -> phase transitions -> 
actions with resource costs -> AI turns -> win/loss conditions.
"""
import pytest
import copy
from src.game.engine import GameEngine, Phase, GameOverReason, PHASE_ACTIONS
from src.game.country import Country, COUNTRY_PRESETS
from src.game.state import GameState
from src.mcp.tools import MCPTools


class TestEngineInit:
    """Test GameEngine initialization."""

    def test_engine_creates_all_countries(self):
        engine = GameEngine(player_country="USA", seed=42)
        assert "USA" in engine.state.countries
        assert engine.state.countries["USA"].is_player is True
        # All presets minus player should be AI
        assert len(engine.state.ai_countries) == len(COUNTRY_PRESETS) - 1

    def test_engine_custom_opponents(self):
        engine = GameEngine(
            player_country="USA",
            ai_countries=["RUS", "CHN"],
            seed=42,
        )
        assert len(engine.state.ai_countries) == 2
        assert "RUS" in engine.state.ai_countries
        assert "CHN" in engine.state.ai_countries

    def test_engine_starts_on_turn_1_intel_phase(self):
        engine = GameEngine(seed=42)
        assert engine.state.turn == 1
        assert engine.state.phase == "intel"
        assert engine.game_over is False

    def test_engine_difficulty_setting(self):
        engine = GameEngine(difficulty="hard", seed=42)
        assert engine.state.ai_difficulty == "hard"


class TestPhaseTransitions:
    """Test phase advancement and gating."""

    def test_phase_order(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        assert engine.current_phase == Phase.INTEL

        # INTEL -> OPS
        result = engine.advance_phase()
        assert result["success"] is True
        assert result["new_phase"] == "ops"

        # OPS -> RESOLVE (auto-advances to NUCLEAR)
        result = engine.advance_phase()
        assert result["success"] is True
        assert result["new_phase"] == "nuclear"
        assert result.get("auto_resolved") is True

    def test_nuclear_phase_ends_turn(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        # Advance through all phases
        engine.advance_phase()  # intel -> ops
        engine.advance_phase()  # ops -> resolve -> nuclear
        result = engine.advance_phase()  # nuclear -> end turn

        assert result["success"] is True
        assert result.get("new_turn") == 2
        assert engine.state.phase == "intel"
        assert engine.state.turn == 2

    def test_end_turn_shortcut(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        result = engine.end_turn()
        assert result["success"] is True
        assert engine.state.turn == 2
        assert engine.state.phase == "intel"


class TestPhaseGating:
    """Test that actions are rejected outside their allowed phase."""

    def test_reject_ops_in_intel_phase(self):
        engine = GameEngine(seed=42)
        valid, msg = engine.validate_action("air_strike")
        assert valid is False
        assert "not allowed in intel phase" in msg

    def test_allow_intel_in_intel_phase(self):
        engine = GameEngine(seed=42)
        valid, msg = engine.validate_action("satellite_recon")
        assert valid is True

    def test_reject_nuclear_in_ops_phase(self):
        engine = GameEngine(seed=42)
        engine.advance_phase()  # -> ops
        valid, msg = engine.validate_action("icbm_strike")
        assert valid is False

    def test_allow_ops_in_ops_phase(self):
        engine = GameEngine(seed=42)
        engine.advance_phase()  # -> ops
        valid, msg = engine.validate_action("air_strike")
        assert valid is True

    def test_mcp_tools_enforce_phase(self):
        engine = GameEngine(seed=42)
        tools = MCPTools(engine.state)
        # Try air_strike in intel phase
        result = tools.submit_action("air_strike", ["RUS"], {"target_type": "infrastructure"})
        assert result["success"] is False
        assert "not allowed" in result.get("error", "")


class TestResourceCosts:
    """Test that actions deduct resources correctly."""

    def test_satellite_recon_costs_fuel(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        tools = MCPTools(engine.state)
        player = engine.player
        initial_fuel = player.fuel

        result = tools.submit_action("satellite_recon", ["eastern_europe"], {})
        assert initial_fuel > player.fuel  # Fuel was deducted

    def test_air_strike_costs_fuel_and_munitions(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        tools = MCPTools(engine.state)
        engine.advance_phase()  # -> ops

        player = engine.player
        initial_fuel = player.fuel
        initial_munitions = player.munitions

        result = tools.submit_action(
            "air_strike", ["RUS"],
            {"target_type": "infrastructure", "sortie_count": 20},
        )
        assert result["success"] is True
        assert player.fuel < initial_fuel
        assert player.munitions < initial_munitions

    def test_insufficient_resources_rejected(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        tools = MCPTools(engine.state)
        # Drain all fuel
        engine.player.fuel = 0

        result = tools.submit_action("satellite_recon", ["eastern_europe"], {})
        assert result["success"] is False

    def test_nuclear_costs_fuel_per_warhead(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        tools = MCPTools(engine.state)
        # Advance to nuclear phase
        engine.advance_phase()  # -> ops
        engine.advance_phase()  # -> resolve -> nuclear

        player = engine.player
        initial_fuel = player.fuel

        result = tools.submit_action(
            "icbm_strike", ["RUS"],
            {"warhead_count": 2, "yield_mt": 0.5, "target_list": ["cities"]},
        )
        assert result["success"] is True
        assert player.fuel <= initial_fuel - 20  # 2 warheads * 10 fuel each


class TestAITurns:
    """Test AI opponent execution."""

    def test_ai_runs_on_turn_end(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        # End the turn -- AI should process
        result = engine.end_turn()
        assert "ai_actions" in result["phases_processed"][-1]

    def test_ai_status_returns_data(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        tools = MCPTools(engine.state)
        # First end a turn so AI has acted
        engine.end_turn()

        status = tools.get_ai_status("RUS")
        assert status["country"] == "RUS"
        assert "personality" in status

    def test_ai_status_redaction_tiers(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        engine.end_turn()  # Let AI act

        controller = engine.state.get_ai_controller()

        # Low intel = minimal info
        low = controller.get_ai_status("RUS", observer_intel_coverage=10)
        assert low["intel_tier"] == 1
        assert "recent_actions" not in low

        # High intel = full details
        high = controller.get_ai_status("RUS", observer_intel_coverage=90)
        assert high["intel_tier"] == 5
        assert "threat_report" in high


class TestWinLossConditions:
    """Test game-ending conditions."""

    def test_infrastructure_collapse_loses(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        engine.player.infrastructure = 0
        result = engine.advance_phase()

        assert result.get("game_over") is not None
        assert engine.game_over is True

    def test_government_overthrow_loses(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        engine.player.government_stability = 0
        result = engine.advance_phase()

        assert result.get("game_over") is not None
        assert engine.game_over_reason in (
            GameOverReason.GOVERNMENT_OVERTHROWN,
        )

    def test_all_ai_eliminated_wins(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        engine.state.countries["RUS"].infrastructure = 0
        result = engine.advance_phase()

        assert result.get("game_over") is not None
        assert engine.winner == "USA"

    def test_game_over_blocks_actions(self):
        engine = GameEngine(
            player_country="USA", ai_countries=["RUS"], seed=42
        )
        engine.player.infrastructure = 0
        engine.advance_phase()  # triggers game over

        valid, msg = engine.validate_action("satellite_recon")
        assert valid is False
        assert "Game is over" in msg


class TestFullGameLoop:
    """Play multiple turns and verify state consistency."""

    def test_play_5_turns(self):
        engine = GameEngine(
            player_country="USA",
            ai_countries=["RUS", "CHN"],
            difficulty="easy",
            seed=42,
        )
        tools = MCPTools(engine.state)

        for turn_num in range(1, 6):
            assert engine.state.turn == turn_num

            # Intel phase: do recon
            result = tools.submit_action("satellite_recon", ["russia"], {})
            # May succeed or fail, either is fine

            # Advance to ops
            engine.advance_phase()

            # Ops phase: air strike
            result = tools.submit_action(
                "air_strike", ["RUS"],
                {"target_type": "infrastructure", "sortie_count": 5},
            )

            # Advance to nuclear (goes through resolve)
            engine.advance_phase()

            # Skip nuclear, end turn
            engine.advance_phase()

            if engine.game_over:
                break

        # Verify state evolved
        assert engine.state.turn >= 2  # At least got past turn 1
        assert len(engine.state.events) > 0  # Events were logged

    def test_briefing_comprehensive(self):
        engine = GameEngine(
            player_country="USA",
            ai_countries=["RUS"],
            seed=42,
        )
        tools = MCPTools(engine.state)
        engine.end_turn()  # Let AI act first

        briefing = tools.request_briefing()

        assert "turn" in briefing
        assert "phase" in briefing
        assert "allowed_actions" in briefing
        assert "resources" in briefing
        assert "military" in briefing
        assert "intel" in briefing
        assert "state" in briefing
        assert "recent_events" in briefing
        assert "ai_opponents" in briefing
        assert "defcon" in briefing

    def test_resources_deplete_over_time(self):
        engine = GameEngine(
            player_country="USA",
            ai_countries=["RUS"],
            seed=42,
        )
        tools = MCPTools(engine.state)
        initial_fuel = engine.player.fuel

        # Burn through several intel ops
        for _ in range(10):
            tools.submit_action("satellite_recon", ["russia"], {})

        assert engine.player.fuel < initial_fuel


class TestCountryPresets:
    """Verify all country presets load correctly."""

    def test_all_presets_exist(self):
        expected = ["USA", "RUS", "CHN", "PRK", "IRN", "GBR", "FRA", "ISR", "IND", "PAK"]
        for code in expected:
            assert code in COUNTRY_PRESETS, f"Missing preset: {code}"

    def test_presets_have_required_fields(self):
        for code, country in COUNTRY_PRESETS.items():
            assert country.name, f"{code} missing name"
            assert country.code == code
            assert country.population > 0, f"{code} missing population"
            assert country.gdp > 0, f"{code} missing GDP"

    def test_nuclear_powers_have_warheads(self):
        nuclear_powers = ["USA", "RUS", "CHN", "PRK", "GBR", "FRA", "ISR", "IND", "PAK"]
        for code in nuclear_powers:
            assert COUNTRY_PRESETS[code].warheads > 0, f"{code} should have warheads"

    def test_iran_has_no_warheads(self):
        assert COUNTRY_PRESETS["IRN"].warheads == 0
