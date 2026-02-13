from __future__ import annotations

from random import randint
from typing import Any

from app.domain.ports import ReviewResult, ReviewerBackend


class MockAIQualityReviewer(ReviewerBackend):
    banned_words = {"spam", "赌博", "诈骗"}

    def review(self, title: str, body: str, metadata: dict[str, Any]) -> ReviewResult:
        text = f"{title}\n{body}".lower()
        if any(word in text for word in self.banned_words):
            return ReviewResult(
                score=20.0,
                label="rejected",
                reason="Contains banned/sensitive words",
                model="mock-reviewer-v1",
                prompt_version="v1",
                raw_response={"metadata": metadata, "decision": "blocked"},
            )

        length_bonus = min(len(body) / 50, 40)
        practical_bonus = 15 if "实战" in body or "案例" in body else 5
        tool_bonus = 15 if "cursor" in text or "copilot" in text or "claude" in text else 5
        score = min(100.0, 35 + length_bonus + practical_bonus + tool_bonus + randint(0, 10))
        label = "approved" if score >= 70 else "rejected"
        return ReviewResult(
            score=round(score, 1),
            label=label,
            reason="Quality passed automated review" if label == "approved" else "Quality below threshold",
            model="mock-reviewer-v1",
            prompt_version="v1",
            raw_response={"metadata": metadata, "score_components": [length_bonus, practical_bonus, tool_bonus]},
        )
