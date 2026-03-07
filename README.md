# Dark Futures

> A turn-based wartime country simulator with a terminal UI, browser UI, and AI agent interface (MCP).

![Python](https://img.shields.io/badge/python-3.12+-blue)
![Textual](https://img.shields.io/badge/TUI-Textual-green)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## Overview

Dark Futures puts you in command of a superpower during a period of extreme global tension. Each turn you allocate intelligence assets, order military operations, run black ops, and — if things go sideways — authorize nuclear strikes. A local MCP server lets an AI agent (OpenClaw) play alongside or advise you in real time.

### Playable Nations

| Country | GDP | Troops | Warheads | Cyber Strength |
|---------|-----|--------|----------|----------------|
| United States | $28T | 1.4M | 1,770 | 95 |
| Russia | $2T | 1.3M | 1,710 | 90 |
| China | $19T | 2.0M | 600 | 85 |

---

## Features

- **Turn-based gameplay** — Four phases per turn: Intel, Ops, Resolve, Nuclear
- **Intelligence system** — Satellite recon, human agents, cyber hacking with detection risk
- **Military system** — Air strikes (sortie-level), naval blockades with resource costs
- **Black ops** — Assassinations, facility sabotage, false flag operations with attribution risk
- **Nuclear system** — ICBM/SLBM strikes with intercept rates, yield calculations, and automatic retaliation logic
- **Random events** — Economic recessions, cyber incidents, diplomatic crises, humanitarian disasters
- **DEFCON tracker** — Live escalation ladder from 5 (peace) to 1 (nuclear war)
- **MCP server** — Secure TLS JSON-RPC 2.0 local server for AI agent integration
- **Save/Load** — SQLite persistence with full state serialization
- **Reproducible RNG** — Seeded numpy RNG for deterministic replays

---

## Architecture

```
dark-futures/
├── main.py                  # Entry point (--mode tui|web|mcp)
├── src/
│   ├── game/
│   │   ├── state.py         # GameState singleton (DEFCON, tension, turn)
│   │   ├── country.py       # Country model + presets (USA, RUS, CHN)
│   │   ├── resources.py     # Per-turn resource production/consumption
│   │   └── events.py        # Random event system
│   ├── systems/
│   │   ├── intel.py         # Satellite recon, agents, cyber hacking
│   │   ├── military.py      # Air strikes, naval blockades
│   │   ├── blackops.py      # Assassinations, sabotage, false flags
│   │   └── nuclear.py       # ICBM/SLBM strikes, damage calculation
│   ├── ui/
│   │   ├── app.py           # Textual App (keybindings, save/load)
│   │   ├── screens/
│   │   │   └── main_screen.py   # Dashboard: map + resources + actions
│   │   └── widgets/
│   │       ├── map_widget.py    # ASCII global status + DEFCON display
│   │       ├── resource_panel.py # Player stats panel
│   │       └── log_widget.py    # Scrolling event log
│   ├── mcp/
│   │   ├── server.py        # Async TLS JSON-RPC 2.0 server (127.0.0.1:8443)
│   │   ├── tools.py         # MCP tool definitions (get_state, submit_action, request_advice)
│   │   └── security.py      # Self-signed TLS cert generation
│   └── utils/
│       ├── persistence.py   # SQLite save/load
│       └── rng.py           # Seeded RNG wrapper
└── tests/
    ├── test_game_state.py
    ├── test_intel.py
    ├── test_nuclear.py
    └── test_persistence.py
```

---

## Installation

**Requirements:** Python 3.12+

```bash
git clone https://github.com/TheEphesian/dark-futures.git
cd dark-futures
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## Running the Game

### Terminal UI (default)
```bash
python main.py
# or
python main.py --mode tui
```

### Web UI (browser)
```bash
python main.py --mode web
# Open browser to the URL printed in terminal
```

### MCP Server (AI agent interface)
```bash
python main.py --mode mcp
# Server starts on https://127.0.0.1:8443
```

### Load a saved game
```bash
python main.py --load quicksave.db
```

---

## Controls (TUI)

| Key | Action |
|-----|--------|
| `S` | Save game |
| `L` | Load game |
| `Q` | Quit |
| Click buttons | Open operation screens |

---

## MCP Interface (AI Agent / OpenClaw)

The MCP server exposes a JSON-RPC 2.0 API over TLS for AI agent integration. Connect to `127.0.0.1:8443` with newline-delimited JSON.

### Available Methods

#### `get_state`
Returns the full serialized game state.
```json
{"jsonrpc": "2.0", "id": 1, "method": "get_state", "params": {}}
```

#### `submit_action`
Execute a game action.
```json
{
  "jsonrpc": "2.0", "id": 2,
  "method": "submit_action",
  "params": {
    "action": "air_strike",
    "targets": ["RUS"],
    "parameters": {"target_type": "infrastructure", "sorties": 200}
  }
}
```

**Available actions:**
| Action | Parameters |
|--------|-----------|
| `satellite_recon` | — |
| `deploy_agent` | — |
| `cyber_hack` | `objective`: steal_intel \| sabotage |
| `air_strike` | `target_type`: bases \| infrastructure \| troops, `sorties`: int |
| `naval_blockade` | — |
| `assassinate` | `target_type`: military_leader \| political_leader \| scientist |
| `sabotage` | `facility_type`: factory \| power_plant \| port \| command_center |
| `false_flag` | targets[1] = country to blame |
| `icbm_strike` | `warheads`: int, `yield_mt`: float |
| `slbm_strike` | `warheads`: int |

#### `request_advice`
Get AI advisor suggestions for the current phase.
```json
{"jsonrpc": "2.0", "id": 3, "method": "request_advice", "params": {"phase": "intel"}}
```

#### `list_tools`
Enumerate available MCP tools and their schemas.

---

## Game Systems

### DEFCON & Tension
- **DEFCON 5** — Normal peacetime operations
- **DEFCON 4** — Increased readiness
- **DEFCON 3** — Air Force on 15-minute alert
- **DEFCON 2** — Next step to nuclear war
- **DEFCON 1** — Nuclear war imminent / in progress
- **Global Tension** (0–100) — Raised by aggressive actions, lowers 2 points per turn passively

### Intel Operations
- *Satellite recon* — Success chance based on intel coverage (0–100%), costs fuel
- *Deploy agent* — Human HUMINT; detection raises tension, compromised agents are lost
- *Cyber hack* — Strength vs. target's cyber defense; traced ops spike tension

### Military Operations
- *Air strike* — Sortie count × air superiority × weather × defense modifiers; consumes fuel + munitions
- *Naval blockade* — Requires naval superiority ratio >0.7; cuts target GDP and morale

### Black Ops
- *Assassinate* — Success probability modified by active agents and target's security; attribution risk escalates DEFCON
- *Sabotage* — Factory / power plant / port / command center; traced ops raise tension
- *False flag* — High-risk: if exposed, both victims identify the orchestrator

### Nuclear
- *ICBM strike* — 92% launch success, 15–30% intercept rate; triggers retaliation (95% chance)
- *SLBM strike* — 95% launch success, 15% intercept; stealthier (less warning)
- Both immediately set DEFCON 1 and max tension

---

## Development

### Run tests
```bash
pytest
```

### Lint
```bash
ruff check src/ tests/
```

### Type check
```bash
mypy src/
```

### Dev roadmap
- [ ] Week 1 — Core models, TUI dashboard
- [ ] Week 2 — Military ops screens, MCP server
- [ ] Week 3 — Nuclear system UI, AI opponent, web export

---

## License

MIT — See LICENSE for details.
