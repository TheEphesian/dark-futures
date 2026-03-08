from typing import Dict, List

from ..game.state import GameState
from ..systems.intel import IntelSystem
from ..systems.military import MilitarySystem
from ..systems.blackops import BlackOpsSystem
from ..systems.nuclear import NuclearSystem


class MCPTools:
    """MCP tool definitions exposed to AI agents (OpenClaw)"""

    def __init__(self, game_state: GameState):
        self.state = game_state
        self.intel = IntelSystem(game_state)
        self.military = MilitarySystem(game_state)
        self.blackops = BlackOpsSystem(game_state)
        self.nuclear = NuclearSystem(game_state)

    def get_state(self) -> Dict:
        """Return full serialized game state"""
        return self.state.to_dict()

    def get_game_status(self) -> Dict:
        """Get current game status including phase, win/loss state."""
        from ..game.engine import PHASE_ACTIONS
        status = self.state.to_dict()
        status["allowed_actions"] = PHASE_ACTIONS.get(self.state.phase, [])
        return status

    def get_ai_status(self, country_code: str) -> Dict:
        """Get AI opponent status, redacted based on player's intel coverage."""
        if country_code not in self.state.ai_countries:
            return {"error": f"{country_code} is not an AI country"}

        player = self.state.countries.get(self.state.player_country)
        if not player:
            return {"error": "Player country not found"}

        intel_coverage = getattr(player, "intel_coverage", 0.0)
        controller = self.state.get_ai_controller()
        return controller.get_ai_status(country_code, observer_intel_coverage=intel_coverage)

    def get_all_ai_status(self) -> Dict[str, Dict]:
        """Get status for all AI countries, each redacted by player intel."""
        return {code: self.get_ai_status(code) for code in self.state.ai_countries}

    def submit_action(
        self, action: str, targets: List[str], parameters: Dict
    ) -> Dict:
        """Execute a game action with phase validation.

        action: satellite_recon | deploy_agent | cyber_hack |
                air_strike | naval_blockade |
                assassinate | sabotage | false_flag |
                icbm_strike | slbm_strike
        """
        # Phase validation
        valid, msg = self.state.validate_action(action)
        if not valid:
            return {"success": False, "error": msg}

        country = self.state.countries.get(self.state.player_country)
        if not country:
            return {"success": False, "error": "Player country not found"}

        if action == "satellite_recon":
            success, intel = self.intel.satellite_recon(
                country, targets[0] if targets else "unknown"
            )
            return {"success": success, "intel": intel}

        elif action == "deploy_agent":
            success, msg = self.intel.deploy_agent(
                country, targets[0] if targets else "unknown"
            )
            return {"success": success, "message": msg}

        elif action == "cyber_hack":
            success, result = self.intel.cyber_hack(
                country,
                targets[0] if targets else "unknown",
                parameters.get("objective", "intelligence"),
            )
            return {"success": success, "result": result}

        elif action == "air_strike":
            return self.military.air_strike(
                country,
                targets[0] if targets else "unknown",
                parameters.get("target_type", "infrastructure"),
                parameters.get("sortie_count", 10),
            )

        elif action == "naval_blockade":
            return self.military.naval_blockade(
                country, targets[0] if targets else "unknown"
            )

        elif action == "assassinate":
            return self.blackops.assassinate(
                country,
                targets[0] if targets else "unknown",
                parameters.get("target_type", "military_leader"),
            )

        elif action == "sabotage":
            return self.blackops.sabotage(
                country,
                targets[0] if targets else "unknown",
                parameters.get("target", "infrastructure"),
            )

        elif action == "false_flag":
            return self.blackops.false_flag(
                country,
                targets[0] if targets else "unknown",
                parameters.get("blamed_country", "unknown"),
            )

        elif action == "icbm_strike":
            return self.nuclear.launch_icbm_strike(
                country,
                targets[0] if targets else "unknown",
                parameters.get("target_list", ["cities"]),
                parameters.get("warhead_count", 1),
                parameters.get("yield_mt", 0.5),
            )

        elif action == "slbm_strike":
            return self.nuclear.slbm_strike(
                country,
                targets[0] if targets else "unknown",
                parameters.get("warhead_count", 1),
            )

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def advance_phase(self) -> Dict:
        """Advance to next game phase."""
        from ..game.engine import Phase
        old_phase = self.state.phase

        # Use engine if available, otherwise manual advance
        try:
            from ..game.engine import GameEngine
            # Create a temporary phase advancer
            phase = Phase(self.state.phase)
            new_phase = phase.next
            self.state.phase = new_phase.value
            return {
                "success": True,
                "old_phase": old_phase,
                "new_phase": new_phase.value,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def request_briefing(self) -> Dict:
        """Return a structured intelligence briefing for the AI agent"""
        from ..game.engine import PHASE_ACTIONS

        state = self.state
        player = state.countries.get(state.player_country)

        briefing: Dict = {
            "turn": state.turn,
            "phase": state.phase,
            "allowed_actions": PHASE_ACTIONS.get(state.phase, []),
            "defcon": state.defcon,
            "global_tension": state.global_tension,
            "your_country": state.player_country,
        }

        if player:
            briefing["resources"] = {
                "fuel": getattr(player, "fuel", 0),
                "munitions": getattr(player, "munitions", 0),
                "gdp": getattr(player, "gdp", 0),
                "morale": getattr(player, "morale", 0),
            }
            briefing["military"] = {
                "troops": getattr(player, "active_troops", 0),
                "aircraft": getattr(player, "aircraft", 0),
                "tanks": getattr(player, "tanks", 0),
                "naval": getattr(player, "naval_vessels", 0),
                "warheads": getattr(player, "warheads", 0),
                "icbms": getattr(player, "icbms", 0),
                "slbms": getattr(player, "slbms", 0),
            }
            briefing["intel"] = {
                "coverage": getattr(player, "intel_coverage", 0),
                "agents_active": getattr(player, "agents_active", 0),
                "cyber_strength": getattr(player, "cyber_strength", 0),
            }
            briefing["state"] = {
                "infrastructure": getattr(player, "infrastructure", 0),
                "government_stability": getattr(player, "government_stability", 0),
                "population": getattr(player, "population", 0),
            }

        briefing["recent_events"] = state.events[-10:]
        briefing["ai_opponents"] = self.get_all_ai_status()

        return briefing

    def end_turn(self) -> Dict:
        """End current turn and advance game state"""
        self.state.advance_turn()
        return {
            "success": True,
            "new_turn": self.state.turn,
            "phase": self.state.phase,
            "events": self.state.events[-5:],
        }
