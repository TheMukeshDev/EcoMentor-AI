from dataclasses import dataclass
from typing import Optional


@dataclass
class CarbonHistory:
    uid: str
    date: str
    carbon_score: float
    transport: float = 0.0
    electricity: float = 0.0
    food: float = 0.0
    waste: float = 0.0
    activity_count: int = 0
    created_at: Optional[str] = None
