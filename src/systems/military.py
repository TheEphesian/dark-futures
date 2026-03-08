from typing import Dict, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


class MilitarySystem:
    """Conventional military operations"""

    def __init__(self, game_state: "GameState"):
        self.state = game_state

    def air_strike(
        self,
        attacker: "Country",
        target_country: str,
        target_type: str,
        sortie_count: int,
    ) -> Dict:
        """Launch conventional air strike. Costs: fuel (sorties*0.5), munitions (sorties*0.3)."""
        rng = self.state.rng

        fuel_cost = int(sortie_count * 0.5)
        munitions_cost = int(sortie_count * 0.3)

        if attacker.fuel < fuel_cost:
            return {"success": False, "reason": f"Insufficient fuel: have {attacker.fuel}, need {fuel_cost}"}
        if attacker.munitions < munitions_cost:
            return {"success": False, "reason": f"Insufficient munitions: have {attacker.munitions}, need {munitions_cost}"}

        target = self.state.countries.get(target_country)
        if not target:
            return {"success": False, "reason": "Invalid target"}

        # Deduct costs upfront
        attacker.fuel = max(0, attacker.fuel - fuel_cost)
        attacker.munitions = max(0, attacker.munitions - munitions_cost)

        air_superiority = attacker.aircraft / max(
            attacker.aircraft + target.aircraft, 1
        )
        weather_mod = float(rng.uniform(0.7, 1.0))
        defense_mod = 1.0 - (target.cyber_strength / 200)
        effectiveness = air_superiority * weather_mod * defense_mod

        attacker_losses = int(
            sortie_count * float(rng.uniform(0.02, 0.15)) * (1 - air_superiority)
        )
        attacker.aircraft = max(0, attacker.aircraft - attacker_losses)

        damage_mult = float(rng.uniform(0.5, 1.5))
        damage = 0
        casualties = 0

        if target_type == "infrastructure":
            damage = int(sortie_count * effectiveness * damage_mult * 0.1)
            target.infrastructure = max(0, target.infrastructure - damage)
        elif target_type == "troops":
            casualties = int(sortie_count * effectiveness * damage_mult * 100)
            target.active_troops = max(
                0.0, target.active_troops - casualties / 1_000_000
            )
        elif target_type == "bases":
            base_dmg = int(sortie_count * effectiveness * 0.2)
            target.munitions = max(0, target.munitions - base_dmg)

        self.state.global_tension = min(
            100.0, self.state.global_tension + sortie_count * 0.5
        )
        if self.state.defcon > 2 and float(rng.random()) < 0.3:
            self.state.defcon -= 1
            self.state.log_event("DEFCON level decreased!", "critical")

        result = {
            "success": True,
            "sorties": sortie_count,
            "losses": attacker_losses,
            "effectiveness": round(effectiveness, 3),
            "target_damage": damage if target_type == "infrastructure" else casualties,
            "fuel_spent": fuel_cost,
            "munitions_spent": munitions_cost,
        }

        self.state.log_event(
            f"{attacker.name}: Air strike on {target_country} ({target_type}) - "
            f"eff: {effectiveness:.1%}, losses: {attacker_losses}",
            "warning",
        )
        return result

    def naval_blockade(self, country: "Country", target_country: str) -> Dict:
        """Establish naval blockade. Costs: 5 fuel."""
        rng = self.state.rng

        target = self.state.countries.get(target_country)
        if not target:
            return {"success": False, "reason": "Invalid target"}

        fuel_cost = 5
        if country.fuel < fuel_cost:
            return {"success": False, "reason": f"Insufficient fuel: have {country.fuel}, need {fuel_cost}"}

        country.fuel = max(0, country.fuel - fuel_cost)

        effectiveness = float(rng.uniform(0.3, 0.8))
        target.fuel = max(0, int(target.fuel * (1 - effectiveness * 0.3)))
        target.munitions = max(0, int(target.munitions * (1 - effectiveness * 0.2)))

        self.state.global_tension = min(
            100.0, self.state.global_tension + float(rng.uniform(10, 20))
        )

        self.state.log_event(
            f"{country.name}: Naval blockade of {target_country} (eff: {effectiveness:.0%})",
            "warning",
        )

        return {
            "success": True,
            "effectiveness": round(effectiveness, 3),
            "target_fuel_remaining": target.fuel,
            "target_munitions_remaining": target.munitions,
            "fuel_spent": fuel_cost,
        }
