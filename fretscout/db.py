"""SQLite database helpers for FretScout."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS listings (
    listing_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    shipping REAL NOT NULL,
    all_in_price REAL NOT NULL,
    condition TEXT,
    location TEXT,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    max_price REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    listing_id TEXT,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (alert_id) REFERENCES saved_alerts(alert_id)
);
"""


def get_connection(db_path: str | Path = "fretscout.db") -> sqlite3.Connection:
    """Return a SQLite connection with row access by name."""

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create database schema if it does not exist."""

    connection.executescript(SCHEMA_SQL)
    connection.commit()


def initialize_database(db_path: str | Path = "fretscout.db") -> sqlite3.Connection:
    """Create a database connection and ensure schema exists."""

    connection = get_connection(db_path)
    create_schema(connection)
    return connection

