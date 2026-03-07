from dataclasses import dataclass
from typing import Dict


@dataclass
class ResourceTick:
    """Per-turn resource production/consumption"""
    fuel_production: int = 5
    fuel_consumption: int = 3
    munitions_production: int = 3
    munitions_consumption: int = 0  # increases with ops


def apply_resource_tick(country, tick: ResourceTick = None):
    """Apply per-turn resource changes to a country"""
    if tick is None:
        tick = ResourceTick()

    net_fuel = tick.fuel_production - tick.fuel_consumption
    net_munitions = tick.munitions_production - tick.munitions_consumption

    country.fuel = max(0, min(100, country.fuel + net_fuel))
    country.munitions = max(0, min(100, country.munitions + net_munitions))

    # GDP affects production rates
    gdp_modifier = min(country.gdp / 10.0, 2.0)
    country.fuel = min(100, int(country.fuel + gdp_modifier))
