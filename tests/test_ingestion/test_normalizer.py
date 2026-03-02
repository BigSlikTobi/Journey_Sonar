"""Unit tests for the data normalization engine."""

from app.ingestion.normalizer import build_normalized_fields, normalize_payload


class TestNormalizer:
    def test_basic_field_mapping(self, sample_raw_event, sample_normalization_rules):
        result = normalize_payload(sample_raw_event, sample_normalization_rules)
        assert result["event_type"] == "support_ticket_created"
        assert result["actor_id"] == "alice@example.com"
        assert result["properties.subject"] == "Cannot connect database"

    def test_transform_map(self, sample_raw_event, sample_normalization_rules):
        result = normalize_payload(sample_raw_event, sample_normalization_rules)
        assert result["properties.priority"] == "high"

    def test_build_normalized_fields(self, sample_raw_event, sample_normalization_rules):
        fields = build_normalized_fields(sample_raw_event, sample_normalization_rules)
        assert fields["event_type"] == "support_ticket_created"
        assert fields["actor_id"] == "alice@example.com"
        assert "subject" in fields["properties"]
        assert "body" in fields["properties"]
        assert fields["properties"]["priority"] == "high"

    def test_empty_rules(self):
        fields = build_normalized_fields({"key": "value"}, {})
        assert fields["event_type"] == "unknown"
        assert fields["properties"] == {}

    def test_missing_source_path(self):
        rules = {
            "field_mappings": {
                "event_type": {"source_path": "$.nonexistent"},
            }
        }
        fields = build_normalized_fields({"key": "value"}, rules)
        assert fields["event_type"] == "unknown"
