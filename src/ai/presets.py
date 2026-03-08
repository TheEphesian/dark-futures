"""Pre-built AI personality profiles for country archetypes."""
from typing import Dict
from .personality import AIPersonality, PersonalityProfile


# Country-specific AI profiles
COUNTRY_PROFILES: Dict[str, PersonalityProfile] = {
    "RUS": PersonalityProfile(
        personality=AIPersonality.AGGRESSIVE,
        intel_weight=0.6,
        military_weight=0.85,
        blackops_weight=0.7,
        nuclear_threshold=0.65,
        aggression_bias=0.75,
        preferred_intel="agent",
        preferred_strike="air",
        preferred_blackop="false_flag",
        resource_conserve_threshold=0.2,
        failure_memory_weight=0.5,
    ),
    "CHN": PersonalityProfile(
        personality=AIPersonality.OPPORTUNISTIC,
        intel_weight=0.9,
        military_weight=0.5,
        blackops_weight=0.8,
        nuclear_threshold=0.85,
        aggression_bias=0.4,
        preferred_intel="cyber",
        preferred_strike="naval",
        preferred_blackop="sabotage",
        resource_conserve_threshold=0.35,
        failure_memory_weight=0.8,
    ),
    "USA": PersonalityProfile(
        personality=AIPersonality.DEFENSIVE,
        intel_weight=0.85,
        military_weight=0.7,
        blackops_weight=0.6,
        nuclear_threshold=0.9,
        aggression_bias=0.35,
        preferred_intel="satellite",
        preferred_strike="air",
        preferred_blackop="sabotage",
        resource_conserve_threshold=0.25,
        failure_memory_weight=0.7,
    ),
    "PRK": PersonalityProfile(
        personality=AIPersonality.AGGRESSIVE,
        intel_weight=0.4,
        military_weight=0.7,
        blackops_weight=0.5,
        nuclear_threshold=0.5,
        aggression_bias=0.9,
        preferred_intel="agent",
        preferred_strike="air",
        preferred_blackop="assassinate",
        resource_conserve_threshold=0.15,
        failure_memory_weight=0.3,
    ),
    "IRN": PersonalityProfile(
        personality=AIPersonality.OPPORTUNISTIC,
        intel_weight=0.6,
        military_weight=0.5,
        blackops_weight=0.75,
        nuclear_threshold=0.75,
        aggression_bias=0.55,
        preferred_intel="agent",
        preferred_strike="naval",
        preferred_blackop="false_flag",
        resource_conserve_threshold=0.3,
        failure_memory_weight=0.6,
    ),
}

# Default profile for unknown countries
_DEFAULT_PROFILE = PersonalityProfile(
    personality=AIPersonality.DEFENSIVE,
    intel_weight=0.5,
    military_weight=0.5,
    blackops_weight=0.5,
    nuclear_threshold=0.8,
    aggression_bias=0.4,
)


def get_ai_profile(country_code: str) -> PersonalityProfile:
    """Get AI personality profile for a country.
    
    Returns country-specific profile if available, otherwise a balanced default.
    """
    import copy
    profile = COUNTRY_PROFILES.get(country_code, _DEFAULT_PROFILE)
    return copy.deepcopy(profile)
