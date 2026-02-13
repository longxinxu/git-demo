from __future__ import annotations

import os

from app.domain.ports import CrawlerBackend, ReviewerBackend
from app.infra.mock_crawler import MockResourceCrawler
from app.infra.mock_reviewer import MockAIQualityReviewer
from app.infra.openai_reviewer import OpenAIReviewer
from app.infra.tavily_crawler import TavilyCrawler


def build_reviewer() -> ReviewerBackend:
    backend = os.getenv("APP_REVIEWER_BACKEND", "mock").lower()
    if backend == "openai":
        return OpenAIReviewer()
    return MockAIQualityReviewer()


def build_crawler() -> CrawlerBackend:
    backend = os.getenv("APP_CRAWLER_BACKEND", "mock").lower()
    if backend == "tavily":
        return TavilyCrawler()
    return MockResourceCrawler()
