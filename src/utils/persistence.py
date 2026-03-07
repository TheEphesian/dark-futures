import json
import sqlite3
from pathlib import Path

from ..game.state import GameState
from ..game.country import Country


_DDL = """
CREATE TABLE IF NOT EXISTS game_state (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    turn      INTEGER,
    phase     TEXT,
    player_country TEXT,
    defcon    INTEGER,
    global_tension REAL,
    seed      INTEGER,
    countries TEXT,
    events    TEXT,
    saved_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


def save_game(game_state: GameState, filename: str) -> None:
    """Persist game state to SQLite in data/saves/"""
    save_dir = Path("data/saves")
    save_dir.mkdir(parents=True, exist_ok=True)
    db_path = save_dir / filename

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(_DDL)

    countries_json = json.dumps(
        {k: v.to_dict() for k, v in game_state.countries.items()}
    )
    events_json = json.dumps(game_state.events[-100:])

    cursor.execute(
        """INSERT INTO game_state
           (turn, phase, player_country, defcon, global_tension, seed, countries, events)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            game_state.turn,
            game_state.phase,
            game_state.player_country,
            game_state.defcon,
            game_state.global_tension,
            game_state.seed,
            countries_json,
            events_json,
        ),
    )
    conn.commit()
    conn.close()
    print(f"Game saved to {db_path}")


def load_game(filename: str) -> GameState:
    """Load most recent save from data/saves/"""
    db_path = Path("data/saves") / filename
    if not db_path.exists():
        raise FileNotFoundError(f"Save file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT turn, phase, player_country, defcon, global_tension,
                  seed, countries, events
           FROM game_state ORDER BY id DESC LIMIT 1"""
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError("No save data found in file")

    (turn, phase, player_country, defcon, global_tension,
     seed, countries_json, events_json) = row

    game_state = GameState(
        turn=turn,
        phase=phase,
        player_country=player_country,
        defcon=defcon,
        global_tension=global_tension,
        seed=seed,
    )

    countries_data = json.loads(countries_json)
    for code, data in countries_data.items():
        mil = data.get("military", {})
        nuke = data.get("nuclear", {})
        res = data.get("resources", {})
        country = Country(
            name=data["name"],
            code=data["code"],
            gdp=data.get("gdp", 0.0),
            fuel=res.get("fuel", 100),
            munitions=res.get("munitions", 100),
            morale=res.get("morale", 100),
            active_troops=mil.get("troops", 0.0),
            tanks=mil.get("tanks", 0),
            aircraft=mil.get("aircraft", 0),
            naval_vessels=mil.get("naval", 0),
            icbms=nuke.get("icbms", 0),
            slbms=nuke.get("slbms", 0),
            warheads=nuke.get("warheads", 0),
            population=data.get("population", 0),
            infrastructure=data.get("infrastructure", 100),
            government_stability=data.get("government_stability", 100),
            cyber_strength=data.get("cyber_strength", 0),
            intel_coverage=data.get("intel_coverage", 0.0),
            agents_active=data.get("agents_active", 0),
        )
        game_state.countries[code] = country

    game_state.events = json.loads(events_json)
    print(f"Game loaded from {db_path}")
    return game_state
