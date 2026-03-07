from typing import Dict, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


class BlackOpsSystem:
    """Covert operations"""

    def __init__(self, game_state: "GameState"):
        self.state = game_state

    def assassinate(
        self, country: "Country", target_country: str, target_type: str
    ) -> Dict:
        """
        Assassination attempt.
        target_type: military_leader | political_leader | scientist
        """
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
                f"{target_country} attributes assassination to {country.name}!",
                "critical",
            )

        country.morale = max(0, country.morale - 5)
        return result

    def sabotage_facility(
        self, country: "Country", target_country: str, facility_type: str
    ) -> Dict:
        """
        Sabotage enemy facility.
        facility_type: factory | power_plant | port | command_center
        """
        rng = self.state.rng

        success_chance = float(
            np.clip(0.5 + (country.agents_active * 0.08), 0.2, 0.75)
        )
        success = rng.random() < success_chance
        traced = rng.random() < 0.6

        result: Dict = {
            "success": success,
            "facility_type": facility_type,
            "traced": traced,
        }

        target = self.state.countries.get(target_country)
        if success and target:
            damage = float(rng.uniform(0.2, 0.4))
            if facility_type == "factory":
                target.munitions = max(0, int(target.munitions * (1 - damage)))
                result["impact"] = f"Production reduced {damage:.0%}"
            elif facility_type == "power_plant":
                target.infrastructure = max(
                    0, target.infrastructure - int(100 * damage)
                )
                result["impact"] = "Power grid damaged"
            elif facility_type == "port":
                target.fuel = max(0, int(target.fuel * (1 - damage)))
                result["impact"] = "Supply chain disrupted"
            elif facility_type == "command_center":
                target.cyber_strength = max(
                    0, int(target.cyber_strength * (1 - damage))
                )
                result["impact"] = "C2 capabilities degraded"

            self.state.log_event(
                f"Sabotage of {target_country} {facility_type} successful", "warning"
            )
        else:
            self.state.log_event(
                f"Sabotage attempt on {target_country} {facility_type} failed", "info"
            )

        if traced:
            self.state.global_tension = min(
                100.0,
                self.state.global_tension + float(rng.uniform(15, 30)),
            )
            self.state.log_event(
                f"{target_country} traced sabotage to {country.name}", "critical"
            )

        return result

    def false_flag(
        self, country: "Country", target: str, blamed: str
    ) -> Dict:
        """False flag operation: attack target, frame another country."""
        rng = self.state.rng

        sophistication = country.cyber_strength + (country.agents_active * 5)
        success_chance = float(np.clip(sophistication / 150, 0.2, 0.7))
        success = rng.random() < success_chance

        result: Dict = {"success": success}

        if success:
            self.state.global_tension = min(
                100.0,
                self.state.global_tension + float(rng.uniform(25, 50)),
            )
            if float(rng.random()) < 0.3:
                result["alliance_break"] = f"{target} breaks ties with {blamed}"
            self.state.log_event(
                f"False flag: {target} believes {blamed} attacked them", "critical"
            )
        else:
            self.state.global_tension = min(
                100.0,
                self.state.global_tension + float(rng.uniform(40, 60)),
            )
            if self.state.defcon > 1:
                self.state.defcon -= 1
            self.state.log_event(
                f"False flag EXPOSED! {target} and {blamed} identify {country.name}",
                "critical",
            )

        country.morale = max(0, country.morale - 10)
        return result
