from __future__ import annotations

from typing import Protocol


class AIQualityReviewer(Protocol):
    """Port for content quality review."""

    def review(self, title: str, body: str) -> tuple[float, str]:
        ...


class ResourceCrawler(Protocol):
    """Port for fetching external learning resources."""

    def fetch_latest(self) -> tuple[str, str, str]:
        ...
