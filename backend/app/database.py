"""
Database — SQLite setup and helpers. No ORM, just raw SQL.
"""

import sqlite3
from app.config import DB_PATH


def init_db():
    """Create tables if they don't exist. Call once at startup."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id              TEXT PRIMARY KEY,
            created_at      TEXT NOT NULL,
            event_type      INTEGER NOT NULL,
            event_cause     INTEGER NOT NULL,
            veh_type        INTEGER NOT NULL,
            corridor        INTEGER NOT NULL,
            police_station  INTEGER NOT NULL,
            latitude        REAL NOT NULL,
            longitude       REAL NOT NULL,
            hour            INTEGER NOT NULL,
            day_of_week     INTEGER NOT NULL,
            month           INTEGER NOT NULL,
            priority        INTEGER,
            road_closure    INTEGER,
            risk_score      INTEGER,
            risk_level      TEXT,
            officers        INTEGER,
            barricades      INTEGER,
            escalation      TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    """Get a new SQLite connection. Caller must close it."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def save_incident(incident: dict):
    """Save an analyzed incident to the database."""
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO incidents
        (id, created_at, event_type, event_cause, veh_type, corridor,
         police_station, latitude, longitude, hour, day_of_week, month,
         priority, road_closure, risk_score, risk_level,
         officers, barricades, escalation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident["id"], incident["created_at"],
        incident["event_type"], incident["event_cause"],
        incident["veh_type"], incident["corridor"],
        incident["police_station"], incident["latitude"], incident["longitude"],
        incident["hour"], incident["day_of_week"], incident["month"],
        incident.get("priority"), incident.get("road_closure"),
        incident.get("risk_score"), incident.get("risk_level"),
        incident.get("officers"), incident.get("barricades"),
        incident.get("escalation"),
    ))
    conn.commit()
    conn.close()


def get_all_incidents() -> list[dict]:
    """Get all logged incidents."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]
