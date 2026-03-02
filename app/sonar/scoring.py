"""Core Sonar scoring algorithms: Health, Opportunity, Urgency, Composite.

These are the algorithms that determine where in the customer journey
the team should focus effort.
"""

from __future__ import annotations

from app.common.types import GoalPriority, GoalStatus

PRIORITY_WEIGHT = {
    GoalPriority.CRITICAL: 4,
    GoalPriority.HIGH: 3,
    GoalPriority.MEDIUM: 2,
    GoalPriority.LOW: 1,
}


def compute_health_score(
    positive_count: int,
    negative_count: int,
    neutral_count: int,
) -> tuple[float, dict]:
    """Health Score (0-100): How well is this node performing?

    High score = healthy node, low score = problematic node.

    Returns (score, components_dict).
    """
    total = positive_count + negative_count + neutral_count

    if total == 0:
        return 50.0, {"positive": 0, "negative": 0, "neutral": 0, "total": 0, "note": "no data"}

    raw = (positive_count - negative_count) / total  # Range: -1.0 to 1.0
    score = (raw + 1.0) * 50.0  # Normalize to 0-100

    return round(score, 2), {
        "positive": positive_count,
        "negative": negative_count,
        "neutral": neutral_count,
        "total": total,
        "raw_ratio": round(raw, 4),
    }


def compute_opportunity_score(
    goal_gaps: list[dict],
) -> tuple[float, dict]:
    """Opportunity Score (0-100): How much improvement potential exists?

    Args:
        goal_gaps: List of dicts with keys:
            - gap_percentage: float (absolute gap as %)
            - priority: GoalPriority
            - status: GoalStatus
            - goal_id: str

    Returns (score, components_dict).
    """
    if not goal_gaps:
        return 0.0, {"note": "no goals attached", "goal_count": 0}

    weighted_gaps = []
    for g in goal_gaps:
        priority = g.get("priority", GoalPriority.MEDIUM)
        weight = PRIORITY_WEIGHT.get(priority, 2)
        gap_pct = abs(g.get("gap_percentage", 0))
        weighted_gaps.append(gap_pct * weight)

    score = min(100.0, sum(weighted_gaps) / len(goal_gaps))

    return round(score, 2), {
        "goal_count": len(goal_gaps),
        "weighted_gaps": [round(g, 2) for g in weighted_gaps],
        "goals": [g.get("goal_id", "") for g in goal_gaps],
    }


def compute_urgency_score(
    goal_gaps: list[dict],
    current_negative_rate: float,
    previous_negative_rate: float,
    descendant_count: int,
) -> tuple[float, dict]:
    """Urgency Score (0-100): How time-sensitive is action on this node?

    Factors:
    1. Off-track/at-risk goals with high priority
    2. Negative signal acceleration (current vs previous rate)
    3. Cascading impact (how many downstream nodes affected)

    Returns (score, components_dict).
    """
    factors: list[float] = []
    components: dict = {}

    # Factor 1: Goal deadline urgency
    for g in goal_gaps:
        status = g.get("status")
        if status in (GoalStatus.OFF_TRACK, GoalStatus.AT_RISK):
            priority = g.get("priority", GoalPriority.MEDIUM)
            weight = PRIORITY_WEIGHT.get(priority, 2)
            factors.append(80 + weight * 5)
    components["goal_urgency_factors"] = len([f for f in factors if f > 0])

    # Factor 2: Negative signal acceleration
    if previous_negative_rate > 0 and current_negative_rate > previous_negative_rate * 1.5:
        factors.append(70.0)
        components["negative_acceleration"] = True
    else:
        components["negative_acceleration"] = False
    components["current_negative_rate"] = round(current_negative_rate, 4)
    components["previous_negative_rate"] = round(previous_negative_rate, 4)

    # Factor 3: Cascading impact
    if descendant_count > 5:
        factors.append(50 + min(30, descendant_count * 2))
    components["descendant_count"] = descendant_count

    score = min(100.0, max(factors)) if factors else 0.0

    return round(score, 2), components


def compute_composite_score(
    health_score: float,
    opportunity_score: float,
    urgency_score: float,
    health_weight: float = 0.35,
    opportunity_weight: float = 0.40,
    urgency_weight: float = 0.25,
) -> tuple[float, dict]:
    """Composite Score (0-100): Final ranking score for the focus map.

    Note: Health is inverted — low health = high need to focus.

    Returns (score, components_dict).
    """
    composite = (
        health_weight * (100 - health_score)
        + opportunity_weight * opportunity_score
        + urgency_weight * urgency_score
    )
    score = min(100.0, max(0.0, composite))

    return round(score, 2), {
        "health_score": health_score,
        "health_inverted": round(100 - health_score, 2),
        "opportunity_score": opportunity_score,
        "urgency_score": urgency_score,
        "weights": {
            "health": health_weight,
            "opportunity": opportunity_weight,
            "urgency": urgency_weight,
        },
    }
