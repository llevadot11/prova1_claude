"""SQLite TTL cache para respuestas externas (Open-Meteo, Anthropic)."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager

from app.config import settings

_DDL = """
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);
"""


@contextmanager
def _conn():
    settings.cache_db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.cache_db)
    try:
        con.execute(_DDL)
        yield con
        con.commit()
    finally:
        con.close()


def get(key: str) -> str | None:
    now = int(time.time())
    with _conn() as con:
        row = con.execute(
            "SELECT value FROM cache WHERE key = ? AND expires_at > ?", (key, now)
        ).fetchone()
        return row[0] if row else None


def put(key: str, value: str, ttl_seconds: int) -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, value, int(time.time()) + ttl_seconds),
        )
