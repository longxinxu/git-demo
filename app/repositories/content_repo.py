from __future__ import annotations

from datetime import datetime

from app.db import get_conn


class ContentRepository:
    def list_contents(self) -> list[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM contents ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_content(self, title: str, category: str, summary: str, body: str, source: str = "user_upload") -> None:
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO contents (title, category, summary, body, quality_score, status, source, created_at)
                VALUES (?, ?, ?, ?, 0, 'pending', ?, ?)
                """,
                (title, category, summary, body, source, now),
            )

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

    def add_resource_update(self, title: str, url: str, summary: str) -> None:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO resource_updates (title, url, summary, fetched_at) VALUES (?, ?, ?, ?)",
                (title, url, summary, datetime.utcnow().isoformat()),
            )

    def list_resource_updates(self) -> list[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM resource_updates ORDER BY fetched_at DESC LIMIT 8"
            ).fetchall()
        return [dict(row) for row in rows]
