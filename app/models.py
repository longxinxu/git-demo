from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContentItem:
    id: int
    title: str
    category: str
    summary: str
    body: str
    quality_score: float
    status: str
    source: str
    created_at: datetime
    last_reviewed_at: datetime | None


@dataclass
class ResourceUpdate:
    id: int
    title: str
    url: str
    summary: str
    fetched_at: datetime
