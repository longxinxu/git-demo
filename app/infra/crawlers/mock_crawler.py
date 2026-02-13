from __future__ import annotations

from random import randint


class MockResourceCrawler:
    """Mock crawler. In production, replace with real search API calls."""

    curated = [
        (
            "OpenAI Cookbook Prompting Guide",
            "https://github.com/openai/openai-cookbook",
            "覆盖从提示词设计到评估流程的系统资源。",
        ),
        (
            "Anthropic Prompt Engineering",
            "https://docs.anthropic.com",
            "高质量 prompt 与安全策略实践。",
        ),
        (
            "LangChain Use Cases",
            "https://python.langchain.com",
            "AI Agent 与 RAG 的典型应用案例。",
        ),
    ]

    def fetch_latest(self) -> tuple[str, str, str]:
        index = randint(0, len(self.curated) - 1)
        return self.curated[index]
