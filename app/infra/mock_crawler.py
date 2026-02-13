from __future__ import annotations

from random import sample

from app.domain.ports import CrawlerBackend, ResourceItem


class MockResourceCrawler(CrawlerBackend):
    curated = [
        ResourceItem(
            title="OpenAI Cookbook Prompting Guide",
            url="https://github.com/openai/openai-cookbook",
            summary="覆盖从提示词设计到评估流程的系统资源。",
        ),
        ResourceItem(
            title="Anthropic Prompt Engineering",
            url="https://docs.anthropic.com",
            summary="高质量 prompt 与安全策略实践。",
        ),
        ResourceItem(
            title="LangChain Use Cases",
            url="https://python.langchain.com",
            summary="AI Agent 与 RAG 的典型应用案例。",
        ),
    ]

    def fetch_latest(self, topic: str, limit: int) -> list[ResourceItem]:
        limit = max(1, min(limit, len(self.curated)))
        picked = sample(self.curated, k=limit)
        return [
            ResourceItem(
                title=item.title,
                url=item.url,
                summary=f"[{topic}] {item.summary}",
                raw={"topic": topic, "source": "mock"},
            )
            for item in picked
        ]
