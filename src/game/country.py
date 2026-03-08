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
    "PRK": Country(
        name="North Korea",
        code="PRK",
        gdp=0.03,
        active_troops=1.28,
        tanks=3500,
        aircraft=946,
        naval_vessels=630,
        warheads=50,
        icbms=10,
        slbms=2,
        bombers=0,
        population=26,
        intel_coverage=15.0,
        cyber_strength=65,
        fuel=30,
        munitions=50,
        morale=95,
        government_stability=90,
    ),
    "IRN": Country(
        name="Iran",
        code="IRN",
        gdp=0.4,
        active_troops=0.58,
        tanks=1513,
        aircraft=551,
        naval_vessels=398,
        warheads=0,
        icbms=0,
        slbms=0,
        bombers=0,
        population=88,
        intel_coverage=30.0,
        cyber_strength=70,
        fuel=80,
        munitions=65,
        morale=75,
    ),
    "GBR": Country(
        name="United Kingdom",
        code="GBR",
        gdp=3.1,
        active_troops=0.15,
        tanks=227,
        aircraft=733,
        naval_vessels=75,
        warheads=225,
        icbms=0,
        slbms=48,
        bombers=0,
        population=68,
        intel_coverage=65.0,
        cyber_strength=88,
        fuel=70,
        munitions=70,
        morale=80,
    ),
    "FRA": Country(
        name="France",
        code="FRA",
        gdp=2.8,
        active_troops=0.2,
        tanks=406,
        aircraft=1055,
        naval_vessels=180,
        warheads=290,
        icbms=0,
        slbms=64,
        bombers=0,
        population=68,
        intel_coverage=55.0,
        cyber_strength=82,
        fuel=65,
        munitions=68,
        morale=75,
    ),
    "ISR": Country(
        name="Israel",
        code="ISR",
        gdp=0.5,
        active_troops=0.17,
        tanks=1370,
        aircraft=601,
        naval_vessels=67,
        warheads=90,
        icbms=25,
        slbms=0,
        bombers=0,
        population=9,
        intel_coverage=75.0,
        cyber_strength=92,
        fuel=55,
        munitions=75,
        morale=90,
        government_stability=85,
    ),
    "IND": Country(
        name="India",
        code="IND",
        gdp=3.7,
        active_troops=1.46,
        tanks=4614,
        aircraft=2182,
        naval_vessels=295,
        warheads=172,
        icbms=12,
        slbms=8,
        bombers=0,
        population=1420,
        intel_coverage=40.0,
        cyber_strength=60,
        fuel=60,
        munitions=60,
        morale=80,
    ),
    "PAK": Country(
        name="Pakistan",
        code="PAK",
        gdp=0.35,
        active_troops=0.65,
        tanks=2824,
        aircraft=1372,
        naval_vessels=100,
        warheads=170,
        icbms=0,
        slbms=0,
        bombers=0,
        population=230,
        intel_coverage=25.0,
        cyber_strength=45,
        fuel=45,
        munitions=50,
        morale=75,
        government_stability=70,
    ),
}
