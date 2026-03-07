from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

from .screens.main_screen import MainScreen
from ..game.state import GameState


class DarkFuturesApp(App):
    """Main Textual application for Dark Futures"""

    TITLE = "Dark Futures"
    SUB_TITLE = "Wartime Country Simulator"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save", "Save Game"),
        Binding("l", "load", "Load Game"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, game_state: GameState = None):
        super().__init__()
        self.game_state = game_state or GameState()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield MainScreen(game_state=self.game_state)
        yield Footer()

    def action_save(self) -> None:
        """Save current game"""
        from ..utils.persistence import save_game
        save_game(self.game_state, "quicksave.db")
        self.notify("Game saved!", severity="information")

    def action_load(self) -> None:
        """Load saved game"""
        from ..utils.persistence import load_game
        try:
            self.game_state = load_game("quicksave.db")
            self.notify("Game loaded!", severity="information")
            self.refresh()
        except FileNotFoundError:
            self.notify("No save file found", severity="error")
