"""Tests for ForecastService."""

import pytest
from unittest.mock import MagicMock
from app.services.forecast_service import ForecastService


@pytest.fixture
def mock_deps():
    """Create mock dependencies for ForecastService."""
    carbon_history_repo = MagicMock()
    user_repo = MagicMock()
    return carbon_history_repo, user_repo


@pytest.fixture
def service(mock_deps):
    """Create a ForecastService with mock dependencies."""
    carbon, user = mock_deps
    return ForecastService(carbon, user)


class TestForecastService:
    """Tests for ForecastService.get_forecast."""

    def test_insufficient_data_response(self, service, mock_deps):
        """Should return default response with < 3 data points."""
        carbon, user = mock_deps
        carbon.find_by_user_and_date_range.return_value = [{"carbon_score": 10}]
        user.get.return_value = {}
        result = service.get_forecast("user-1", 30)
        assert result["forecast_days"] == 30
        assert result["trend"] == "stable"
        assert "Log at least 3 days" in result["top_lever"]["action"]

    def test_valid_forecast_with_data(self, service, mock_deps):
        """Should compute valid forecast with enough data."""
        carbon, user = mock_deps
        # Declining trend: 20, 18, 16, 14, 12, 10
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 20 - i * 2, "transport": 10, "electricity": 5, "food": 3, "waste": 2}
            for i in range(6)
        ]
        user.get.return_value = {"level": "Explorer"}
        result = service.get_forecast("user-1", 30)
        assert result["forecast_days"] == 30
        assert "predicted_total_kg" in result
        assert result["trend"] == "improving"

    def test_clamps_days_to_valid_range(self, service, mock_deps):
        """Should clamp forecast days between 7 and 90."""
        carbon, user = mock_deps
        carbon.find_by_user_and_date_range.return_value = [{"carbon_score": 10}]
        user.get.return_value = {}
        result = service.get_forecast("user-1", 3)
        assert result["forecast_days"] == 7

    def test_clamps_days_max(self, service, mock_deps):
        """Should clamp forecast days to max 90."""
        carbon, user = mock_deps
        carbon.find_by_user_and_date_range.return_value = [{"carbon_score": 10}]
        user.get.return_value = {}
        result = service.get_forecast("user-1", 200)
        assert result["forecast_days"] == 90

    def test_linear_regression_constant(self, service):
        """Should return slope 0 for constant data."""
        slope, intercept = service._linear_regression([5, 5, 5, 5])
        assert slope == 0.0
        assert intercept == 5.0

    def test_linear_regression_increasing(self, service):
        """Should return positive slope for increasing data."""
        slope, _ = service._linear_regression([1, 2, 3, 4, 5])
        assert slope > 0

    def test_linear_regression_decreasing(self, service):
        """Should return negative slope for decreasing data."""
        slope, _ = service._linear_regression([10, 8, 6, 4, 2])
        assert slope < 0

    def test_linear_regression_empty(self, service):
        """Should handle empty list."""
        slope, intercept = service._linear_regression([])
        assert slope == 0.0
        assert intercept == 0.0

    def test_determine_trend_improving(self, service):
        """Should classify negative slope as improving."""
        assert service._determine_trend(-0.1) == "improving"

    def test_determine_trend_stable(self, service):
        """Should classify near-zero slope as stable."""
        assert service._determine_trend(0.01) == "stable"
        assert service._determine_trend(-0.03) == "stable"

    def test_determine_trend_worsening(self, service):
        """Should classify positive slope as worsening."""
        assert service._determine_trend(0.2) == "worsening"

    def test_identify_top_lever_empty(self, service):
        """Should return default lever for no history."""
        result = service._identify_top_lever([])
        assert result["projected_saving_kg"] == 0.0

    def test_identify_top_lever_with_data(self, service):
        """Should identify worst category as top lever."""
        history = [{"transport": 20, "electricity": 5, "food": 3, "waste": 1}]
        result = service._identify_top_lever(history)
        assert "transport" in result["action"].lower() or "car" in result["action"].lower()
        assert result["projected_saving_kg"] > 0

    def test_confidence_interval_single_value(self, service):
        """Should use 20% margin for single value."""
        low, high = service._confidence_interval([10], 100)
        assert low == 80.0
        assert high == 120.0

    def test_predict_positive(self, service):
        """Should predict positive totals."""
        result = service._predict(0.5, 10, 5, 10)
        assert result > 0

    def test_predict_clamped_to_zero(self, service):
        """Daily values should be clamped to >= 0."""
        result = service._predict(-100, 10, 0, 5)
        assert result >= 0
