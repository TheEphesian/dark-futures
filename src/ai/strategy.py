"""Strategy engine - converts threat reports into action plans."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country
    from .personality import PersonalityProfile
    from .threat_assessment import ThreatReport


class ActionCategory(Enum):
    INTEL = auto()
    MILITARY = auto()
    BLACKOPS = auto()
    NUCLEAR = auto()


@dataclass
class PlannedAction:
    """A single action the AI plans to execute."""
    category: ActionCategory
    action_name: str          # e.g. "air_strike", "deploy_agent", "sabotage"
    target_country: str
    priority: float = 0.0     # Higher = execute first
    params: Dict = field(default_factory=dict)  # Action-specific parameters
    
    def __repr__(self):
        return f"PlannedAction({self.action_name} -> {self.target_country}, pri={self.priority:.1f})"


@dataclass
class ActionPlan:
    """Ordered list of actions for one AI turn."""
    country_code: str
    turn: int
    actions: List[PlannedAction] = field(default_factory=list)
    posture: str = "defensive"
    reasoning: str = ""
    
    def add(self, action: PlannedAction):
        self.actions.append(action)
        self.actions.sort(key=lambda a: a.priority, reverse=True)
    
    @property
    def action_count(self) -> int:
        return len(self.actions)


class StrategyEngine:
    """Converts threat assessment + personality into concrete action plans."""
    
    # Max actions per turn by difficulty
    MAX_ACTIONS = {"easy": 2, "normal": 3, "hard": 4}
    
    def __init__(self, game_state: "GameState", difficulty: str = "normal"):
        self.state = game_state
        self.difficulty = difficulty
        self.max_actions = self.MAX_ACTIONS.get(difficulty, 3)
    
    def plan(
        self,
        country: "Country",
        profile: "PersonalityProfile",
        threat_report: "ThreatReport",
        action_history: Optional[Dict] = None,
    ) -> ActionPlan:
        """Generate an action plan for this turn."""
        plan = ActionPlan(
            country_code=country.code,
            turn=self.state.turn,
            posture=threat_report.recommended_posture,
        )
        
        rng = self.state.rng
        history = action_history or {}
        
        # Determine available action categories based on escalation ladder
        available = self._escalation_ladder(profile, threat_report)
        
        # Generate candidate actions for each available category
        candidates: List[PlannedAction] = []
        
        if ActionCategory.INTEL in available:
            candidates.extend(self._plan_intel(country, profile, threat_report, history, rng))
        
        if ActionCategory.MILITARY in available:
            candidates.extend(self._plan_military(country, profile, threat_report, history, rng))
        
        if ActionCategory.BLACKOPS in available:
            candidates.extend(self._plan_blackops(country, profile, threat_report, history, rng))
        
        if ActionCategory.NUCLEAR in available:
            candidates.extend(self._plan_nuclear(country, profile, threat_report, rng))
        
        # Filter by resource constraints
        candidates = self._filter_by_resources(candidates, country, profile)
        
        # Add randomized variance so AI isn't perfectly predictable
        for c in candidates:
            c.priority += float(rng.uniform(-5, 5)) * (1 - profile.failure_memory_weight)
        
        # Sort and take top N
        candidates.sort(key=lambda a: a.priority, reverse=True)
        for action in candidates[:self.max_actions]:
            plan.add(action)
        
        plan.reasoning = (
            f"Posture: {plan.posture}, "
            f"Highest threat: {threat_report.highest_threat}, "
            f"Actions planned: {plan.action_count}"
        )
        
        return plan
    
    def _escalation_ladder(
        self, profile: "PersonalityProfile", report: "ThreatReport"
    ) -> List[ActionCategory]:
        """Determine which action categories are available based on DEFCON and personality."""
        defcon = self.state.defcon
        available = [ActionCategory.INTEL]  # Always available
        
        if defcon <= 4 or profile.aggression_bias > 0.6:
            available.append(ActionCategory.BLACKOPS)
        
        if defcon <= 3 or (profile.aggression_bias > 0.7 and self.state.global_tension > 30):
            available.append(ActionCategory.MILITARY)
        
        # Nuclear: only when DEFCON is critical AND threat exceeds personality threshold
        if defcon <= 2:
            max_threat = max(
                (t.composite_threat for t in report.threats.values()), default=0
            )
            normalized_threat = max_threat / 100
            if normalized_threat >= profile.nuclear_threshold:
                available.append(ActionCategory.NUCLEAR)
        
        return available
    
    def _plan_intel(
        self, country: "Country", profile: "PersonalityProfile",
        report: "ThreatReport", history: Dict, rng
    ) -> List[PlannedAction]:
        """Generate intel action candidates."""
        actions = []
        weight = profile.intel_weight * 100
        
        # Satellite recon on highest threat
        if report.highest_threat:
            actions.append(PlannedAction(
                category=ActionCategory.INTEL,
                action_name="satellite_recon",
                target_country=report.highest_threat,
                priority=weight * 0.8,
                params={"region": report.highest_threat},
            ))
        
        # Deploy agents -- skip targets where agents were previously compromised
        for code, threat in report.threats.items():
            compromised_count = history.get(f"agent_compromised_{code}", 0)
            if compromised_count >= 2 and rng.random() < profile.failure_memory_weight:
                continue  # Learn from past failures
            
            if threat.composite_threat > 30:
                actions.append(PlannedAction(
                    category=ActionCategory.INTEL,
                    action_name="deploy_agent",
                    target_country=code,
                    priority=weight * 0.6 + threat.composite_threat * 0.3,
                    params={"target_country": code},
                ))
        
        # Cyber hack against highest intel threat
        if report.highest_threat:
            ht = report.get_threat(report.highest_threat)
            if ht.intel_threat > 40 or profile.preferred_intel == "cyber":
                actions.append(PlannedAction(
                    category=ActionCategory.INTEL,
                    action_name="cyber_hack",
                    target_country=report.highest_threat,
                    priority=weight * 0.7,
                    params={
                        "target": report.highest_threat,
                        "objective": rng.choice(["steal_intel", "disrupt_comms", "plant_malware"]),
                    },
                ))
        
        return actions
    
    def _plan_military(
        self, country: "Country", profile: "PersonalityProfile",
        report: "ThreatReport", history: Dict, rng
    ) -> List[PlannedAction]:
        """Generate military action candidates."""
        actions = []
        weight = profile.military_weight * 100
        
        # Pick target: aggressive profiles hit strongest, others hit most vulnerable
        if profile.aggression_bias > 0.6:
            target_code = report.highest_threat
        else:
            target_code = report.most_vulnerable
        
        if not target_code:
            return actions
        
        target_threat = report.get_threat(target_code)
        
        # Air strike
        if country.aircraft > 50:
            sortie_count = max(5, int(country.aircraft * rng.uniform(0.02, 0.08)))
            target_type = rng.choice(["infrastructure", "troops", "bases"])
            
            # Bias target type by personality
            if profile.personality.name == "AGGRESSIVE":
                target_type = rng.choice(["troops", "troops", "infrastructure", "bases"])
            
            actions.append(PlannedAction(
                category=ActionCategory.MILITARY,
                action_name="air_strike",
                target_country=target_code,
                priority=weight * 0.9 + target_threat.military_threat * 0.2,
                params={
                    "target_type": target_type,
                    "sortie_count": sortie_count,
                },
            ))
        
        # Naval blockade
        if country.naval_vessels > 30:
            actions.append(PlannedAction(
                category=ActionCategory.MILITARY,
                action_name="naval_blockade",
                target_country=target_code,
                priority=weight * 0.6 + target_threat.economic_threat * 0.3,
                params={},
            ))
        
        return actions
    
    def _plan_blackops(
        self, country: "Country", profile: "PersonalityProfile",
        report: "ThreatReport", history: Dict, rng
    ) -> List[PlannedAction]:
        """Generate black ops action candidates."""
        actions = []
        weight = profile.blackops_weight * 100
        
        # Target most vulnerable country for blackops
        target_code = report.most_vulnerable
        if not target_code:
            return actions
        
        target_threat = report.get_threat(target_code)
        
        # Sabotage -- preferred for opportunistic profiles
        sab_target = rng.choice(["nuclear", "infrastructure", "comms"])
        if target_threat.nuclear_threat > 60:
            sab_target = "nuclear"  # Prioritize disabling nukes
        
        actions.append(PlannedAction(
            category=ActionCategory.BLACKOPS,
            action_name="sabotage",
            target_country=target_code,
            priority=weight * 0.8 + target_threat.vulnerability * 0.2,
            params={"target": sab_target},
        ))
        
        # Assassination
        if profile.aggression_bias > 0.5 or target_threat.composite_threat > 50:
            target_type = rng.choice(["military_leader", "political_leader", "scientist"])
            if target_threat.nuclear_threat > 70:
                target_type = "scientist"  # Slow their nuclear program
            
            actions.append(PlannedAction(
                category=ActionCategory.BLACKOPS,
                action_name="assassinate",
                target_country=target_code,
                priority=weight * 0.6 + profile.aggression_bias * 20,
                params={"target_type": target_type},
            ))
        
        # False flag -- only for opportunistic profiles with multiple enemies
        if (profile.personality == profile.personality.__class__["OPPORTUNISTIC"] 
                and len(report.threats) >= 2):
            sorted_threats = report.sorted_by_threat()
            if len(sorted_threats) >= 2:
                actions.append(PlannedAction(
                    category=ActionCategory.BLACKOPS,
                    action_name="false_flag",
                    target_country=sorted_threats[0].country_code,
                    priority=weight * 0.7,
                    params={"blamed_country": sorted_threats[1].country_code},
                ))
        
        return actions
    
    def _plan_nuclear(
        self, country: "Country", profile: "PersonalityProfile",
        report: "ThreatReport", rng
    ) -> List[PlannedAction]:
        """Generate nuclear action candidates -- ONLY called when conditions met."""
        actions = []
        
        if country.warheads <= 0:
            return actions
        
        target_code = report.highest_threat
        if not target_code:
            return actions
        
        # Prefer SLBM for first strike (stealthier), ICBM for full retaliation
        if country.slbms > 0:
            warhead_count = max(1, min(country.slbms, int(country.slbms * rng.uniform(0.2, 0.5))))
            actions.append(PlannedAction(
                category=ActionCategory.NUCLEAR,
                action_name="slbm_strike",
                target_country=target_code,
                priority=200,  # Nuclear is always highest priority when unlocked
                params={"warhead_count": warhead_count},
            ))
        elif country.icbms > 0:
            warhead_count = max(1, min(country.icbms, int(country.icbms * rng.uniform(0.3, 0.6))))
            targets = rng.choice(
                ["cities", "silos", "command_centers"],
                size=min(3, warhead_count),
                replace=True,
            ).tolist()
            actions.append(PlannedAction(
                category=ActionCategory.NUCLEAR,
                action_name="launch_icbm_strike",
                target_country=target_code,
                priority=200,
                params={
                    "target_list": targets,
                    "warhead_count": warhead_count,
                    "yield_mt": float(rng.uniform(0.5, 5.0)),
                },
            ))
        
        return actions
    
    def _filter_by_resources(
        self, candidates: List[PlannedAction], country: "Country",
        profile: "PersonalityProfile"
    ) -> List[PlannedAction]:
        """Remove actions the country can't afford."""
        threshold = profile.resource_conserve_threshold * 100
        filtered = []
        
        for action in candidates:
            # Skip military actions if low on fuel/munitions
            if action.category == ActionCategory.MILITARY:
                if country.fuel < threshold or country.munitions < threshold:
                    continue
            
            # Skip expensive intel if low fuel
            if action.action_name == "satellite_recon" and country.fuel < threshold * 0.5:
                continue
            
            # Nuclear requires actual warheads
            if action.category == ActionCategory.NUCLEAR and country.warheads <= 0:
                continue
            
            filtered.append(action)
        
        return filtered
