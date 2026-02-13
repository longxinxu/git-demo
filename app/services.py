from __future__ import annotations

from datetime import datetime
from random import randint

from .db import get_conn


class AIQualityReviewer:
    """A mock reviewer that simulates model-based moderation and scoring."""

    banned_words = {"spam", "赌博", "诈骗"}

    def review(self, title: str, body: str) -> tuple[float, str]:
        text = f"{title}\n{body}".lower()
        if any(word in text for word in self.banned_words):
            return 20.0, "flagged"

        length_bonus = min(len(body) / 50, 40)
        practical_bonus = 15 if "实战" in body or "案例" in body else 5
        tool_bonus = 15 if "cursor" in text or "copilot" in text or "claude" in text else 5
        score = min(100.0, 35 + length_bonus + practical_bonus + tool_bonus + randint(0, 10))
        status = "approved" if score >= 70 else "needs_improvement"
        return round(score, 1), status


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

    def review_pending(self, reviewer: AIQualityReviewer) -> int:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, body FROM contents WHERE status = 'pending'"
            ).fetchall()
            updated = 0
            for row in rows:
                score, status = reviewer.review(row["title"], row["body"])
                conn.execute(
                    "UPDATE contents SET quality_score=?, status=?, last_reviewed_at=? WHERE id=?",
                    (score, status, datetime.utcnow().isoformat(), row["id"]),
                )
                updated += 1
        return updated

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


class ResourceCrawler:
    """Mock crawler. In production, replace with real search API calls."""

    curated = [
        (
            "OpenAI Cookbook Prompting Guide",
            "https://github.com/openai/openai-cookbook",
            "覆盖从提示词设计到评估流程的系统资源。",
        ),
        (
            "Anthropic Prompt Engineering",
            "https://docs.anthropic.com",
            "高质量 prompt 与安全策略实践。",
        ),
        (
            "LangChain Use Cases",
            "https://python.langchain.com",
            "AI Agent 与 RAG 的典型应用案例。",
        ),
    ]

    def fetch_latest(self) -> tuple[str, str, str]:
        index = randint(0, len(self.curated) - 1)
        return self.curated[index]
