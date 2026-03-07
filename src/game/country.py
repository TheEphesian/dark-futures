from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Country:
    """Represents a nation"""
    name: str
    code: str  # USA, RUS, CHN, etc.
    is_player: bool = False

    # Resources
    gdp: float = 0.0        # Trillions USD
    fuel: int = 100         # 0-100
    munitions: int = 100    # 0-100
    morale: int = 100       # 0-100

    # Military
    active_troops: float = 0.0   # Millions
    tanks: int = 0
    aircraft: int = 0
    naval_vessels: int = 0

    # Nuclear
    icbms: int = 0
    slbms: int = 0       # Sub-launched
    bombers: int = 0
    warheads: int = 0

    # Intel
    intel_coverage: float = 0.0   # 0-100% of globe
    agents_active: int = 0
    cyber_strength: int = 0       # 0-100

    # State
    population: int = 0        # Millions
    infrastructure: int = 100  # 0-100
    government_stability: int = 100  # 0-100

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "gdp": self.gdp,
            "resources": {
                "fuel": self.fuel,
                "munitions": self.munitions,
                "morale": self.morale,
            },
            "military": {
                "troops": self.active_troops,
                "tanks": self.tanks,
                "aircraft": self.aircraft,
                "naval": self.naval_vessels,
            },
            "nuclear": {
                "icbms": self.icbms,
                "slbms": self.slbms,
                "warheads": self.warheads,
            },
            "population": self.population,
            "infrastructure": self.infrastructure,
            "government_stability": self.government_stability,
            "cyber_strength": self.cyber_strength,
            "intel_coverage": self.intel_coverage,
            "agents_active": self.agents_active,
        }


# Preset country configurations
COUNTRY_PRESETS: Dict[str, Country] = {
    "USA": Country(
        name="United States",
        code="USA",
        gdp=28.0,
        active_troops=1.4,
        tanks=6612,
        aircraft=13247,
        naval_vessels=490,
        warheads=1770,
        icbms=400,
        slbms=240,
        bombers=46,
        population=335,
        intel_coverage=85.0,
        cyber_strength=95,
        fuel=95,
        munitions=95,
        morale=90,
    ),
    "RUS": Country(
        name="Russia",
        code="RUS",
        gdp=2.0,
        active_troops=1.3,
        tanks=12000,
        aircraft=4173,
        naval_vessels=605,
        warheads=1710,
        icbms=320,
        slbms=160,
        bombers=60,
        population=144,
        intel_coverage=70.0,
        cyber_strength=90,
        fuel=90,
        munitions=90,
        morale=80,
    ),
    "CHN": Country(
        name="China",
        code="CHN",
        gdp=19.0,
        active_troops=2.0,
        tanks=5000,
        aircraft=3285,
        naval_vessels=730,
        warheads=600,
        icbms=100,
        slbms=48,
        bombers=20,
        population=1412,
        intel_coverage=60.0,
        cyber_strength=85,
        fuel=85,
        munitions=85,
        morale=85,
    ),
}
