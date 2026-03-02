"""Unit tests for Sonar scoring algorithms."""

from app.common.types import GoalPriority, GoalStatus
from app.sonar.scoring import (
    compute_composite_score,
    compute_health_score,
    compute_opportunity_score,
    compute_urgency_score,
)


class TestHealthScore:
    def test_all_positive(self):
        score, _ = compute_health_score(100, 0, 0)
        assert score == 100.0

    def test_all_negative(self):
        score, _ = compute_health_score(0, 100, 0)
        assert score == 0.0

    def test_balanced(self):
        score, _ = compute_health_score(50, 50, 0)
        assert score == 50.0

    def test_no_data(self):
        score, comp = compute_health_score(0, 0, 0)
        assert score == 50.0
        assert comp["note"] == "no data"

    def test_mostly_positive(self):
        score, _ = compute_health_score(80, 20, 0)
        assert score == 80.0


class TestOpportunityScore:
    def test_no_goals(self):
        score, comp = compute_opportunity_score([])
        assert score == 0.0
        assert comp["goal_count"] == 0

    def test_single_critical_goal(self):
        gaps = [{"gap_percentage": 50, "priority": GoalPriority.CRITICAL, "goal_id": "g1"}]
        score, _ = compute_opportunity_score(gaps)
        # 50 * 4 (critical weight) / 1 goal = 200 -> capped at 100
        assert score == 100.0

    def test_single_low_priority_goal(self):
        gaps = [{"gap_percentage": 10, "priority": GoalPriority.LOW, "goal_id": "g1"}]
        score, _ = compute_opportunity_score(gaps)
        # 10 * 1 / 1 = 10
        assert score == 10.0


class TestUrgencyScore:
    def test_no_factors(self):
        score, _ = compute_urgency_score([], 0, 0, 0)
        assert score == 0.0

    def test_off_track_critical_goal(self):
        gaps = [{"status": GoalStatus.OFF_TRACK, "priority": GoalPriority.CRITICAL}]
        score, _ = compute_urgency_score(gaps, 0, 0, 0)
        assert score == 100.0  # 80 + 4*5 = 100

    def test_negative_acceleration(self):
        score, comp = compute_urgency_score([], 3.0, 1.0, 0)
        assert score == 70.0
        assert comp["negative_acceleration"] is True

    def test_cascading_impact(self):
        score, comp = compute_urgency_score([], 0, 0, 10)
        # 50 + min(30, 10*2) = 50 + 20 = 70
        assert score == 70.0


class TestCompositeScore:
    def test_healthy_no_opportunity(self):
        score, _ = compute_composite_score(100.0, 0.0, 0.0)
        # 0.35*(100-100) + 0.40*0 + 0.25*0 = 0
        assert score == 0.0

    def test_unhealthy_high_opportunity_urgent(self):
        score, _ = compute_composite_score(0.0, 100.0, 100.0)
        # 0.35*100 + 0.40*100 + 0.25*100 = 100
        assert score == 100.0

    def test_moderate_situation(self):
        score, _ = compute_composite_score(50.0, 50.0, 50.0)
        # 0.35*50 + 0.40*50 + 0.25*50 = 17.5 + 20 + 12.5 = 50
        assert score == 50.0
