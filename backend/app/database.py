"""
Database — SQLite setup and helpers. No ORM, just raw SQL.
"""

import sqlite3
from app.config import DB_PATH, OTHER_DB_PATH


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
            escalation      TEXT,
            status          TEXT DEFAULT 'ACTIVE'
        )
    """)

    # Try to add status column in case table was created previously without it
    try:
        conn.execute("ALTER TABLE incidents ADD COLUMN status TEXT DEFAULT 'ACTIVE'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create post-learning feedback table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incident_feedback (
            incident_id     TEXT PRIMARY KEY,
            submitted_at    TEXT NOT NULL,
            actual_officers INTEGER NOT NULL,
            actual_barricades INTEGER NOT NULL,
            actual_road_closure INTEGER NOT NULL,
            actual_priority INTEGER NOT NULL,
            feedback_notes  TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents (id)
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
         officers, barricades, escalation, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident["id"], incident["created_at"],
        incident["event_type"], incident["event_cause"],
        incident["veh_type"], incident["corridor"],
        incident["police_station"], incident["latitude"], incident["longitude"],
        incident["hour"], incident["day_of_week"], incident["month"],
        incident.get("priority"), incident.get("road_closure"),
        incident.get("risk_score"), incident.get("risk_level"),
        incident.get("officers"), incident.get("barricades"),
        incident.get("escalation"), incident.get("status", "ACTIVE"),
    ))
    conn.commit()
    conn.close()


def get_all_incidents() -> list[dict]:
    """Get all logged incidents."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_incident_by_id(incident_id: str) -> dict | None:
    """Fetch a single incident by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_incidents_by_station(station_id: int, status: str = None) -> list[dict]:
    """Get incidents assigned to a specific police station, optionally filtering by status."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE police_station = ? AND status = ? ORDER BY created_at DESC",
            (station_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE police_station = ? ORDER BY created_at DESC",
            (station_id,)
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_feedback_and_resolve(feedback: dict):
    """
    Save post-learning feedback and mark the incident status as RESOLVED.
    Runs inside a single transaction to maintain consistency.
    """
    conn = get_connection()
    try:
        with conn:
            # 1. Insert feedback record
            conn.execute("""
                INSERT OR REPLACE INTO incident_feedback
                (incident_id, submitted_at, actual_officers, actual_barricades,
                 actual_road_closure, actual_priority, feedback_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback["incident_id"], feedback["submitted_at"],
                feedback["actual_officers"], feedback["actual_barricades"],
                feedback["actual_road_closure"], feedback["actual_priority"],
                feedback.get("feedback_notes")
            ))
            # 2. Update status to RESOLVED
            conn.execute(
                "UPDATE incidents SET status = 'RESOLVED' WHERE id = ?",
                (feedback["incident_id"],)
            )
    finally:
        conn.close()


def get_feedback_for_incident(incident_id: str) -> dict | None:
    """Fetch post-learning feedback for a given incident."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM incident_feedback WHERE incident_id = ?", (incident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Secondary Database for "Other" Incidents ───────────────────

def init_other_db():
    """Create the other incidents database and tables."""
    conn = sqlite3.connect(str(OTHER_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS other_incidents (
            incident_id     TEXT PRIMARY KEY,
            latitude        REAL NOT NULL,
            longitude       REAL NOT NULL,
            time            TEXT NOT NULL,
            description     TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_other_incident(incident_id: str, latitude: float, longitude: float, time: str, description: str):
    """Save custom description for cause 'Other' in the secondary database."""
    conn = sqlite3.connect(str(OTHER_DB_PATH))
    conn.execute("""
        INSERT OR REPLACE INTO other_incidents (incident_id, latitude, longitude, time, description)
        VALUES (?, ?, ?, ?, ?)
    """, (incident_id, latitude, longitude, time, description))
    conn.commit()
    conn.close()


def get_other_incident(incident_id: str) -> dict | None:
    """Retrieve other incident description from the secondary database."""
    conn = sqlite3.connect(str(OTHER_DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM other_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Routing Helpers ─────────────────────────────────────────────

def get_active_incidents() -> list[dict]:
    """Get all ACTIVE incidents with location, priority, and road closure info."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, latitude, longitude, priority, road_closure, risk_level "
        "FROM incidents WHERE status = 'ACTIVE' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
