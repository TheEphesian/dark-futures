"""AI Controller - top-level orchestrator for NPC turns."""
from typing import Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game.state import GameState

from .personality import PersonalityProfile
from .threat_assessment import ThreatAssessor, ThreatReport
from .strategy import StrategyEngine, ActionPlan
from .executor import AIExecutor
from .presets import get_ai_profile


class AIController:
    """Orchestrates AI turns for all NPC countries.
    
    Usage:
        controller = AIController(game_state, difficulty="normal")
        results = controller.process_all_ai_turns()
    """
    
    def __init__(self, game_state: "GameState", difficulty: str = "normal"):
        self.state = game_state
        self.difficulty = difficulty
        
        # Persistent state across turns
        self._profiles: Dict[str, PersonalityProfile] = {}
        self._action_histories: Dict[str, Dict] = {}
        self._threat_reports: Dict[str, ThreatReport] = {}
        self._turn_results: Dict[str, List[Dict]] = {}
        
        # Initialize profiles for all AI countries
        for code in game_state.ai_countries:
            profile = get_ai_profile(code)
            self._profiles[code] = profile.scale_by_difficulty(difficulty)
            self._action_histories[code] = {}
    
    def process_all_ai_turns(self) -> Dict[str, List[Dict]]:
        """Process turns for ALL AI countries. Returns {country_code: [results]}."""
        self._turn_results = {}
        
        for code in self.state.ai_countries:
            country = self.state.countries.get(code)
            if not country:
                continue
            
            results = self.process_single_turn(code)
            self._turn_results[code] = results
        
        return self._turn_results
    
    def process_single_turn(self, country_code: str) -> List[Dict]:
        """Process one AI country's full turn: assess -> plan -> execute."""
        country = self.state.countries.get(country_code)
        if not country:
            return []
        
        profile = self._profiles.get(country_code)
        if not profile:
            profile = get_ai_profile(country_code).scale_by_difficulty(self.difficulty)
            self._profiles[country_code] = profile
        
        history = self._action_histories.get(country_code, {})
        
        # Phase 1: Threat Assessment
        accuracy = {"easy": 0.7, "normal": 0.9, "hard": 1.0}.get(self.difficulty, 0.9)
        assessor = ThreatAssessor(self.state, accuracy=accuracy)
        threat_report = assessor.assess(country)
        self._threat_reports[country_code] = threat_report
        
        self.state.log_event(
            f"[AI:{country_code}] Threat assessment: posture={threat_report.recommended_posture}, "
            f"highest_threat={threat_report.highest_threat}",
            "info",
        )
        
        # Phase 2: Strategy Planning
        engine = StrategyEngine(self.state, difficulty=self.difficulty)
        plan = engine.plan(country, profile, threat_report, history)
        
        self.state.log_event(
            f"[AI:{country_code}] Strategy: {plan.reasoning}",
            "info",
        )
        
        # Phase 3: Execution
        executor = AIExecutor(self.state)
        results = executor.execute_plan(country, plan, history)
        
        return results
    
    def get_ai_status(self, country_code: str, observer_intel_coverage: float = 0.0) -> Dict:
        """Get AI status, redacted based on observer's intel coverage.
        
        Args:
            country_code: The AI country to query
            observer_intel_coverage: Observer's intel_coverage (0-100), controls detail level
        """
        profile = self._profiles.get(country_code)
        report = self._threat_reports.get(country_code)
        results = self._turn_results.get(country_code, [])
        
        status: Dict = {"country_code": country_code, "active": country_code in self.state.ai_countries}
        
        # Always visible
        status["personality"] = profile.personality.name if profile else "UNKNOWN"
        
        # Partially visible based on intel coverage
        if observer_intel_coverage >= 30:
            status["posture"] = report.recommended_posture if report else "unknown"
            status["actions_taken"] = len(results)
        
        if observer_intel_coverage >= 50:
            # Show action types but not targets
            status["action_types"] = [r.get("category", "?") for r in results]
        
        if observer_intel_coverage >= 70:
            # Show recent actions with targets
            status["recent_actions"] = [
                {
                    "action": r.get("action_name"),
                    "target": r.get("target_country"),
                    "success": r.get("success"),
                }
                for r in results[-5:]
            ]
        
        if observer_intel_coverage >= 85:
            # Full threat report visible
            if report:
                status["threat_assessment"] = {
                    code: {
                        "composite": round(t.composite_threat, 1),
                        "military": round(t.military_threat, 1),
                        "nuclear": round(t.nuclear_threat, 1),
                    }
                    for code, t in report.threats.items()
                }
        
        return status
    
    @property
    def profiles(self) -> Dict[str, PersonalityProfile]:
        return self._profiles
    
    @property
    def threat_reports(self) -> Dict[str, ThreatReport]:
        return self._threat_reports
