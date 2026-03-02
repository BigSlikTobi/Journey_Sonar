"""Anomaly detection for Sonar: identifies nodes with sudden score changes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnomalyAlert:
    node_id: str
    node_name: str
    score_type: str
    previous_value: float
    current_value: float
    change_pct: float
    severity: str  # "high", "medium", "low"


def detect_score_anomalies(
    score_history: list[dict],
    threshold_pct: float = 20.0,
) -> list[AnomalyAlert]:
    """Detect anomalies by comparing current scores to recent history.

    Args:
        score_history: List of dicts with keys:
            - node_id, node_name, score_type
            - current_value, previous_value
        threshold_pct: Minimum percentage change to flag as anomaly.

    Returns list of AnomalyAlert for nodes with significant score changes.
    """
    alerts: list[AnomalyAlert] = []

    for entry in score_history:
        prev = entry.get("previous_value", 0)
        curr = entry.get("current_value", 0)

        if prev == 0:
            continue

        change_pct = abs((curr - prev) / prev * 100)

        if change_pct >= threshold_pct:
            if change_pct >= 50:
                severity = "high"
            elif change_pct >= 30:
                severity = "medium"
            else:
                severity = "low"

            alerts.append(AnomalyAlert(
                node_id=entry.get("node_id", ""),
                node_name=entry.get("node_name", ""),
                score_type=entry.get("score_type", ""),
                previous_value=prev,
                current_value=curr,
                change_pct=round(change_pct, 2),
                severity=severity,
            ))

    alerts.sort(key=lambda a: a.change_pct, reverse=True)
    return alerts
