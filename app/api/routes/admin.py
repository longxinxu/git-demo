from __future__ import annotations

from fastapi import APIRouter

from app.services.job_queue import JobQueue


def build_admin_router(job_queue: JobQueue) -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.get("/jobs")
    async def list_jobs():
        return job_queue.get_status()

    return router
