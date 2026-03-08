"""Dark Futures - Entry point with CLI, TUI, and MCP server modes."""
import argparse
import asyncio
import sys

# Allow running as module or script
if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_engine(args):
    """Create GameEngine from CLI args."""
    from src.game.engine import GameEngine
    from src.game.country import COUNTRY_PRESETS

    ai = [c for c in COUNTRY_PRESETS if c != args.country]
    if args.opponents:
        ai = [c.strip().upper() for c in args.opponents.split(",")]

    return GameEngine(
        player_country=args.country,
        ai_countries=ai,
        difficulty=args.difficulty,
        seed=args.seed,
    )


def run_cli(args):
    """Simple text CLI for quick testing."""
    from src.game.engine import GameEngine, PHASE_ACTIONS
    from src.mcp.tools import MCPTools

    engine = create_engine(args)
    tools = MCPTools(engine.state)

    print("\n=== DARK FUTURES ===")
    print(f"Playing as: {engine.player.name}")
    print(f"Opponents: {', '.join(engine.state.ai_countries)}")
    print(f"Difficulty: {engine.state.ai_difficulty}\n")

    while not engine.game_over:
        status = engine.get_status()
        print(f"\n--- Turn {status['turn']} | Phase: {status['phase'].upper()} "
              f"| DEFCON: {status['defcon']} | Tension: {status['global_tension']}% ---")

        player = status["player"]
        print(f"  Fuel: {player['resources']['fuel']} | "
              f"Munitions: {player['resources']['munitions']} | "
              f"Morale: {player['resources']['morale']}")
        print(f"  Troops: {player['military']['troops']}M | "
              f"Aircraft: {player['military']['aircraft']} | "
              f"Warheads: {player['nuclear']['warheads']}")

        allowed = PHASE_ACTIONS.get(status["phase"], [])
        print(f"\nAvailable actions: {', '.join(allowed) if allowed else '(none - auto phase)'}")
        print("Commands: [action] [target] [params] | next (advance phase) | "
              "end (end turn) | status | briefing | quit")

        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not cmd:
            continue
        elif cmd == "quit" or cmd == "q":
            print("Exiting...")
            break
        elif cmd == "next" or cmd == "n":
            result = engine.advance_phase()
            print(f"  -> {result}")
        elif cmd == "end" or cmd == "e":
            result = engine.end_turn()
            print(f"  -> Turn ended. Now turn {result['turn']}, phase {result['phase']}")
        elif cmd == "status" or cmd == "s":
            import json
            print(json.dumps(engine.get_status(), indent=2, default=str))
        elif cmd == "briefing" or cmd == "b":
            import json
            print(json.dumps(tools.request_briefing(), indent=2, default=str))
        else:
            parts = cmd.split()
            action = parts[0]
            valid, msg = engine.validate_action(action)
            if not valid:
                print(f"  Invalid: {msg}")
                continue

            targets = [parts[1]] if len(parts) > 1 else ["RUS"]
            params = {}
            if action == "cyber_hack":
                params["objective"] = parts[2] if len(parts) > 2 else "intelligence"
            elif action == "air_strike":
                params["target_type"] = parts[2] if len(parts) > 2 else "infrastructure"
                params["sortie_count"] = int(parts[3]) if len(parts) > 3 else 10
            elif action == "assassinate":
                params["target_type"] = parts[2] if len(parts) > 2 else "military_leader"
            elif action == "sabotage":
                params["target"] = parts[2] if len(parts) > 2 else "infrastructure"
            elif action == "false_flag":
                params["blamed_country"] = parts[2] if len(parts) > 2 else "CHN"
            elif action == "icbm_strike":
                params["warhead_count"] = int(parts[2]) if len(parts) > 2 else 1
                params["yield_mt"] = float(parts[3]) if len(parts) > 3 else 0.5
                params["target_list"] = [parts[4]] if len(parts) > 4 else ["cities"]
            elif action == "slbm_strike":
                params["warhead_count"] = int(parts[2]) if len(parts) > 2 else 1

            result = tools.submit_action(action, targets, params)
            print(f"  -> {result}")

        # Print recent events
        recent = engine.state.events[-3:]
        if recent:
            print("\n  Recent events:")
            for ev in recent:
                print(f"    [{ev['severity'].upper()}] {ev['event']}")

    if engine.game_over:
        print(f"\n{'='*50}")
        print(f"GAME OVER: {engine.game_over_reason.value}")
        if engine.winner:
            print(f"WINNER: {engine.winner}")
        else:
            print("No winner.")
        print(f"{'='*50}\n")


def run_mcp(args):
    """Start MCP server for AI agents."""
    from src.game.engine import GameEngine
    from src.mcp.server import MCPServer

    engine = create_engine(args)
    server = MCPServer(engine.state)
    print(f"Starting MCP server on {server.host}:{server.port}...")
    asyncio.run(server.start())


def run_tui(args):
    """Start Textual TUI."""
    try:
        from src.ui.app import DarkFuturesApp
        engine = create_engine(args)
        app = DarkFuturesApp(engine)
        app.run()
    except ImportError:
        print("TUI requires 'textual' package. Install with: pip install textual")
        print("Falling back to CLI mode...")
        run_cli(args)


def main():
    parser = argparse.ArgumentParser(description="Dark Futures - Turn-based wartime simulator")
    parser.add_argument("--mode", choices=["cli", "tui", "mcp"], default="cli",
                        help="Interface mode (default: cli)")
    parser.add_argument("--country", default="USA",
                        help="Player country code (default: USA)")
    parser.add_argument("--opponents", default=None,
                        help="Comma-separated AI country codes (default: all others)")
    parser.add_argument("--difficulty", choices=["easy", "normal", "hard"], default="normal",
                        help="AI difficulty (default: normal)")
    parser.add_argument("--seed", type=int, default=None,
                        help="RNG seed for reproducibility")

    args = parser.parse_args()

    modes = {"cli": run_cli, "tui": run_tui, "mcp": run_mcp}
    modes[args.mode](args)


if __name__ == "__main__":
    main()
