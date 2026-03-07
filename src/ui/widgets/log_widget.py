from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from textual.widget import Widget

from ...game.state import GameState

SEVERITY_STYLES = {
    "info": "white",
    "warning": "yellow",
    "critical": "bold red",
}


class LogWidget(Widget):
    """Scrolling event log"""

    def __init__(self, game_state: GameState, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def render(self) -> RenderableType:
        events = self.game_state.events[-20:]  # Last 20 events
        text = Text()

        for entry in reversed(events):
            style = SEVERITY_STYLES.get(entry.get("severity", "info"), "white")
            turn = entry.get("turn", 0)
            msg = entry.get("event", "")
            text.append(f"[T{turn:03d}] {msg}\n", style=style)

        return Panel(text, title="[bold cyan]Event Log[/bold cyan]", border_style="cyan")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.refresh)
