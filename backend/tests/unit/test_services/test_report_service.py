"""Tests for ReportService."""

import pytest
from unittest.mock import MagicMock
from app.services.report_service import ReportService


@pytest.fixture
def mock_deps():
    """Create mock dependencies for ReportService."""
    ai_service = MagicMock()
    carbon_history_repo = MagicMock()
    user_repo = MagicMock()
    cache_service = MagicMock()
    return ai_service, carbon_history_repo, user_repo, cache_service


@pytest.fixture
def service(mock_deps):
    """Create a ReportService with mock dependencies."""
    ai, carbon, user, cache = mock_deps
    return ReportService(ai, carbon, user, cache)


class TestReportService:
    """Tests for ReportService.generate_report."""

    def test_returns_cached_report(self, service, mock_deps):
        """Should return cached report if available."""
        _, _, _, cache = mock_deps
        cache.get.return_value = {"total_co2e_kg": 42.0}
        result = service.generate_report("user-1")
        assert result["total_co2e_kg"] == 42.0

    def test_generates_report_on_cache_miss(self, service, mock_deps):
        """Should call Gemini when cache misses."""
        ai, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {"level": "Explorer", "streak": 7}
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 12, "transport": 5, "electricity": 3, "food": 3, "waste": 1}
        ]
        ai._call_gemini.return_value = {
            "period": {"start": "2026-06-01", "end": "2026-06-07"},
            "total_co2e_kg": 12.0,
            "vs_last_week_pct": -5.0,
            "vs_global_avg_pct": -86.7,
            "biggest_win": "Low transport emissions (5 kg CO2e)",
            "top_opportunity": {"action": "Walk more", "saving_kg": 2.0},
            "challenge": {"title": "Green Week", "description": "Use bus daily", "target_saving_kg": 3.0},
            "streak_days": 7,
        }
        result = service.generate_report("user-1")
        assert result["total_co2e_kg"] == 12.0
        cache.set.assert_called_once()

    def test_returns_fallback_on_gemini_failure(self, service, mock_deps):
        """Should return fallback report when Gemini fails."""
        ai, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = None
        result = service.generate_report("user-1")
        assert "total_co2e_kg" in result
        assert "biggest_win" in result
        assert "challenge" in result

    def test_returns_fallback_on_invalid_response(self, service, mock_deps):
        """Should return fallback when validation fails."""
        ai, carbon, user, cache = mock_deps
        cache.get.return_value = None
        user.get.return_value = {}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = {"bad": "data"}
        result = service.generate_report("user-1")
        assert "period" in result

    def test_category_totals(self, service):
        """Should sum categories correctly."""
        entries = [
            {"transport": 5, "electricity": 3, "food": 2, "waste": 1},
            {"transport": 10, "electricity": 7, "food": 4, "waste": 2},
        ]
        result = service._category_totals(entries)
        assert result["transport"] == 15
        assert result["food"] == 6

    def test_compute_pct_change_positive(self, service):
        """Should compute percentage increase."""
        assert service._compute_pct_change(110, 100) == 10.0

    def test_compute_pct_change_negative(self, service):
        """Should compute percentage decrease."""
        assert service._compute_pct_change(90, 100) == -10.0

    def test_compute_pct_change_zero_previous(self, service):
        """Should return 0.0 when previous is zero."""
        assert service._compute_pct_change(50, 0) == 0.0
