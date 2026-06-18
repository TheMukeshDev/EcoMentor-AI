"""Pydantic schemas for AI feature requests and responses.

Covers all 5 core AI features: Coach, Report, Simulator, Habit, Forecast.
Every schema enforces extra='forbid' to reject unknown fields.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Coach ──────────────────────────────────────────────────────────


class CoachAction(BaseModel):
    """A single action in a carbon reduction plan."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., max_length=200)
    estimated_saving_kg: float = Field(..., ge=0, le=500)
    difficulty: int = Field(..., ge=1, le=5)
    habit_days: int = Field(..., ge=1, le=90)


class CoachWeekPlan(BaseModel):
    """One week's reduction goal within a coach plan."""

    model_config = ConfigDict(extra="forbid")

    week: int = Field(..., ge=1, le=12)
    goal_kg: float = Field(..., ge=0, le=500)
    actions: list[str] = Field(..., max_length=5)


class CoachResponse(BaseModel):
    """Validated response from the Carbon Coach AI feature."""

    model_config = ConfigDict(extra="forbid")

    top_3_categories: list[str] = Field(..., min_length=1, max_length=5)
    reduction_plan: list[CoachWeekPlan] = Field(..., min_length=1, max_length=12)


# ── Weekly Report ──────────────────────────────────────────────────


class ReportOpportunity(BaseModel):
    """An identified opportunity for carbon reduction."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., max_length=200)
    saving_kg: float = Field(..., ge=0, le=500)


class ReportChallenge(BaseModel):
    """A challenge proposed in the weekly report."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=300)
    target_saving_kg: float = Field(..., ge=0, le=500)


class WeeklyReportPeriod(BaseModel):
    """Date range for the weekly report."""

    model_config = ConfigDict(extra="forbid")

    start: str = Field(..., max_length=20)
    end: str = Field(..., max_length=20)


class WeeklyReportResponse(BaseModel):
    """Validated response for the Weekly Sustainability Report."""

    model_config = ConfigDict(extra="forbid")

    period: WeeklyReportPeriod
    total_co2e_kg: float = Field(..., ge=0)
    vs_last_week_pct: float = Field(...)
    vs_global_avg_pct: float = Field(...)
    biggest_win: str = Field(..., max_length=200)
    top_opportunity: ReportOpportunity
    challenge: ReportChallenge
    streak_days: int = Field(..., ge=0)


# ── What-If Simulator ─────────────────────────────────────────────


class SimulatorRequest(BaseModel):
    """Request body for the What-If Simulator."""

    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(..., min_length=3, max_length=500)


class SimulatorMonthProjection(BaseModel):
    """Monthly CO2 projection in a what-if scenario."""

    model_config = ConfigDict(extra="forbid")

    month: int = Field(..., ge=1, le=12)
    co2e_kg: float = Field(..., ge=0)


class SimulatorEquivalents(BaseModel):
    """Real-world equivalents for carbon savings."""

    model_config = ConfigDict(extra="forbid")

    trees_planted: float = Field(..., ge=0)
    km_not_driven: float = Field(..., ge=0)
    flights_avoided: float = Field(..., ge=0)


class SimulatorResponse(BaseModel):
    """Validated response from the What-If Simulator."""

    model_config = ConfigDict(extra="forbid")

    scenario_description: str = Field(..., max_length=500)
    annual_saving_kg: float = Field(..., ge=0, le=3000)
    monthly_projection: list[SimulatorMonthProjection] = Field(
        ..., min_length=1, max_length=12
    )
    equivalents: SimulatorEquivalents
    steps: list[str] = Field(..., min_length=1, max_length=10)
    difficulty: int = Field(..., ge=1, le=10)


# ── Habit Engine ───────────────────────────────────────────────────


class HabitCard(BaseModel):
    """A single habit suggestion card."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=300)
    category: str = Field(..., max_length=50)
    impact_kg_per_month: float = Field(..., ge=0, le=500)
    difficulty: int = Field(..., ge=1, le=5)
    days_to_form: int = Field(..., ge=7, le=90)
    tracking_metric: str = Field(..., max_length=100)


class HabitResponse(BaseModel):
    """Validated response from the Habit Engine."""

    model_config = ConfigDict(extra="forbid")

    habits: list[HabitCard] = Field(..., min_length=1, max_length=5)


# ── Carbon Forecast ───────────────────────────────────────────────


class ForecastRequest(BaseModel):
    """Query parameters for the forecast endpoint."""

    model_config = ConfigDict(extra="forbid")

    days: int = Field(default=30, ge=7, le=90)


class ForecastTopLever(BaseModel):
    """The single best lever for reducing future emissions."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., max_length=200)
    projected_saving_kg: float = Field(..., ge=0)


class ForecastResponse(BaseModel):
    """Validated response from the Carbon Forecast."""

    model_config = ConfigDict(extra="forbid")

    forecast_days: int = Field(..., ge=7, le=90)
    predicted_total_kg: float = Field(..., ge=0)
    vs_personal_target_kg: float = Field(...)
    trend: Literal["improving", "stable", "worsening"]
    confidence_low: float = Field(..., ge=0)
    confidence_high: float = Field(...)
    top_lever: ForecastTopLever
