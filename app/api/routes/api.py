from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schemas.api import (
    ContentCreate,
    FavoriteRequest,
    LearningPathResponse,
    ReportCreate,
    ReviewDecision,
    SyncConfig,
)
from app.services.content_service import ContentService


def build_api_router(service: ContentService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/dashboard")
    def get_dashboard():
        return service.get_dashboard_data()

    @router.get("/contents")
    def list_contents(status: str | None = None):
        return service.list_contents(status=status)

    @router.post("/contents")
    def create_content(payload: ContentCreate):
        content_id = service.submit_content(
            title=payload.title,
            category=payload.category,
            summary=payload.summary,
            body=payload.body,
        )
        item = service.get_content(content_id)
        return {"id": content_id, "item": item}

    @router.get("/learning-path", response_model=LearningPathResponse)
    def get_learning_path():
        approved = [item for item in service.list_contents(status="approved")]
        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in approved:
            grouped[item["category"]].append(item)
        path = [{"category": k, "items": v} for k, v in grouped.items()]
        return {"path": path, "generated_at": datetime.utcnow()}

    @router.get("/favorites")
    def list_favorites(user_id: int = 1):
        return service.list_favorites(user_id)

    @router.post("/favorites/{content_id}")
    def add_favorite(content_id: int, payload: FavoriteRequest):
        service.add_favorite(payload.user_id, content_id)
        return {"ok": True}

    @router.delete("/favorites/{content_id}")
    def delete_favorite(content_id: int, user_id: int = 1):
        service.remove_favorite(user_id, content_id)
        return {"ok": True}

    @router.post("/reports")
    def create_report(payload: ReportCreate):
        report_id = service.create_report(payload.content_id, payload.reason, payload.user_id)
        return {"id": report_id}

    @router.get("/admin/review-queue")
    def review_queue():
        return service.list_pending_contents()

    @router.post("/admin/reviews/{content_id}")
    def review_content(content_id: int, payload: ReviewDecision):
        if not service.get_content(content_id):
            raise HTTPException(status_code=404, detail="content not found")
        service.manual_review(content_id, payload.score, payload.status)
        return {"ok": True}

    @router.get("/admin/reports")
    def admin_reports():
        return service.list_reports()

    @router.get("/admin/sync-config", response_model=SyncConfig)
    def get_sync_config():
        return service.get_sync_config()

    @router.put("/admin/sync-config", response_model=SyncConfig)
    def set_sync_config(payload: SyncConfig):
        service.update_sync_config(payload.enabled, payload.interval_minutes)
        return service.get_sync_config()

    @router.post("/admin/trigger-sync")
    def trigger_sync():
        reviewed = service.sync_latest_resource()
        return {"message": "sync complete", "reviewed": reviewed}

    return router
