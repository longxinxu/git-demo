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

    def submit_content(self, title: str, category: str, summary: str, body: str) -> int:
        self.repo.add_content(title=title, category=category, summary=summary, body=body)
        return self.review_pending()

    def review_pending(self) -> int:
        pending_items = self.repo.list_pending_contents()
        updated = 0
        for item in pending_items:
            score, status = self.reviewer.review(item["title"], item["body"])
            self.repo.update_review_result(item["id"], score, status)
            updated += 1
        return updated

    def sync_latest_resource(self) -> int:
        title, url, summary = self.crawler.fetch_latest()
        self.repo.add_resource_update(title, url, summary)
        return self.review_pending()

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
