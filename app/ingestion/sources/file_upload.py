"""File upload source adapter — parses CSV/JSON file uploads into event payloads."""

from __future__ import annotations

import csv
import io
import json
from typing import Any


def parse_uploaded_file(content: bytes, filename: str) -> list[dict[str, Any]]:
    """Parse an uploaded file (CSV or JSON) into a list of raw event dicts."""
    if filename.endswith(".json"):
        return _parse_json(content)
    elif filename.endswith(".csv"):
        return _parse_csv(content)
    else:
        raise ValueError(f"Unsupported file format: {filename}. Use .json or .csv")


def _parse_json(content: bytes) -> list[dict[str, Any]]:
    data = json.loads(content.decode("utf-8"))
    if isinstance(data, list):
        return data
    return [data]


def _parse_csv(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]
