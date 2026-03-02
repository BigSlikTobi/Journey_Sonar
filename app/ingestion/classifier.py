"""Pluggable NLP text classifier for unstructured data.

Provides a Protocol (interface) and a simple keyword-based implementation.
Swap in an LLM-based classifier later without changing consuming code.
"""

from __future__ import annotations

import re
from typing import Protocol

from app.ingestion.schemas import Classification


class TextClassifier(Protocol):
    async def classify(self, text: str, workspace_id: str | None = None) -> Classification: ...


class KeywordClassifier:
    """Simple keyword-based classifier — good enough to start.

    Maps predefined keyword patterns to intents, extracts basic sentiment
    from positive/negative word counts.
    """

    INTENT_PATTERNS: dict[str, list[str]] = {
        "billing_complaint": ["billing", "charge", "invoice", "payment", "refund", "overcharged"],
        "feature_request": ["feature", "wish", "would be nice", "suggestion", "could you add"],
        "onboarding_help": ["getting started", "how do i", "setup", "configure", "first time"],
        "bug_report": ["bug", "broken", "error", "crash", "not working", "doesn't work"],
        "performance_issue": ["slow", "timeout", "latency", "performance", "loading"],
    }

    POSITIVE_WORDS = {"great", "love", "excellent", "amazing", "helpful", "thank", "good", "easy"}
    NEGATIVE_WORDS = {"bad", "terrible", "awful", "frustrating", "annoying", "hate", "difficult", "confusing"}

    async def classify(self, text: str, workspace_id: str | None = None) -> Classification:
        text_lower = text.lower()
        words = set(re.findall(r"\w+", text_lower))

        # Intent detection
        intent = "general"
        best_score = 0
        for candidate_intent, keywords in self.INTENT_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                intent = candidate_intent

        # Sentiment
        pos_count = len(words & self.POSITIVE_WORDS)
        neg_count = len(words & self.NEGATIVE_WORDS)
        total = pos_count + neg_count
        sentiment = (pos_count - neg_count) / total if total > 0 else 0.0

        # Topics
        topics = [
            kw for intent_kws in self.INTENT_PATTERNS.values()
            for kw in intent_kws if kw in text_lower
        ]

        confidence = min(1.0, best_score / 3) if best_score > 0 else 0.2

        return Classification(
            intent=intent,
            sentiment=round(sentiment, 2),
            topics=list(set(topics)),
            confidence=round(confidence, 2),
            extracted_entities={},
        )
