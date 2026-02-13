from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.content_service import ContentService


def build_content_router(service: ContentService, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        dashboard = service.get_dashboard_data()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "contents": dashboard["contents"],
                "updates": dashboard["updates"],
                "stats": dashboard["stats"],
            },
        )

    @router.post("/upload")
    async def upload_content(
        title: str = Form(...),
        category: str = Form(...),
        summary: str = Form(...),
        body: str = Form(...),
    ):
        result = service.submit_content(title=title, category=category, summary=summary, body=body)
        return RedirectResponse(url=f"/?trace_id={result['trace_id']}", status_code=303)

    return router
