# Dark Futures

A turn-based wartime country simulator with TUI, Web UI, and MCP interface for AI agents.

Built with Python 3.12+, Textual, asyncio, FastMCP, NumPy, and SQLite3.

## Quick Start

```bash
git clone https://github.com/TheEphesian/dark-futures.git
cd dark-futures
pip install -e ".[dev]"

# Terminal UI mode
python main.py

# AI agent MCP server mode
python main.py --mode mcp

# Run tests
pytest
```

## Architecture

```
src/
  game/         # Core models: GameState, Country, Resources, Events
  systems/      # Intel, Military, BlackOps, Nuclear operations
  ai/           # Enemy AI opponent system (NEW)
  ui/           # Textual TUI: main screen, map, resources, event log
  mcp/          # MCP server (TLS, JSON-RPC 2.0) for OpenClaw AI agent
  utils/        # SQLite persistence, seeded RNG
tests/          # Unit + integration tests
```

## Game Systems

| System | Operations |
|--------|------------|
| **Intel** | Satellite recon, agent deployment, cyber hacking |
| **Military** | Air strikes (sortie-based), naval blockades |
| **Black Ops** | Assassinations, facility sabotage, false flag ops |
| **Nuclear** | ICBM/SLBM strikes with intercept rates and retaliation |

## AI Opponent System

NPC countries are controlled by a multi-personality AI that evaluates the board each turn and selects actions through the same Intel/Military/BlackOps/Nuclear systems the player uses.

### Architecture

The AI pipeline runs each turn in three phases:

1. **Threat Assessment** (`ThreatAssessor`) - Scores every country across 4 dimensions:
   - Military threat (troop/tank/aircraft ratio)
   - Nuclear threat (warhead comparison x DEFCON proximity)
   - Economic threat (GDP ratio)
   - Intel threat (cyber strength + active agents)
   - Produces a composite score and recommends a strategic posture

2. **Strategy Planning** (`StrategyEngine`) - Converts threat report + personality into an `ActionPlan`:
   - Escalation ladder gates action categories by DEFCON level
   - Resource-aware filtering (skips air strikes when low on fuel)
   - Target prioritization (strongest threat vs. most vulnerable)
   - Randomized variance prevents perfectly predictable behavior

3. **Execution** (`AIExecutor`) - Translates planned actions into system calls:
   - Routes through IntelSystem, MilitarySystem, BlackOpsSystem, NuclearSystem
   - Logs all AI decisions to the event stream
   - Tracks action history for learning (avoids repeating failed ops)

### Personality Types

Each NPC country has a personality archetype that tunes its behavior:

| Personality | Description | Intel | Military | BlackOps | Nuclear Threshold |
|------------|-------------|-------|----------|----------|-------------------|
| **AGGRESSIVE** | Favors military action, lower escalation threshold | Medium | High | Medium | Low |
| **DEFENSIVE** | Builds intel, retaliates only when attacked | High | Medium | Low | High |
| **OPPORTUNISTIC** | Waits for weakness, heavy on covert ops | High | Low | High | High |

### Country Profiles

| Country | Personality | Style |
|---------|------------|-------|
| **RUS** | Aggressive | Heavy military, willing to use false flags, moderate nuclear threshold |
| **CHN** | Opportunistic | Cyber-focused intel, patient escalation, naval preference |
| **USA** | Defensive | Satellite intel, retaliatory strikes, high nuclear threshold |
| **PRK** | Aggressive | Hair-trigger aggression, low resource conservation, low nuclear threshold |
| **IRN** | Opportunistic | Agent-based intel, false flag preference, moderate aggression |

### Difficulty Scaling

| Setting | Max Actions/Turn | Assessment Accuracy | Behavior |
|---------|-----------------|-------------------|----------|
| **Easy** | 2 | 70% | Lower aggression, higher nuclear threshold, weaker action weights |
| **Normal** | 3 | 90% | Balanced profiles as defined |
| **Hard** | 4 | 100% | Higher aggression, lower nuclear threshold, stronger action weights |

### Intel-Based Redaction

The MCP `get_ai_status` tool reveals opponent info scaled by your intel coverage:

| Intel Coverage | Visible Data |
|---------------|-------------|
| 0-29% | Personality type only |
| 30-49% | + Strategic posture and action count |
| 50-69% | + Action categories used this turn |
| 70-84% | + Recent actions with targets and outcomes |
| 85-100% | + Full threat assessment data |

### Integration

The AI system integrates into the game loop automatically:

```python
# GameState.advance_turn() automatically calls process_ai_turns()
state = GameState(
    player_country="USA",
    ai_countries=["RUS", "CHN"],
    ai_difficulty="normal",  # easy | normal | hard
)

# AI turns execute after each player turn
state.advance_turn()  # Player turn resolves, then AI acts

# Query AI status via MCP (redacted by player intel)
tools = MCPTools(state)
status = tools.get_ai_status("RUS")
all_status = tools.get_all_ai_status()
```

## Global State

- **DEFCON** (1-5): 5 = peace, 1 = nuclear war imminent
- **Global Tension** (0-100): Drives escalation, affects AI behavior
- **Turn Phases**: intel -> ops -> resolve -> nuclear

## MCP Interface

Secure local server on `127.0.0.1:8443` (TLS, JSON-RPC 2.0) for AI agent integration.

Available tools: `get_state`, `submit_action`, `get_available_actions`, `get_ai_status`, `get_all_ai_status`

## Tech Stack

- **Python 3.12+** with type hints and dataclasses
- **Textual 0.80+** for terminal UI
- **textual-web** for browser export
- **FastMCP** for AI agent server
- **NumPy** for probability calculations and seeded RNG
- **SQLite3** for save/load persistence
- **PyOpenSSL** for TLS on MCP server

## License

MIT
