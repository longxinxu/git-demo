from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class ReviewResult:
    score: float
    label: str
    reason: str
    model: str
    prompt_version: str
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResourceItem:
    title: str
    url: str
    summary: str
    raw: dict[str, Any] = field(default_factory=dict)


class ReviewerBackend(Protocol):
    def review(self, title: str, body: str, metadata: dict[str, Any]) -> ReviewResult:
        ...


class CrawlerBackend(Protocol):
    def fetch_latest(self, topic: str, limit: int) -> list[ResourceItem]:
        ...
