from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.admin import build_admin_router
from app.api.routes.content import build_content_router
from app.api.routes.resource import build_resource_router
from app.db import init_db
from app.infra.crawlers.mock_crawler import MockResourceCrawler
from app.infra.reviewers.mock_reviewer import MockAIQualityReviewer
from app.repositories.content_repo import ContentRepository
from app.services.content_service import ContentService
from app.services.job_queue import JobQueue, PeriodicJobScheduler

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="AI Coding 学习平台")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

repo = ContentRepository()
reviewer = MockAIQualityReviewer()
crawler = MockResourceCrawler()
content_service = ContentService(repo=repo, reviewer=reviewer, crawler=crawler)
job_queue = JobQueue(max_history=100)
periodic_scheduler = PeriodicJobScheduler()


async def sync_resources_task() -> int:
    return content_service.sync_latest_resource()


async def review_pending_task() -> int:
    return content_service.review_pending()


async def enqueue_sync_resources_task() -> bool:
    return await job_queue.enqueue(
        job_name="sync_resources_task",
        fn=sync_resources_task,
        dedupe_key="sync_resources:minute",
        dedupe_window_s=45,
    )


async def enqueue_review_pending_task() -> bool:
    return await job_queue.enqueue(
        job_name="review_pending_task",
        fn=review_pending_task,
        dedupe_key="review_pending:minute",
        dedupe_window_s=20,
    )


app.include_router(build_content_router(content_service, templates))
app.include_router(build_resource_router(enqueue_sync_resources_task))
app.include_router(build_admin_router(job_queue))


@app.on_event("startup")
async def startup() -> None:
    init_db()
    await job_queue.start()
    periodic_scheduler.start()

    if not repo.list_contents():
        repo.add_content(
            "Cursor + Claude 打造 PR 自动化助手",
            "实战案例",
            "从需求拆解到提交 PR 的完整链路",
            "本案例展示如何用 Cursor 与 Claude 协作完成需求分析、代码生成、测试与回归。",
            source="editorial",
        )
        repo.add_content(
            "AI Coding Skill 地图",
            "skills",
            "构建 prompt、代码审查、测试自动化三层能力",
            "从 prompt 设计开始，延展到代码结构化输出、单元测试策略和上线监控。",
            source="editorial",
        )
        await enqueue_review_pending_task()

    periodic_scheduler.schedule(60, enqueue_sync_resources_task)
    periodic_scheduler.schedule(30, enqueue_review_pending_task)


@app.on_event("shutdown")
async def shutdown() -> None:
    periodic_scheduler.stop()
    await job_queue.stop()
