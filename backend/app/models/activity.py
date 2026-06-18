from dataclasses import dataclass
from typing import Optional


@dataclass
class Activity:
    id: str
    uid: str
    date: str
    transport: str
    distance: float
    ac_usage: str
    food_type: str
    plastic_waste: float
    carbon_score: float
    created_at: Optional[str] = None
