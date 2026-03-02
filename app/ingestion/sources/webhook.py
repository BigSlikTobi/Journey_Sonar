"""Webhook source adapter — handles incoming webhook payloads."""

from __future__ import annotations

from datetime import datetime, timezone


def extract_webhook_metadata(headers: dict[str, str]) -> dict:
    """Extract useful metadata from incoming webhook headers."""
    return {
        "content_type": headers.get("content-type", ""),
        "user_agent": headers.get("user-agent", ""),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
