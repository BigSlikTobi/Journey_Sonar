"""Core rule evaluation engine for the Mapping module.

Evaluates MappingRule.conditions against normalized event data.

Condition format:
{
    "match_all": [
        {"field": "event_type", "operator": "equals", "value": "support_ticket_created"},
        {"field": "properties.priority", "operator": "in", "value": ["urgent", "high"]}
    ],
    "match_any": [
        {"field": "classification.intent", "operator": "equals", "value": "billing_complaint"}
    ]
}

Supported operators: equals, not_equals, in, not_in, contains, overlaps,
gt, lt, gte, lte, regex, exists, not_exists.
"""

from __future__ import annotations

import re
from typing import Any


def evaluate_rule(conditions: dict, event_data: dict) -> bool:
    """Evaluate a mapping rule's conditions against event data.

    Returns True if the event matches the rule.
    """
    match_all = conditions.get("match_all", [])
    match_any = conditions.get("match_any", [])

    # All match_all conditions must pass
    if match_all:
        if not all(_evaluate_condition(c, event_data) for c in match_all):
            return False

    # At least one match_any condition must pass (if any are defined)
    if match_any:
        if not any(_evaluate_condition(c, event_data) for c in match_any):
            return False

    return True


def _evaluate_condition(condition: dict, event_data: dict) -> bool:
    """Evaluate a single condition against event data."""
    field = condition.get("field", "")
    operator = condition.get("operator", "equals")
    expected = condition.get("value")

    actual = _resolve_field(event_data, field)

    match operator:
        case "equals":
            return actual == expected
        case "not_equals":
            return actual != expected
        case "in":
            return actual in expected if isinstance(expected, list) else False
        case "not_in":
            return actual not in expected if isinstance(expected, list) else True
        case "contains":
            if isinstance(actual, (list, str)):
                return expected in actual
            return False
        case "overlaps":
            if isinstance(actual, list) and isinstance(expected, list):
                return bool(set(actual) & set(expected))
            return False
        case "gt":
            return _safe_compare(actual, expected, lambda a, b: a > b)
        case "lt":
            return _safe_compare(actual, expected, lambda a, b: a < b)
        case "gte":
            return _safe_compare(actual, expected, lambda a, b: a >= b)
        case "lte":
            return _safe_compare(actual, expected, lambda a, b: a <= b)
        case "regex":
            if isinstance(actual, str) and isinstance(expected, str):
                return bool(re.search(expected, actual))
            return False
        case "exists":
            return actual is not None
        case "not_exists":
            return actual is None
        case _:
            return False


def _resolve_field(data: dict, field_path: str) -> Any | None:
    """Resolve a dot-separated field path from nested dict data."""
    parts = field_path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _safe_compare(actual: Any, expected: Any, comparator) -> bool:
    try:
        return comparator(actual, expected)
    except (TypeError, ValueError):
        return False
