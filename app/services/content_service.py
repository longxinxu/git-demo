from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from app.domain.ports import CrawlerBackend, ResourceItem, ReviewerBackend
from app.infra.resilience import CircuitBreaker, RetryConfig, call_with_retry_and_circuit
from app.repositories.content_repo import ContentRepository


class ContentService:
    def __init__(
        self,
        repo: ContentRepository,
        reviewer: ReviewerBackend,
        crawler: CrawlerBackend,
    ) -> None:
        self.repo = repo
        self.reviewer = reviewer
        self.crawler = crawler
        self.retry_config = RetryConfig(
            max_retries=int(os.getenv("APP_MAX_RETRIES", "2")),
            base_delay=float(os.getenv("APP_BACKOFF_BASE_SECONDS", "0.1")),
        )
        self.reviewer_circuit = CircuitBreaker(
            failure_threshold=int(os.getenv("APP_REVIEWER_CIRCUIT_FAILURES", "3")),
            recovery_timeout=float(os.getenv("APP_REVIEWER_CIRCUIT_RESET_SECONDS", "30")),
        )
        self.crawler_circuit = CircuitBreaker(
            failure_threshold=int(os.getenv("APP_CRAWLER_CIRCUIT_FAILURES", "3")),
            recovery_timeout=float(os.getenv("APP_CRAWLER_CIRCUIT_RESET_SECONDS", "30")),
        )

    def _new_trace(self) -> str:
        return uuid4().hex

    def submit_content(self, title: str, category: str, summary: str, body: str) -> dict:
        trace_id = self._new_trace()
        self.repo.add_content(title=title, category=category, summary=summary, body=body)
        reviewed = self.review_pending(trace_id=trace_id)
        return {"reviewed": reviewed, "trace_id": trace_id}

    def review_pending(self, trace_id: str | None = None) -> int:
        current_trace_id = trace_id or self._new_trace()
        pending_items = self.repo.list_pending_contents()
        updated = 0
        for item in pending_items:
            request_payload = {
                "title": item["title"],
                "body": item["body"],
                "metadata": {"content_item_id": item["id"], "trace_id": current_trace_id},
            }
            error_code = None
            response_payload = {}
            try:
                result = call_with_retry_and_circuit(
                    lambda: self.reviewer.review(item["title"], item["body"], request_payload["metadata"]),
                    retry=self.retry_config,
                    circuit=self.reviewer_circuit,
                )
                self.repo.update_review_result(
                    item["id"],
                    score=result.score,
                    status=result.label,
                    reason=result.reason,
                    model=result.model,
                    prompt_version=result.prompt_version,
                )
                response_payload = {
                    "score": result.score,
                    "label": result.label,
                    "reason": result.reason,
                    "model": result.model,
                    "prompt_version": result.prompt_version,
                    "raw": result.raw_response,
                }
                updated += 1
            except Exception as exc:  # noqa: BLE001
                error_code = type(exc).__name__
                response_payload = {"error": str(exc)}
            finally:
                self.repo.add_review_log(
                    trace_id=current_trace_id,
                    content_item_id=item["id"],
                    backend=self.reviewer.__class__.__name__,
                    request_payload=request_payload,
                    response_payload=response_payload,
                    error_code=error_code,
                )
        return updated

    def sync_latest_resource(self, topic: str = "ai coding", limit: int = 1) -> dict:
        trace_id = self._new_trace()
        request_payload = {"topic": topic, "limit": limit}
        error_code = None
        response_payload = {}
        resources: list[ResourceItem] = []
        try:
            resources = call_with_retry_and_circuit(
                lambda: self.crawler.fetch_latest(topic=topic, limit=limit),
                retry=self.retry_config,
                circuit=self.crawler_circuit,
            )
            response_payload = {
                "items": [
                    {"title": item.title, "url": item.url, "summary": item.summary, "raw": item.raw}
                    for item in resources
                ]
            }
            for item in resources:
                self.repo.add_resource_update(item.title, item.url, item.summary)
        except Exception as exc:  # noqa: BLE001
            error_code = type(exc).__name__
            response_payload = {"error": str(exc)}
        finally:
            self.repo.add_crawler_log(
                trace_id=trace_id,
                backend=self.crawler.__class__.__name__,
                request_payload=request_payload,
                response_payload=response_payload,
                error_code=error_code,
            )

        reviewed = self.review_pending(trace_id=trace_id)
        return {"reviewed": reviewed, "fetched": len(resources), "trace_id": trace_id}

    def get_dashboard_data(self) -> dict:
        contents = self.repo.list_contents()
        updates = self.repo.list_resource_updates()
        stats = {
            "total": len(contents),
            "approved": len([c for c in contents if c["status"] == "approved"]),
            "pending": len([c for c in contents if c["status"] != "approved"]),
            "last_sync": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
        return {"contents": contents, "updates": updates, "stats": stats}
