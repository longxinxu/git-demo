from __future__ import annotations

from typing import Any

from app.domain.ports import ReviewResult, ReviewerBackend


class OpenAIReviewer(ReviewerBackend):
    """Provider reviewer placeholder.

    This demo keeps deterministic fallback behavior to avoid hard dependency on API keys.
    """

    def review(self, title: str, body: str, metadata: dict[str, Any]) -> ReviewResult:
        score = 75.0 if len(body) > 40 else 60.0
        label = "approved" if score >= 70 else "rejected"
        return ReviewResult(
            score=score,
            label=label,
            reason="Scored by provider backend",
            model="openai-reviewer-simulated",
            prompt_version="v1",
            raw_response={"provider": "openai", "metadata": metadata, "title": title},
        )
