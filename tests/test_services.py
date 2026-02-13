import app.db as db_module
from app.db import get_session, init_db
from app.infra.factory import build_crawler, build_reviewer
from app.infra.mock_crawler import MockResourceCrawler
from app.infra.mock_reviewer import MockAIQualityReviewer
from app.models import CrawlerLog, ReviewLog
from app.repositories.content_repo import ContentRepository
from app.services.content_service import ContentService


class DeterministicReviewer:
    def __init__(self):
        self.calls = 0

    def review(self, title: str, body: str, metadata: dict):
        self.calls += 1
        return type("R", (), {
            "score": 65.0,
            "label": "rejected",
            "reason": "below threshold",
            "model": "deterministic",
            "prompt_version": "test",
            "raw_response": {"metadata": metadata},
        })()


class DeterministicCrawler:
    def fetch_latest(self, topic: str, limit: int):
        return [type("I", (), {"title": "title", "url": "https://example.com", "summary": "summary", "raw": {}})()]


def test_reviewer_flags_banned_content():
    reviewer = MockAIQualityReviewer()
    result = reviewer.review("垃圾内容", "这是诈骗教程", {"trace_id": "t"})
    assert result.score == 20.0
    assert result.label == "rejected"


def test_review_pending_only_processes_pending(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    init_db()

    repo = ContentRepository()
    reviewer = DeterministicReviewer()
    service = ContentService(repo=repo, reviewer=reviewer, crawler=DeterministicCrawler())

    repo.add_content("A", "cat", "sum", "body")
    repo.add_content("B", "cat", "sum", "body")

    reviewed = service.review_pending()
    assert reviewed == 2
    assert reviewer.calls == 2

    reviewed_again = service.review_pending()
    assert reviewed_again == 0

    with get_session() as session:
        logs = session.query(ReviewLog).all()
        assert len(logs) == 2
        assert all(log.trace_id for log in logs)


def test_sync_latest_resource_triggers_review_and_logs(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    init_db()

    repo = ContentRepository()
    reviewer = DeterministicReviewer()
    service = ContentService(repo=repo, reviewer=reviewer, crawler=DeterministicCrawler())
    repo.add_content("A", "cat", "sum", "body")

    result = service.sync_latest_resource(topic="python", limit=1)

    assert result["reviewed"] == 1
    assert result["fetched"] == 1
    assert result["trace_id"]
    assert len(repo.list_resource_updates()) == 1

    with get_session() as session:
        logs = session.query(CrawlerLog).all()
        assert len(logs) == 1
        assert logs[0].trace_id == result["trace_id"]


def test_mock_crawler_returns_items():
    crawler = MockResourceCrawler()
    items = crawler.fetch_latest(topic="ai", limit=2)
    assert len(items) == 2
    assert all(item.url.startswith("http") for item in items)


def test_factory_backend_switch(monkeypatch):
    monkeypatch.setenv("APP_REVIEWER_BACKEND", "openai")
    monkeypatch.setenv("APP_CRAWLER_BACKEND", "tavily")
    assert build_reviewer().__class__.__name__ == "OpenAIReviewer"
    assert build_crawler().__class__.__name__ == "TavilyCrawler"
