"""SQLite persistence layer."""

# region Imports

import sqlite3
import time
from contextlib import contextmanager

from .config import DATA_DIR, DB_PATH

# endregion

# region Constants

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            REAL    NOT NULL,
    app_name      TEXT    NOT NULL,
    window_title  TEXT,
    exe_path      TEXT,
    idle          INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ts ON snapshots(ts);
"""

# endregion

# region Private Methods


@contextmanager
def _conn():
    """Context manager that yields a committed, auto-closed SQLite connection."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


# endregion

# region Public Methods / API


def init_db() -> None:
    """Create the snapshots table and index if they do not already exist."""
    with _conn() as con:
        con.executescript(_SCHEMA)


def record(*, app_name: str, window_title: str, exe_path: str, idle: bool) -> None:
    """Insert a single activity snapshot into the database.

    Args:
        app_name: Process name of the active window.
        window_title: Title text of the active window.
        exe_path: Full path to the running executable.
        idle: True if the user was idle at the time of the snapshot.
    """
    with _conn() as con:
        con.execute(
            "INSERT INTO snapshots (ts, app_name, window_title, exe_path, idle) VALUES (?,?,?,?,?)",
            (time.time(), app_name, window_title, exe_path, int(idle)),
        )


def query_range(start_ts: float, end_ts: float, include_idle: bool = False) -> list[sqlite3.Row]:
    """Return all snapshots in [start_ts, end_ts).

    Args:
        start_ts: Unix timestamp range start (inclusive).
        end_ts: Unix timestamp range end (exclusive).
        include_idle: If True, include snapshots marked as idle.

    Returns:
        List of sqlite3.Row objects ordered by timestamp.
    """
    idle_filter = "" if include_idle else "AND idle = 0"
    with _conn() as con:
        return con.execute(
            f"SELECT * FROM snapshots WHERE ts >= ? AND ts < ? {idle_filter} ORDER BY ts",
            (start_ts, end_ts),
        ).fetchall()


def db_stats() -> dict:
    """Return summary statistics about the database.

    Returns:
        Dict with keys: total_snapshots, oldest_ts, newest_ts.
    """
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        oldest = con.execute("SELECT MIN(ts) FROM snapshots").fetchone()[0]
        newest = con.execute("SELECT MAX(ts) FROM snapshots").fetchone()[0]
    return {"total_snapshots": total, "oldest_ts": oldest, "newest_ts": newest}


# endregion
