from __future__ import annotations

from datetime import datetime

from app.domain.ports import AIQualityReviewer, ResourceCrawler
from app.repositories.content_repo import ContentRepository


class ContentService:
    def __init__(
        self,
        repo: ContentRepository,
        reviewer: AIQualityReviewer,
        crawler: ResourceCrawler,
    ) -> None:
        self.repo = repo
        self.reviewer = reviewer
        self.crawler = crawler

    def list_contents(self, status: str | None = None) -> list[dict]:
        return self.repo.list_contents(status=status)

    def get_content(self, content_id: int) -> dict | None:
        return self.repo.get_content(content_id)

    def submit_content(self, title: str, category: str, summary: str, body: str) -> int:
        content_id = self.repo.add_content(title=title, category=category, summary=summary, body=body)
        self.review_pending()
        return content_id

    def review_pending(self) -> int:
        pending_items = self.repo.list_pending_contents()
        updated = 0
        for item in pending_items:
            result = self.reviewer.review(item["title"], item["body"])
            score, status = result[0], result[1]
            self.repo.update_review_result(item["id"], score, status)
            updated += 1
        return updated

    def manual_review(self, content_id: int, score: float, status: str) -> None:
        self.repo.update_review_result(content_id, score, status)

    def list_pending_contents(self) -> list[dict]:
        return self.repo.list_pending_contents()

    def sync_latest_resource(self) -> int:
        title, url, summary = self.crawler.fetch_latest()
        self.repo.add_resource_update(title, url, summary)
        return self.review_pending()

    def list_favorites(self, user_id: int) -> list[dict]:
        favorite_ids = set(self.repo.list_favorite_ids(user_id))
        return [item for item in self.repo.list_contents(status="approved") if item["id"] in favorite_ids]

    def add_favorite(self, user_id: int, content_id: int) -> None:
        self.repo.add_favorite(user_id, content_id)

    def remove_favorite(self, user_id: int, content_id: int) -> None:
        self.repo.remove_favorite(user_id, content_id)

    def create_report(self, content_id: int, reason: str, user_id: int | None) -> int:
        return self.repo.add_report(content_id, reason, user_id)

    def list_reports(self) -> list[dict]:
        return self.repo.list_reports()

    def get_sync_config(self) -> dict:
        return self.repo.get_sync_config()

    def update_sync_config(self, enabled: bool, interval_minutes: int) -> None:
        self.repo.update_sync_config(enabled=enabled, interval_minutes=interval_minutes)

    def get_dashboard_data(self) -> dict:
        contents = self.repo.list_contents()
        updates = self.repo.list_resource_updates()
        stats = {
            "total": len(contents),
            "approved": len([c for c in contents if c["status"] == "approved"]),
            "pending": len([c for c in contents if c["status"] != "approved"]),
            "last_sync": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
        return {"contents": contents, "updates": updates, "stats": stats}
