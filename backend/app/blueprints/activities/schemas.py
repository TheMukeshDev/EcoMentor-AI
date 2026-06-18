"""Pydantic schemas for activity endpoints.

All schemas enforce extra='forbid' to reject unknown fields.
"""

from pydantic import BaseModel, ConfigDict, Field


class LogActivityRequest(BaseModel):
    """Request body for logging a new activity."""

    model_config = ConfigDict(extra="forbid")

    date: str | None = Field(None, max_length=20)
    transport: str = Field(
        ..., pattern="^(walking|bicycle|metro|bus|bike|car|plane)$"
    )
    distance: float = Field(..., ge=0, le=10000)
    ac_usage: str = Field(..., pattern="^(none|1-2|3-5|6\\+)$")
    food_type: str = Field(
        ..., pattern="^(vegan|vegetarian|non_vegetarian)$"
    )
    plastic_waste: float = Field(..., ge=0, le=1000)
