from app.db import init_db
from app.infra.crawlers.mock_crawler import MockResourceCrawler
from app.infra.reviewers.mock_reviewer import MockAIQualityReviewer
from app.repositories.content_repo import ContentRepository
from app.services.content_service import ContentService


class DeterministicReviewer:
    model_name = "deterministic"
    prompt_version = "test"

    def __init__(self):
        self.calls = 0

    def review(self, title: str, body: str):
        self.calls += 1
        return 65.0, "flagged", "below threshold"


class DeterministicCrawler:
    def fetch_latest(self):
        return ("title", "https://example.com", "summary")


def test_reviewer_flags_banned_content():
    reviewer = MockAIQualityReviewer()
    score, status = reviewer.review("垃圾内容", "这是诈骗教程")
    assert score == 20.0
    assert status == "flagged"


def test_reviewer_scores_content_in_valid_range():
    reviewer = MockAIQualityReviewer()
    score, status = reviewer.review(
        "Cursor 工作流",
        "这是一个AI coding实战案例，讲解如何结合 Copilot 做自动化测试与代码审查。",
    )
    assert 0 <= score <= 100
    assert status in {"approved", "needs_improvement"}


def test_review_pending_only_processes_pending(monkeypatch, tmp_path):
    import app.db as db_module

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
    assert reviewer.calls == 2


def test_sync_latest_resource_triggers_review(monkeypatch, tmp_path):
    import app.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    init_db()

    repo = ContentRepository()
    reviewer = DeterministicReviewer()
    service = ContentService(repo=repo, reviewer=reviewer, crawler=DeterministicCrawler())
    repo.add_content("A", "cat", "sum", "body")

    reviewed = service.sync_latest_resource()

    assert reviewed == 1
    assert reviewer.calls == 1
    assert len(repo.list_resource_updates()) == 1


def test_mock_crawler_returns_triplet():
    crawler = MockResourceCrawler()
    title, url, summary = crawler.fetch_latest()
    assert isinstance(title, str)
    assert isinstance(url, str)
    assert isinstance(summary, str)
