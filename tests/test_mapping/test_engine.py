"""Unit tests for the mapping rule evaluation engine."""

from app.mapping.engine import evaluate_rule


class TestEvaluateRule:
    def test_match_all_passes(self):
        conditions = {
            "match_all": [
                {"field": "event_type", "operator": "equals", "value": "ticket_created"},
                {"field": "properties.priority", "operator": "in", "value": ["urgent", "high"]},
            ]
        }
        event = {"event_type": "ticket_created", "properties": {"priority": "high"}}
        assert evaluate_rule(conditions, event) is True

    def test_match_all_fails(self):
        conditions = {
            "match_all": [
                {"field": "event_type", "operator": "equals", "value": "ticket_created"},
                {"field": "properties.priority", "operator": "equals", "value": "urgent"},
            ]
        }
        event = {"event_type": "ticket_created", "properties": {"priority": "low"}}
        assert evaluate_rule(conditions, event) is False

    def test_match_any(self):
        conditions = {
            "match_any": [
                {"field": "classification.intent", "operator": "equals", "value": "billing"},
                {"field": "classification.intent", "operator": "equals", "value": "onboarding"},
            ]
        }
        event = {"classification": {"intent": "onboarding"}}
        assert evaluate_rule(conditions, event) is True

    def test_match_any_none_match(self):
        conditions = {
            "match_any": [
                {"field": "classification.intent", "operator": "equals", "value": "billing"},
            ]
        }
        event = {"classification": {"intent": "onboarding"}}
        assert evaluate_rule(conditions, event) is False

    def test_combined_match_all_and_any(self):
        conditions = {
            "match_all": [
                {"field": "event_type", "operator": "equals", "value": "ticket"},
            ],
            "match_any": [
                {"field": "properties.tags", "operator": "contains", "value": "billing"},
                {"field": "properties.tags", "operator": "contains", "value": "payment"},
            ],
        }
        event = {"event_type": "ticket", "properties": {"tags": ["billing", "support"]}}
        assert evaluate_rule(conditions, event) is True

    def test_exists_operator(self):
        conditions = {"match_all": [{"field": "actor_id", "operator": "exists"}]}
        assert evaluate_rule(conditions, {"actor_id": "user@test.com"}) is True
        assert evaluate_rule(conditions, {"other": "value"}) is False

    def test_regex_operator(self):
        conditions = {
            "match_all": [
                {"field": "properties.url", "operator": "regex", "value": r"/signup.*"}
            ]
        }
        event = {"properties": {"url": "/signup/step-2"}}
        assert evaluate_rule(conditions, event) is True

    def test_empty_conditions(self):
        assert evaluate_rule({}, {"anything": "data"}) is True
