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
    """Orchestrates AI turns for all NPC countries."""

    def __init__(self, game_state: "GameState", difficulty: str = "normal"):
        self.state = game_state
        self.difficulty = difficulty

        self._profiles: Dict[str, PersonalityProfile] = {}
        self._action_histories: Dict[str, Dict] = {}
        self._threat_reports: Dict[str, ThreatReport] = {}
        self._turn_results: Dict[str, List[Dict]] = {}

        for code in game_state.ai_countries:
            profile = get_ai_profile(code)
            self._profiles[code] = profile.scale_by_difficulty(difficulty)
            self._action_histories[code] = {}

    def process_all_ai_turns(self) -> Dict[str, List[Dict]]:
        """Process turns for ALL AI countries."""
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
        engine = StrategyEngine(self.state, profile)
        plan = engine.plan(country, threat_report, history)

        self.state.log_event(
            f"[AI:{country_code}] Strategy planned: {len(plan.actions)} actions, "
            f"priority={plan.priority}",
            "info",
        )

        # Phase 3: Execute Actions
        executor = AIExecutor(self.state)
        results = executor.execute(country, plan)

        # Update action history
        for r in results:
            action_type = r.get("action_type", "unknown")
            if action_type not in history:
                history[action_type] = {"attempts": 0, "successes": 0, "failures": 0}
            history[action_type]["attempts"] += 1
            if r.get("success"):
                history[action_type]["successes"] += 1
            else:
                history[action_type]["failures"] += 1
        self._action_histories[country_code] = history

        successes = sum(1 for r in results if r.get("success"))
        self.state.log_event(
            f"[AI:{country_code}] Turn complete: {successes}/{len(results)} actions succeeded",
            "info" if successes > 0 else "warning",
        )

        return results

    def get_ai_status(self, country_code: str, observer_intel_coverage: float = 0.0) -> Dict:
        """Get AI status with 5-tier intel redaction based on observer's coverage.

        Visibility tiers:
        - 0-29%:  Personality type only
        - 30-49%: + posture and action count
        - 50-69%: + action categories used
        - 70-84%: + recent actions with targets and success/fail
        - 85-100%: + full threat assessment data
        """
        profile = self._profiles.get(country_code)
        if not profile:
            return {"country": country_code, "status": "unknown"}

        coverage = observer_intel_coverage
        status: Dict = {"country": country_code}

        # Tier 1 (0-29%): Personality only
        status["personality"] = profile.personality.value
        status["intel_tier"] = 1

        # Tier 2 (30-49%): + posture and action count
        if coverage >= 30:
            status["intel_tier"] = 2
            threat_report = self._threat_reports.get(country_code)
            if threat_report:
                status["posture"] = threat_report.recommended_posture
            last_results = self._turn_results.get(country_code, [])
            status["last_action_count"] = len(last_results)

        # Tier 3 (50-69%): + action categories
        if coverage >= 50:
            status["intel_tier"] = 3
            history = self._action_histories.get(country_code, {})
            status["action_categories"] = list(history.keys())

        # Tier 4 (70-84%): + recent actions with details
        if coverage >= 70:
            status["intel_tier"] = 4
            last_results = self._turn_results.get(country_code, [])
            status["recent_actions"] = [
                {
                    "action_type": r.get("action_type", "unknown"),
                    "target": r.get("target", "unknown"),
                    "success": r.get("success", False),
                }
                for r in last_results[-5:]
            ]

        # Tier 5 (85-100%): + full threat assessment
        if coverage >= 85:
            status["intel_tier"] = 5
            threat_report = self._threat_reports.get(country_code)
            if threat_report:
                status["threat_report"] = {
                    "highest_threat": threat_report.highest_threat,
                    "recommended_posture": threat_report.recommended_posture,
                    "scores": {
                        code: {
                            "military": round(s.military_score, 2),
                            "nuclear": round(s.nuclear_score, 2),
                            "economic": round(s.economic_score, 2),
                            "intel": round(s.intel_score, 2),
                            "composite": round(s.composite, 2),
                        }
                        for code, s in threat_report.threat_scores.items()
                    } if hasattr(threat_report, 'threat_scores') else {},
                }
            history = self._action_histories.get(country_code, {})
            status["full_history"] = history

        return status

    def get_threat_report(self, country_code: str) -> Optional[ThreatReport]:
        """Get the most recent threat report for a country."""
        return self._threat_reports.get(country_code)

    def get_action_history(self, country_code: str) -> Dict:
        """Get cumulative action history for a country."""
        return self._action_histories.get(country_code, {})

    def get_last_results(self, country_code: str) -> List[Dict]:
        """Get results from the most recent turn for a country."""
        return self._turn_results.get(country_code, [])
