"""Pydantic schemas for AI blueprint endpoints.

All schemas enforce extra='forbid' to reject unknown fields.
Includes both request schemas and Gemini response validation schemas.
"""

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────


class RecommendationsRequest(BaseModel):
    """Request body for AI recommendations."""

    model_config = ConfigDict(extra="forbid")

    score: float = Field(default=0, ge=0, le=100)
    transport: str = Field(default="walking", max_length=50)
    food: str = Field(default="vegetarian", max_length=50)
    ac_usage: str = Field(default="none", max_length=50)


class ChatRequest(BaseModel):
    """Request body for AI chat."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=2000)


class WhatsIfRequest(BaseModel):
    """Request body for legacy what-if analysis."""

    model_config = ConfigDict(extra="forbid")

    transport: str = Field(default="walking", max_length=50)
    distance: float = Field(default=0, ge=0, le=100000)
    food_type: str = Field(default="vegetarian", max_length=50)
    ac_usage: str = Field(default="none", max_length=50)
    plastic_waste: float = Field(default=0, ge=0, le=1000)
    scenario_description: str = Field(..., min_length=1, max_length=500)


class FeedbackRequest(BaseModel):
    """Request body for AI feedback submission."""

    model_config = ConfigDict(extra="forbid")

    feedback_type: str = Field(..., pattern="^(like|dislike|suggestion|other)$")
    message: str = Field(..., min_length=1, max_length=1000)


# ── Gemini response validation schemas ────────────────────────────


class GeminiChatResponse(BaseModel):
    """Validated chat response from Gemini."""

    model_config = ConfigDict(extra="forbid")

    response: str = Field(..., description="Conversational text response")
    carbon_reduction_actionable: str = Field(
        ..., description="Actionable tip to reduce carbon footprint"
    )
    estimated_reduction_kg: float = Field(
        ..., description="Estimated carbon reduction in kg CO2e"
    )


class GeminiWhatsIfResponse(BaseModel):
    """Validated what-if response from Gemini."""

    model_config = ConfigDict(extra="forbid")

    estimated_impact: str = Field(..., description="positive, negative, or neutral")
    carbon_saved: float = Field(
        ..., description="Estimated daily carbon saved in kg CO2e"
    )
    comparison: str = Field(
        ..., description="Comparison against current footprint"
    )
    tip: str = Field(..., description="Practical suggestion")
    savings_forecast_30_days: float = Field(
        ..., description="30-day projected savings in kg CO2e"
    )


class GeminiRecommendationsResponse(BaseModel):
    """Validated recommendations response from Gemini."""

    model_config = ConfigDict(extra="forbid")

    tips: list[str] = Field(..., description="List of 3 personalized tips")
    projected_weekly_savings_kg: float = Field(
        ..., description="Estimated weekly savings in kg CO2e"
    )


class GeminiWeeklyReportResponse(BaseModel):
    """Validated weekly report response from Gemini."""

    model_config = ConfigDict(extra="forbid")

    biggest_contributor: str = Field(
        ..., description="Highest emissions category"
    )
    best_improvement: str = Field(
        ..., description="Category where user improved most"
    )
    next_week_goal: str = Field(..., description="Suggested goal for next week")
    summary: str = Field(..., description="Motivational summary")
    carbon_reduction_target_kg: float = Field(
        ..., description="Target reduction in kg CO2e"
    )


class CarbonSavingsForecastResponse(BaseModel):
    """Validated savings forecast response from Gemini."""

    model_config = ConfigDict(extra="forbid")

    current_weekly_footprint_kg: float = Field(
        ..., description="Current weekly footprint in kg CO2e"
    )
    forecast_1_month_kg: float = Field(
        ..., description="Projected monthly savings"
    )
    forecast_3_months_kg: float = Field(
        ..., description="Projected 3-month savings"
    )
    forecast_6_months_kg: float = Field(
        ..., description="Projected 6-month savings"
    )
    motivation_message: str = Field(
        ..., description="Inspirational message"
    )
