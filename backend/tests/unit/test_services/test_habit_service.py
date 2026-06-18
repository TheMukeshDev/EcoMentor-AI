"""Tests for HabitService."""

import pytest
from unittest.mock import MagicMock
from app.services.habit_service import HabitService


@pytest.fixture
def mock_deps():
    """Create mock dependencies for HabitService."""
    ai_service = MagicMock()
    activity_repo = MagicMock()
    carbon_history_repo = MagicMock()
    user_repo = MagicMock()
    cache_service = MagicMock()
    return ai_service, activity_repo, carbon_history_repo, user_repo, cache_service


@pytest.fixture
def service(mock_deps):
    """Create a HabitService with mock dependencies."""
    ai, activity, carbon, user, cache = mock_deps
    return HabitService(ai, activity, carbon, user, cache)


class TestHabitService:
    """Tests for HabitService.get_habits."""

    def test_returns_cached_result(self, service, mock_deps):
        """Should return cached habits if available."""
        _, _, _, _, cache = mock_deps
        cache.get.return_value = {"habits": [{"title": "Test"}]}
        result = service.get_habits("user-1")
        assert result["habits"][0]["title"] == "Test"

    def test_applies_car_rule(self, service, mock_deps):
        """Should trigger car rule when > 5 car trips."""
        ai, activity, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {"level": "Beginner", "streak": 0}
        activity.find_by_user_and_date_range.return_value = [
            {"transport": "car"} for _ in range(8)
        ]
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 10, "electricity": 5}
        ]
        ai._call_gemini.return_value = None  # Force fallback
        result = service.get_habits("user-1")
        assert any("transit" in h.get("title", "").lower() or "transit" in h.get("description", "").lower()
                    for h in result["habits"])

    def test_applies_beef_rule(self, service, mock_deps):
        """Should trigger beef rule when > 3 non-veg meals."""
        ai, activity, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        activity.find_by_user_and_date_range.return_value = [
            {"food_type": "non_vegetarian"} for _ in range(5)
        ]
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = None
        result = service.get_habits("user-1")
        assert any("plant" in h.get("title", "").lower() or "plant" in h.get("description", "").lower()
                    for h in result["habits"])

    def test_applies_electricity_rule(self, service, mock_deps):
        """Should trigger electricity rule when > 300 kWh/month."""
        ai, activity, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        activity.find_by_user_and_date_range.return_value = []
        # 80 kWh/week * 4 = 320 kWh/month
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 10, "electricity": 80}
        ]
        ai._call_gemini.return_value = None
        result = service.get_habits("user-1")
        assert any("energy" in h.get("title", "").lower() or "energy" in h.get("description", "").lower()
                    for h in result["habits"])

    def test_returns_defaults_when_no_rules_match(self, service, mock_deps):
        """Should return default habits when no rules trigger."""
        ai, activity, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        activity.find_by_user_and_date_range.return_value = []
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = None
        result = service.get_habits("user-1")
        assert "habits" in result
        assert len(result["habits"]) >= 1

    def test_caches_result(self, service, mock_deps):
        """Should cache the generated habits."""
        ai, activity, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        activity.find_by_user_and_date_range.return_value = []
        carbon.find_by_user_and_date_range.return_value = []
        service.get_habits("user-1")
        cache.set.assert_called_once()

    def test_personalize_with_ai_success(self, service, mock_deps):
        """Should enhance rule habits with Gemini personalization."""
        ai, activity, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {"level": "Explorer", "streak": 10}
        activity.find_by_user_and_date_range.return_value = [
            {"transport": "car"} for _ in range(8)
        ]
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 15, "electricity": 10}
        ]
        ai._call_gemini.return_value = {
            "habits": [
                {
                    "title": "Green Commute",
                    "description": "Take the bus instead of driving (save ~1 kg CO2e/trip)",
                    "category": "transport",
                    "impact_kg_per_month": 20.0,
                    "difficulty": 2,
                    "days_to_form": 21,
                    "tracking_metric": "bus trips per week",
                }
            ]
        }
        result = service.get_habits("user-1")
        assert result["habits"][0]["title"] == "Green Commute"

    def test_count_transport(self, service):
        """Should count specific transport types."""
        activities = [{"transport": "car"}, {"transport": "bus"}, {"transport": "car"}]
        assert service._count_transport(activities, "car") == 2

    def test_count_food(self, service):
        """Should count specific food types."""
        activities = [{"food_type": "vegetarian"}, {"food_type": "non_vegetarian"}]
        assert service._count_food(activities, "non_vegetarian") == 1

    def test_weekly_avg_empty(self, service):
        """Should return 0.0 for empty history."""
        assert service._weekly_avg([]) == 0.0
