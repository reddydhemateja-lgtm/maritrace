 
"""Simple SQLite persistence for investigations.

Stores the full investigation record as a JSON blob so the schema never
breaks when fields are added/removed from the investigation pipeline.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "maritrace.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    """Create tables if they don't exist. Call once at startup."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                case_number TEXT PRIMARY KEY,
                slick_id    INTEGER,
                region      TEXT,
                payload     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_inv_created
                ON investigations(created_at DESC)
        """)
        c.commit()


def save_investigation(record: dict):
    """Upsert one investigation."""
    with _conn() as c:
        c.execute("""
            INSERT OR REPLACE INTO investigations
                (case_number, slick_id, region, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            record["case_number"],
            record.get("slick_id"),
            record.get("region"),
            json.dumps(record, default=str),
            record.get("created_at", ""),
        ))
        c.commit()


def load_all() -> dict:
    """Return {case_number: record} for every stored investigation."""
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT case_number, payload FROM investigations ORDER BY created_at DESC"
            ).fetchall()
        return {r["case_number"]: json.loads(r["payload"]) for r in rows}
    except Exception:
        return {}


def delete_investigation(case_number: str):
    with _conn() as c:
        c.execute("DELETE FROM investigations WHERE case_number = ?", (case_number,))
        c.commit()


def count() -> int:
    with _conn() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM investigations").fetchone()
    return row["n"] if row else 0