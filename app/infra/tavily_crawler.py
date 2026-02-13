from __future__ import annotations

from app.domain.ports import CrawlerBackend, ResourceItem


class TavilyCrawler(CrawlerBackend):
    """Provider crawler placeholder with deterministic demo output."""

    def fetch_latest(self, topic: str, limit: int) -> list[ResourceItem]:
        return [
            ResourceItem(
                title=f"Tavily result for {topic}",
                url="https://tavily.com",
                summary="Provider-backed search result",
                raw={"provider": "tavily", "limit": limit},
            )
        ][: max(1, limit)]
