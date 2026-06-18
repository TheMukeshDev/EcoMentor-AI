"""Tests for data models."""

import pytest


class TestModels:
    """Tests for dataclass models."""

    def test_user_defaults(self):
        """Should create User with default values."""
        from app.models.user import User
        u = User(uid="u1", email="a@b.com", name="Alice")
        assert u.uid == "u1"
        assert u.points == 0
        assert u.streak == 0
        assert u.level == "Beginner"
        assert u.badge == "Seedling"
        assert u.created_at is None

    def test_user_custom_values(self):
        """Should accept custom values."""
        from app.models.user import User
        u = User(uid="u2", email="b@c.com", name="Bob", points=100, streak=5, level="Explorer")
        assert u.points == 100
        assert u.streak == 5

    def test_activity_creation(self):
        """Should create Activity with all fields."""
        from app.models.activity import Activity
        a = Activity(
            id="a1", uid="u1", date="2026-01-01", transport="car",
            distance=10.0, ac_usage="high", food_type="mixed",
            plastic_waste=0.5, carbon_score=15.0,
        )
        assert a.carbon_score == 15.0
        assert a.created_at is None

    def test_carbon_history_defaults(self):
        """Should create CarbonHistory with category defaults."""
        from app.models.carbon_history import CarbonHistory
        ch = CarbonHistory(uid="u1", date="2026-01-01", carbon_score=20.0)
        assert ch.transport == 0.0
        assert ch.electricity == 0.0
        assert ch.food == 0.0
        assert ch.waste == 0.0

    def test_footprint_creation(self):
        """Should create Footprint."""
        from app.models.footprint import Footprint
        f = Footprint(user_id="u1", period="2026-06", total_kg=10.0, categories={"transport": 5.0})
        assert f.user_id == "u1"
        assert f.total_kg == 10.0

    def test_recommendation_creation(self):
        """Should create Recommendation."""
        from app.models.recommendation import Recommendation
        r = Recommendation(
            id="r1", user_id="u1", category="transport", title="Walk more",
            description="Walking saves carbon", potential_saving_kg=5.0, difficulty="easy"
        )
        assert r.category == "transport"

    def test_challenge_creation(self):
        """Should create Challenge."""
        from app.models.challenge import Challenge
        c = Challenge(id="c1", uid="u1", title="Green Week", reward=100)
        assert c.title == "Green Week"
        assert c.reward == 100

    def test_report_creation(self):
        """Should create Report."""
        from app.models.report import Report
        r = Report(
            id="r1", uid="u1", period="2026-06", total_carbon=50.0,
            transport_avg=20.0, electricity_avg=15.0, food_avg=10.0, waste_avg=5.0
        )
        assert r.total_carbon == 50.0

    def test_leaderboard_entry_creation(self):
        """Should create LeaderboardEntry."""
        from app.models.leaderboard_entry import LeaderboardEntry
        le = LeaderboardEntry(uid="u1", name="Alice", points=100, streak=5, level="Beginner", badge="Seedling")
        assert le.points == 100

    def test_ai_report_creation(self):
        """Should create AIReport."""
        from app.models.ai_report import AIReport
        ar = AIReport(uid="u1", type="weekly", content={"key": "val"}, generated_at="now", expires_at="later")
        assert ar.type == "weekly"

    def test_models_init_imports(self):
        """Should import all models from __init__."""
        from app.models import (
            User, Activity, Footprint, Recommendation,
            Challenge, Report, LeaderboardEntry, AIReport,
        )
        assert User is not None
        assert Activity is not None
