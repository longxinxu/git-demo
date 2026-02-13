from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter


def build_resource_router(trigger_sync_job: Callable[[], Awaitable[bool]]) -> APIRouter:
    router = APIRouter()

    @router.post("/trigger-sync")
    async def trigger_sync():
        enqueued = await trigger_sync_job()
        return {"message": "job enqueued" if enqueued else "duplicate skipped", "enqueued": enqueued}

    return router
