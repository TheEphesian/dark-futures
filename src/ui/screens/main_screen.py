from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button

from ...game.state import GameState
from ..widgets.map_widget import MapWidget
from ..widgets.resource_panel import ResourcePanel
from ..widgets.log_widget import LogWidget


class MainScreen(Screen):
    """Main dashboard screen"""

    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state

    def compose(self):
        with Vertical():
            with Horizontal(id="top-section"):
                yield MapWidget(self.game_state, id="map")
                yield ResourcePanel(self.game_state, id="resources")

            with Horizontal(id="actions"):
                yield Button("Intel Operations", id="btn-intel", variant="primary")
                yield Button("Military Ops", id="btn-military", variant="primary")
                yield Button("Black Ops", id="btn-blackops", variant="warning")
                yield Button("Nuclear Options", id="btn-nuclear", variant="error")
                yield Button("End Turn", id="btn-endturn", variant="success")

            yield LogWidget(self.game_state, id="log")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle action button clicks"""
        btn = event.button.id

        if btn == "btn-intel":
            self.app.push_screen("intel")
        elif btn == "btn-military":
            self.app.push_screen("military")
        elif btn == "btn-blackops":
            self.app.push_screen("blackops")
        elif btn == "btn-nuclear":
            if self.game_state.defcon <= 2:
                self.app.push_screen("nuclear")
            else:
                self.app.notify(
                    "Nuclear options locked until DEFCON 2", severity="warning"
                )
        elif btn == "btn-endturn":
            self._end_turn()

    def _end_turn(self) -> None:
        """Process end of turn: advance state, trigger events, refresh UI"""
        self.game_state.advance_turn()

        from ...game.events import trigger_random_events
        trigger_random_events(self.game_state)

        self.refresh()
        self.app.notify(f"Turn {self.game_state.turn} begins")
