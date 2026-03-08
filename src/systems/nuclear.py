from typing import Dict, List, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..game.state import GameState
    from ..game.country import Country


class NuclearSystem:
    """Nuclear warfare operations"""

    def __init__(self, game_state: "GameState"):
        self.state = game_state

    def launch_icbm_strike(
        self,
        country: "Country",
        target_country: str,
        target_list: List[str],
        warhead_count: int,
        yield_mt: float,
    ) -> Dict:
        """ICBM strike. Costs: warheads + 10 fuel per warhead.
        target_list items: cities | silos | command_centers
        """
        rng = self.state.rng
        fuel_cost = warhead_count * 10

        if country.icbms < warhead_count or country.warheads < warhead_count:
            return {"success": False, "reason": f"Insufficient warheads/ICBMs: have {country.warheads} warheads, {country.icbms} ICBMs, need {warhead_count}"}
        if country.fuel < fuel_cost:
            return {"success": False, "reason": f"Insufficient fuel: have {country.fuel}, need {fuel_cost}"}

        # Deduct fuel
        country.fuel = max(0, country.fuel - fuel_cost)

        launch_success_rate = 0.92
        successful_launches = sum(
            1 for _ in range(warhead_count) if float(rng.random()) < launch_success_rate
        )

        target = self.state.countries.get(target_country)
        intercept_rate = 0.30 if (target and target.code == "USA") else 0.15
        intercepted = sum(
            1
            for _ in range(successful_launches)
            if float(rng.random()) < intercept_rate
        )

        warheads_hit = successful_launches - intercepted

        target_damage = (
            self._calculate_nuclear_damage(target, target_list, warheads_hit, yield_mt, rng)
            if target
            else {}
        )

        country.icbms = max(0, country.icbms - warhead_count)
        country.warheads = max(0, country.warheads - warhead_count)

        self.state.defcon = 1
        self.state.global_tension = 100.0

        result = {
            "success": True,
            "launched": warhead_count,
            "successful_launches": successful_launches,
            "intercepted": intercepted,
            "warheads_hit": warheads_hit,
            "damage": target_damage,
            "fuel_spent": fuel_cost,
        }

        self.state.log_event(
            f"{country.name} LAUNCHES NUCLEAR STRIKE on {target_country}! "
            f"{warheads_hit}/{warhead_count} warheads hit targets",
            "critical",
        )

        if target and target.warheads > 0 and float(rng.random()) < 0.95:
            result["retaliation_incoming"] = True
            self.state.log_event(
                f"{target_country} RETALIATING with nuclear strike!", "critical"
            )

        return result

    def slbm_strike(
        self, country: "Country", target_country: str, warhead_count: int
    ) -> Dict:
        """SLBM strike -- higher stealth, less warning. Costs: warheads + 8 fuel per warhead."""
        rng = self.state.rng
        fuel_cost = warhead_count * 8

        if country.slbms < warhead_count or country.warheads < warhead_count:
            return {"success": False, "reason": f"Insufficient SLBMs/warheads: have {country.warheads} warheads, {country.slbms} SLBMs, need {warhead_count}"}
        if country.fuel < fuel_cost:
            return {"success": False, "reason": f"Insufficient fuel: have {country.fuel}, need {fuel_cost}"}

        # Deduct fuel
        country.fuel = max(0, country.fuel - fuel_cost)

        successful_launches = sum(
            1 for _ in range(warhead_count) if float(rng.random()) < 0.95
        )
        target = self.state.countries.get(target_country)
        intercept_rate = 0.10 if (target and target.code == "USA") else 0.05
        intercepted = sum(
            1
            for _ in range(successful_launches)
            if float(rng.random()) < intercept_rate
        )

        warheads_hit = successful_launches - intercepted

        target_damage = (
            self._calculate_nuclear_damage(
                target, ["cities"], warheads_hit, 0.475, rng
            )
            if target
            else {}
        )

        country.slbms = max(0, country.slbms - warhead_count)
        country.warheads = max(0, country.warheads - warhead_count)

        self.state.defcon = 1
        self.state.global_tension = 100.0

        result = {
            "success": True,
            "launched": warhead_count,
            "successful_launches": successful_launches,
            "intercepted": intercepted,
            "warheads_hit": warheads_hit,
            "damage": target_damage,
            "stealth_bonus": True,
            "fuel_spent": fuel_cost,
        }

        self.state.log_event(
            f"{country.name} SLBM STRIKE on {target_country}! "
            f"{warheads_hit}/{warhead_count} warheads hit",
            "critical",
        )

        if target and target.warheads > 0 and float(rng.random()) < 0.85:
            result["retaliation_incoming"] = True

        return result

    def _calculate_nuclear_damage(
        self,
        target: "Country",
        target_list: List[str],
        warheads_hit: int,
        yield_mt: float,
        rng,
    ) -> Dict:
        """Calculate nuclear strike damage on target country"""
        damage: Dict = {"warheads_hit": warheads_hit, "yield_mt": yield_mt}

        destruction_factor = warheads_hit * yield_mt

        for tgt in target_list:
            if tgt == "cities":
                pop_loss = int(destruction_factor * rng.uniform(50_000, 200_000))
                infra_loss = int(destruction_factor * rng.uniform(5, 15))
                target.infrastructure = max(0, target.infrastructure - infra_loss)
                target.morale = max(0, target.morale - int(rng.integers(30, 60)))
                damage["civilian_casualties"] = pop_loss
                damage["infrastructure_damage"] = infra_loss
            elif tgt == "silos":
                silos_destroyed = int(destruction_factor * rng.uniform(0.5, 2.0))
                target.icbms = max(0, target.icbms - silos_destroyed)
                damage["silos_destroyed"] = silos_destroyed
            elif tgt == "command_centers":
                target.government_stability = max(
                    0,
                    target.government_stability - int(destruction_factor * rng.uniform(10, 30)),
                )
                target.cyber_strength = max(
                    0, target.cyber_strength - int(destruction_factor * rng.uniform(5, 15))
                )
                damage["command_disruption"] = True

        return damage
