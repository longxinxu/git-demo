import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                body TEXT NOT NULL,
                quality_score REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                source TEXT NOT NULL DEFAULT 'user_upload',
                created_at TEXT NOT NULL,
                last_reviewed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resource_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                summary TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
            """
        )


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
