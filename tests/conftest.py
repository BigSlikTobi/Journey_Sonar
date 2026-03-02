"""Shared test fixtures for the Customer Journey Mapper test suite."""

from __future__ import annotations

import uuid

import pytest


@pytest.fixture
def workspace_id() -> uuid.UUID:
    """A stable workspace UUID for tests."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_node_payload() -> dict:
    return {
        "name": "Onboarding",
        "type": "STAGE",
        "parent_node_id": None,
        "input_schema": {"event_type": "signup_started"},
        "output_schema": {"user_status": "onboarding"},
        "metadata": {},
        "position": 0,
    }


@pytest.fixture
def sample_raw_event() -> dict:
    return {
        "type": "support_ticket_created",
        "requester": {"email": "alice@example.com"},
        "subject": "Cannot connect database",
        "description": "I'm having trouble getting started with the database setup. The connection keeps timing out and I'm frustrated.",
        "priority": "2",
        "created_at": "2025-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_normalization_rules() -> dict:
    return {
        "field_mappings": {
            "event_type": {"source_path": "$.type", "transform": "lowercase"},
            "actor_id": {"source_path": "$.requester.email"},
            "properties.subject": {"source_path": "$.subject"},
            "properties.body": {"source_path": "$.description"},
            "properties.priority": {
                "source_path": "$.priority",
                "transform": "map",
                "map": {"1": "urgent", "2": "high", "3": "normal", "4": "low"},
            },
            "occurred_at": {"source_path": "$.created_at", "transform": "iso_datetime"},
        }
    }
