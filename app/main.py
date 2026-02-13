from __future__ import annotations

import asyncio
import contextlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.content import build_content_router
from app.api.routes.resource import build_resource_router
from app.db import init_db
from app.infra.factory import build_crawler, build_reviewer
from app.repositories.content_repo import ContentRepository
from app.services.content_service import ContentService

app = FastAPI(title="AI Coding 学习平台")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

repo = ContentRepository()
reviewer = build_reviewer()
crawler = build_crawler()
content_service = ContentService(repo=repo, reviewer=reviewer, crawler=crawler)

app.include_router(build_content_router(content_service, templates))
app.include_router(build_resource_router(content_service))


async def scheduler_loop() -> None:
    while True:
        content_service.sync_latest_resource()
        await asyncio.sleep(60)


@app.on_event("startup")
async def startup() -> None:
    init_db()
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
        content_service.review_pending()

    app.state.scheduler_task = asyncio.create_task(scheduler_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    task = getattr(app.state, "scheduler_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
