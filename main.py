import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.game.state import GameState
from src.game.country import COUNTRY_PRESETS
from src.ui.app import DarkFuturesApp
from src.mcp.server import MCPServer


def initialize_game() -> GameState:
    """Initialize new game state"""
    game_state = GameState()

    # Set up countries
    game_state.player_country = "USA"
    game_state.countries = {
        "USA": COUNTRY_PRESETS["USA"],
        "RUS": COUNTRY_PRESETS["RUS"],
        "CHN": COUNTRY_PRESETS["CHN"],
    }
    game_state.countries["USA"].is_player = True

    game_state.log_event("Dark Futures initialized", "info")
    game_state.log_event("Choose your actions wisely, Mr. President", "info")

    return game_state


async def run_mcp_server(game_state: GameState):
    """Run MCP server in background"""
    server = MCPServer(game_state)
    await server.start()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Dark Futures - Wartime Country Simulator")
    parser.add_argument(
        "--mode", choices=["tui", "web", "mcp"], default="tui", help="Launch mode"
    )
    parser.add_argument("--load", type=str, help="Load save file")

    args = parser.parse_args()

    # Initialize or load game
    if args.load:
        from src.utils.persistence import load_game
        game_state = load_game(args.load)
    else:
        game_state = initialize_game()

    if args.mode == "tui":
        app = DarkFuturesApp(game_state)
        app.run()

    elif args.mode == "web":
        app = DarkFuturesApp(game_state)
        app.run()

    elif args.mode == "mcp":
        asyncio.run(run_mcp_server(game_state))


if __name__ == "__main__":
    main()
