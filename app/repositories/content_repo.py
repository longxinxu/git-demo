from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select

from app.db import get_session
from app.models import ContentItem, ContentStatus, ContentVersion, CrawlerLog, ResourceUpdate, Review, ReviewLog


class ContentRepository:
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
                status=ContentStatus.pending_review.value,
                created_at=now,
                updated_at=now,
            )
            session.add(item)
            session.flush()
            session.add(
                ContentVersion(
                    content_item_id=item.id,
                    version_no=1,
                    body=body,
                    change_note="initial upload",
                    created_at=now,
                )
            )

    def list_pending_contents(self) -> list[dict]:
        with get_session() as session:
            pending = session.execute(
                select(ContentItem).where(ContentItem.status == ContentStatus.pending_review.value)
            ).scalars().all()
            output = []
            for item in pending:
                latest_version = session.execute(
                    select(ContentVersion)
                    .where(ContentVersion.content_item_id == item.id)
                    .order_by(ContentVersion.version_no.desc())
                    .limit(1)
                ).scalar_one()
                output.append({"id": item.id, "title": item.title, "body": latest_version.body})
        return output

    def update_review_result(
        self,
        content_id: int,
        score: float,
        status: str,
        reason: str,
        model: str,
        prompt_version: str,
    ) -> None:
        with get_session() as session:
            item = session.get(ContentItem, content_id)
            if item is None:
                return
            item.status = status
            item.updated_at = datetime.utcnow()
            session.add(
                Review(
                    content_item_id=content_id,
                    score=score,
                    label=status,
                    reason=reason,
                    model=model,
                    prompt_version=prompt_version,
                    created_at=datetime.utcnow(),
                )
            )

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

    def add_review_log(
        self,
        trace_id: str,
        content_item_id: int | None,
        backend: str,
        request_payload: dict,
        response_payload: dict,
        error_code: str | None,
    ) -> None:
        with get_session() as session:
            session.add(
                ReviewLog(
                    trace_id=trace_id,
                    content_item_id=content_item_id,
                    backend=backend,
                    request_payload=json.dumps(request_payload, ensure_ascii=False),
                    response_payload=json.dumps(response_payload, ensure_ascii=False),
                    error_code=error_code,
                )
            )

    def add_crawler_log(
        self,
        trace_id: str,
        backend: str,
        request_payload: dict,
        response_payload: dict,
        error_code: str | None,
    ) -> None:
        with get_session() as session:
            session.add(
                CrawlerLog(
                    trace_id=trace_id,
                    backend=backend,
                    request_payload=json.dumps(request_payload, ensure_ascii=False),
                    response_payload=json.dumps(response_payload, ensure_ascii=False),
                    error_code=error_code,
                )
            )
