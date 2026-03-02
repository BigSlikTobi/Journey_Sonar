"""Shared enums and type aliases used across modules."""

from __future__ import annotations

import enum


class NodeType(str, enum.Enum):
    JOURNEY_ROOT = "JOURNEY_ROOT"
    STAGE = "STAGE"
    TOUCHPOINT = "TOUCHPOINT"
    MICRO_ACTION = "MICRO_ACTION"


class SourceType(str, enum.Enum):
    WEBHOOK = "WEBHOOK"
    API_POLL = "API_POLL"
    FILE_UPLOAD = "FILE_UPLOAD"
    SDK_EVENT = "SDK_EVENT"


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class SignalType(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class GoalType(str, enum.Enum):
    CONVERSION_RATE = "CONVERSION_RATE"
    THROUGHPUT = "THROUGHPUT"
    TIME_TO_COMPLETE = "TIME_TO_COMPLETE"
    DROP_OFF_RATE = "DROP_OFF_RATE"
    SATISFACTION_SCORE = "SATISFACTION_SCORE"
    CUSTOM = "CUSTOM"


class TargetDirection(str, enum.Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    BETWEEN = "BETWEEN"


class GoalStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    OFF_TRACK = "OFF_TRACK"
    EXCEEDED = "EXCEEDED"


class GoalPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ScoreType(str, enum.Enum):
    HEALTH = "HEALTH"
    OPPORTUNITY = "OPPORTUNITY"
    URGENCY = "URGENCY"
    COMPOSITE = "COMPOSITE"


class ReportType(str, enum.Enum):
    FOCUS_MAP = "FOCUS_MAP"
    TREND_ANALYSIS = "TREND_ANALYSIS"
    ANOMALY_ALERT = "ANOMALY_ALERT"


class SuggestionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
