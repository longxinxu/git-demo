from __future__ import annotations

from random import randint


class MockAIQualityReviewer:
    """A mock reviewer that simulates model-based moderation and scoring."""

    banned_words = {"spam", "赌博", "诈骗"}

    def review(self, title: str, body: str) -> tuple[float, str]:
        text = f"{title}\n{body}".lower()
        if any(word in text for word in self.banned_words):
            return 20.0, "flagged"

        length_bonus = min(len(body) / 50, 40)
        practical_bonus = 15 if "实战" in body or "案例" in body else 5
        tool_bonus = 15 if "cursor" in text or "copilot" in text or "claude" in text else 5
        score = min(100.0, 35 + length_bonus + practical_bonus + tool_bonus + randint(0, 10))
        status = "approved" if score >= 70 else "needs_improvement"
        return round(score, 1), status
