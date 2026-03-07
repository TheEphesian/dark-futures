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

    def submit_action(
        self, action: str, targets: List[str], parameters: Dict
    ) -> Dict:
        """
        Execute a game action on behalf of the AI agent.

        action: satellite_recon | deploy_agent | cyber_hack |
                air_strike | naval_blockade |
                assassinate | sabotage | false_flag |
                icbm_strike | slbm_strike
        targets: list of country codes / region names
        parameters: action-specific dict
        """
        country = self.state.countries.get(self.state.player_country)
        if not country:
            return {"success": False, "error": "Player country not found"}

        if action == "satellite_recon":
            success, intel = self.intel.satellite_recon(country, targets[0])
            return {"success": success, "intel": intel}

        elif action == "deploy_agent":
            success, msg = self.intel.deploy_agent(country, targets[0])
            return {"success": success, "message": msg}

        elif action == "cyber_hack":
            success, result = self.intel.cyber_hack(
                country, targets[0], parameters.get("objective", "steal_intel")
            )
            return {"success": success, "result": result}

        elif action == "air_strike":
            return self.military.air_strike(
                country,
                targets[0],
                parameters.get("target_type", "infrastructure"),
                parameters.get("sorties", 100),
            )

        elif action == "naval_blockade":
            return self.military.naval_blockade(country, targets[0])

        elif action == "assassinate":
            return self.blackops.assassinate(
                country, targets[0], parameters.get("target_type", "military_leader")
            )

        elif action == "sabotage":
            return self.blackops.sabotage_facility(
                country, targets[0], parameters.get("facility_type", "factory")
            )

        elif action == "false_flag":
            return self.blackops.false_flag(
                country,
                targets[0],
                targets[1] if len(targets) > 1 else "unknown",
            )

        elif action == "icbm_strike":
            return self.nuclear.launch_icbm_strike(
                country,
                targets[0],
                targets[1:],
                parameters.get("warheads", 10),
                parameters.get("yield_mt", 1.0),
            )

        elif action == "slbm_strike":
            return self.nuclear.slbm_strike(
                country, targets[0], parameters.get("warheads", 5)
            )

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def request_advice(self, phase: str) -> Dict:
        """Return strategic AI advisor suggestions for the given phase"""
        suggestions = []
        country = self.state.countries.get(self.state.player_country)

        if phase == "intel":
            if country and country.intel_coverage < 70:
                suggestions.append({
                    "action": "satellite_recon",
                    "rationale": "Low intel coverage — gather intelligence",
                    "risk": "low",
                })
            if self.state.global_tension > 50 and country and country.agents_active < 3:
                suggestions.append({
                    "action": "deploy_agent",
                    "rationale": "High tension — deploy human intel asset",
                    "risk": "medium",
                })

        elif phase == "ops":
            if self.state.defcon <= 3:
                suggestions.append({
                    "action": "air_strike",
                    "rationale": "Escalation imminent — consider preemptive strike",
                    "risk": "high",
                })

        elif phase == "nuclear":
            if self.state.defcon == 1:
                suggestions.append({
                    "action": "icbm_strike",
                    "targets": ["enemy_silos", "command_centers"],
                    "rationale": "Counterforce strike to limit retaliation capability",
                    "risk": "catastrophic",
                })

        return {"phase": phase, "turn": self.state.turn, "suggestions": suggestions}

    def list_tools(self) -> List[Dict]:
        """List available MCP tools with schemas for agent discovery"""
        return [
            {
                "name": "get_state",
                "description": "Get current full game state",
                "parameters": {},
            },
            {
                "name": "submit_action",
                "description": "Execute a game action",
                "parameters": {
                    "action": "string — one of: satellite_recon, deploy_agent, cyber_hack, "
                              "air_strike, naval_blockade, assassinate, sabotage, "
                              "false_flag, icbm_strike, slbm_strike",
                    "targets": "list[str] — target country codes or regions",
                    "parameters": "dict — action-specific params (sorties, warheads, etc.)",
                },
            },
            {
                "name": "request_advice",
                "description": "Get AI advisor suggestions",
                "parameters": {"phase": "string — intel | ops | nuclear"},
            },
        ]
