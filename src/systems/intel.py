from typing import Dict, Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


class IntelSystem:
    """Handles intelligence gathering operations"""

    def __init__(self, game_state: "GameState"):
        self.state = game_state

    def satellite_recon(self, country: "Country", region: str) -> Tuple[bool, Dict]:
        """
        Satellite reconnaissance of region.
        Returns: (success, intel_data)
        """
        rng = self.state.rng

        base_chance = country.intel_coverage / 100
        weather_penalty = rng.uniform(0.0, 0.2)
        success_chance = float(np.clip(base_chance - weather_penalty, 0.1, 0.95))

        success = rng.random() < success_chance

        if success:
            accuracy = float(rng.uniform(0.6, 0.95) * (country.intel_coverage / 100))
            intel = {
                "region": region,
                "military_activity": rng.choice(["low", "medium", "high"]),
                "troop_count_estimate": int(rng.uniform(5000, 50000)),
                "accuracy": accuracy,
                "timestamp": self.state.turn,
            }
            country.fuel = max(0, country.fuel - 2)
            self.state.log_event(
                f"{country.name}: Satellite recon of {region} successful (acc: {accuracy:.0%})",
                "info",
            )
            return True, intel
        else:
            country.fuel = max(0, country.fuel - 1)
            self.state.log_event(
                f"{country.name}: Satellite recon of {region} failed", "warning"
            )
            return False, {}

    def deploy_agent(self, country: "Country", target_country: str) -> Tuple[bool, str]:
        """
        Deploy human intelligence asset.
        Returns: (success, result_msg)
        """
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
        """
        Cyber operation against enemy systems.
        Returns: (success, result)
        """
        rng = self.state.rng

        target_country = self.state.countries.get(target)
        if not target_country:
            return False, {"error": "Invalid target"}

        strength_diff = country.cyber_strength - target_country.cyber_strength
        base_chance = 0.5 + (strength_diff / 200)
        success_chance = float(np.clip(base_chance, 0.1, 0.8))

        success = rng.random() < success_chance
        traced = rng.random() < (0.5 if success else 0.8)

        result: Dict = {"success": success, "traced": traced, "objective": objective}

        if success:
            if objective == "steal_intel":
                result["data"] = f"Classified {target} intelligence"
            elif objective == "sabotage":
                damage = int(rng.integers(5, 15))
                target_country.infrastructure = max(
                    0, target_country.infrastructure - damage
                )
                result["damage"] = f"Infrastructure damaged by {damage} points"
            self.state.log_event(
                f"{country.name}: Cyber op vs {target} succeeded", "info"
            )
        else:
            self.state.log_event(
                f"{country.name}: Cyber op vs {target} failed", "warning"
            )

        if traced:
            self.state.global_tension = min(
                100.0, self.state.global_tension + float(rng.uniform(10, 25))
            )
            self.state.log_event(
                f"{target} traced cyber attack to {country.name}!", "critical"
            )

        country.morale = max(0, country.morale - 2)
        return success, result
