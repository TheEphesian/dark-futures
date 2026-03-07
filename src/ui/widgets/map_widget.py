from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from textual.widget import Widget

from ...game.state import GameState

DEFCON_COLORS = {1: "red", 2: "bright_red", 3: "yellow", 4: "green", 5: "bright_green"}


class MapWidget(Widget):
    """ASCII world map showing global status"""

    def __init__(self, game_state: GameState, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def render(self) -> RenderableType:
        gs = self.game_state
        defcon_color = DEFCON_COLORS.get(gs.defcon, "white")

        tension_bar = self._tension_bar(gs.global_tension)

        lines = Text()
        lines.append("  GLOBAL STATUS\n\n", style="bold white")
        lines.append(f"  DEFCON: ", style="white")
        lines.append(f"{gs.defcon}", style=f"bold {defcon_color}")
        lines.append(f"  |  Turn: {gs.turn}\n\n", style="white")
        lines.append(f"  Tension: {tension_bar} {gs.global_tension:.0f}%\n\n", style="white")
        lines.append(f"  Phase:   {gs.phase.upper()}\n\n", style="cyan")

        lines.append("  Nations\n", style="bold white")
        for code, country in gs.countries.items():
            marker = "[YOU] " if country.is_player else "      "
            lines.append(
                f"  {marker}{country.name:20s} "
                f"DEFCON:{gs.defcon}  Tension:{gs.global_tension:.0f}%\n",
                style="bright_white" if country.is_player else "white",
            )

        return Panel(lines, title="[bold cyan]Dark Futures[/bold cyan]", border_style="cyan")

    def _tension_bar(self, tension: float) -> str:
        filled = int(tension / 10)
        return "[" + "#" * filled + "." * (10 - filled) + "]"

    def on_mount(self) -> None:
        self.set_interval(2.0, self.refresh)
