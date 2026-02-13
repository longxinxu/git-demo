from app.db import init_db
from app.services import AIQualityReviewer, ContentRepository


class DeterministicReviewer:
    model_name = "deterministic"
    prompt_version = "test"

    def __init__(self):
        self.calls = 0

    def review(self, title: str, body: str):
        self.calls += 1
        return 65.0, "rejected", "below threshold"


def test_reviewer_flags_banned_content():
    reviewer = AIQualityReviewer()
    score, status, reason = reviewer.review("垃圾内容", "这是诈骗教程")
    assert score == 20.0
    assert status == "rejected"
    assert reason


def test_reviewer_scores_content_in_valid_range():
    reviewer = AIQualityReviewer()
    score, status, reason = reviewer.review(
        "Cursor 工作流",
        "这是一个AI coding实战案例，讲解如何结合 Copilot 做自动化测试与代码审查。",
    )
    assert 0 <= score <= 100
    assert status in {"approved", "rejected"}
    assert reason


def test_review_pending_only_processes_pending(monkeypatch, tmp_path):
    import app.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    init_db()

    repo = ContentRepository()
    reviewer = DeterministicReviewer()

    repo.add_content("A", "cat", "sum", "body")
    repo.add_content("B", "cat", "sum", "body")

    reviewed = repo.review_pending(reviewer)
    assert reviewed == 2
    assert reviewer.calls == 2

    reviewed_again = repo.review_pending(reviewer)
    assert reviewed_again == 0
    assert reviewer.calls == 2
