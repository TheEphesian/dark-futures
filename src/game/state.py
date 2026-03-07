from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class GameState:
    """Central game state - single source of truth"""

    # Core
    turn: int = 0
    phase: str = "intel"  # intel, ops, resolve, nuclear
    player_country: str = "USA"
    ai_countries: List[str] = field(default_factory=list)

    # Countries (dict of Country objects)
    countries: Dict[str, object] = field(default_factory=dict)

    # Global state
    defcon: int = 5  # 5 = peace, 1 = nuclear war
    global_tension: float = 0.0  # 0-100

    # Event log
    events: List[Dict] = field(default_factory=list)

    # RNG seed for reproducibility
    seed: int = field(default_factory=lambda: int(np.random.randint(0, 2**32)))
    rng: object = field(init=False)

    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)

    def advance_turn(self):
        """Progress to next turn"""
        self.turn += 1
        self.phase = "intel"
        self.global_tension = float(np.clip(self.global_tension - 2, 0, 100))

    def log_event(self, event: str, severity: str = "info"):
        """Add event to log"""
        self.events.append(
            {"turn": self.turn, "event": event, "severity": severity}
        )

    def to_dict(self) -> dict:
        """Serialize for MCP/saving"""
        return {
            "turn": self.turn,
            "phase": self.phase,
            "player_country": self.player_country,
            "defcon": self.defcon,
            "global_tension": self.global_tension,
            "countries": {k: v.to_dict() for k, v in self.countries.items()},
            "events": self.events[-50:],
        }
