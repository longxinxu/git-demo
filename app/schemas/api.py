from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ContentStatus = Literal["pending", "approved", "rejected", "archived"]


class ContentCreate(BaseModel):
    title: str
    category: str
    summary: str
    body: str


class ContentItemDTO(BaseModel):
    id: int
    title: str
    category: str
    summary: str
    body: str
    quality_score: float = 0
    status: ContentStatus
    source: str
    created_at: str
    last_reviewed_at: str | None = None


class DashboardStats(BaseModel):
    total: int
    approved: int
    pending: int
    last_sync: str


class DashboardResponse(BaseModel):
    contents: list[ContentItemDTO]
    updates: list[dict]
    stats: DashboardStats


class FavoriteRequest(BaseModel):
    user_id: int = Field(default=1)


class ReportCreate(BaseModel):
    content_id: int
    reason: str
    user_id: int | None = None


class ReviewDecision(BaseModel):
    status: Literal["approved", "rejected"]
    score: float = Field(default=85)


class SyncConfig(BaseModel):
    enabled: bool
    interval_minutes: int
    updated_at: str | None = None


class LearningPathStep(BaseModel):
    category: str
    items: list[ContentItemDTO]


class LearningPathResponse(BaseModel):
    path: list[LearningPathStep]
    generated_at: datetime
