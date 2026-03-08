from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from ..ai.controller import AIController


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

    # AI configuration
    ai_difficulty: str = "normal"  # easy, normal, hard
    _ai_controller: Optional[object] = field(default=None, repr=False)

    # Event log
    events: List[Dict] = field(default_factory=list)

    # RNG seed for reproducibility
    seed: int = field(default_factory=lambda: int(np.random.randint(0, 2**32)))
    rng: object = field(init=False)

    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)

    def advance_turn(self):
        """Progress to next turn, then process AI turns.

        NOTE: In MVP mode with GameEngine, the engine manages phase transitions
        and calls process_ai_turns() directly. This method is kept for backward
        compatibility with direct state manipulation.
        """
        self.turn += 1
        self.phase = "intel"
        self.global_tension = float(np.clip(self.global_tension - 2, 0, 100))

        # Fire events and resource ticks
        from .events import trigger_random_events
        from .resources import apply_resource_tick
        trigger_random_events(self)
        for country in self.countries.values():
            apply_resource_tick(country)

        # Process AI country turns
        self.process_ai_turns()

    def process_ai_turns(self) -> Dict[str, List]:
        """Run AI turns for all NPC countries."""
        if not self.ai_countries:
            return {}

        from ..ai.controller import AIController

        if self._ai_controller is None:
            self._ai_controller = AIController(self, difficulty=self.ai_difficulty)

        results = self._ai_controller.process_all_ai_turns()

        self.log_event(
            f"AI turns processed: {', '.join(f'{k}({len(v)} actions)' for k, v in results.items())}",
            "info",
        )

        return results

    def get_ai_controller(self) -> "AIController":
        """Get or create the AI controller instance."""
        if self._ai_controller is None:
            from ..ai.controller import AIController
            self._ai_controller = AIController(self, difficulty=self.ai_difficulty)
        return self._ai_controller

    def validate_action(self, action: str) -> tuple:
        """Check if action is valid in current phase.

        Returns (is_valid: bool, message: str).
        """
        from .engine import PHASE_ACTIONS
        allowed = PHASE_ACTIONS.get(self.phase, [])
        if action not in allowed:
            return False, (
                f"Action '{action}' not allowed in {self.phase} phase. "
                f"Allowed: {allowed}"
            )
        return True, "ok"

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
            "ai_countries": self.ai_countries,
            "defcon": self.defcon,
            "global_tension": self.global_tension,
            "countries": {
                code: c.to_dict() if hasattr(c, "to_dict") else (
                    c.__dict__ if hasattr(c, "__dict__") else str(c)
                )
                for code, c in self.countries.items()
            },
            "events": self.events[-20:],
        }
