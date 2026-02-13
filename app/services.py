from __future__ import annotations

from datetime import datetime
from random import randint

from sqlalchemy import func, select

from .db import get_session
from .models import ContentItem, ContentStatus, ContentVersion, ResourceUpdate, Review


class AIQualityReviewer:
    """A mock reviewer that simulates model-based moderation and scoring."""

    banned_words = {"spam", "赌博", "诈骗"}
    model_name = "mock-reviewer-v1"
    prompt_version = "v1"

    def review(self, title: str, body: str) -> tuple[float, str, str]:
        text = f"{title}\n{body}".lower()
        if any(word in text for word in self.banned_words):
            return 20.0, "rejected", "Contains banned/sensitive words"

        length_bonus = min(len(body) / 50, 40)
        practical_bonus = 15 if "实战" in body or "案例" in body else 5
        tool_bonus = 15 if "cursor" in text or "copilot" in text or "claude" in text else 5
        score = min(100.0, 35 + length_bonus + practical_bonus + tool_bonus + randint(0, 10))
        if score >= 70:
            return round(score, 1), "approved", "Quality passed automated review"
        return round(score, 1), "rejected", "Quality below approval threshold"


class ContentRepository:
    valid_transitions = {
        ContentStatus.draft.value: {ContentStatus.pending_review.value, ContentStatus.archived.value},
        ContentStatus.pending_review.value: {ContentStatus.approved.value, ContentStatus.rejected.value, ContentStatus.archived.value},
        ContentStatus.approved.value: {ContentStatus.archived.value},
        ContentStatus.rejected.value: {ContentStatus.archived.value, ContentStatus.pending_review.value},
        ContentStatus.archived.value: set(),
    }

    def _enforce_transition(self, current: str, target: str) -> None:
        if target not in self.valid_transitions.get(current, set()):
            raise ValueError(f"Invalid status transition: {current} -> {target}")

    def list_contents(self) -> list[dict]:
        with get_session() as session:
            items = session.execute(select(ContentItem).order_by(ContentItem.created_at.desc())).scalars().all()
            output = []
            for item in items:
                latest_version = session.execute(
                    select(ContentVersion)
                    .where(ContentVersion.content_item_id == item.id)
                    .order_by(ContentVersion.version_no.desc())
                    .limit(1)
                ).scalar_one_or_none()
                latest_review = session.execute(
                    select(Review)
                    .where(Review.content_item_id == item.id)
                    .order_by(Review.created_at.desc())
                    .limit(1)
                ).scalar_one_or_none()
                output.append(
                    {
                        "id": item.id,
                        "title": item.title,
                        "category": item.category,
                        "summary": item.summary,
                        "body": latest_version.body if latest_version else "",
                        "quality_score": latest_review.score if latest_review else 0,
                        "status": item.status,
                        "source": item.source,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "last_reviewed_at": latest_review.created_at.isoformat() if latest_review else None,
                    }
                )
        return output

    def add_content(self, title: str, category: str, summary: str, body: str, source: str = "user_upload") -> None:
        now = datetime.utcnow()
        with get_session() as session:
            item = ContentItem(
                title=title,
                category=category,
                summary=summary,
                source=source,
                status=ContentStatus.draft.value,
                created_at=now,
                updated_at=now,
            )
            session.add(item)
            session.flush()
            version = ContentVersion(
                content_item_id=item.id,
                version_no=1,
                body=body,
                change_note="initial upload",
                created_at=now,
            )
            session.add(version)
            self._enforce_transition(item.status, ContentStatus.pending_review.value)
            item.status = ContentStatus.pending_review.value

    def review_pending(self, reviewer: AIQualityReviewer) -> int:
        with get_session() as session:
            pending_items = session.execute(
                select(ContentItem).where(ContentItem.status == ContentStatus.pending_review.value)
            ).scalars().all()
            updated = 0
            for item in pending_items:
                latest_version = session.execute(
                    select(ContentVersion)
                    .where(ContentVersion.content_item_id == item.id)
                    .order_by(ContentVersion.version_no.desc())
                    .limit(1)
                ).scalar_one()
                score, label, reason = reviewer.review(item.title, latest_version.body)
                if label not in {ContentStatus.approved.value, ContentStatus.rejected.value}:
                    label = ContentStatus.rejected.value
                self._enforce_transition(item.status, label)
                item.status = label
                item.updated_at = datetime.utcnow()
                session.add(
                    Review(
                        content_item_id=item.id,
                        score=score,
                        label=label,
                        reason=reason,
                        model=reviewer.model_name,
                        prompt_version=reviewer.prompt_version,
                        created_at=datetime.utcnow(),
                    )
                )
                updated += 1
        return updated

    def add_resource_update(self, title: str, url: str, summary: str) -> None:
        with get_session() as session:
            session.add(ResourceUpdate(title=title, url=url, summary=summary, fetched_at=datetime.utcnow()))

    def list_resource_updates(self) -> list[dict]:
        with get_session() as session:
            rows = session.execute(
                select(ResourceUpdate).order_by(ResourceUpdate.fetched_at.desc()).limit(8)
            ).scalars().all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "url": row.url,
                "summary": row.summary,
                "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
            }
            for row in rows
        ]


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
