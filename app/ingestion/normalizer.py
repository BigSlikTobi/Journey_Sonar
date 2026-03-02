"""Rule-based normalization engine.

Applies DataSource.normalization_rules to transform raw payloads into canonical events.
Rules use JSONPath extraction + simple transforms.

Example normalization_rules:
{
    "field_mappings": {
        "event_type": {"source_path": "$.type", "transform": "lowercase"},
        "actor_id": {"source_path": "$.requester.email"},
        "properties.subject": {"source_path": "$.subject"},
        "occurred_at": {"source_path": "$.created_at", "transform": "iso_datetime"}
    }
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jsonpath_ng import parse as jsonpath_parse


def normalize_payload(raw_payload: dict, rules: dict) -> dict:
    """Apply normalization rules to a raw payload, returning canonical fields.

    Returns a flat dict with keys like 'event_type', 'actor_id', 'properties.*', 'occurred_at'.
    """
    field_mappings = rules.get("field_mappings", {})
    result: dict[str, Any] = {}

    for target_field, rule in field_mappings.items():
        source_path = rule.get("source_path")
        if not source_path:
            continue

        value = _extract_jsonpath(raw_payload, source_path)
        if value is None:
            continue

        transform = rule.get("transform")
        if transform:
            value = _apply_transform(value, transform, rule)

        result[target_field] = value

    return result


def _extract_jsonpath(data: dict, path: str) -> Any | None:
    """Extract a value from a dict using a JSONPath expression."""
    try:
        expr = jsonpath_parse(path)
        matches = expr.find(data)
        if matches:
            return matches[0].value
    except Exception:
        pass
    return None


def _apply_transform(value: Any, transform: str, rule: dict) -> Any:
    """Apply a named transform to a value."""
    match transform:
        case "lowercase":
            return str(value).lower() if value else value
        case "uppercase":
            return str(value).upper() if value else value
        case "iso_datetime":
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
        case "map":
            mapping = rule.get("map", {})
            return mapping.get(str(value), value)
        case "to_string":
            return str(value)
        case "to_int":
            return int(value) if value is not None else None
        case _:
            return value


def build_normalized_fields(raw_payload: dict, rules: dict) -> dict:
    """Convenience: normalize and split into standard fields.

    Returns {event_type, actor_id, properties, occurred_at} ready for NormalizedEvent creation.
    """
    flat = normalize_payload(raw_payload, rules)

    properties: dict[str, Any] = {}
    for key, value in flat.items():
        if key.startswith("properties."):
            prop_key = key[len("properties."):]
            properties[prop_key] = value

    return {
        "event_type": flat.get("event_type", "unknown"),
        "actor_id": flat.get("actor_id"),
        "properties": properties,
        "occurred_at": flat.get("occurred_at", datetime.now(timezone.utc)),
    }
