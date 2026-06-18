"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.ai_schemas import (
    CoachResponse,
    WeeklyReportResponse,
    SimulatorRequest,
    SimulatorResponse,
    HabitResponse,
    ForecastResponse,
)


class TestCoachResponseSchema:
    """Tests for CoachResponse schema validation."""

    def test_valid_response(self):
        """Should accept valid coaching plan."""
        data = {
            "top_3_categories": ["transport", "food", "electricity"],
            "reduction_plan": [
                {"week": 1, "goal_kg": 5.0, "actions": ["Walk to work"]},
            ],
        }
        validated = CoachResponse(**data)
        assert len(validated.top_3_categories) == 3

    def test_rejects_extra_fields(self):
        """Should reject unknown fields with extra='forbid'."""
        data = {
            "top_3_categories": ["transport"],
            "reduction_plan": [{"week": 1, "goal_kg": 5.0, "actions": ["x"]}],
            "unknown_field": "hack",
        }
        with pytest.raises(ValidationError):
            CoachResponse(**data)

    def test_rejects_empty_categories(self):
        """Should reject empty top_3_categories list."""
        data = {
            "top_3_categories": [],
            "reduction_plan": [{"week": 1, "goal_kg": 5.0, "actions": ["x"]}],
        }
        with pytest.raises(ValidationError):
            CoachResponse(**data)


class TestSimulatorRequestSchema:
    """Tests for SimulatorRequest schema validation."""

    def test_valid_request(self):
        """Should accept valid scenario."""
        data = {"scenario": "I bike to work every day"}
        validated = SimulatorRequest(**data)
        assert validated.scenario == "I bike to work every day"

    def test_rejects_short_scenario(self):
        """Should reject scenarios shorter than 3 chars."""
        with pytest.raises(ValidationError):
            SimulatorRequest(scenario="ab")

    def test_rejects_extra_fields(self):
        """Should reject unknown fields."""
        with pytest.raises(ValidationError):
            SimulatorRequest(scenario="valid", inject="malicious")


class TestSimulatorResponseSchema:
    """Tests for SimulatorResponse schema validation."""

    def test_valid_response(self):
        """Should accept valid simulator response."""
        data = {
            "scenario_description": "Biking to work",
            "annual_saving_kg": 500.0,
            "monthly_projection": [{"month": i, "co2e_kg": i * 40.0} for i in range(1, 13)],
            "equivalents": {"trees_planted": 22.7, "km_not_driven": 2924, "flights_avoided": 2.5},
            "steps": ["Buy a bike", "Plan route"],
            "difficulty": 4,
        }
        validated = SimulatorResponse(**data)
        assert validated.annual_saving_kg == 500.0

    def test_rejects_negative_savings(self):
        """Should reject negative annual_saving_kg."""
        data = {
            "scenario_description": "Bad scenario",
            "annual_saving_kg": -100.0,
            "monthly_projection": [{"month": 1, "co2e_kg": 0}],
            "equivalents": {"trees_planted": 0, "km_not_driven": 0, "flights_avoided": 0},
            "steps": ["step"],
            "difficulty": 1,
        }
        with pytest.raises(ValidationError):
            SimulatorResponse(**data)

    def test_rejects_excessive_savings(self):
        """Should reject annual_saving_kg > 3000."""
        data = {
            "scenario_description": "Impossible scenario",
            "annual_saving_kg": 5000.0,
            "monthly_projection": [{"month": 1, "co2e_kg": 0}],
            "equivalents": {"trees_planted": 0, "km_not_driven": 0, "flights_avoided": 0},
            "steps": ["step"],
            "difficulty": 1,
        }
        with pytest.raises(ValidationError):
            SimulatorResponse(**data)


class TestHabitResponseSchema:
    """Tests for HabitResponse schema validation."""

    def test_valid_response(self):
        """Should accept valid habit cards."""
        data = {
            "habits": [
                {
                    "title": "Plant-Based Meals",
                    "description": "Replace 3 meals per week",
                    "category": "food",
                    "impact_kg_per_month": 36.0,
                    "difficulty": 3,
                    "days_to_form": 21,
                    "tracking_metric": "meals per week",
                }
            ]
        }
        validated = HabitResponse(**data)
        assert len(validated.habits) == 1

    def test_rejects_empty_habits(self):
        """Should reject empty habits list."""
        with pytest.raises(ValidationError):
            HabitResponse(habits=[])


class TestForecastResponseSchema:
    """Tests for ForecastResponse schema validation."""

    def test_valid_response(self):
        """Should accept valid forecast."""
        data = {
            "forecast_days": 30,
            "predicted_total_kg": 300.0,
            "vs_personal_target_kg": -10.0,
            "trend": "improving",
            "confidence_low": 250.0,
            "confidence_high": 350.0,
            "top_lever": {
                "action": "Use public transport",
                "projected_saving_kg": 20.0,
            },
        }
        validated = ForecastResponse(**data)
        assert validated.trend == "improving"

    def test_rejects_invalid_trend(self):
        """Should reject invalid trend values."""
        data = {
            "forecast_days": 30,
            "predicted_total_kg": 300.0,
            "vs_personal_target_kg": -10.0,
            "trend": "unknown_trend",
            "confidence_low": 250.0,
            "confidence_high": 350.0,
            "top_lever": {"action": "test", "projected_saving_kg": 0.0},
        }
        with pytest.raises(ValidationError):
            ForecastResponse(**data)
