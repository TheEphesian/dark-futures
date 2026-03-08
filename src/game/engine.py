"""GameEngine - Central game loop orchestrator for Dark Futures MVP."""
from typing import Dict, List, Optional, Tuple
from enum import Enum
import copy

import numpy as np

from .state import GameState
from .country import Country, COUNTRY_PRESETS
from .events import trigger_random_events
from .resources import apply_resource_tick


class Phase(str, Enum):
    INTEL = "intel"
    OPS = "ops"
    RESOLVE = "resolve"
    NUCLEAR = "nuclear"

    @property
    def next(self) -> "Phase":
        order = [Phase.INTEL, Phase.OPS, Phase.RESOLVE, Phase.NUCLEAR]
        idx = order.index(self)
        return order[(idx + 1) % len(order)]


# Which actions are allowed in which phase
PHASE_ACTIONS: Dict[str, List[str]] = {
    "intel": ["satellite_recon", "deploy_agent", "cyber_hack"],
    "ops": ["air_strike", "naval_blockade", "assassinate", "sabotage", "false_flag"],
    "resolve": [],
    "nuclear": ["icbm_strike", "slbm_strike"],
}


class GameOverReason(str, Enum):
    NUCLEAR_ANNIHILATION = "nuclear_annihilation"
    INFRASTRUCTURE_COLLAPSE = "infrastructure_collapse"
    GOVERNMENT_OVERTHROWN = "government_overthrown"
    MORALE_COLLAPSE = "morale_collapse"
    VICTORY_LAST_STANDING = "victory_last_standing"
    VICTORY_DOMINATION = "victory_domination"


class GameEngine:
    """Central game loop orchestrator.

    Manages initialization, phase transitions, event/resource ticks,
    AI turns, and win/loss condition checks.
    """

    def __init__(
        self,
        player_country: str = "USA",
        ai_countries: Optional[List[str]] = None,
        difficulty: str = "normal",
        seed: Optional[int] = None,
    ):
        if ai_countries is None:
            ai_countries = [c for c in COUNTRY_PRESETS if c != player_country]

        kwargs: Dict = {"player_country": player_country, "ai_difficulty": difficulty}
        if seed is not None:
            kwargs["seed"] = seed
        self.state = GameState(**kwargs)

        for code in [player_country] + ai_countries:
            if code in COUNTRY_PRESETS:
                country = copy.deepcopy(COUNTRY_PRESETS[code])
                country.is_player = (code == player_country)
                self.state.countries[code] = country
            else:
                self.state.countries[code] = Country(
                    name=code, code=code, is_player=(code == player_country),
                    gdp=1.0, population=50, active_troops=0.2,
                    warheads=0, icbms=0, slbms=0,
                )

        self.state.ai_countries = list(ai_countries)
        self.state.turn = 1
        self.state.phase = Phase.INTEL.value

        self.game_over: bool = False
        self.game_over_reason: Optional[GameOverReason] = None
        self.winner: Optional[str] = None

        self.state.log_event(
            f"Game started: {player_country} vs {', '.join(ai_countries)} "
            f"(difficulty: {difficulty})",
            "info",
        )

    @property
    def current_phase(self) -> Phase:
        return Phase(self.state.phase)

    @property
    def player(self) -> Country:
        return self.state.countries[self.state.player_country]

    def validate_action(self, action: str) -> Tuple[bool, str]:
        """Check if an action is valid in the current phase."""
        if self.game_over:
            return False, f"Game is over: {self.game_over_reason.value}"
        allowed = PHASE_ACTIONS.get(self.state.phase, [])
        if action not in allowed:
            return False, (
                f"Action '{action}' not allowed in {self.state.phase} phase. "
                f"Allowed: {allowed or 'none (auto-resolve phase)'}"
            )
        return True, "ok"

    def advance_phase(self) -> Dict:
        """Advance to the next phase. RESOLVE auto-processes and skips to NUCLEAR."""
        if self.game_over:
            return {"success": False, "reason": f"Game over: {self.game_over_reason.value}"}

        old_phase = self.current_phase
        new_phase = old_phase.next

        if old_phase == Phase.NUCLEAR:
            return self._end_turn()

        self.state.phase = new_phase.value

        result: Dict = {
            "success": True,
            "old_phase": old_phase.value,
            "new_phase": new_phase.value,
            "turn": self.state.turn,
        }

        if new_phase == Phase.RESOLVE:
            resolve_result = self._process_resolve_phase()
            result["resolve"] = resolve_result
            self.state.phase = Phase.NUCLEAR.value
            result["new_phase"] = Phase.NUCLEAR.value
            result["auto_resolved"] = True

        self.state.log_event(
            f"Phase: {old_phase.value} -> {result['new_phase']}", "info",
        )

        game_status = self._check_game_over()
        if game_status:
            result["game_over"] = game_status

        return result

    def end_turn(self) -> Dict:
        """Shortcut: advance through remaining phases and end the turn."""
        if self.game_over:
            return {"success": False, "reason": f"Game over: {self.game_over_reason.value}"}

        results: List[Dict] = []
        safety = 0
        while self.state.phase != Phase.INTEL.value or safety == 0:
            r = self.advance_phase()
            results.append(r)
            if r.get("new_turn"):
                break
            safety += 1
            if safety > 5:
                break

        return {
            "success": True,
            "phases_processed": results,
            "turn": self.state.turn,
            "phase": self.state.phase,
            "game_over": self.game_over,
        }

    def _end_turn(self) -> Dict:
        """Process end of turn: AI turns, advance counter, tension decay."""
        ai_results = self.state.process_ai_turns()

        self.state.turn += 1
        self.state.phase = Phase.INTEL.value
        self.state.global_tension = float(
            np.clip(self.state.global_tension - 2, 0, 100)
        )

        game_status = self._check_game_over()

        result: Dict = {
            "success": True,
            "new_turn": self.state.turn,
            "new_phase": Phase.INTEL.value,
            "ai_actions": {
                code: len(actions) for code, actions in ai_results.items()
            },
            "defcon": self.state.defcon,
            "global_tension": self.state.global_tension,
        }

        if game_status:
            result["game_over"] = game_status

        self.state.log_event(f"=== Turn {self.state.turn} begins ===", "info")
        return result

    def _process_resolve_phase(self) -> Dict:
        """Fire random events and apply resource ticks for all countries."""
        events_before = len(self.state.events)
        trigger_random_events(self.state)
        for code, country in self.state.countries.items():
            apply_resource_tick(country)
        events_fired = self.state.events[events_before:]
        return {
            "events_fired": len(events_fired),
            "event_details": events_fired,
        }

    def _check_game_over(self) -> Optional[Dict]:
        """Check all win/loss conditions."""
        player = self.player
        player_code = self.state.player_country

        if player.infrastructure <= 0:
            reason = (GameOverReason.NUCLEAR_ANNIHILATION
                      if self.state.defcon == 1
                      else GameOverReason.INFRASTRUCTURE_COLLAPSE)
            return self._set_game_over(reason, None, f"{player.name} has been destroyed.")

        if player.government_stability <= 0:
            return self._set_game_over(
                GameOverReason.GOVERNMENT_OVERTHROWN, None,
                f"{player.name}'s government has been overthrown.",
            )

        if player.morale <= 0:
            return self._set_game_over(
                GameOverReason.MORALE_COLLAPSE, None,
                f"{player.name}'s population has lost all will to fight.",
            )

        ai_eliminated = [
            code for code in self.state.ai_countries
            if (c := self.state.countries.get(code))
            and (c.infrastructure <= 0 or c.government_stability <= 0)
        ]

        if len(ai_eliminated) == len(self.state.ai_countries) and self.state.ai_countries:
            return self._set_game_over(
                GameOverReason.VICTORY_LAST_STANDING, player_code,
                f"{player.name} is the last power standing.",
            )

        total_troops = sum(c.active_troops for c in self.state.countries.values())
        if total_troops > 0:
            player_share = player.active_troops / total_troops
            if player_share > 0.8 and player.infrastructure > 90:
                return self._set_game_over(
                    GameOverReason.VICTORY_DOMINATION, player_code,
                    f"{player.name} has achieved military domination.",
                )

        if self.state.defcon == 1:
            if all(c.infrastructure < 20 for c in self.state.countries.values()):
                return self._set_game_over(
                    GameOverReason.NUCLEAR_ANNIHILATION, None,
                    "Nuclear war has destroyed civilization.",
                )

        return None

    def _set_game_over(
        self, reason: GameOverReason, winner: Optional[str], message: str
    ) -> Dict:
        self.game_over = True
        self.game_over_reason = reason
        self.winner = winner
        self.state.log_event(f"GAME OVER: {message}", "critical")
        return {
            "game_over": True,
            "reason": reason.value,
            "winner": winner,
            "message": message,
        }

    def get_status(self) -> Dict:
        """Full game status for display/API."""
        status: Dict = {
            "turn": self.state.turn,
            "phase": self.state.phase,
            "defcon": self.state.defcon,
            "global_tension": round(self.state.global_tension, 1),
            "game_over": self.game_over,
        }
        if self.game_over:
            status["game_over_reason"] = self.game_over_reason.value
            status["winner"] = self.winner

        status["player"] = self.player.to_dict()
        status["ai_countries"] = {
            code: self.state.countries[code].to_dict()
            for code in self.state.ai_countries
            if code in self.state.countries
        }
        status["recent_events"] = self.state.events[-10:]
        return status
