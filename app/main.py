from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db
from .services import AIQualityReviewer, ContentRepository, ResourceCrawler

app = FastAPI(title="AI Coding 学习平台")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
repo = ContentRepository()
reviewer = AIQualityReviewer()
crawler = ResourceCrawler()


async def scheduler_loop() -> None:
    while True:
        repo.review_pending(reviewer)
        title, url, summary = crawler.fetch_latest()
        repo.add_resource_update(title, url, summary)
        await asyncio.sleep(60)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    # seed some starter content
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
        repo.review_pending(reviewer)

    app.state.scheduler_task = asyncio.create_task(scheduler_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    task = getattr(app.state, "scheduler_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    contents = repo.list_contents()
    updates = repo.list_resource_updates()
    stats = {
        "total": len(contents),
        "approved": len([c for c in contents if c["status"] == "approved"]),
        "pending": len([c for c in contents if c["status"] != "approved"]),
        "last_sync": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "contents": contents,
            "updates": updates,
            "stats": stats,
        },
    )


@app.post("/upload")
async def upload_content(
    title: str = Form(...),
    category: str = Form(...),
    summary: str = Form(...),
    body: str = Form(...),
):
    repo.add_content(title=title, category=category, summary=summary, body=body)
    repo.review_pending(reviewer)
    return RedirectResponse(url="/", status_code=303)


@app.post("/trigger-sync")
async def trigger_sync():
    title, url, summary = crawler.fetch_latest()
    repo.add_resource_update(title, url, summary)
    reviewed = repo.review_pending(reviewer)
    return {"message": "sync complete", "reviewed": reviewed}
