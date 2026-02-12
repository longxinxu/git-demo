from app.services import AIQualityReviewer


def test_reviewer_flags_banned_content():
    reviewer = AIQualityReviewer()
    score, status = reviewer.review("垃圾内容", "这是诈骗教程")
    assert score == 20.0
    assert status == "flagged"


def test_reviewer_scores_content_in_valid_range():
    reviewer = AIQualityReviewer()
    score, status = reviewer.review(
        "Cursor 工作流",
        "这是一个AI coding实战案例，讲解如何结合 Copilot 做自动化测试与代码审查。",
    )
    assert 0 <= score <= 100
    assert status in {"approved", "needs_improvement", "flagged"}
