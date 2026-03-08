"""Threat assessment engine - evaluates all countries and produces threat scores."""
from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


@dataclass
class CountryThreat:
    """Threat scores for a single country relative to the assessor."""
    country_code: str
    military_threat: float = 0.0    # 0-100
    nuclear_threat: float = 0.0     # 0-100
    economic_threat: float = 0.0    # 0-100
    intel_threat: float = 0.0       # 0-100
    composite_threat: float = 0.0   # Weighted aggregate 0-100
    is_player: bool = False

    # Tactical intel
    estimated_strength: float = 0.0   # Overall power rating
    vulnerability: float = 0.0        # How exploitable (inverse of defense)


@dataclass  
class ThreatReport:
    """Complete threat assessment for one AI country."""
    assessor_code: str
    turn: int
    threats: Dict[str, CountryThreat] = field(default_factory=dict)
    highest_threat: str = ""
    most_vulnerable: str = ""
    recommended_posture: str = "defensive"  # defensive | probing | aggressive | nuclear

    def get_threat(self, country_code: str) -> CountryThreat:
        return self.threats.get(country_code, CountryThreat(country_code=country_code))

    def sorted_by_threat(self) -> List[CountryThreat]:
        return sorted(self.threats.values(), key=lambda t: t.composite_threat, reverse=True)


class ThreatAssessor:
    """Evaluates threat levels from each country's perspective."""

    def __init__(self, game_state: "GameState", accuracy: float = 1.0):
        self.state = game_state
        self.accuracy = accuracy  # 0-1, reduced on easy difficulty

    def assess(self, country: "Country") -> ThreatReport:
        """Generate full threat report for given country."""
        report = ThreatReport(
            assessor_code=country.code,
            turn=self.state.turn,
        )

        for code, other in self.state.countries.items():
            if code == country.code:
                continue
            threat = self._assess_country(country, other)
            report.threats[code] = threat

        # Determine highest threat and most vulnerable
        if report.threats:
            sorted_threats = report.sorted_by_threat()
            report.highest_threat = sorted_threats[0].country_code

            most_vuln = max(report.threats.values(), key=lambda t: t.vulnerability)
            report.most_vulnerable = most_vuln.country_code

            # Determine recommended posture based on DEFCON and threat levels
            max_threat = sorted_threats[0].composite_threat
            report.recommended_posture = self._determine_posture(max_threat)

        return report

    def _assess_country(self, us: "Country", them: "Country") -> CountryThreat:
        """Score a single country as a threat."""
        rng = self.state.rng
        threat = CountryThreat(country_code=them.code, is_player=them.is_player)

        # Apply accuracy noise (fog of war)
        noise = lambda val: float(val * rng.uniform(
            max(0.5, self.accuracy - 0.2), 
            min(1.5, self.accuracy + 0.2)
        ))

        # Military threat: conventional force comparison
        our_power = us.active_troops * 1000 + us.tanks * 5 + us.aircraft * 10 + us.naval_vessels * 8
        their_power = them.active_troops * 1000 + them.tanks * 5 + them.aircraft * 10 + them.naval_vessels * 8
        if our_power > 0:
            mil_ratio = noise(their_power / our_power)
            threat.military_threat = float(np.clip(mil_ratio * 50, 0, 100))

        # Nuclear threat: warhead comparison weighted by DEFCON
        defcon_mult = (6 - self.state.defcon) / 5  # 0 at DEFCON 5, 1 at DEFCON 1
        if us.warheads > 0:
            nuke_ratio = noise(them.warheads / max(us.warheads, 1))
            threat.nuclear_threat = float(np.clip(nuke_ratio * 50 * (1 + defcon_mult), 0, 100))
        elif them.warheads > 0:
            threat.nuclear_threat = float(np.clip(noise(80 + defcon_mult * 20), 0, 100))

        # Economic threat: GDP comparison
        if us.gdp > 0:
            econ_ratio = noise(them.gdp / us.gdp)
            threat.economic_threat = float(np.clip(econ_ratio * 40, 0, 100))

        # Intel threat: cyber + agents
        intel_power = them.cyber_strength + them.agents_active * 10
        our_intel = us.cyber_strength + us.agents_active * 10
        if our_intel > 0:
            intel_ratio = noise(intel_power / max(our_intel, 1))
            threat.intel_threat = float(np.clip(intel_ratio * 50, 0, 100))

        # Composite: weighted average
        threat.composite_threat = (
            threat.military_threat * 0.35 +
            threat.nuclear_threat * 0.30 +
            threat.economic_threat * 0.15 +
            threat.intel_threat * 0.20
        )

        # Estimated overall strength
        threat.estimated_strength = noise(
            their_power * 0.001 + them.warheads * 2 + them.gdp * 100 + them.cyber_strength
        )

        # Vulnerability: inverse of defensive capability
        defense_score = (
            them.infrastructure / 100 * 0.3 +
            them.government_stability / 100 * 0.3 +
            them.cyber_strength / 100 * 0.2 +
            them.morale / 100 * 0.2
        )
        threat.vulnerability = float(np.clip((1 - defense_score) * 100, 0, 100))

        return threat

    def _determine_posture(self, max_threat: float) -> str:
        """Determine recommended strategic posture."""
        defcon = self.state.defcon
        tension = self.state.global_tension

        if defcon <= 2 and max_threat > 70:
            return "nuclear"
        elif defcon <= 3 and (max_threat > 50 or tension > 70):
            return "aggressive"
        elif max_threat > 30 or tension > 40:
            return "probing"
        return "defensive"
