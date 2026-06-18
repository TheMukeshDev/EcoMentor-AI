from pydantic import BaseModel, Field


class RecommendationsRequest(BaseModel):
    score: float = Field(default=0, ge=0, le=100)
    transport: str = Field(default="walking", max_length=50)
    food: str = Field(default="vegetarian", max_length=50)
    ac_usage: str = Field(default="none", max_length=50)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class WhatsIfRequest(BaseModel):
    transport: str = Field(default="walking", max_length=50)
    distance: float = Field(default=0, ge=0)
    food_type: str = Field(default="vegetarian", max_length=50)
    ac_usage: str = Field(default="none", max_length=50)
    plastic_waste: float = Field(default=0, ge=0)
    scenario_description: str = Field(..., min_length=1, max_length=500)


class FeedbackRequest(BaseModel):
    feedback_type: str = Field(..., pattern="^(like|dislike|suggestion|other)$")
    message: str = Field(..., min_length=1, max_length=1000)
