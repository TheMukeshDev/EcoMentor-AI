from pydantic import BaseModel, Field


class RecommendationsRequest(BaseModel):
    score: float = Field(default=0, ge=0, le=100)
    transport: str = Field(default="walking", max_length=50)
    food: str = Field(default="vegetarian", max_length=50)
    ac_usage: str = Field(default="none", max_length=50)
