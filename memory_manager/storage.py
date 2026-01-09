import sqlite3
from pathlib import Path

DB_PATH = Path("memory.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_storage() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # DROP existing tables (alignment reset)
    cursor.execute("DROP TABLE IF EXISTS memory_entries")
    cursor.execute("DROP TABLE IF EXISTS memory_audit_log")

    # Recreate memory_entries (FINAL SPEC)
    cursor.execute("""
    CREATE TABLE memory_entries (
        id TEXT PRIMARY KEY,
        context TEXT NOT NULL,
        content TEXT NOT NULL,
        confidence_level TEXT NOT NULL,
        source TEXT NOT NULL,
        promotion_gate INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        last_used_at TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)

    # Indexes
    cursor.execute(
        "CREATE INDEX idx_memory_context ON memory_entries(context)"
    )
    cursor.execute(
        "CREATE INDEX idx_memory_status ON memory_entries(status)"
    )
    cursor.execute(
        "CREATE INDEX idx_memory_last_used ON memory_entries(last_used_at)"
    )

    # Recreate audit log table (unchanged for now)
    cursor.execute("""
    CREATE TABLE memory_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_id TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        details TEXT
    )
    """)

    conn.commit()
    conn.close()