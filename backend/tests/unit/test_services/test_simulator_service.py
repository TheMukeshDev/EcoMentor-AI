"""Tests for SimulatorService."""

import pytest
from unittest.mock import MagicMock
from app.services.simulator_service import SimulatorService


@pytest.fixture
def mock_deps():
    """Create mock dependencies for SimulatorService."""
    ai_service = MagicMock()
    carbon_history_repo = MagicMock()
    user_repo = MagicMock()
    return ai_service, carbon_history_repo, user_repo


@pytest.fixture
def service(mock_deps):
    """Create a SimulatorService with mock dependencies."""
    ai, carbon, user = mock_deps
    return SimulatorService(ai, carbon, user)


class TestSimulatorService:
    """Tests for SimulatorService.simulate."""

    def test_simulate_returns_validated_result(self, service, mock_deps):
        """Should return validated result from Gemini."""
        ai, carbon, user = mock_deps
        user.get.return_value = {"level": "Explorer", "diet_type": "mixed", "primary_transport": "car"}
        carbon.find_by_user_and_date_range.return_value = [
            {"carbon_score": 13} for _ in range(7)
        ]
        ai._call_gemini.return_value = {
            "scenario_description": "Stop eating beef entirely",
            "annual_saving_kg": 1400.0,
            "monthly_projection": [{"month": i, "co2e_kg": round(116.7 * i, 2)} for i in range(1, 13)],
            "equivalents": {"trees_planted": 63.6, "km_not_driven": 8187.0, "flights_avoided": 7.0},
            "steps": ["Replace beef with chicken or tofu", "Track meals weekly"],
            "difficulty": 4,
        }
        result = service.simulate("user-1", "I stop eating beef")
        assert result["annual_saving_kg"] == 1400.0
        assert len(result["monthly_projection"]) == 12

    def test_simulate_clamps_hallucinated_savings(self, service, mock_deps):
        """Should clamp annual_saving_kg to 0-3000 range."""
        ai, carbon, user = mock_deps
        user.get.return_value = {}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = {
            "scenario_description": "Test",
            "annual_saving_kg": 5000.0,
            "monthly_projection": [{"month": 1, "co2e_kg": 100}],
            "equivalents": {"trees_planted": 1, "km_not_driven": 1, "flights_avoided": 1},
            "steps": ["Step 1"],
            "difficulty": 5,
        }
        result = service.simulate("user-1", "Test scenario")
        assert result["annual_saving_kg"] <= 3000

    def test_simulate_returns_fallback_on_failure(self, service, mock_deps):
        """Should return fallback when Gemini fails."""
        ai, carbon, user = mock_deps
        user.get.return_value = {}
        carbon.find_by_user_and_date_range.return_value = []
        ai._call_gemini.return_value = None
        result = service.simulate("user-1", "I switch to cycling")
        assert "scenario_description" in result
        assert "annual_saving_kg" in result
        assert len(result["monthly_projection"]) == 12

    def test_compute_equivalents(self, service):
        """Should compute real-world equivalents correctly."""
        equiv = service._compute_equivalents(1000)
        assert equiv["trees_planted"] == round(1000 / 22.0, 1)
        assert equiv["flights_avoided"] == round(1000 / 200.0, 1)

    def test_weekly_avg_uses_global_default(self, service):
        """Should use global average when no history."""
        avg = service._compute_weekly_avg([])
        assert avg == 90.4

    def test_weekly_avg_with_data(self, service):
        """Should compute weekly average from data."""
        history = [{"carbon_score": 10}] * 14
        avg = service._compute_weekly_avg(history)
        assert avg == 70.0
