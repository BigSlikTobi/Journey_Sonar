"""Metric computation logic for each GoalType.

Each metric calculator takes signal aggregation data and produces a current_value.
"""

from __future__ import annotations

from app.common.types import GoalStatus, GoalType, TargetDirection


def compute_metric(
    goal_type: GoalType,
    metric_definition: dict,
    signal_data: dict,
) -> float:
    """Compute the current metric value from signal data.

    Args:
        goal_type: The type of goal metric to compute.
        metric_definition: Declarative definition from Goal.metric_definition.
        signal_data: Aggregated signal data from the Mapping Engine.

    Returns:
        The computed metric value.
    """
    match goal_type:
        case GoalType.CONVERSION_RATE:
            return _compute_conversion_rate(signal_data)
        case GoalType.THROUGHPUT:
            return _compute_throughput(signal_data)
        case GoalType.DROP_OFF_RATE:
            return _compute_drop_off_rate(signal_data)
        case GoalType.TIME_TO_COMPLETE:
            return _compute_time_to_complete(signal_data)
        case GoalType.SATISFACTION_SCORE:
            return _compute_satisfaction_score(signal_data)
        case GoalType.CUSTOM:
            return signal_data.get("custom_value", 0.0)
        case _:
            return 0.0


def _compute_conversion_rate(data: dict) -> float:
    numerator = data.get("numerator_actors", 0)
    denominator = data.get("denominator_actors", 0)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _compute_throughput(data: dict) -> float:
    count = data.get("positive_count", 0)
    days = data.get("days_in_range", 1)
    return count / days if days > 0 else 0.0


def _compute_drop_off_rate(data: dict) -> float:
    entered = data.get("entered_actors", 0)
    exited = data.get("exited_actors", 0)
    if entered == 0:
        return 0.0
    return (entered - exited) / entered


def _compute_time_to_complete(data: dict) -> float:
    return data.get("median_duration_seconds", 0.0)


def _compute_satisfaction_score(data: dict) -> float:
    positive = data.get("positive_count", 0)
    negative = data.get("negative_count", 0)
    total = positive + negative
    if total == 0:
        return 0.5
    return positive / total


def determine_goal_status(
    current_value: float,
    target_value: float,
    target_direction: TargetDirection,
    target_range: dict | None = None,
) -> GoalStatus:
    """Determine goal status based on current vs target value."""
    if target_value == 0:
        return GoalStatus.ON_TRACK

    match target_direction:
        case TargetDirection.ABOVE:
            ratio = current_value / target_value
            if ratio >= 1.0:
                return GoalStatus.EXCEEDED
            elif ratio >= 0.9:
                return GoalStatus.ON_TRACK
            elif ratio >= 0.75:
                return GoalStatus.AT_RISK
            else:
                return GoalStatus.OFF_TRACK

        case TargetDirection.BELOW:
            if current_value <= target_value:
                return GoalStatus.EXCEEDED
            ratio = target_value / current_value if current_value > 0 else 0
            if ratio >= 0.9:
                return GoalStatus.ON_TRACK
            elif ratio >= 0.75:
                return GoalStatus.AT_RISK
            else:
                return GoalStatus.OFF_TRACK

        case TargetDirection.BETWEEN:
            if target_range:
                low = target_range.get("min", 0)
                high = target_range.get("max", 1)
                if low <= current_value <= high:
                    return GoalStatus.EXCEEDED
                spread = high - low
                if spread > 0:
                    distance = min(abs(current_value - low), abs(current_value - high))
                    ratio = distance / spread
                    if ratio <= 0.1:
                        return GoalStatus.ON_TRACK
                    elif ratio <= 0.25:
                        return GoalStatus.AT_RISK
            return GoalStatus.OFF_TRACK

    return GoalStatus.OFF_TRACK
