from typing import Dict, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


# Resource costs per operation
BLACKOPS_COSTS = {
    "assassinate": {"fuel": 8, "gdp": 0.02},
    "sabotage": {"fuel": 5, "munitions": 5},
    "false_flag": {"fuel": 10, "gdp": 0.03},
}


def _check_resources(country: "Country", costs: Dict) -> tuple:
    for resource, amount in costs.items():
        current = getattr(country, resource, 0)
        if current < amount:
            return False, f"Insufficient {resource}: have {current}, need {amount}"
    return True, "ok"


def _deduct_resources(country: "Country", costs: Dict):
    for resource, amount in costs.items():
        current = getattr(country, resource, 0)
        if isinstance(current, float):
            setattr(country, resource, max(0.0, current - amount))
        else:
            setattr(country, resource, max(0, current - amount))


class BlackOpsSystem:
    """Covert operations"""

    def __init__(self, game_state: "GameState"):
        self.state = game_state

    def assassinate(
        self, country: "Country", target_country: str, target_type: str
    ) -> Dict:
        """Assassination attempt. Costs: 8 fuel, 0.02 GDP.
        target_type: military_leader | political_leader | scientist
        """
        ok, msg = _check_resources(country, BLACKOPS_COSTS["assassinate"])
        if not ok:
            return {"success": False, "reason": msg}

        _deduct_resources(country, BLACKOPS_COSTS["assassinate"])
        rng = self.state.rng

        base_chances = {
            "military_leader": 0.35,
            "political_leader": 0.25,
            "scientist": 0.45,
        }
        base_chance = base_chances.get(target_type, 0.3)

        intel_mod = country.agents_active * 0.05
        target = self.state.countries.get(target_country)
        security_mod = (target.cyber_strength / 200) if target else 0

        success_chance = float(
            np.clip(base_chance + intel_mod - security_mod, 0.1, 0.6)
        )
        attribution_chance = float(rng.uniform(0.3, 0.7))

        success = rng.random() < success_chance
        attributed = rng.random() < attribution_chance

        result: Dict = {
            "success": success,
            "target_type": target_type,
            "attributed": attributed,
        }

        if success and target:
            if target_type == "military_leader":
                target.morale = max(0, target.morale - int(rng.integers(15, 30)))
                result["impact"] = "Military operations disrupted"
            elif target_type == "political_leader":
                target.government_stability = max(
                    0,
                    target.government_stability - int(rng.integers(20, 40)),
                )
                self.state.global_tension = min(
                    100.0, self.state.global_tension + 30
                )
                result["impact"] = "Government destabilized"
            elif target_type == "scientist":
                target.warheads = int(target.warheads * 0.95)
                result["impact"] = "Nuclear program delayed"

            self.state.log_event(
                f"Assassination of {target_country} {target_type} SUCCESSFUL",
                "critical",
            )
        else:
            if float(rng.random()) < 0.4:
                country.agents_active = max(0, country.agents_active - 1)
                result["agent_lost"] = True
            self.state.log_event(
                f"Assassination attempt on {target_country} {target_type} FAILED",
                "warning",
            )

        if attributed:
            self.state.global_tension = min(
                100.0,
                self.state.global_tension + float(rng.uniform(20, 40)),
            )
            if self.state.defcon > 2:
                self.state.defcon -= 1
            self.state.log_event(
                f"{country.name} ATTRIBUTED to assassination attempt on {target_country}",
                "critical",
            )

        return result

    def sabotage(
        self, country: "Country", target_country: str, sabotage_target: str
    ) -> Dict:
        """Sabotage operation. Costs: 5 fuel, 5 munitions.
        sabotage_target: infrastructure | military | nuclear | communications
        """
        ok, msg = _check_resources(country, BLACKOPS_COSTS["sabotage"])
        if not ok:
            return {"success": False, "reason": msg}

        _deduct_resources(country, BLACKOPS_COSTS["sabotage"])
        rng = self.state.rng

        target = self.state.countries.get(target_country)
        if not target:
            return {"success": False, "reason": "Invalid target"}

        base_chance = 0.4 + (country.agents_active * 0.05)
        success_chance = float(np.clip(base_chance, 0.15, 0.7))
        success = rng.random() < success_chance
        detected = rng.random() < 0.35

        result: Dict = {
            "success": success,
            "sabotage_target": sabotage_target,
            "detected": detected,
        }

        if success:
            if sabotage_target == "infrastructure":
                dmg = int(rng.integers(10, 25))
                target.infrastructure = max(0, target.infrastructure - dmg)
                result["damage"] = dmg
            elif sabotage_target == "military":
                target.munitions = max(0, target.munitions - int(rng.integers(5, 15)))
                target.fuel = max(0, target.fuel - int(rng.integers(5, 15)))
                result["impact"] = "Military supplies damaged"
            elif sabotage_target == "nuclear":
                target.warheads = max(0, target.warheads - int(rng.integers(1, 5)))
                result["impact"] = "Nuclear warheads compromised"
            elif sabotage_target == "communications":
                target.cyber_strength = max(
                    0, target.cyber_strength - int(rng.integers(10, 25))
                )
                result["impact"] = "Communications disrupted"

            self.state.log_event(
                f"Sabotage of {target_country} {sabotage_target} SUCCESSFUL",
                "warning",
            )
        else:
            self.state.log_event(
                f"Sabotage attempt on {target_country} {sabotage_target} FAILED",
                "info",
            )

        if detected:
            self.state.global_tension = min(
                100.0,
                self.state.global_tension + float(rng.uniform(10, 25)),
            )
            self.state.log_event(
                f"Sabotage operation on {target_country} was DETECTED", "critical"
            )

        return result

    def false_flag(
        self, country: "Country", target_country: str, blamed_country: str
    ) -> Dict:
        """False flag operation. Costs: 10 fuel, 0.03 GDP."""
        ok, msg = _check_resources(country, BLACKOPS_COSTS["false_flag"])
        if not ok:
            return {"success": False, "reason": msg}

        _deduct_resources(country, BLACKOPS_COSTS["false_flag"])
        rng = self.state.rng

        target = self.state.countries.get(target_country)
        blamed = self.state.countries.get(blamed_country)

        if not target or not blamed:
            return {"success": False, "reason": "Invalid target or blamed country"}

        success_chance = float(np.clip(0.35 + country.agents_active * 0.05, 0.15, 0.6))
        success = rng.random() < success_chance
        discovered = rng.random() < 0.25

        result: Dict = {
            "success": success,
            "target": target_country,
            "blamed": blamed_country,
            "discovered": discovered,
        }

        if success and not discovered:
            self.state.global_tension = min(
                100.0, self.state.global_tension + float(rng.uniform(15, 30))
            )
            if blamed:
                blamed.morale = max(0, blamed.morale - int(rng.integers(5, 15)))
            result["impact"] = f"{target_country} blames {blamed_country}"
            self.state.log_event(
                f"False flag: {target_country} now blames {blamed_country}",
                "warning",
            )
        elif discovered:
            self.state.global_tension = min(
                100.0, self.state.global_tension + float(rng.uniform(20, 40))
            )
            country.morale = max(0, country.morale - int(rng.integers(10, 20)))
            result["impact"] = "Operation discovered - diplomatic backlash"
            self.state.log_event(
                f"False flag by {country.name} DISCOVERED - international condemnation",
                "critical",
            )
        else:
            self.state.log_event("False flag operation FAILED", "info")

        return result
