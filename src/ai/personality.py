"""AI Personality system - defines behavioral archetypes for NPC countries."""
from dataclasses import dataclass
from enum import Enum, auto


class AIPersonality(Enum):
    """Core personality archetypes."""
    AGGRESSIVE = auto()    # Favors military action, lower escalation threshold
    DEFENSIVE = auto()     # Builds intel, retaliates only when attacked  
    OPPORTUNISTIC = auto() # Waits for weakness, heavy on blackops and intel


@dataclass
class PersonalityProfile:
    """Tunable weight vector controlling AI behavior."""
    personality: AIPersonality

    # Action category weights (0.0 - 1.0, higher = more likely)
    intel_weight: float = 0.5
    military_weight: float = 0.5
    blackops_weight: float = 0.5

    # Escalation thresholds
    nuclear_threshold: float = 0.8  # 0-1, how much threat before considering nukes
    aggression_bias: float = 0.5    # 0=passive, 1=hair-trigger

    # Tactical preferences
    preferred_intel: str = "satellite"   # satellite | agent | cyber
    preferred_strike: str = "air"        # air | naval
    preferred_blackop: str = "sabotage"  # assassinate | sabotage | false_flag

    # Resource management
    resource_conserve_threshold: float = 0.3  # Below this %, avoid costly ops

    # Learning modifiers  
    failure_memory_weight: float = 0.7  # How much past failures affect decisions

    def scale_by_difficulty(self, difficulty: str) -> "PersonalityProfile":
        """Return a new profile scaled by difficulty level."""
        import copy
        p = copy.deepcopy(self)
        if difficulty == "easy":
            p.aggression_bias *= 0.6
            p.nuclear_threshold = min(1.0, p.nuclear_threshold + 0.2)
            p.intel_weight *= 0.7
            p.military_weight *= 0.7
            p.blackops_weight *= 0.7
        elif difficulty == "hard":
            p.aggression_bias = min(1.0, p.aggression_bias * 1.3)
            p.nuclear_threshold = max(0.3, p.nuclear_threshold - 0.15)
            p.intel_weight = min(1.0, p.intel_weight * 1.2)
            p.military_weight = min(1.0, p.military_weight * 1.2)
            p.blackops_weight = min(1.0, p.blackops_weight * 1.2)
        return p
