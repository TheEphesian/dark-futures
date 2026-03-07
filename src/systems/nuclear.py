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
        """ICBM strike. target_list items: cities | silos | command_centers"""
        rng = self.state.rng

        if country.icbms < warhead_count or country.warheads < warhead_count:
            return {"success": False, "reason": "Insufficient warheads"}

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
        """Submarine-launched ballistic missile strike -- higher stealth, less warning."""
        rng = self.state.rng

        if country.slbms < warhead_count or country.warheads < warhead_count:
            return {"success": False, "reason": "Insufficient SLBMs"}

        successful_launches = sum(
            1 for _ in range(warhead_count) if float(rng.random()) < 0.95
        )
        target = self.state.countries.get(target_country)
        intercepted = sum(
            1 for _ in range(successful_launches) if float(rng.random()) < 0.15
        )
        warheads_hit = successful_launches - intercepted

        target_damage = (
            self._calculate_nuclear_damage(target, ["cities"], warheads_hit, 0.5, rng)
            if target
            else {}
        )

        country.slbms = max(0, country.slbms - warhead_count)
        country.warheads = max(0, country.warheads - warhead_count)
        self.state.defcon = 1
        self.state.global_tension = 100.0

        self.state.log_event(
            f"{country.name} SLBM STRIKE on {target_country}! "
            f"{warheads_hit} warheads detonated",
            "critical",
        )

        return {
            "success": True,
            "strike_type": "SLBM",
            "warheads_hit": warheads_hit,
            "damage": target_damage,
        }

    def _calculate_nuclear_damage(
        self,
        target: "Country",
        target_list: List[str],
        warhead_count: int,
        yield_mt: float,
        rng,
    ) -> Dict:
        """Calculate nuclear strike damage and apply to target country."""
        damage: Dict = {}

        casualties_per_warhead = int(float(rng.uniform(50_000, 500_000)) * yield_mt)
        total_casualties = min(
            warhead_count * casualties_per_warhead,
            int(target.population * 1_000_000 * 0.8),
        )
        target.population = max(0, target.population - int(total_casualties / 1_000_000))
        damage["casualties"] = total_casualties

        infra_damage = min(warhead_count * 10, 90)
        target.infrastructure = max(0, target.infrastructure - infra_damage)
        damage["infrastructure_destroyed"] = infra_damage

        for t in target_list:
            if t == "silos":
                silos_destroyed = min(int(warhead_count * 0.7), target.icbms)
                target.icbms = max(0, target.icbms - silos_destroyed)
                damage["silos_destroyed"] = silos_destroyed
            elif t == "cities":
                target.morale = 0
                target.government_stability = max(
                    0, target.government_stability - 80
                )
            elif t == "command_centers":
                target.cyber_strength = max(0, int(target.cyber_strength * 0.2))
                damage["command_degraded"] = True

        target.gdp *= 0.3
        target.fuel = max(0, int(target.fuel * 0.2))
        target.munitions = max(0, int(target.munitions * 0.2))

        return damage
