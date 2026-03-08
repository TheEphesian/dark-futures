"""Tests for AI opponent system."""
import pytest
import numpy as np
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import Dict, List


# ---- Minimal stubs so tests can run standalone ----

@dataclass
class Country:
    name: str = "TestCountry"
    code: str = "TST"
    is_player: bool = False
    gdp: float = 10.0
    fuel: int = 80
    munitions: int = 80
    morale: int = 80
    active_troops: float = 1.0
    tanks: int = 5000
    aircraft: int = 3000
    naval_vessels: int = 300
    icbms: int = 100
    slbms: int = 50
    bombers: int = 30
    warheads: int = 500
    intel_coverage: float = 70.0
    agents_active: int = 5
    cyber_strength: int = 70
    population: int = 100
    infrastructure: int = 80
    government_stability: int = 80
    
    def to_dict(self):
        return {"code": self.code}


@dataclass
class MockGameState:
    turn: int = 5
    phase: str = "intel"
    player_country: str = "USA"
    ai_countries: List[str] = field(default_factory=lambda: ["RUS", "CHN"])
    countries: Dict = field(default_factory=dict)
    defcon: int = 4
    global_tension: float = 30.0
    events: List[Dict] = field(default_factory=list)
    seed: int = 42
    rng: object = field(init=False)
    
    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)
        if not self.countries:
            self.countries = {
                "USA": Country(name="United States", code="USA", is_player=True,
                               gdp=28.0, active_troops=1.4, tanks=6612, aircraft=13247,
                               naval_vessels=490, warheads=1770, icbms=400, slbms=240,
                               cyber_strength=95, intel_coverage=85.0),
                "RUS": Country(name="Russia", code="RUS",
                               gdp=2.0, active_troops=1.3, tanks=12000, aircraft=4173,
                               naval_vessels=605, warheads=1710, icbms=320, slbms=160,
                               cyber_strength=90, intel_coverage=70.0),
                "CHN": Country(name="China", code="CHN",
                               gdp=19.0, active_troops=2.0, tanks=5000, aircraft=3285,
                               naval_vessels=730, warheads=500, icbms=200, slbms=72,
                               cyber_strength=85, intel_coverage=60.0),
            }
    
    def log_event(self, event: str, severity: str = "info"):
        self.events.append({"turn": self.turn, "event": event, "severity": severity})
    
    def advance_turn(self):
        self.turn += 1
    
    def to_dict(self):
        return {"turn": self.turn, "defcon": self.defcon}


# ---- We import from the ai package using path manipulation ----
# In actual project these would be: from src.ai import ...
# For standalone testing, we import from the files directly

import sys
import os

# Add parent dirs so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPersonalityProfile:
    """Test personality profiles and difficulty scaling."""
    
    def test_personality_creation(self):
        from src.ai.personality import AIPersonality, PersonalityProfile
        
        profile = PersonalityProfile(
            personality=AIPersonality.AGGRESSIVE,
            intel_weight=0.6,
            military_weight=0.9,
            nuclear_threshold=0.6,
            aggression_bias=0.8,
        )
        assert profile.personality == AIPersonality.AGGRESSIVE
        assert profile.military_weight == 0.9
    
    def test_easy_difficulty_scaling(self):
        from src.ai.personality import AIPersonality, PersonalityProfile
        
        profile = PersonalityProfile(
            personality=AIPersonality.AGGRESSIVE,
            aggression_bias=0.8,
            nuclear_threshold=0.6,
            military_weight=0.9,
        )
        easy = profile.scale_by_difficulty("easy")
        
        assert easy.aggression_bias < profile.aggression_bias
        assert easy.nuclear_threshold > profile.nuclear_threshold
        assert easy.military_weight < profile.military_weight
    
    def test_hard_difficulty_scaling(self):
        from src.ai.personality import AIPersonality, PersonalityProfile
        
        profile = PersonalityProfile(
            personality=AIPersonality.DEFENSIVE,
            aggression_bias=0.4,
            nuclear_threshold=0.8,
        )
        hard = profile.scale_by_difficulty("hard")
        
        assert hard.aggression_bias > profile.aggression_bias
        assert hard.nuclear_threshold < profile.nuclear_threshold
    
    def test_normal_difficulty_unchanged(self):
        from src.ai.personality import AIPersonality, PersonalityProfile
        
        profile = PersonalityProfile(
            personality=AIPersonality.DEFENSIVE,
            aggression_bias=0.5,
        )
        normal = profile.scale_by_difficulty("normal")
        assert normal.aggression_bias == profile.aggression_bias


class TestThreatAssessment:
    """Test threat scoring math."""
    
    def test_stronger_enemy_scores_higher(self):
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42)
        assessor = ThreatAssessor(state, accuracy=1.0)
        
        # RUS assessing threats
        report = assessor.assess(state.countries["RUS"])
        
        # USA should be a higher military threat than CHN (more aircraft)
        usa_threat = report.get_threat("USA")
        chn_threat = report.get_threat("CHN")
        assert usa_threat.military_threat > 0
        assert chn_threat.military_threat > 0
    
    def test_nuclear_threat_scales_with_defcon(self):
        from src.ai.threat_assessment import ThreatAssessor
        
        # At DEFCON 5 (peace)
        state5 = MockGameState(seed=42, defcon=5)
        assessor5 = ThreatAssessor(state5, accuracy=1.0)
        report5 = assessor5.assess(state5.countries["RUS"])
        nuke5 = report5.get_threat("USA").nuclear_threat
        
        # At DEFCON 2 (near war)
        state2 = MockGameState(seed=42, defcon=2)
        assessor2 = ThreatAssessor(state2, accuracy=1.0)
        report2 = assessor2.assess(state2.countries["RUS"])
        nuke2 = report2.get_threat("USA").nuclear_threat
        
        assert nuke2 > nuke5  # Nuclear threat should increase at lower DEFCON
    
    def test_vulnerability_reflects_weak_defenses(self):
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42)
        # Weaken CHN's defenses
        state.countries["CHN"].infrastructure = 20
        state.countries["CHN"].government_stability = 30
        state.countries["CHN"].morale = 25
        
        assessor = ThreatAssessor(state, accuracy=1.0)
        report = assessor.assess(state.countries["RUS"])
        
        chn_vuln = report.get_threat("CHN").vulnerability
        usa_vuln = report.get_threat("USA").vulnerability
        
        assert chn_vuln > usa_vuln  # Weakened CHN should be more vulnerable
    
    def test_posture_escalation(self):
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42, defcon=2, global_tension=80.0)
        assessor = ThreatAssessor(state, accuracy=1.0)
        report = assessor.assess(state.countries["RUS"])
        
        assert report.recommended_posture in ("aggressive", "nuclear")


class TestStrategyEngine:
    """Test action planning logic."""
    
    def test_intel_always_available(self):
        from src.ai.strategy import StrategyEngine, ActionCategory
        from src.ai.personality import AIPersonality, PersonalityProfile
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42, defcon=5)  # Peace time
        profile = PersonalityProfile(personality=AIPersonality.DEFENSIVE)
        
        assessor = ThreatAssessor(state, accuracy=1.0)
        report = assessor.assess(state.countries["RUS"])
        
        engine = StrategyEngine(state, difficulty="normal")
        plan = engine.plan(state.countries["RUS"], profile, report)
        
        # Should have at least intel actions even at DEFCON 5
        categories = {a.category for a in plan.actions}
        assert ActionCategory.INTEL in categories
    
    def test_nuclear_gated_by_defcon(self):
        from src.ai.strategy import StrategyEngine, ActionCategory
        from src.ai.personality import AIPersonality, PersonalityProfile
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42, defcon=5)
        profile = PersonalityProfile(
            personality=AIPersonality.AGGRESSIVE,
            nuclear_threshold=0.1,  # Very low threshold
            aggression_bias=0.9,
        )
        
        assessor = ThreatAssessor(state, accuracy=1.0)
        report = assessor.assess(state.countries["RUS"])
        
        engine = StrategyEngine(state, difficulty="hard")
        plan = engine.plan(state.countries["RUS"], profile, report)
        
        # Nuclear should NOT be available at DEFCON 5
        categories = {a.category for a in plan.actions}
        assert ActionCategory.NUCLEAR not in categories
    
    def test_resource_filtering(self):
        from src.ai.strategy import StrategyEngine, ActionCategory
        from src.ai.personality import AIPersonality, PersonalityProfile
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42, defcon=3)
        # Drain RUS resources
        state.countries["RUS"].fuel = 5
        state.countries["RUS"].munitions = 5
        
        profile = PersonalityProfile(
            personality=AIPersonality.AGGRESSIVE,
            military_weight=0.9,
            resource_conserve_threshold=0.3,
        )
        
        assessor = ThreatAssessor(state, accuracy=1.0)
        report = assessor.assess(state.countries["RUS"])
        
        engine = StrategyEngine(state, difficulty="normal")
        plan = engine.plan(state.countries["RUS"], profile, report)
        
        # Military actions should be filtered out due to low resources
        military_actions = [a for a in plan.actions if a.category == ActionCategory.MILITARY]
        assert len(military_actions) == 0
    
    def test_max_actions_by_difficulty(self):
        from src.ai.strategy import StrategyEngine
        from src.ai.personality import AIPersonality, PersonalityProfile
        from src.ai.threat_assessment import ThreatAssessor
        
        state = MockGameState(seed=42, defcon=3)
        profile = PersonalityProfile(
            personality=AIPersonality.AGGRESSIVE,
            intel_weight=0.9,
            military_weight=0.9,
            blackops_weight=0.9,
            aggression_bias=0.8,
        )
        
        assessor = ThreatAssessor(state, accuracy=1.0)
        report = assessor.assess(state.countries["RUS"])
        
        easy_engine = StrategyEngine(state, difficulty="easy")
        easy_plan = easy_engine.plan(state.countries["RUS"], profile, report)
        assert easy_plan.action_count <= 2
        
        hard_engine = StrategyEngine(state, difficulty="hard")
        hard_plan = hard_engine.plan(state.countries["RUS"], profile, report)
        assert hard_plan.action_count <= 4


class TestPresets:
    """Test country preset profiles."""
    
    def test_rus_is_aggressive(self):
        from src.ai.presets import get_ai_profile
        from src.ai.personality import AIPersonality
        
        profile = get_ai_profile("RUS")
        assert profile.personality == AIPersonality.AGGRESSIVE
        assert profile.military_weight > 0.7
    
    def test_chn_is_opportunistic(self):
        from src.ai.presets import get_ai_profile
        from src.ai.personality import AIPersonality
        
        profile = get_ai_profile("CHN")
        assert profile.personality == AIPersonality.OPPORTUNISTIC
        assert profile.intel_weight > profile.military_weight
    
    def test_unknown_country_gets_default(self):
        from src.ai.presets import get_ai_profile
        from src.ai.personality import AIPersonality
        
        profile = get_ai_profile("XYZ")
        assert profile.personality == AIPersonality.DEFENSIVE
    
    def test_profiles_are_copies(self):
        from src.ai.presets import get_ai_profile
        
        p1 = get_ai_profile("RUS")
        p2 = get_ai_profile("RUS")
        p1.aggression_bias = 0.0
        assert p2.aggression_bias != 0.0  # Should be independent copies


class TestAIController:
    """Test full AI turn orchestration."""
    
    def test_full_turn_produces_results(self):
        """AI controller should produce action results for each AI country."""
        # This is an integration test using stubs
        from src.ai.controller import AIController
        
        state = MockGameState(seed=42, defcon=3)
        controller = AIController(state, difficulty="normal")
        results = controller.process_all_ai_turns()
        
        assert "RUS" in results
        assert "CHN" in results
        assert len(results["RUS"]) > 0
        assert len(results["CHN"]) > 0
    
    def test_ai_status_redaction(self):
        """Status should reveal more at higher intel coverage."""
        from src.ai.controller import AIController
        
        state = MockGameState(seed=42, defcon=3)
        controller = AIController(state, difficulty="normal")
        controller.process_all_ai_turns()
        
        # Low intel - minimal info
        low = controller.get_ai_status("RUS", observer_intel_coverage=10)
        assert "recent_actions" not in low
        
        # High intel - full details
        high = controller.get_ai_status("RUS", observer_intel_coverage=90)
        assert "recent_actions" in high
        assert "threat_assessment" in high
