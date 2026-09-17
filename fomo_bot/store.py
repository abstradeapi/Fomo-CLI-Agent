import json
import sqlite3
from datetime import datetime, timezone


class Store:
    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id TEXT PRIMARY KEY,
                handle TEXT NOT NULL UNIQUE,
                display_name TEXT,
                solana TEXT,
                evm TEXT,
                added_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS processed_swaps (
                swap_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT,
                payload TEXT NOT NULL,
                seen_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_processed_user ON processed_swaps(user_id);
            CREATE TABLE IF NOT EXISTS positions (
                user_id TEXT NOT NULL,
                position_key TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, position_key)
            );
            """
        )
        self.connection.commit()

    def close(self):
        self.connection.close()

    def add_trader(self, profile):
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO watchlist (user_id, handle, display_name, solana, evm, added_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                handle = excluded.handle,
                display_name = excluded.display_name,
                solana = excluded.solana,
                evm = excluded.evm
            """,
            (profile.get("id"), profile.get("userHandle"), profile.get("displayName"), profile.get("solana"), profile.get("evm"), now),
        )
        self.connection.commit()

    def remove_trader(self, handle):
        cursor = self.connection.execute("DELETE FROM watchlist WHERE lower(handle) = lower(?)", (handle.lstrip("@"),))
        self.connection.commit()
        return cursor.rowcount > 0

    def traders(self):
        return [dict(row) for row in self.connection.execute("SELECT * FROM watchlist ORDER BY lower(handle)")]

    def save_swap(self, user_id, swap):
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO processed_swaps (swap_id, user_id, created_at, payload, seen_at) VALUES (?, ?, ?, ?, ?)",
            (swap.get("id"), user_id, swap.get("createdAt"), json.dumps(swap), datetime.now(timezone.utc).isoformat()),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def positions(self, user_id):
        rows = self.connection.execute("SELECT position_key, payload FROM positions WHERE user_id = ?", (user_id,))
        return {row["position_key"]: json.loads(row["payload"]) for row in rows}

    def replace_positions(self, user_id, positions):
        now = datetime.now(timezone.utc).isoformat()
        with self.connection:
            self.connection.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
            self.connection.executemany(
                "INSERT INTO positions (user_id, position_key, payload, updated_at) VALUES (?, ?, ?, ?)",
                [(user_id, key, json.dumps(value), now) for key, value in positions.items()],
            )
