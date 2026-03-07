from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from ...game.state import GameState


class ResourcePanel(Widget):
    """Displays player country resources and military stats"""

    def __init__(self, game_state: GameState, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def render(self) -> RenderableType:
        gs = self.game_state
        player = gs.countries.get(gs.player_country)

        if not player:
            return Panel("No player country found", title="Resources")

        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Stat", style="white")
        table.add_column("Value", style="bright_white", justify="right")

        table.add_row("GDP", f"${player.gdp:.1f}T")
        table.add_row("Fuel", self._bar(player.fuel))
        table.add_row("Munitions", self._bar(player.munitions))
        table.add_row("Morale", self._bar(player.morale))
        table.add_row("", "")
        table.add_row("Troops", f"{player.active_troops:.1f}M")
        table.add_row("Aircraft", f"{player.aircraft:,}")
        table.add_row("Naval", f"{player.naval_vessels:,}")
        table.add_row("", "")
        table.add_row("Warheads", f"{player.warheads:,}")
        table.add_row("ICBMs", f"{player.icbms:,}")
        table.add_row("SLBMs", f"{player.slbms:,}")
        table.add_row("", "")
        table.add_row("Intel Cov.", f"{player.intel_coverage:.0f}%")
        table.add_row("Agents", f"{player.agents_active}")
        table.add_row("Cyber Str.", self._bar(player.cyber_strength))
        table.add_row("Population", f"{player.population}M")
        table.add_row("Infra.", self._bar(player.infrastructure))

        return Panel(
            table,
            title=f"[bold cyan]{player.name}[/bold cyan]",
            border_style="cyan",
        )

    def _bar(self, value: int, width: int = 10) -> str:
        filled = int((value / 100) * width)
        filled = max(0, min(width, filled))
        color = "green" if value > 60 else "yellow" if value > 30 else "red"
        return f"[{color}]{'|' * filled}{'.' * (width - filled)}[/{color}] {value}"

    def on_mount(self) -> None:
        self.set_interval(2.0, self.refresh)
