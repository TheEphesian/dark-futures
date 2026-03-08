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

    def get_ai_status(self, country_code: str) -> Dict:
        """Get AI opponent status, redacted based on player's intel coverage.
        
        Visibility levels based on player's intel_coverage of the target:
        - 0-29%: Personality type only
        - 30-49%: + posture and action count
        - 50-69%: + action categories used
        - 70-84%: + recent actions with targets and success/fail
        - 85-100%: + full threat assessment data
        
        Args:
            country_code: AI country code to query (e.g. "RUS", "CHN")
            
        Returns:
            Dict with AI status info, detail scaled by intel coverage
        """
        if country_code not in self.state.ai_countries:
            return {"error": f"{country_code} is not an AI country"}
        
        # Get player's intel coverage of the target
        player = self.state.countries.get(self.state.player_country)
        if not player:
            return {"error": "Player country not found"}
        
        intel_coverage = getattr(player, "intel_coverage", 0.0)
        
        # Delegate to AIController's redaction-aware status method
        controller = self.state.get_ai_controller()
        return controller.get_ai_status(country_code, observer_intel_coverage=intel_coverage)

    def get_all_ai_status(self) -> Dict[str, Dict]:
        """Get status for all AI countries, each redacted by player intel."""
        return {code: self.get_ai_status(code) for code in self.state.ai_countries}

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
                parameters.get("target_list", ["cities"]),
                parameters.get("warhead_count", 10),
                parameters.get("yield_mt", 0.5),
            )

        elif action == "slbm_strike":
            return self.nuclear.slbm_strike(
                country,
                targets[0],
                parameters.get("warhead_count", 5),
            )

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def get_available_actions(self) -> List[Dict]:
        """Return list of available actions with descriptions"""
        return [
            {
                "action": "satellite_recon",
                "description": "Satellite reconnaissance of a region",
                "targets": "region name",
                "parameters": {},
                "cost": "2 fuel (success) / 1 fuel (failure)",
            },
            {
                "action": "deploy_agent",
                "description": "Deploy human intelligence asset to target country",
                "targets": "country code",
                "parameters": {},
                "cost": "Risk of agent loss",
            },
            {
                "action": "cyber_hack",
                "description": "Cyber operation against target",
                "targets": "country code",
                "parameters": {"objective": "steal_intel | disrupt_comms | sabotage_systems"},
                "cost": "Risk of detection + tension increase",
            },
            {
                "action": "air_strike",
                "description": "Conventional air strike",
                "targets": "country code",
                "parameters": {
                    "target_type": "bases | infrastructure | troops",
                    "sorties": "number of sorties (default 100)",
                },
                "cost": "fuel + munitions + aircraft losses",
            },
            {
                "action": "naval_blockade",
                "description": "Naval blockade of target country",
                "targets": "country code",
                "parameters": {},
                "cost": "Tension increase",
            },
            {
                "action": "assassinate",
                "description": "Assassination attempt on target",
                "targets": "country code",
                "parameters": {"target_type": "military_leader | political_leader | scientist"},
                "cost": "Risk of attribution + agent loss",
            },
            {
                "action": "sabotage",
                "description": "Sabotage enemy facility",
                "targets": "country code",
                "parameters": {"facility_type": "factory | power_plant | military_base | nuclear_facility"},
                "cost": "Risk of detection",
            },
            {
                "action": "false_flag",
                "description": "False flag operation",
                "targets": ["target country code", "country to blame"],
                "parameters": {},
                "cost": "Risk of exposure + massive tension",
            },
            {
                "action": "icbm_strike",
                "description": "ICBM nuclear strike",
                "targets": "country code",
                "parameters": {
                    "target_list": "cities | silos | command_centers",
                    "warhead_count": "number of warheads",
                    "yield_mt": "yield in megatons",
                },
                "cost": "ICBMs + warheads consumed, DEFCON 1, retaliation likely",
            },
            {
                "action": "slbm_strike",
                "description": "Submarine-launched nuclear strike",
                "targets": "country code",
                "parameters": {"warhead_count": "number of warheads"},
                "cost": "SLBMs + warheads consumed, DEFCON 1",
            },
            {
                "action": "get_ai_status",
                "description": "Get AI opponent status (redacted by intel coverage)",
                "targets": "country code",
                "parameters": {},
                "cost": "None",
            },
            {
                "action": "get_all_ai_status",
                "description": "Get status for all AI countries",
                "targets": "none",
                "parameters": {},
                "cost": "None",
            },
        ]
