from fastapi.testclient import TestClient


def test_submission_review_publish_flow(monkeypatch, tmp_path):
    import app.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "e2e.db")

    from app.main import app
    from app.db import init_db

    init_db()

    with TestClient(app) as client:
        submit = client.post(
            "/api/contents",
            json={
                "title": "E2E 投稿内容",
                "category": "实战案例",
                "summary": "端到端烟雾测试",
                "body": "这是一次投稿->审核->上线流程验证",
            },
        )
        assert submit.status_code == 200
        content_id = submit.json()["id"]

        queue = client.get("/api/admin/review-queue")
        assert queue.status_code == 200

        review = client.post(f"/api/admin/reviews/{content_id}", json={"status": "approved", "score": 95})
        assert review.status_code == 200

        online = client.get("/api/contents?status=approved")
        assert online.status_code == 200
        assert any(item["id"] == content_id for item in online.json())
