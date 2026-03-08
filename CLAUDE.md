# CLAUDE.md — Dark Futures

Cold War nuclear strategy game. Turn-based, single-player vs AI countries.
Textual TUI with optional MCP server for external tool integration.

## Quick Start

```bash
python -m pip install -e .
# CLI mode (headless)
python -c "from src.game.engine import GameEngine; e = GameEngine(); e.start_new_game('USA','normal'); print(e.state)"
# TUI mode
python src/main.py --mode tui
# MCP server (JSON-RPC over TLS on 127.0.0.1:8443)
python src/main.py --mode mcp
```

## Run Tests

```bash
python -m pytest tests/ -v
```

Key test files:
- `tests/test_mvp_integration.py` — Full 5-turn game loop, phase transitions, AI turns, win/loss
- `tests/test_ai.py` — Personality profiles, threat assessment, strategy, controller pipeline
- `tests/test_nuclear.py` — ICBM/SLBM strikes, interception, retaliation chains
- `tests/test_intel.py` — Intel coverage, satellite recon, agent deployment, cyber ops
- `tests/test_persistence.py` — SQLite save/load roundtrip
- `tests/test_game_state.py` — GameState initialization and basic operations

## Architecture

```
src/
  main.py              # Entry point: --mode cli|tui|mcp, --difficulty easy|normal|hard
  game/                # Core simulation
    engine.py          # GameEngine — phase loop, AI orchestration, win/loss checks
    state.py           # GameState dataclass — single source of truth
    country.py         # Country dataclass + 10 COUNTRY_PRESETS
    events.py          # Random event system (recession, cyber incident, diplomatic crisis)
    resources.py       # Per-turn resource tick (fuel + munitions production)
  ai/                  # NPC decision-making
    controller.py      # AIController — orchestrates assess → plan → execute per NPC
    threat_assessment.py  # ThreatAssessor — scores countries on 4 threat dimensions
    strategy.py        # StrategyEngine — escalation ladder, action planning, resource filtering
    executor.py        # AIExecutor — routes planned actions to game systems
    personality.py     # AIPersonality enum + PersonalityProfile weight vectors
    presets.py         # Country-specific profiles (RUS=aggressive, CHN=opportunistic, etc.)
  systems/             # Action resolution
    intel.py           # satellite_recon, deploy_agent, cyber_hack
    military.py        # air_strike, naval_blockade
    blackops.py        # assassinate, sabotage, false_flag
    nuclear.py         # ICBM/SLBM strikes with intercept probability + retaliation
  mcp/                 # External tool interface
    server.py          # MCPServer — JSON-RPC 2.0 over self-signed TLS
    tools.py           # MCPTools — get_state, submit_action, request_briefing, get_ai_status
    security.py        # Self-signed TLS cert generation (pyOpenSSL)
  ui/                  # Textual TUI
    app.py             # DarkFuturesApp (Textual Application subclass)
    screens/
      main_screen.py   # Dashboard: map + resources + action buttons + event log
    widgets/
      map_widget.py    # ASCII global status display
      resource_panel.py  # Player resource/military stats
      log_widget.py    # Scrolling event log
  utils/
    persistence.py     # SQLite save/load via json serialization
    rng.py             # SeededRNG wrapper around numpy.random.Generator
tests/
```

## Game Loop

Each turn has 4 phases executed in strict order:

```
INTEL → OPS → RESOLVE → NUCLEAR → (next turn)
```

1. **INTEL** — Player and AI gather intelligence (satellite_recon, deploy_agent, cyber_hack)
2. **OPS** — Military and covert operations (air_strike, naval_blockade, assassinate, sabotage, false_flag)
3. **RESOLVE** — Auto-advances: random events fire, resource ticks apply, AI executes turns
4. **NUCLEAR** — Nuclear strikes (icbm_strike, slbm_strike) with interception and retaliation chains

After NUCLEAR, the turn counter increments and the cycle repeats.

### Phase-Action Mapping

| Phase    | Allowed Actions |
|----------|----------------|
| INTEL    | satellite_recon, deploy_agent, cyber_hack |
| OPS      | air_strike, naval_blockade, assassinate, sabotage, false_flag |
| RESOLVE  | (automatic — events + resources + AI) |
| NUCLEAR  | icbm_strike, slbm_strike |

## AI System

NPC countries use a 3-stage pipeline each turn:

1. **ThreatAssessor** — Scores every country across 4 dimensions: military strength, nuclear capability, intel coverage, and hostility. Produces a ranked threat list.
2. **StrategyEngine** — Consults the country's PersonalityProfile weight vectors to choose actions from an escalation ladder. Filters by available resources.
3. **AIExecutor** — Routes planned actions to the appropriate game system (intel/military/blackops/nuclear).

### AI Personalities

```python
class AIPersonality(str, Enum):
    AGGRESSIVE = "aggressive"      # High military_weight, low nuclear_threshold
    DEFENSIVE = "defensive"        # High intel_weight, high nuclear_threshold
    OPPORTUNISTIC = "opportunistic" # Balanced, exploits weakness
```

Each personality has a `PersonalityProfile` dataclass with tunable weights:
- `intel_weight` — Preference for intelligence gathering
- `military_weight` — Preference for conventional military action
- `blackops_weight` — Preference for covert operations
- `nuclear_threshold` — How threatened before considering nuclear options

### Country Presets

| Code | Country       | Personality   | Nuclear | Notes |
|------|--------------|---------------|---------|-------|
| USA  | United States | defensive     | Yes     | Player default |
| RUS  | Russia       | aggressive    | Yes     | High military, low nuclear threshold |
| CHN  | China        | opportunistic | Yes     | Balanced, exploits weakness |
| PRK  | North Korea  | aggressive    | Yes     | Limited but unpredictable |
| IRN  | Iran         | opportunistic | No*     | Pursuing nuclear capability |
| GBR  | United Kingdom | defensive  | Yes     | NATO ally |
| FRA  | France       | defensive     | Yes     | Independent nuclear doctrine |
| ISR  | Israel       | defensive     | Yes     | Undeclared arsenal |
| IND  | India        | defensive     | Yes     | Regional power |
| PAK  | Pakistan     | aggressive    | Yes     | Regional rival to India |

### 5-Tier Intel Redaction

AI status visibility scales with the player's `intel_coverage` on a target:

| Coverage   | Visible Info |
|------------|-------------|
| 0–29%      | Country name + personality only |
| 30–49%     | + general threat level |
| 50–69%     | + resource estimates (rounded) |
| 70–84%     | + specific action plans |
| 85–100%    | Full state (exact numbers, strategy details) |

## Difficulty Levels

| Setting  | Max Actions/Turn | Assessment Accuracy | Aggression Scaling |
|----------|-----------------|--------------------|-----------|
| Easy     | 1               | Low                | 0.7x |
| Normal   | 2               | Medium             | 1.0x |
| Hard     | 3               | High               | 1.3x |

## Win/Loss Conditions

**Loss conditions** (player eliminated):
- `NUCLEAR_ANNIHILATION` — Player's nuclear damage exceeds survival threshold
- `INFRASTRUCTURE_COLLAPSE` — Player's infrastructure drops to 0
- `GOVERNMENT_OVERTHROWN` — Player's stability drops to 0
- `MORALE_COLLAPSE` — Player's morale drops to 0

**Win conditions:**
- `VICTORY_LAST_STANDING` — All other countries eliminated
- `VICTORY_DOMINATION` — Player's military strength exceeds all others combined

## GameState

`GameState` is the single source of truth, a dataclass containing:
- `turn: int` — Current turn number
- `phase: str` — Current phase (intel/ops/resolve/nuclear)
- `countries: Dict[str, Country]` — All country states keyed by country code
- `player_country: str` — Player's country code
- `difficulty: str` — easy/normal/hard
- `game_over: bool` — Whether game has ended
- `game_over_reason: Optional[str]` — Why game ended
- `event_log: List[str]` — History of all events
- `rng_seed: int` — For deterministic replay

## Country Dataclass

Each country tracks:
- **Resources**: `fuel`, `munitions`, `fuel_production`, `munitions_production`
- **Military**: `conventional_forces`, `air_power`, `naval_power`
- **Nuclear**: `nuclear_weapons`, `icbms`, `slbms`, `missile_defense`
- **Intel**: `intel_coverage` (dict of coverage % per target country)
- **Status**: `infrastructure`, `stability`, `morale`, `is_eliminated`
- **AI**: `personality` (AIPersonality enum), `is_player` (bool)

## Nuclear System Details

Nuclear strikes follow a resolution chain:
1. **Launch** — Attacker commits ICBM or SLBM
2. **Intercept** — Defender's `missile_defense` gives a probability of interception
3. **Damage** — If not intercepted, applies damage to infrastructure/stability/morale
4. **Retaliation** — Defender may auto-retaliate if they have nuclear capability and AI personality allows it

## MCP Server

JSON-RPC 2.0 over self-signed TLS on `127.0.0.1:8443`. Tools exposed:
- `get_state` — Full game state (redacted by intel coverage for AI countries)
- `submit_action` — Player submits an action for the current phase
- `request_briefing` — Natural language summary of current situation
- `get_ai_status` — AI country statuses (redacted by intel tier)

## Random Events

Events fire during the RESOLVE phase with configurable probability:
- Economic recession (resource production penalty)
- Cyber incident (intel coverage disruption)
- Diplomatic crisis (stability hit)
- Arms deal (military boost)
- Nuclear accident (infrastructure + stability damage)

## Persistence

Save/load via SQLite using JSON serialization of the full GameState. Located in `src/utils/persistence.py`. Roundtrip tested in `tests/test_persistence.py`.

## RNG

`SeededRNG` in `src/utils/rng.py` wraps `numpy.random.Generator` for deterministic replay. The seed is stored in GameState and used for all random decisions (events, interception rolls, AI choices).

## Dependencies

```toml
# pyproject.toml
python = ">=3.12"
textual = "*"     # TUI framework
numpy = "*"       # RNG + calculations
pyOpenSSL = "*"   # MCP TLS certs
```

## Design Principles

1. **GameState is king** — All mutations go through GameState. No hidden state in systems.
2. **Phase discipline** — Actions are only valid in their designated phase. Engine enforces this.
3. **Deterministic replay** — SeededRNG ensures identical seeds produce identical games.
4. **Intel fog of war** — Player never sees raw AI state; everything filtered through intel coverage tiers.
5. **AI plays by the same rules** — NPC countries use the same action systems as the player. No cheating (except difficulty scaling).
6. **Separation of concerns** — Systems (intel/military/blackops/nuclear) are stateless resolvers. They take state in, return mutations out.

## Roadmap / Next Steps

- [ ] Diplomacy system (alliances, treaties, UN resolutions)
- [ ] Espionage counter-intelligence (detect/block enemy agents)
- [ ] Technology tree (research upgrades for weapons/defense/intel)
- [ ] Campaign mode (linked scenarios with persistent consequences)
- [ ] Multiplayer via MCP (multiple human players connecting to same server)
- [ ] Sound/music integration for TUI
- [ ] Map widget improvements (real geographic layout, animated strikes)
