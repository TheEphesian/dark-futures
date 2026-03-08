from typing import Dict, Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


# Resource costs per operation
INTEL_COSTS = {
    "satellite_recon": {"fuel": 2},
    "deploy_agent": {"fuel": 5, "gdp": 0.01},
    "cyber_hack": {"fuel": 3},
}


def _check_resources(country: "Country", costs: Dict) -> Tuple[bool, str]:
    """Check if country has enough resources. Returns (ok, error_msg)."""
    for resource, amount in costs.items():
        current = getattr(country, resource, 0)
        if isinstance(current, float):
            if current < amount:
                return False, f"Insufficient {resource}: have {current:.2f}, need {amount}"
        else:
            if current < amount:
                return False, f"Insufficient {resource}: have {current}, need {amount}"
    return True, "ok"


def _deduct_resources(country: "Country", costs: Dict):
    """Deduct resource costs from country."""
    for resource, amount in costs.items():
        current = getattr(country, resource, 0)
        setattr(country, resource, max(0, current - amount) if isinstance(current, int) else max(0.0, current - amount))


class IntelSystem:
    """Handles intelligence gathering operations"""

    def __init__(self, game_state: "GameState"):
        self.state = game_state

    def satellite_recon(self, country: "Country", region: str) -> Tuple[bool, Dict]:
        """Satellite reconnaissance of region. Costs: 2 fuel."""
        ok, msg = _check_resources(country, INTEL_COSTS["satellite_recon"])
        if not ok:
            return False, {"error": msg}

        rng = self.state.rng

        base_chance = country.intel_coverage / 100
        weather_penalty = rng.uniform(0.0, 0.2)
        success_chance = float(np.clip(base_chance - weather_penalty, 0.1, 0.95))

        success = rng.random() < success_chance

        # Always pay the cost
        _deduct_resources(country, INTEL_COSTS["satellite_recon"])

        if success:
            accuracy = float(rng.uniform(0.6, 0.95) * (country.intel_coverage / 100))
            intel = {
                "region": region,
                "military_activity": rng.choice(["low", "medium", "high"]),
                "troop_count_estimate": int(rng.uniform(5000, 50000)),
                "accuracy": accuracy,
                "timestamp": self.state.turn,
            }
            self.state.log_event(
                f"{country.name}: Satellite recon of {region} successful (acc: {accuracy:.0%})",
                "info",
            )
            return True, intel
        else:
            self.state.log_event(
                f"{country.name}: Satellite recon of {region} failed", "warning"
            )
            return False, {}

    def deploy_agent(self, country: "Country", target_country: str) -> Tuple[bool, str]:
        """Deploy human intelligence asset. Costs: 5 fuel, 0.01 GDP."""
        ok, msg = _check_resources(country, INTEL_COSTS["deploy_agent"])
        if not ok:
            return False, msg

        _deduct_resources(country, INTEL_COSTS["deploy_agent"])
        rng = self.state.rng

        detection_chance = 0.3
        target = self.state.countries.get(target_country)
        if target and target.cyber_strength > 80:
            detection_chance += 0.2

        detected = rng.random() < detection_chance

        if detected:
            self.state.global_tension = min(
                100.0, self.state.global_tension + float(rng.uniform(5, 15))
            )
            country.agents_active = max(0, country.agents_active - 1)
            msg = f"Agent deployed to {target_country} was COMPROMISED"
            self.state.log_event(f"{country.name}: {msg}", "critical")
            return False, msg
        else:
            country.agents_active += 1
            intel_value = rng.choice(
                ["leadership movements", "troop deployments", "nuclear readiness"]
            )
            msg = f"Agent successfully deployed to {target_country}. Intel: {intel_value}"
            self.state.log_event(f"{country.name}: {msg}", "info")
            return True, msg

    def cyber_hack(
        self, country: "Country", target: str, objective: str
    ) -> Tuple[bool, Dict]:
        """Cyber operation. Costs: 3 fuel. objective: intelligence | sabotage | disruption"""
        ok, msg = _check_resources(country, INTEL_COSTS["cyber_hack"])
        if not ok:
            return False, {"error": msg}

        _deduct_resources(country, INTEL_COSTS["cyber_hack"])
        rng = self.state.rng

        base_chance = country.cyber_strength / 100
        target_country = self.state.countries.get(target)
        defense = (target_country.cyber_strength / 100) if target_country else 0.5

        success_chance = float(np.clip(base_chance - defense * 0.5, 0.1, 0.85))
        success = rng.random() < success_chance
        detected = rng.random() < 0.4

        result = {"objective": objective, "success": success, "detected": detected}

        if success:
            if objective == "intelligence":
                result["data"] = rng.choice(
                    [
                        "military deployment plans",
                        "nuclear launch codes (partial)",
                        "diplomatic communications",
                    ]
                )
            elif objective == "sabotage" and target_country:
                damage = int(rng.integers(5, 20))
                target_country.infrastructure = max(
                    0, target_country.infrastructure - damage
                )
                result["damage"] = damage
            elif objective == "disruption" and target_country:
                target_country.cyber_strength = max(
                    0, target_country.cyber_strength - int(rng.integers(5, 15))
                )

        if detected:
            self.state.global_tension = min(
                100.0, self.state.global_tension + float(rng.uniform(5, 15))
            )

        severity = "info" if success else "warning"
        self.state.log_event(
            f"{country.name}: Cyber {objective} vs {target} - {'SUCCESS' if success else 'FAILED'}"
            + (f" [DETECTED]" if detected else ""),
            severity,
        )

        return success, result
