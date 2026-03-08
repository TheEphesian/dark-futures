"""AI Executor - translates planned actions into actual system calls."""
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country
    from .strategy import ActionPlan, PlannedAction

from ..systems.intel import IntelSystem
from ..systems.military import MilitarySystem
from ..systems.blackops import BlackOpsSystem
from ..systems.nuclear import NuclearSystem


class AIExecutor:
    """Executes action plans through game system interfaces."""
    
    def __init__(self, game_state: "GameState"):
        self.state = game_state
        self.intel = IntelSystem(game_state)
        self.military = MilitarySystem(game_state)
        self.blackops = BlackOpsSystem(game_state)
        self.nuclear = NuclearSystem(game_state)
        
        # Track results for learning
        self._turn_results: List[Dict] = []
    
    def execute_plan(
        self, country: "Country", plan: "ActionPlan", action_history: Dict
    ) -> List[Dict]:
        """Execute all actions in an action plan. Returns list of results."""
        self._turn_results = []
        
        for action in plan.actions:
            result = self._execute_action(country, action)
            result["action_name"] = action.action_name
            result["target_country"] = action.target_country
            result["category"] = action.category.name
            self._turn_results.append(result)
            
            # Update action history for learning
            self._update_history(action, result, action_history)
            
            # Log AI decision
            success_str = "SUCCESS" if result.get("success", False) else "FAILED"
            self.state.log_event(
                f"[AI:{country.code}] {action.action_name} on {action.target_country}: {success_str}",
                "info" if result.get("success") else "warning",
            )
        
        return self._turn_results
    
    def _execute_action(self, country: "Country", action: "PlannedAction") -> Dict:
        """Route a planned action to the correct system."""
        try:
            name = action.action_name
            target = action.target_country
            params = action.params
            
            # Intel operations
            if name == "satellite_recon":
                success, data = self.intel.satellite_recon(
                    country, params.get("region", target)
                )
                return {"success": success, "data": data}
            
            elif name == "deploy_agent":
                success, msg = self.intel.deploy_agent(country, target)
                return {"success": success, "message": msg}
            
            elif name == "cyber_hack":
                success, data = self.intel.cyber_hack(
                    country, target, params.get("objective", "steal_intel")
                )
                return {"success": success, "data": data}
            
            # Military operations
            elif name == "air_strike":
                return self.military.air_strike(
                    country, target,
                    params.get("target_type", "infrastructure"),
                    params.get("sortie_count", 10),
                )
            
            elif name == "naval_blockade":
                return self.military.naval_blockade(country, target)
            
            # Black ops
            elif name == "assassinate":
                return self.blackops.assassinate(
                    country, target, params.get("target_type", "military_leader")
                )
            
            elif name == "sabotage":
                return self.blackops.sabotage(
                    country, target, params.get("target", "infrastructure")
                )
            
            elif name == "false_flag":
                return self.blackops.false_flag(
                    country, target, params.get("blamed_country", target)
                )
            
            # Nuclear operations
            elif name == "launch_icbm_strike":
                return self.nuclear.launch_icbm_strike(
                    country, target,
                    params.get("target_list", ["silos"]),
                    params.get("warhead_count", 1),
                    params.get("yield_mt", 1.0),
                )
            
            elif name == "slbm_strike":
                return self.nuclear.slbm_strike(
                    country, target, params.get("warhead_count", 1)
                )
            
            else:
                return {"success": False, "reason": f"Unknown action: {name}"}
        
        except Exception as e:
            return {"success": False, "reason": f"Execution error: {str(e)}"}
    
    def _update_history(
        self, action: "PlannedAction", result: Dict, history: Dict
    ):
        """Update action history for future learning."""
        key_prefix = f"{action.action_name}_{action.target_country}"
        
        # Track attempts
        attempts_key = f"{key_prefix}_attempts"
        history[attempts_key] = history.get(attempts_key, 0) + 1
        
        # Track failures
        if not result.get("success", False):
            fail_key = f"{key_prefix}_failures"
            history[fail_key] = history.get(fail_key, 0) + 1
        
        # Special tracking: compromised agents
        if action.action_name == "deploy_agent" and not result.get("success", False):
            comp_key = f"agent_compromised_{action.target_country}"
            history[comp_key] = history.get(comp_key, 0) + 1
    
    @property
    def last_results(self) -> List[Dict]:
        return self._turn_results
