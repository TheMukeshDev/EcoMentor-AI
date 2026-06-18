"""Tests for CoachService."""

import pytest
from unittest.mock import MagicMock, patch
from app.services.coach_service import CoachService


@pytest.fixture
def mock_deps():
    """Create mock dependencies for CoachService."""
    ai_service = MagicMock()
    carbon_history_repo = MagicMock()
    activity_repo = MagicMock()
    user_repo = MagicMock()
    cache_service = MagicMock()
    return ai_service, carbon_history_repo, activity_repo, user_repo, cache_service


@pytest.fixture
def service(mock_deps):
    """Create a CoachService with mock dependencies."""
    ai, carbon, activity, user, cache = mock_deps
    return CoachService(ai, carbon, activity, user, cache)


class TestCoachService:
    """Tests for CoachService.get_coaching_plan."""

    def test_returns_cached_result(self, service, mock_deps):
        """Should return cached plan if available."""
        _, _, _, _, cache = mock_deps
        cache.get.return_value = {"top_3_categories": ["transport"], "reduction_plan": []}
        result = service.get_coaching_plan("user-1")
        assert result["top_3_categories"] == ["transport"]
        cache.get.assert_called_once_with("user-1", "coach")

    def test_calls_gemini_on_cache_miss(self, service, mock_deps):
        """Should call Gemini when cache misses."""
        ai, carbon, _, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {"level": "Beginner", "streak": 5}
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 10, "transport": 5, "electricity": 2, "food": 2, "waste": 1}
        ]
        ai._call_gemini.return_value = {
            "top_3_categories": ["transport", "electricity", "food"],
            "reduction_plan": [
                {"week": 1, "goal_kg": 5.0, "actions": ["Walk more (save ~2 kg CO2e)"]}
            ],
        }
        result = service.get_coaching_plan("user-1")
        assert "top_3_categories" in result
        ai._call_gemini.assert_called_once()

    def test_returns_fallback_on_gemini_failure(self, service, mock_deps):
        """Should return fallback plan when Gemini fails."""
        ai, carbon, _, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {"level": "Beginner", "streak": 0}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = None
        result = service.get_coaching_plan("user-1")
        assert "top_3_categories" in result
        assert "reduction_plan" in result
        assert len(result["reduction_plan"]) > 0

    def test_returns_fallback_on_validation_error(self, service, mock_deps):
        """Should return fallback when Gemini returns invalid data."""
        ai, carbon, _, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = {"invalid": "data"}
        result = service.get_coaching_plan("user-1")
        assert "top_3_categories" in result

    def test_caches_valid_result(self, service, mock_deps):
        """Should cache valid Gemini response."""
        ai, carbon, _, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = {
            "top_3_categories": ["transport", "food", "electricity"],
            "reduction_plan": [
                {"week": 1, "goal_kg": 3.0, "actions": ["Take bus (save ~1 kg CO2e)"]}
            ],
        }
        service.get_coaching_plan("user-1")
        cache.set.assert_called_once()

    def test_aggregate_categories_with_data(self, service):
        """Should compute category averages correctly."""
        history = [
            {"transport": 10, "electricity": 5, "food": 3, "waste": 1},
            {"transport": 6, "electricity": 4, "food": 2, "waste": 2},
        ]
        result = service._aggregate_categories(history)
        assert result["worst"] == "transport"
        assert result["averages"]["transport"] == 8.0

    def test_aggregate_categories_empty(self, service):
        """Should return defaults for empty history."""
        result = service._aggregate_categories([])
        assert result["worst"] == "transport"

    def test_weekly_avg_empty(self, service):
        """Should return 0.0 for empty history."""
        assert service._weekly_avg([]) == 0.0

    def test_weekly_avg_with_data(self, service):
        """Should compute weekly average correctly."""
        history = [{"carbon_score": 10}] * 7
        result = service._weekly_avg(history)
        assert result == 70.0
