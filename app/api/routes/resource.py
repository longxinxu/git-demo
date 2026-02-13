from __future__ import annotations

from fastapi import APIRouter

from app.services.content_service import ContentService


def build_resource_router(service: ContentService) -> APIRouter:
    router = APIRouter()

    @router.post("/trigger-sync")
    async def trigger_sync():
        reviewed = service.sync_latest_resource()
        return {"message": "sync complete", "reviewed": reviewed}

    return router
