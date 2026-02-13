from __future__ import annotations

from datetime import datetime

from app.db import get_conn


class ContentRepository:
    def list_contents(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM contents"
        params: tuple[object, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        with get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_content(self, content_id: int) -> dict | None:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM contents WHERE id=?", (content_id,)).fetchone()
        return dict(row) if row else None

    def add_content(self, title: str, category: str, summary: str, body: str, source: str = "user_upload") -> int:
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO contents (title, category, summary, body, quality_score, status, source, created_at)
                VALUES (?, ?, ?, ?, 0, 'pending', ?, ?)
                """,
                (title, category, summary, body, source, now),
            )
        return int(cur.lastrowid)

    def list_pending_contents(self) -> list[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, body FROM contents WHERE status = 'pending'"
            ).fetchall()
        return [dict(row) for row in rows]

    def update_review_result(self, content_id: int, score: float, status: str) -> None:
        with get_conn() as conn:
            conn.execute(
                "UPDATE contents SET quality_score=?, status=?, last_reviewed_at=? WHERE id=?",
                (score, status, datetime.utcnow().isoformat(), content_id),
            )

    def add_resource_update(self, title: str, url: str, summary: str) -> int:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO resource_updates (title, url, summary, fetched_at) VALUES (?, ?, ?, ?)",
                (title, url, summary, datetime.utcnow().isoformat()),
            )
        return int(cur.lastrowid)

    def list_resource_updates(self) -> list[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM resource_updates ORDER BY fetched_at DESC LIMIT 8"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_favorite(self, user_id: int, content_id: int) -> None:
        with get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO favorites (user_id, content_item_id, created_at) VALUES (?, ?, ?)",
                (user_id, content_id, datetime.utcnow().isoformat()),
            )

    def remove_favorite(self, user_id: int, content_id: int) -> None:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM favorites WHERE user_id=? AND content_item_id=?",
                (user_id, content_id),
            )

    def list_favorite_ids(self, user_id: int) -> list[int]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT content_item_id FROM favorites WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [int(row["content_item_id"]) for row in rows]

    def add_report(self, content_id: int, reason: str, user_id: int | None = None) -> int:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO reports (content_item_id, user_id, reason, created_at) VALUES (?, ?, ?, ?)",
                (content_id, user_id, reason, datetime.utcnow().isoformat()),
            )
        return int(cur.lastrowid)

    def list_reports(self) -> list[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM reports ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def update_sync_config(self, enabled: bool, interval_minutes: int) -> None:
        with get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_configs (
                    id INTEGER PRIMARY KEY,
                    enabled INTEGER NOT NULL,
                    interval_minutes INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO sync_configs (id, enabled, interval_minutes, updated_at)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  enabled=excluded.enabled,
                  interval_minutes=excluded.interval_minutes,
                  updated_at=excluded.updated_at
                """,
                (1 if enabled else 0, interval_minutes, datetime.utcnow().isoformat()),
            )

    def get_sync_config(self) -> dict:
        with get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_configs (
                    id INTEGER PRIMARY KEY,
                    enabled INTEGER NOT NULL,
                    interval_minutes INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            row = conn.execute(
                "SELECT enabled, interval_minutes, updated_at FROM sync_configs WHERE id=1"
            ).fetchone()
        if not row:
            self.update_sync_config(enabled=True, interval_minutes=60)
            return self.get_sync_config()
        return {
            "enabled": bool(row["enabled"]),
            "interval_minutes": int(row["interval_minutes"]),
            "updated_at": row["updated_at"],
        }
